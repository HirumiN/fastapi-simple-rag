from fastapi.testclient import TestClient
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.db import Base
from app import models, crud, schemas
from app.rag import embed_text_with_gemini

# Use a separate test PostgreSQL database
SQLALCHEMY_DATABASE_URL = "postgresql://admin:1@localhost:5432/ragdb_test"

test_engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override the get_db dependency to use the test database
def override_get_db():
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@pytest.fixture(name="session", scope="function")
async def session_fixture():
    # Ensure pgvector extension is enabled for the test database
    with test_engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()
    
    # Drop all tables first to ensure a clean state
    Base.metadata.drop_all(bind=test_engine)
    # Create all tables defined in models.py
    Base.metadata.create_all(bind=test_engine)
    
    db_session = TestingSessionLocal()
    try:
        # Create a user
        user = crud.create_user(db_session, schemas.UserCreate(nama="test", email="test@example.com"))
        db_session.commit()
        db_session.refresh(user)

        # Add some activities with real embeddings
        text1 = "Meeting with client at 10 AM on Monday."
        embedding1 = await embed_text_with_gemini(text1)
        crud.create_rags_embedding(db_session, schemas.RAGSEmbeddingCreate(
            id_user=user.id_user,
            source_type="tugas",
            text_original=text1
        ), embedding1)
        
        text2 = "Dentist appointment on Tuesday afternoon."
        embedding2 = await embed_text_with_gemini(text2)
        crud.create_rags_embedding(db_session, schemas.RAGSEmbeddingCreate(
            id_user=user.id_user,
            source_type="jadwal",
            text_original=text2
        ), embedding2)

        db_session.commit()
        yield db_session
    finally:
        db_session.close()
        # Drop all tables after tests
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(name="client", scope="function")
async def client_fixture(session):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Personalized RAG System" in response.text

@pytest.mark.asyncio
async def test_add_activity(client, session):
    # Verify initial state
    embedding_in_db = crud.get_all_rags_embeddings(session)
    assert len(embedding_in_db) == 2

    activity_text = "Final project submission deadline is Friday."
    response = client.post(
        "/add-activity",
        data={
            "source_type": "tugas",
            "text_original": activity_text,
            "id_user": "1"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Verify embedding was saved
    embedding_in_db = crud.get_all_rags_embeddings(session)
    assert len(embedding_in_db) == 3
    new_embedding = embedding_in_db[2]
    assert new_embedding.source_type == "tugas"
    assert new_embedding.text_original == activity_text
    assert new_embedding.embedding is not None
    assert len(new_embedding.embedding) == 768

@pytest.mark.asyncio
async def test_delete_activity(client, session):
    # Verify initial state
    embedding_in_db = crud.get_all_rags_embeddings(session)
    assert len(embedding_in_db) == 2
    embedding_id_to_delete = embedding_in_db[0].id_embedding

    response_delete = client.post(
        f"/delete-activity/{embedding_id_to_delete}",
        follow_redirects=False
    )
    assert response_delete.status_code == 303
    assert response_delete.headers["location"] == "/"

    # Verify it's deleted
    embedding_after_delete = crud.get_all_rags_embeddings(session)
    assert len(embedding_after_delete) == 1
    assert all(emb.id_embedding != embedding_id_to_delete for emb in embedding_after_delete)

@pytest.mark.asyncio
async def test_rag_query(client, session):
    user_id = 1
    query_data = {
        "id_user": user_id,
        "question": "When is my meeting?",
        "top_k": 2
    }
    response = client.post("/rag/query", json=query_data)
    
    if response.status_code != 200:
        print(f"RAG Query failed with status {response.status_code}: {response.text}")

    assert response.status_code == 200
    json_response = response.json()
    
    assert "answer" in json_response
    assert "context_docs" in json_response
    assert json_response["answer"] is not None
    # Check that the context contains relevant information
    assert any("Meeting with client" in doc["text_original"] for doc in json_response["context_docs"])

    # Verify chat history is saved
    chat_history = crud.get_chat_history(session, user_id)
    # Should be at least 2 entries (user question + assistant answer)
    assert len(chat_history) >= 2
    user_message_exists = any(entry.role == "user" and entry.message == query_data["question"] for entry in chat_history)
    assistant_message_exists = any(entry.role == "assistant" and entry.message == json_response["answer"] for entry in chat_history)
    assert user_message_exists
    assert assistant_message_exists