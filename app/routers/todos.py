# app/routers/todos.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas, crud, db
from app.utils.session import get_current_user
from app.utils.embeddings import create_embedding_background

router = APIRouter(prefix="/todos", tags=["Todo"])

def get_db():
    yield from db.get_db()


@router.get("/", response_model=List[schemas.Todo])
async def list_todos(request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    return crud.get_todos(db_session, user_id=user.id_user if user else None)


@router.post("/", response_model=schemas.Todo)
async def create_todo(todo: schemas.TodoCreate, background_tasks: BackgroundTasks, request: Request, db_session: Session = Depends(get_db)):
    user = get_current_user(request, db_session)
    if user:
        todo.id_user = user.id_user

    db_todo = crud.create_todo(db_session, todo)

    # prepare text to embed
    text_for_embedding = f"Todo: {db_todo.nama}. Description: {db_todo.deskripsi or ''}. Deadline: {db_todo.tenggat or ''}"

    # schedule background embedding (background function handles its own DB session)
    background_tasks.add_task(
        create_embedding_background,
        db_todo.id_user,
        "todo",
        db_todo.id_todo,
        text_for_embedding
    )

    return db_todo


@router.put("/{todo_id}", response_model=schemas.Todo)
async def update_todo(todo_id: int, todo_update: schemas.TodoCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):
    updated = crud.update_todo(db_session, todo_id, todo_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Optionally re-generate embedding on update
    text_for_embedding = f"Todo: {updated.nama}. Description: {updated.deskripsi or ''}. Deadline: {updated.tenggat or ''}"
    background_tasks.add_task(
        create_embedding_background,
        updated.id_user,
        "todo",
        updated.id_todo,
        text_for_embedding
    )
    return updated


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, db_session: Session = Depends(get_db)):
    deleted = crud.delete_todo(db_session, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}
