from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)


# ── Password ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_token(user_id: int, roles: list[str]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "roles": roles, "exp": exp},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def _parse_token(token: str) -> Optional["UserCtx"]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return UserCtx(int(payload["sub"]), payload.get("roles", []))
    except Exception:
        return None


# ── User context ──────────────────────────────────────────────────────────────

class UserCtx:
    def __init__(self, user_id: int, roles: list[str]):
        self.user_id = user_id
        self.roles   = roles

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    @property
    def can_admin(self) -> bool:
        return self.has_role("admin", "content_editor", "moderator")

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserCtx]:
    if not creds:
        return None
    return _parse_token(creds.credentials)


async def require_auth(
    user: Optional[UserCtx] = Depends(get_current_user),
) -> UserCtx:
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user


async def require_admin_access(
    user: UserCtx = Depends(require_auth),
) -> UserCtx:
    if not user.can_admin:
        raise HTTPException(status_code=403, detail="Нет прав доступа к панели управления")
    return user
