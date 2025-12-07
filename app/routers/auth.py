from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os, secrets
from datetime import datetime, timedelta
from authlib.integrations.httpx_client import AsyncOAuth2Client
from dotenv import load_dotenv

from app import crud, schemas, db
from app.utils.session import sessions


router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


def get_db():
    yield from db.get_db()


# Login
@router.get("/login")
async def login():
    oauth = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    authorization_url, state = oauth.create_authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar"]
    )

    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {"state": state}

    response = RedirectResponse(authorization_url)
    response.set_cookie("session_id", session_id)
    return response


# Callback
@router.get("/callback")
async def callback(request: Request, code: str, state: str, db_session: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions or sessions[session_id]["state"] != state:
        raise HTTPException(400, "Invalid state")

    oauth = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    token = await oauth.fetch_token(
        "https://oauth2.googleapis.com/token",
        authorization_response=str(request.url)
    )

    userinfo = await oauth.get("https://www.googleapis.com/oauth2/v2/userinfo")
    user_data = userinfo.json()

    user = crud.get_user_by_email(db_session, user_data["email"])
    if not user:
        user = crud.create_user(db_session, schemas.UserCreate(
            nama=user_data["name"],
            email=user_data["email"]
        ))

    # Update tokens
    user.access_token = token["access_token"]
    user.refresh_token = token.get("refresh_token")
    user.token_expiry = datetime.utcnow() + timedelta(seconds=token["expires_in"])
    db_session.commit()

    sessions[session_id] = user.id_user
    return RedirectResponse("/")


# Logout
@router.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse("/")
    response.delete_cookie("session_id")
    return response
