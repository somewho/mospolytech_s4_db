from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import (
    UserCtx, create_token, get_current_user, hash_password, verify_password,
)
from app.database import get_db

router = APIRouter(prefix="/api/auth")


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    email: str
    password: str


class RegisterBody(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_roles(db: Session, user_id: int) -> list[str]:
    rows = db.execute(text("""
        SELECT r.name FROM role r
        JOIN user_role ur ON r.role_id = ur.role_id
        WHERE ur.user_id = :uid
    """), {"uid": user_id}).fetchall()
    return [r[0] for r in rows]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT user_id, password_hash FROM app_user WHERE email = :e"),
        {"e": body.email},
    ).first()
    if not row or not verify_password(body.password, row[1]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    roles = _user_roles(db, row[0])
    user  = db.execute(
        text("SELECT user_id, first_name, last_name, email, rating FROM app_user WHERE user_id = :uid"),
        {"uid": row[0]},
    ).mappings().first()
    return {
        "access_token": create_token(row[0], roles),
        "user":  dict(user),
        "roles": roles,
        "can_admin": any(r in roles for r in ("admin", "content_editor", "moderator")),
    }


@router.post("/register", status_code=201)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if db.execute(text("SELECT 1 FROM app_user WHERE email = :e"), {"e": body.email}).first():
        raise HTTPException(status_code=409, detail="Email уже зарегистрирован")

    row = db.execute(text("""
        INSERT INTO app_user (first_name, last_name, email, password_hash)
        VALUES (:fn, :ln, :email, :pw)
        RETURNING user_id, first_name, last_name, email
    """), {
        "fn":    body.first_name,
        "ln":    body.last_name,
        "email": body.email,
        "pw":    hash_password(body.password),
    }).mappings().first()
    db.commit()

    # Назначаем роль 'user'
    uid     = row["user_id"]
    role_id = db.execute(text("SELECT role_id FROM role WHERE name = 'user'")).scalar()
    if role_id:
        try:
            db.execute(
                text("INSERT INTO user_role (user_id, role_id) VALUES (:u, :r)"),
                {"u": uid, "r": role_id},
            )
            db.commit()
        except Exception:
            db.rollback()

    roles = _user_roles(db, uid)
    return {
        "access_token": create_token(uid, roles),
        "user":  dict(row),
        "roles": roles,
        "can_admin": False,
    }


@router.get("/me")
def me(
    user: Optional[UserCtx] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return {"user": None, "roles": [], "can_admin": False}

    row = db.execute(
        text("SELECT user_id, first_name, last_name, email, rating FROM app_user WHERE user_id = :uid"),
        {"uid": user.user_id},
    ).mappings().first()
    return {
        "user":      dict(row) if row else None,
        "roles":     user.roles,
        "can_admin": user.can_admin,
    }
