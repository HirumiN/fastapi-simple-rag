from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app import schemas, crud, rag, db
from app.utils.session import get_current_user

router = APIRouter(prefix="/rag", tags=["RAG"])

def get_db():
    yield from db.get_db()


@router.post("/query", response_model=schemas.RAGResponse)
async def rag_query(query: schemas.RAGQuery, request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    if user:
        query.id_user = user.id_user

    query_embedding = await rag.embed_text_with_gemini(query.question)
    context_docs = rag.retrieve_similar_rags(db_session, query_embedding, query.top_k)
    augmented = rag.augment_prompt(query.question, context_docs)
    answer = await rag.generate_answer_with_gemini(augmented)

    if query.id_user:
        crud.create_ai_chat_history(db_session, schemas.AIChatHistoryCreate(
            id_user=query.id_user, role="user", message=query.question
        ))
        crud.create_ai_chat_history(db_session, schemas.AIChatHistoryCreate(
            id_user=query.id_user, role="assistant", message=answer
        ))

    return schemas.RAGResponse(answer=answer, context_docs=context_docs)
