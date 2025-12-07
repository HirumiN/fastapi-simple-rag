# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# import db module (harus ada: app/db.py)
from app import db

# import routers (pastikan file-file router ada di app/routers/)
from app.routers import auth, rag_routes, todos, jadwal_matkul, ukm

# APPLICATION LIFESPAN: buat table + hnsw index saat startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables if not exist
    db.Base.metadata.create_all(bind=db.engine)
    # create hnsw index for pgvector (implementasi di db.create_hnsw_index)
    try:
        db.create_hnsw_index()
    except Exception:
        # jangan crash kalau index sudah ada atau db belum support
        pass
    yield

# instantiate app
app = FastAPI(lifespan=lifespan, title="FastAPI RAG App")

# mount static + templates (opsional, untuk template rendering)
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir) if os.path.isdir(templates_dir) else None

# Register routers (prefix & tags sudah di router files)
app.include_router(auth.router)
app.include_router(rag_routes.router)
app.include_router(todos.router)
app.include_router(jadwal_matkul.router)
app.include_router(ukm.router)


# simple root for health-check / quick UI link
@app.get("/", tags=["root"])
async def root():
    return {"status": "ok", "message": "FastAPI RAG app is running"}


# if run as script (development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
