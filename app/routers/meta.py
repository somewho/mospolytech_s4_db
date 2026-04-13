from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.meta import TABLES, GROUP_ORDER
from app import crud

router = APIRouter(prefix="/api/meta")


@router.get("/tables")
def get_tables_meta():
    """Отдаёт список всех таблиц, сгруппированных для sidebar."""
    groups: dict[str, list] = {}
    for name, meta in TABLES.items():
        group = meta["group"]
        groups.setdefault(group, []).append({
            "name": name,
            "label": meta["label"],
        })
    result = []
    for g in GROUP_ORDER:
        if g in groups:
            result.append({"group": g, "tables": groups[g]})
    return result


@router.get("/tables/{table_name}")
def get_table_meta(table_name: str):
    """Полная метаинформация о таблице, включая описание колонок."""
    if table_name not in TABLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return TABLES[table_name]


@router.get("/fk/{table_name}/{label_col}")
def get_fk_options(table_name: str, label_col: str, db: Session = Depends(get_db)):
    """Варианты для FK-select: [{value, label}]."""
    try:
        return crud.fk_options(db, table_name, label_col)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
