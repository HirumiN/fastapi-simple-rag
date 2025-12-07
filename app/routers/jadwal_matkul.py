# app/routers/jadwal_matkul.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas, crud, db
from app.utils.session import get_current_user
from app.utils.embeddings import create_embedding_background

router = APIRouter(prefix="/jadwal-matkul", tags=["JadwalMatkul"])

def get_db():
    yield from db.get_db()


@router.get("/", response_model=List[schemas.JadwalMatkul])
async def list_jadwal(request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    return crud.get_jadwal_matkul(db_session, user_id=user.id_user if user else None)


@router.post("/", response_model=schemas.JadwalMatkul)
async def create_jadwal(jadwal: schemas.JadwalMatkulCreate, background_tasks: BackgroundTasks, request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    if user:
        jadwal.id_user = user.id_user
    db_jadwal = crud.create_jadwal_matkul(db_session, jadwal)

    text_for_embedding = f"Jadwal: {db_jadwal.nama} pada {db_jadwal.hari} {db_jadwal.jam_mulai}-{db_jadwal.jam_selesai}. SKS: {db_jadwal.sks}"

    background_tasks.add_task(
        create_embedding_background,
        db_jadwal.id_user,
        "jadwal_matkul",
        db_jadwal.id_jadwal,
        text_for_embedding
    )
    return db_jadwal


@router.put("/{jadwal_id}", response_model=schemas.JadwalMatkul)
async def update_jadwal(jadwal_id: int, jadwal_update: schemas.JadwalMatkulCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):
    updated = crud.update_jadwal_matkul(db_session, jadwal_id, jadwal_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Jadwal not found")

    text_for_embedding = f"Jadwal: {updated.nama} pada {updated.hari} {updated.jam_mulai}-{updated.jam_selesai}. SKS: {updated.sks}"
    background_tasks.add_task(
        create_embedding_background,
        updated.id_user,
        "jadwal_matkul",
        updated.id_jadwal,
        text_for_embedding
    )
    return updated


@router.delete("/{jadwal_id}")
async def delete_jadwal(jadwal_id: int, db_session: Session = Depends(get_db)):
    deleted = crud.delete_jadwal_matkul(db_session, jadwal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jadwal not found")
    return {"message": "Jadwal Matkul deleted successfully"}
