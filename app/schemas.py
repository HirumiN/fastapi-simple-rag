from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# User Schemas
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

    class Config:
        from_attributes = True

# RAGSEmbedding Schemas
class RAGSEmbeddingBase(BaseModel):
    id_user: Optional[int] = None
    source_type: str
    source_id: Optional[str] = None
    text_original: str

class RAGSEmbeddingCreate(RAGSEmbeddingBase):
    pass

class RAGSEmbedding(RAGSEmbeddingBase):
    id_embedding: int
    embedding: List[float] # This will be handled as a list of floats in Pydantic
    created_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# AI Chat History Schemas
class AIChatHistoryBase(BaseModel):
    id_user: int
    role: str
    message: str

class AIChatHistoryCreate(AIChatHistoryBase):
    pass

class AIChatHistory(AIChatHistoryBase):
    id_chat: int
    created_at: datetime

    class Config:
        from_attributes = True

# Request body for /add-activity
class ActivityCreate(RAGSEmbeddingBase):
    pass

# Request body for /rag/query
class RAGQuery(BaseModel):
    id_user: Optional[int] = None
    question: str
    top_k: int = 5

# Response for /rag/query
class RAGResponse(BaseModel):
    answer: str
    context_docs: List[RAGSEmbedding]

# Google Calendar Integration (Optional)
class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
