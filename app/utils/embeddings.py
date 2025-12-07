# app/utils/embeddings.py
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app import crud, schemas, db, rag

logger = logging.getLogger("embeddings")
logger.setLevel(logging.INFO)

def create_embedding_background(id_user: Optional[int], source_type: str, source_id: Optional[int], text_original: str):
    """
    This runs in FastAPI BackgroundTasks (sync context).
    It creates its own DB session, runs the async embedder, and writes to DB.
    """
    SessionLocal = getattr(db, "SessionLocal", None)
    if SessionLocal is None:
        logger.error("db.SessionLocal not found. Please export SessionLocal from app/db.py")
        return

    db_session: Session = SessionLocal()
    try:
        # run the async embedder in a fresh event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        embedding_list = loop.run_until_complete(rag.embed_text_with_gemini(text_original))
        loop.close()

        emb_create = schemas.RAGSEmbeddingCreate(
            id_user=id_user,
            source_type=source_type,
            source_id=str(source_id) if source_id is not None else None,
            text_original=text_original
        )

        crud.create_rags_embedding(db_session, emb_create, embedding_list)
        logger.info("Created embedding for %s:%s", source_type, source_id)
    except Exception as e:
        logger.exception("Failed to create embedding in background: %s", e)
    finally:
        try:
            db_session.close()
        except Exception:
            pass
