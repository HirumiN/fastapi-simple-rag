from sqlalchemy.orm import Session
from . import models, schemas
from pgvector.sqlalchemy import Vector
from typing import List

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
    db_user = db.query(models.User).filter(models.User.id_user == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def get_rags_embeddings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.RAGSEmbedding).offset(skip).limit(limit).all()

def create_rags_embedding(db: Session, embedding: schemas.RAGSEmbeddingCreate, vector_embedding: List[float]):
    db_embedding = models.RAGSEmbedding(
        id_user=embedding.id_user,
        source_type=embedding.source_type,
        source_id=embedding.source_id,
        text_original=embedding.text_original,
        embedding=vector_embedding
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

def create_ai_chat_history(db: Session, chat_entry: schemas.AIChatHistoryCreate):
    db_chat_entry = models.AIChatHistory(
        id_user=chat_entry.id_user,
        role=chat_entry.role,
        message=chat_entry.message
    )
    db.add(db_chat_entry)
    db.commit()
    db.refresh(db_chat_entry)
    return db_chat_entry

def get_chat_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.AIChatHistory).filter(models.AIChatHistory.id_user == user_id).offset(skip).limit(limit).all()

def get_all_rags_embeddings(db: Session):
    return db.query(models.RAGSEmbedding).all()
