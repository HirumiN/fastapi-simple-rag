# app/routers/ukm.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas, crud, db
from app.utils.session import get_current_user
from app.utils.embeddings import create_embedding_background

router = APIRouter(prefix="/ukm", tags=["UKM"])

def get_db():
    yield from db.get_db()


@router.get("/", response_model=List[schemas.UKM])
async def list_ukm(request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    return crud.get_ukm(db_session, user_id=user.id_user if user else None)


@router.post("/", response_model=schemas.UKM)
async def create_ukm(ukm: schemas.UKMCreate, background_tasks: BackgroundTasks, request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    if user:
        ukm.id_user = user.id_user
    db_ukm = crud.create_ukm(db_session, ukm)

    text_for_embedding = f"UKM: {db_ukm.nama}. Role: {db_ukm.jabatan}. {db_ukm.deskripsi or ''}"

    background_tasks.add_task(
        create_embedding_background,
        db_ukm.id_user,
        "ukm",
        db_ukm.id_ukm,
        text_for_embedding
    )
    return db_ukm


@router.put("/{ukm_id}", response_model=schemas.UKM)
async def update_ukm(ukm_id: int, ukm_update: schemas.UKMCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):
    updated = crud.update_ukm(db_session, ukm_id, ukm_update)
    if not updated:
        raise HTTPException(status_code=404, detail="UKM not found")

    text_for_embedding = f"UKM: {updated.nama}. Role: {updated.jabatan}. {updated.deskripsi or ''}"
    background_tasks.add_task(
        create_embedding_background,
        updated.id_user,
        "ukm",
        updated.id_ukm,
        text_for_embedding
    )
    return updated


@router.delete("/{ukm_id}")
async def delete_ukm(ukm_id: int, db_session: Session = Depends(get_db)):
    deleted = crud.delete_ukm(db_session, ukm_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="UKM not found")
    return {"message": "UKM deleted successfully"}
