from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from . import models, schemas, crud, db, rag

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    db.Base.metadata.create_all(bind=db.engine)
    db.create_hnsw_index()
    yield

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2Templates
templates = Jinja2Templates(directory="app/templates")

# Dependency to get DB session
def get_db():
    yield from db.get_db()

# Root endpoint - Render HTML template (Section 8, 10)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db_session: Session = Depends(get_db)):
    rags_embeddings = crud.get_all_rags_embeddings(db_session)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "rags_embeddings": rags_embeddings}
    )

# POST /add-activity (Section 8)
@app.post("/add-activity", response_class=RedirectResponse)
async def add_activity(
    source_type: str = Form(...),
    text_original: str = Form(...),
    id_user: Optional[int] = Form(None),
    db_session: Session = Depends(get_db)
):
    try:
        embedding_list = await rag.embed_text_with_gemini(text_original)
        activity_create = schemas.RAGSEmbeddingCreate(
            id_user=id_user,
            source_type=source_type,
            source_id=None, # Inferred from GEMINI.md, source_id is optional and can be set to None or a meaningful ID later
            text_original=text_original
        )
        crud.create_rags_embedding(db_session, activity_create, embedding_list)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST /delete-activity/{id} (Section 8)
@app.post("/delete-activity/{embedding_id}", response_class=RedirectResponse)
async def delete_activity(embedding_id: int, db_session: Session = Depends(get_db)):
    crud.delete_rags_embedding(db_session, embedding_id)
    return RedirectResponse(url="/", status_code=303)

# POST /rag/query (Section 8)
@app.post("/rag/query", response_model=schemas.RAGResponse)
async def rag_query(query: schemas.RAGQuery, db_session: Session = Depends(get_db)):
    try:
        # 1. Embed question
        query_embedding = await rag.embed_text_with_gemini(query.question)
        
        # 2. Find similar rows
        context_docs = rag.retrieve_similar_rags(db_session, query_embedding, query.top_k)
        
        # 3. Build augmented prompt
        augmented_prompt = rag.augment_prompt(query.question, context_docs)
        
        # 4. Call Gemini generate
        answer = await rag.generate_answer_with_gemini(augmented_prompt)

        # 5. Save chat history (for user question)
        if query.id_user:
            crud.create_ai_chat_history(db_session, schemas.AIChatHistoryCreate(
                id_user=query.id_user, role="user", message=query.question
            ))
            crud.create_ai_chat_history(db_session, schemas.AIChatHistoryCreate(
                id_user=query.id_user, role="assistant", message=answer
            ))
        
        return schemas.RAGResponse(answer=answer, context_docs=context_docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional: POST /calendar/create-event (Section 13)
@app.post("/calendar/create-event")
async def create_calendar_event(event: schemas.CalendarEventCreate):
    """
    Handles the creation of a Google Calendar event.

    TODO:
    1. Authenticate with Google Calendar API.
       - This typically involves setting up OAuth 2.0 credentials in the Google Cloud Console.
       - You might need to store refresh tokens securely and use them to obtain access tokens.
       - Libraries like `google-auth-oauthlib` and `google-api-python-client` can assist.
    2. Construct the event body using the 'event' data.
       - Ensure `start_time` and `end_time` are in the correct format (e.g., RFC3339).
    3. Call the Google Calendar API to insert the event.
    4. Handle potential API errors (e.g., authentication failure, invalid event data).
    5. Return an appropriate response, including the event ID if successful.
    """
    # Placeholder for future implementation
    # Example using google-api-python-client (requires installation and setup):
    # from google.oauth2.credentials import Credentials
    # from googleapiclient.discovery import build

    # creds = ... # Load or refresh credentials
    # service = build('calendar', 'v3', credentials=creds)

    # event_body = {
    #     'summary': event.summary,
    #     'description': event.description,
    #     'start': {'dateTime': event.start_time.isoformat(), 'timeZone': 'UTC'}, # Adjust timezone as needed
    #     'end': {'dateTime': event.end_time.isoformat(), 'timeZone': 'UTC'},     # Adjust timezone as needed
    # }

    # try:
    #     created_event = service.events().insert(calendarId='primary', body=event_body).execute()
    #     return {"message": "Calendar event created successfully", "event_id": created_event.get('id')}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {e}")
    
    return {"message": "Calendar event creation not yet implemented. Please refer to the code for integration instructions."}

