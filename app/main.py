from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# In-memory session store (use Redis/DB in production)
sessions = {}

# Dependency to get DB session
def get_db():
    yield from db.get_db()

# Helper function to get current user from session
def get_current_user(request: Request, db_session: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    user_id = sessions[session_id]
    return crud.get_user(db_session, user_id)

# Root endpoint - Render HTML template (Section 8, 10)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db_session: Session = Depends(get_db)):
    current_user = get_current_user(request, db_session)
    rags_embeddings = crud.get_all_rags_embeddings(db_session)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "rags_embeddings": rags_embeddings, "current_user": current_user}
    )

# POST /add-activity (Section 8)
@app.post("/add-activity", response_class=RedirectResponse)
async def add_activity(
    request: Request,
    source_type: str = Form(...),
    text_original: str = Form(...),
    id_user: Optional[int] = Form(None),
    db_session: Session = Depends(get_db)
):
    current_user = get_current_user(request, db_session)
    if not id_user and current_user:
        id_user = current_user.id_user
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
async def rag_query(query: schemas.RAGQuery, request: Request, db_session: Session = Depends(get_db)):
    current_user = get_current_user(request, db_session)
    if not query.id_user and current_user:
        query.id_user = current_user.id_user
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

# OAuth endpoints
@app.get("/auth/login")
async def login(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth credentials not configured")
    oauth = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    authorization_url, state = oauth.create_authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        scope=['openid', 'email', 'profile', 'https://www.googleapis.com/auth/calendar']
    )
    # Store state in session for CSRF protection
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {"state": state}
    response = RedirectResponse(authorization_url)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str, state: str, db_session: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions or sessions[session_id].get("state") != state:
        raise HTTPException(status_code=400, detail="Invalid state")

    oauth = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    try:
        token = await oauth.fetch_token(
            'https://oauth2.googleapis.com/token',
            authorization_response=str(request.url)
        )
    except OAuthError:
        raise HTTPException(status_code=400, detail="Failed to fetch token")

    # Get user info
    user_info = await oauth.get('https://www.googleapis.com/oauth2/v2/userinfo')
    user_data = user_info.json()

    # Check if user exists, if not create
    user = crud.get_user_by_email(db_session, user_data['email'])
    if not user:
        user = crud.create_user(db_session, schemas.UserCreate(
            nama=user_data['name'],
            email=user_data['email']
        ))

    # Update user with tokens
    user.access_token = token['access_token']
    user.refresh_token = token.get('refresh_token')
    user.token_expiry = datetime.utcnow() + timedelta(seconds=token['expires_in'])
    db_session.commit()

    # Update session with user_id
    sessions[session_id] = user.id_user

    return RedirectResponse(url="/")

@app.get("/auth/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id")
    return response

# Optional: POST /calendar/create-event (Section 13)
@app.post("/calendar/create-event")
async def create_calendar_event(event: schemas.CalendarEventCreate, request: Request, db_session: Session = Depends(get_db)):
    current_user = get_current_user(request, db_session)
    if not current_user or not current_user.access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=current_user.access_token,
        refresh_token=current_user.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    service = build('calendar', 'v3', credentials=creds)

    event_body = {
        'summary': event.summary,
        'description': event.description,
        'start': {'dateTime': event.start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': event.end_time.isoformat(), 'timeZone': 'UTC'},
    }

    try:
        created_event = service.events().insert(calendarId='primary', body=event_body).execute()
        return {"message": "Calendar event created successfully", "event_id": created_event.get('id')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

