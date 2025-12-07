from fastapi import Request
from sqlalchemy.orm import Session
from app import crud

sessions = {}


def get_current_user(request: Request, db_session: Session):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    user_id = sessions[session_id]
    return crud.get_user(db_session, user_id)
