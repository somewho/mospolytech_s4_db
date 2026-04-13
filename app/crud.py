"""
Generic CRUD operations — работает с любой таблицей через SQLAlchemy Core.
"""
from typing import Any
import bcrypt as _bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.meta import TABLES


def _preprocess(table_name: str, data: dict) -> dict:
    """Таблично-специфичная предобработка перед записью."""
    if table_name == "app_user":
        pw = data.get("password_hash")
        if not pw:  # пусто — не меняем пароль при редактировании
            data.pop("password_hash", None)
        elif not str(pw).startswith("$2"):  # не bcrypt-хэш — хешируем
            data["password_hash"] = _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()
    return data


def _table_meta(table_name: str) -> dict:
    if table_name not in TABLES:
        raise ValueError(f"Unknown table: {table_name}")
    return TABLES[table_name]


def _pk_col(table_name: str) -> str | None:
    return TABLES[table_name].get("pk")


def _composite_pk(table_name: str) -> list[str] | None:
    return TABLES[table_name].get("composite_pk")


def list_records(
    db: Session,
    table_name: str,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    search_column: str | None = None,
) -> tuple[list[dict], int]:
    meta = _table_meta(table_name)
    cols = [c["name"] for c in meta["columns"]]
    select_cols = ", ".join(f'"{c}"' for c in cols)

    where_clause = ""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if search and search_column and search_column in cols:
        where_clause = f'WHERE "{search_column}"::text ILIKE :search'
        params["search"] = f"%{search}%"

    count_q = text(f'SELECT COUNT(*) FROM "{table_name}" {where_clause}')
    total = db.execute(count_q, params).scalar() or 0

    rows_q = text(
        f'SELECT {select_cols} FROM "{table_name}" {where_clause} '
        f'ORDER BY 1 LIMIT :limit OFFSET :offset'
    )
    rows = db.execute(rows_q, params).mappings().all()
    return [dict(r) for r in rows], total


def get_record(db: Session, table_name: str, pk_value: Any) -> dict | None:
    meta = _table_meta(table_name)
    pk = _pk_col(table_name)
    if not pk:
        return None
    cols = [c["name"] for c in meta["columns"]]
    select_cols = ", ".join(f'"{c}"' for c in cols)
    q = text(f'SELECT {select_cols} FROM "{table_name}" WHERE "{pk}" = :pk')
    row = db.execute(q, {"pk": pk_value}).mappings().first()
    return dict(row) if row else None


def create_record(db: Session, table_name: str, data: dict) -> dict:
    data = _preprocess(table_name, data)
    meta = _table_meta(table_name)
    # Исключаем readonly-поля и pk с автогенерацией
    writable = [
        c["name"] for c in meta["columns"]
        if not c.get("readonly") and c["name"] != meta.get("pk")
    ]
    keys = [k for k in writable if k in data and data[k] is not None]
    if not keys:
        raise ValueError("No writable fields provided")

    cols_sql = ", ".join(f'"{k}"' for k in keys)
    vals_sql = ", ".join(f":{k}" for k in keys)
    params = {k: data[k] for k in keys}

    pk = _pk_col(table_name)
    comp = _composite_pk(table_name)
    if pk:
        q = text(f'INSERT INTO "{table_name}" ({cols_sql}) VALUES ({vals_sql}) RETURNING *')
        row = db.execute(q, params).mappings().first()
        db.commit()
        return dict(row)
    else:
        # composite PK — no RETURNING needed
        q = text(f'INSERT INTO "{table_name}" ({cols_sql}) VALUES ({vals_sql})')
        db.execute(q, params)
        db.commit()
        # fetch back
        if comp:
            cond = " AND ".join(f'"{c}" = :{c}' for c in comp if c in data)
            sel = text(f'SELECT * FROM "{table_name}" WHERE {cond}')
            row = db.execute(sel, {c: data[c] for c in comp if c in data}).mappings().first()
            return dict(row) if row else {}
        return {}


def update_record(db: Session, table_name: str, pk_value: Any, data: dict) -> dict | None:
    data = _preprocess(table_name, data)
    meta = _table_meta(table_name)
    pk = _pk_col(table_name)
    if not pk:
        return None
    writable = [
        c["name"] for c in meta["columns"]
        if not c.get("readonly") and c["name"] != pk
    ]
    keys = [k for k in writable if k in data and data[k] is not None]
    if not keys:
        return get_record(db, table_name, pk_value)

    set_sql = ", ".join(f'"{k}" = :{k}' for k in keys)
    params = {k: data[k] for k in keys}
    params["__pk"] = pk_value

    q = text(f'UPDATE "{table_name}" SET {set_sql} WHERE "{pk}" = :__pk RETURNING *')
    row = db.execute(q, params).mappings().first()
    db.commit()
    return dict(row) if row else None


def delete_record(db: Session, table_name: str, pk_value: Any) -> bool:
    meta = _table_meta(table_name)
    pk = _pk_col(table_name)
    if not pk:
        return False
    q = text(f'DELETE FROM "{table_name}" WHERE "{pk}" = :pk')
    result = db.execute(q, {"pk": pk_value})
    db.commit()
    return result.rowcount > 0


def delete_composite(db: Session, table_name: str, pk_data: dict) -> bool:
    comp = _composite_pk(table_name)
    if not comp:
        return False
    cond = " AND ".join(f'"{c}" = :{c}' for c in comp)
    q = text(f'DELETE FROM "{table_name}" WHERE {cond}')
    result = db.execute(q, {c: pk_data[c] for c in comp})
    db.commit()
    return result.rowcount > 0


def fk_options(db: Session, ref_table: str, ref_label: str) -> list[dict]:
    """Загрузить варианты для FK-select.
    ref_label может быть составным через '|': 'last_name|first_name'
    → SQL: last_name || ' ' || COALESCE(first_name, '')
    """
    pk = _pk_col(ref_table)
    if not pk:
        return []
    parts = [p.strip() for p in ref_label.split('|')]
    if len(parts) > 1:
        label_sql = " || ' ' || ".join(f'COALESCE("{p}", \'\')' for p in parts)
        label_sql = f"TRIM({label_sql})"
    else:
        label_sql = f'"{parts[0]}"'
    order_col = parts[0]
    q = text(f'SELECT "{pk}", {label_sql} AS lbl FROM "{ref_table}" ORDER BY "{order_col}" LIMIT 2000')
    rows = db.execute(q).fetchall()
    return [{"value": r[0], "label": str(r[1])} for r in rows]
