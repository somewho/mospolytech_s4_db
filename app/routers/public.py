from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import UserCtx, get_current_user, require_auth
from app.database import get_db

router = APIRouter(prefix="/api/public")


# ── Films ─────────────────────────────────────────────────────────────────────

@router.get("/films")
def list_films(
    page:     int            = Query(1,    ge=1),
    limit:    int            = Query(20,   ge=1, le=100),
    genre_id: Optional[int]  = None,
    search:   Optional[str]  = None,
    sort:     str            = Query("rating"),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    where_parts: list[str] = []
    params: dict = {"limit": limit, "offset": offset}

    if search:
        where_parts.append("f.title ILIKE :search")
        params["search"] = f"%{search}%"
    if genre_id:
        where_parts.append(
            "EXISTS (SELECT 1 FROM film_genre fg WHERE fg.film_id = f.film_id AND fg.genre_id = :gid)"
        )
        params["gid"] = genre_id

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    order_sql = {
        "rating": "f.average_rating DESC NULLS LAST",
        "date":   "f.created_date   DESC NULLS LAST",
        "title":  "f.title          ASC",
    }.get(sort, "f.average_rating DESC NULLS LAST")

    total = db.execute(
        text(f"SELECT COUNT(*) FROM film f {where_sql}"), params
    ).scalar() or 0

    rows = db.execute(text(f"""
        SELECT
            f.film_id,
            f.title,
            f.created_date,
            f.age_restriction,
            f.average_rating,
            COALESCE(
              (SELECT STRING_AGG(g.name, ', ' ORDER BY g.name)
               FROM film_genre fg JOIN genre g ON fg.genre_id = g.genre_id
               WHERE fg.film_id = f.film_id
               LIMIT 3),
              ''
            ) AS genres,
            COALESCE(
              (SELECT p.first_name || ' ' || COALESCE(p.last_name, '')
               FROM film_person fp JOIN person p ON fp.person_id = p.person_id
               WHERE fp.film_id = f.film_id AND fp.role = 'director'
               LIMIT 1),
              ''
            ) AS director
        FROM film f {where_sql}
        ORDER BY {order_sql}
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    return {
        "data":        [dict(r) for r in rows],
        "total":       total,
        "page":        page,
        "total_pages": max(1, -(-total // limit)),
    }


@router.get("/films/{film_id}")
def get_film(film_id: int, db: Session = Depends(get_db)):
    film = db.execute(
        text("SELECT * FROM film WHERE film_id = :fid"), {"fid": film_id}
    ).mappings().first()
    if not film:
        raise HTTPException(status_code=404, detail="Фильм не найден")

    genres = db.execute(text("""
        SELECT g.genre_id, g.name FROM genre g
        JOIN film_genre fg ON g.genre_id = fg.genre_id
        WHERE fg.film_id = :fid ORDER BY g.name
    """), {"fid": film_id}).mappings().all()

    persons = db.execute(text("""
        SELECT p.person_id, p.first_name, p.last_name, p.birth_date, fp.role
        FROM person p
        JOIN film_person fp ON p.person_id = fp.person_id
        WHERE fp.film_id = :fid
        ORDER BY fp.role, p.last_name
    """), {"fid": film_id}).mappings().all()

    reviews = db.execute(text("""
        SELECT r.review_id, r.review_text, r.film_rating,
               r.likes_count, r.dislikes_count, r.created_at,
               u.user_id, u.first_name, u.last_name
        FROM review r
        JOIN app_user u ON r.user_id = u.user_id
        WHERE r.film_id = :fid
        ORDER BY r.created_at DESC LIMIT 30
    """), {"fid": film_id}).mappings().all()

    awards = db.execute(text("""
        SELECT a.award_id, a.name, a.year, a.category, a.status,
               fe.name AS festival_name
        FROM award a
        JOIN festival fe ON a.festival_id = fe.festival_id
        WHERE a.film_id = :fid
        ORDER BY a.year DESC
    """), {"fid": film_id}).mappings().all()

    return {
        "film":    dict(film),
        "genres":  [dict(g) for g in genres],
        "persons": [dict(p) for p in persons],
        "reviews": [dict(r) for r in reviews],
        "awards":  [dict(a) for a in awards],
    }


# ── Genres ────────────────────────────────────────────────────────────────────

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT genre_id, name FROM genre ORDER BY name")
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Persons ───────────────────────────────────────────────────────────────────

@router.get("/persons")
def list_persons(
    search: Optional[str] = None,
    role:   Optional[str] = None,
    db: Session = Depends(get_db),
):
    where_parts: list[str] = []
    params: dict = {}
    if search:
        where_parts.append(
            "(p.first_name ILIKE :search OR p.last_name ILIKE :search)"
        )
        params["search"] = f"%{search}%"
    if role:
        where_parts.append(
            "EXISTS (SELECT 1 FROM person_role pr WHERE pr.person_id = p.person_id AND pr.role = :role)"
        )
        params["role"] = role

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    rows = db.execute(text(f"""
        SELECT p.person_id, p.first_name, p.last_name, p.birth_date,
               COALESCE(
                 (SELECT STRING_AGG(pr.role, ', ' ORDER BY pr.role)
                  FROM person_role pr WHERE pr.person_id = p.person_id),
                 ''
               ) AS roles,
               (SELECT COUNT(*)
                FROM film_person fp WHERE fp.person_id = p.person_id) AS film_count
        FROM person p {where_sql}
        ORDER BY p.last_name, p.first_name
        LIMIT 100
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/persons/{person_id}")
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = db.execute(text("""
        SELECT p.*, c.name AS country_name, ci.name AS city_name
        FROM person p
        LEFT JOIN country c  ON p.country_id = c.country_id
        LEFT JOIN city    ci ON p.city_id    = ci.city_id
        WHERE p.person_id = :pid
    """), {"pid": person_id}).mappings().first()
    if not person:
        raise HTTPException(status_code=404, detail="Персона не найдена")

    roles = db.execute(
        text("SELECT role FROM person_role WHERE person_id = :pid"),
        {"pid": person_id},
    ).scalars().all()

    films = db.execute(text("""
        SELECT f.film_id, f.title, f.created_date, f.average_rating, fp.role
        FROM film f
        JOIN film_person fp ON f.film_id = fp.film_id
        WHERE fp.person_id = :pid
        ORDER BY f.created_date DESC
    """), {"pid": person_id}).mappings().all()

    return {
        "person": dict(person),
        "roles":  list(roles),
        "films":  [dict(f) for f in films],
    }


# ── Festivals ─────────────────────────────────────────────────────────────────

@router.get("/festivals")
def list_festivals(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT f.festival_id, f.name, f.founded_year, f.prestige_rating,
               f.description,
               c.name AS country_name,
               (SELECT COUNT(*) FROM award a WHERE a.festival_id = f.festival_id) AS awards_count
        FROM festival f
        LEFT JOIN country c ON f.country_id = c.country_id
        ORDER BY f.prestige_rating DESC NULLS LAST
    """)).mappings().all()
    return [dict(r) for r in rows]


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.post("/reviews", status_code=201)
def create_review(
    body: dict,
    user: UserCtx = Depends(require_auth),
    db: Session = Depends(get_db),
):
    film_id     = body.get("film_id")
    review_text = (body.get("review_text") or "").strip()
    film_rating = body.get("film_rating")

    if not film_id:
        raise HTTPException(status_code=422, detail="film_id обязателен")
    if not review_text:
        raise HTTPException(status_code=422, detail="Текст рецензии не может быть пустым")
    if film_rating is not None:
        film_rating = int(film_rating)
        if not (1 <= film_rating <= 10):
            raise HTTPException(status_code=422, detail="Оценка должна быть от 1 до 10")

    row = db.execute(text("""
        INSERT INTO review (film_id, user_id, review_text, film_rating)
        VALUES (:fid, :uid, :text, :rating)
        RETURNING review_id, film_id, user_id, review_text, film_rating, created_at
    """), {
        "fid":    film_id,
        "uid":    user.user_id,
        "text":   review_text,
        "rating": film_rating,
    }).mappings().first()
    db.commit()
    return dict(row)


# ── Profile: собственные рецензии ─────────────────────────────────────────────

@router.get("/profile/reviews")
def my_reviews(
    user: UserCtx = Depends(require_auth),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT r.review_id, r.film_rating, r.likes_count, r.created_at,
               r.review_text,
               f.film_id, f.title, f.average_rating
        FROM review r
        JOIN film f ON r.film_id = f.film_id
        WHERE r.user_id = :uid
        ORDER BY r.created_at DESC
    """), {"uid": user.user_id}).mappings().all()
    return [dict(r) for r in rows]
