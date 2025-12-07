from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional


# ==========================
# USER CRUD
# ==========================

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id_user == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        nama=user.nama,
        email=user.email,
        telepon=user.telepon,
        bio=user.bio,
        lokasi=user.lokasi
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# ==========================
# RAG Embedding CRUD
# ==========================

def get_rags_embeddings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.RAGSEmbedding).offset(skip).limit(limit).all()


def create_rags_embedding(db: Session, embedding: schemas.RAGSEmbeddingCreate, vector_embedding: List[float]):
    db_embedding = models.RAGSEmbedding(
        id_user=embedding.id_user,
        source_type=embedding.source_type,
        source_id=embedding.source_id,
        text_original=embedding.text_original,
        embedding=vector_embedding,
    )
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


def delete_rags_embedding(db: Session, embedding_id: int):
    db_embedding = db.query(models.RAGSEmbedding).filter(models.RAGSEmbedding.id_embedding == embedding_id).first()
    if db_embedding:
        db.delete(db_embedding)
        db.commit()
    return db_embedding


def get_all_rags_embeddings(db: Session):
    return db.query(models.RAGSEmbedding).all()


# ==========================
# Chat History CRUD
# ==========================

def create_ai_chat_history(db: Session, chat_entry: schemas.AIChatHistoryCreate):
    db_chat_entry = models.AIChatHistory(
        id_user=chat_entry.id_user,
        role=chat_entry.role,
        message=chat_entry.message,
    )
    db.add(db_chat_entry)
    db.commit()
    db.refresh(db_chat_entry)
    return db_chat_entry


def get_chat_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.AIChatHistory)
        .filter(models.AIChatHistory.id_user == user_id)
        .order_by(models.AIChatHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ==========================
# TODO CRUD
# ==========================

def get_todos(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Todo)
    if user_id is not None:
        query = query.filter(models.Todo.id_user == user_id)
    return query.offset(skip).limit(limit).all()


def create_todo(db: Session, todo: schemas.TodoCreate):
    db_todo = models.Todo(
        id_user=todo.id_user,
        nama=todo.nama,
        tipe=todo.tipe,
        tenggat=todo.tenggat,
        deskripsi=todo.deskripsi,
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def update_todo(db: Session, todo_id: int, todo_update: schemas.TodoCreate):
    db_todo = db.query(models.Todo).filter(models.Todo.id_todo == todo_id).first()
    if db_todo:
        for key, value in todo_update.model_dump().items():
            setattr(db_todo, key, value)
        db.commit()
        db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, todo_id: int):
    db_todo = db.query(models.Todo).filter(models.Todo.id_todo == todo_id).first()
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo


# ==========================
# Jadwal Matkul CRUD
# ==========================

def get_jadwal_matkul(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.JadwalMatkul)
    if user_id is not None:
        query = query.filter(models.JadwalMatkul.id_user == user_id)
    return query.offset(skip).limit(limit).all()


def create_jadwal_matkul(db: Session, jadwal: schemas.JadwalMatkulCreate):
    db_jadwal = models.JadwalMatkul(
        id_user=jadwal.id_user,
        hari=jadwal.hari,
        nama=jadwal.nama,
        jam_mulai=jadwal.jam_mulai,
        jam_selesai=jadwal.jam_selesai,
        sks=jadwal.sks,
    )
    db.add(db_jadwal)
    db.commit()
    db.refresh(db_jadwal)
    return db_jadwal


def update_jadwal_matkul(db: Session, jadwal_id: int, jadwal_update: schemas.JadwalMatkulCreate):
    db_jadwal = db.query(models.JadwalMatkul).filter(models.JadwalMatkul.id_jadwal == jadwal_id).first()
    if db_jadwal:
        for key, value in jadwal_update.model_dump().items():
            setattr(db_jadwal, key, value)
        db.commit()
        db.refresh(db_jadwal)
    return db_jadwal


def delete_jadwal_matkul(db: Session, jadwal_id: int):
    db_jadwal = db.query(models.JadwalMatkul).filter(models.JadwalMatkul.id_jadwal == jadwal_id).first()
    if db_jadwal:
        db.delete(db_jadwal)
        db.commit()
    return db_jadwal


# ==========================
# UKM CRUD
# ==========================

def get_ukm(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.UKM)
    if user_id is not None:
        query = query.filter(models.UKM.id_user == user_id)
    return query.offset(skip).limit(limit).all()


def create_ukm(db: Session, ukm: schemas.UKMCreate):
    db_ukm = models.UKM(
        id_user=ukm.id_user,
        nama=ukm.nama,
        jabatan=ukm.jabatan,
        deskripsi=ukm.deskripsi,
    )
    db.add(db_ukm)
    db.commit()
    db.refresh(db_ukm)
    return db_ukm


def update_ukm(db: Session, ukm_id: int, ukm_update: schemas.UKMCreate):
    db_ukm = db.query(models.UKM).filter(models.UKM.id_ukm == ukm_id).first()
    if db_ukm:
        for key, value in ukm_update.model_dump().items():
            setattr(db_ukm, key, value)
        db.commit()
        db.refresh(db_ukm)
    return db_ukm


def delete_ukm(db: Session, ukm_id: int):
    db_ukm = db.query(models.UKM).filter(models.UKM.id_ukm == ukm_id).first()
    if db_ukm:
        db.delete(db_ukm)
        db.commit()
    return db_ukm
