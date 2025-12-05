from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .db import Base

class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)
    nama = Column(String)
    email = Column(String, unique=True, index=True)
    telepon = Column(String)
    bio = Column(Text)
    lokasi = Column(String)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True)

    rags_embeddings = relationship("RAGSEmbedding", back_populates="owner")
    chat_history = relationship("AIChatHistory", back_populates="owner")


class RAGSEmbedding(Base):
    __tablename__ = "rags_embeddings"

    id_embedding = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    source_type = Column(String)
    source_id = Column(String, nullable=True)
    text_original = Column(Text)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="rags_embeddings")


class AIChatHistory(Base):
    __tablename__ = "ai_chat_history"

    id_chat = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"))
    role = Column(String)  # 'user' or 'assistant'
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="chat_history")
