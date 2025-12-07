from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time

# ==========================
# USER
# ==========================

class UserBase(BaseModel):
    nama: str
    email: str
    telepon: Optional[str] = None
    bio: Optional[str] = None
    lokasi: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id_user: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==========================
# RAGS EMBEDDINGS
# ==========================

class RAGSEmbeddingBase(BaseModel):
    id_user: Optional[int] = None
    source_type: str
    source_id: Optional[str] = None
    text_original: str


class RAGSEmbeddingCreate(RAGSEmbeddingBase):
    pass


class RAGSEmbedding(RAGSEmbeddingBase):
    id_embedding: int
    embedding: List[float]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


# ==========================
# AI CHAT HISTORY
# ==========================

class AIChatHistoryBase(BaseModel):
    id_user: int
    role: str
    message: str


class AIChatHistoryCreate(AIChatHistoryBase):
    pass


class AIChatHistory(AIChatHistoryBase):
    id_chat: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==========================
# RAG QUERY / RESPONSE
# ==========================

class ActivityCreate(RAGSEmbeddingBase):
    pass


class RAGQuery(BaseModel):
    id_user: Optional[int] = None
    question: str
    top_k: int = 5


class RAGResponse(BaseModel):
    answer: str
    context_docs: List[RAGSEmbedding]


# ==========================
# GOOGLE CALENDAR
# ==========================

class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime


# ==========================
# TODO
# ==========================

class TodoBase(BaseModel):
    id_user: Optional[int]
    nama: str
    tipe: str
    tenggat: Optional[datetime]
    deskripsi: Optional[str]


class TodoCreate(TodoBase):
    pass


class Todo(TodoBase):
    id_todo: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==========================
# JADWAL MATA KULIAH
# ==========================

class JadwalMatkulBase(BaseModel):
    id_user: Optional[int]
    hari: str
    nama: str
    jam_mulai: time
    jam_selesai: time
    sks: int


class JadwalMatkulCreate(JadwalMatkulBase):
    pass


class JadwalMatkul(JadwalMatkulBase):
    id_jadwal: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==========================
# UKM
# ==========================

class UKMBase(BaseModel):
    id_user: Optional[int]
    nama: str
    jabatan: str
    deskripsi: Optional[str]


class UKMCreate(UKMBase):
    pass


class UKM(UKMBase):
    id_ukm: int
    created_at: datetime

    model_config = {"from_attributes": True}
