from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import UserCtx, require_admin_access
from app.database import get_db
from app.meta import TABLES
from app import crud

router = APIRouter(prefix="/api/tables")

# Все маршруты admin CRUD требуют роли admin / content_editor / moderator
_ADMIN = Depends(require_admin_access)


def _check_table(table_name: str):
    if table_name not in TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")


@router.get("/{table_name}", dependencies=[_ADMIN])
def list_records(
    table_name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: str | None = Query(None),
    search_column: str | None = Query(None),
    db: Session = Depends(get_db),
):
    _check_table(table_name)
    try:
        records, total = crud.list_records(db, table_name, offset, limit, search, search_column)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"data": records, "total": total, "offset": offset, "limit": limit}


@router.get("/{table_name}/{pk_value}", dependencies=[_ADMIN])
def get_record(table_name: str, pk_value: Any, db: Session = Depends(get_db)):
    _check_table(table_name)
    record = crud.get_record(db, table_name, pk_value)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/{table_name}", status_code=201, dependencies=[_ADMIN])
def create_record(table_name: str, body: dict, db: Session = Depends(get_db)):
    _check_table(table_name)
    try:
        record = crud.create_record(db, table_name, body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    return record


@router.put("/{table_name}/{pk_value}", dependencies=[_ADMIN])
def update_record(table_name: str, pk_value: Any, body: dict, db: Session = Depends(get_db)):
    _check_table(table_name)
    try:
        record = crud.update_record(db, table_name, pk_value, body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{table_name}/{pk_value}", dependencies=[_ADMIN])
def delete_record(table_name: str, pk_value: Any, db: Session = Depends(get_db)):
    _check_table(table_name)
    ok = crud.delete_record(db, table_name, pk_value)
    if not ok:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"ok": True}


@router.delete("/{table_name}", dependencies=[_ADMIN])
def delete_composite(table_name: str, body: dict, db: Session = Depends(get_db)):
    _check_table(table_name)
    ok = crud.delete_composite(db, table_name, body)
    if not ok:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"ok": True}
