# **GEMINI.md**

This file describes the full specification for an AI-powered RAG System using **FastAPI**, **PostgreSQL + pgvector**, **Google Gemini API**, and optional **Gemini CLI Agent Mode** to automatically generate code.

Gemini CLI may read only this file to generate the entire project from scratch.

---

# **1. Project Goal**

Build a fast prototype of a **personalized RAG system** that uses:

* **FastAPI only** (no Laravel)
* **PostgreSQL** with **pgvector** extension
* **Gemini** for:

  * embeddings
  * text generation
* Minimal frontend (simple HTML + Bootstrap)
* CRUD forms for adding/deleting user activities (stored as embeddings)
* RAG retrieval of user-specific context
* Optional Google Calendar integration
* Unit tests
* Gemini CLI agent compatibility

The system must allow:

* Users to enter personal information (tugas, jadwal, hobi, cv, pengalaman, dll)
* System stores these as vector embeddings
* When user asks a question → system performs RAG + Gemini generation

---

# **2. System Architecture (final)**

### Components:

1. **FastAPI backend**
2. **PostgreSQL + pgvector**
3. **Gemini API for embedding & generation**
4. **Simple frontend**
5. **Unit tests (pytest)**

### Architecture Flow:

1. User submits activity → FastAPI → generate embedding → save to DB
2. User asks question → embed question → pgvector similarity search → augmented context → Gemini → answer
3. Responses saved in chat history
4. Optional: output events to Google Calendar

---

# **3. Data Model (final)**

Use the following PostgreSQL tables:

### **users**

```
id_user (PK)
nama
email
telepon
bio
lokasi
```

### **rags_embeddings**

```
id_embedding (PK)
id_user (nullable)
source_type (varchar)      # e.g. tugas, jadwal, cv, hobi
source_id (nullable)
text_original (text)
embedding VECTOR(1536)     # or match Gemini embedding dimension
created_at timestamp
```

### **ai_chat_history**

```
id_chat (PK)
id_user
role ('user'|'assistant')
message text
created_at timestamp
```

---

# **4. PostgreSQL Setup (pgvector)**

Run inside psql:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Create index:

### If pgvector supports HNSW:

```sql
CREATE INDEX rags_embeddings_hnsw_idx
ON rags_embeddings
USING hnsw (embedding vector_l2_ops)
WITH (m=16, ef_construction=200);
```

### If older version → use IVFFLAT:

```sql
CREATE INDEX rags_embeddings_ivfflat_idx
ON rags_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists=100);
```

---

# **5. FastAPI Project Structure**

Gemini CLI should generate:

```
app/
  main.py
  db.py
  models.py
  schemas.py
  crud.py
  rag.py
  templates/index.html
  static/style.css
tests/test_api.py
requirements.txt
GEMINI.md   (this file)
```

---

# **6. Required Python Libraries**

```
fastapi
uvicorn
sqlalchemy
psycopg[binary]
pgvector
jinja2
python-dotenv
httpx
pytest
```

---

# **7. Required Environment Variables**

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragdb
GEMINI_API_KEY=AIzaSyBQDHHbIAE6DNjLXCd8vooOUhRv2NQNHK0
GEMINI_EMBED_URL=https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedText?key=YOUR_KEY
GEMINI_GEN_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateText?key=YOUR_KEY
```

> If using **Gemini CLI instead of REST**, Gemini CLI agent should replace embedding & generation calls with subprocess calls. (See section 12.)

---

# **8. FastAPI Endpoints Specification**

Gemini CLI must implement the following endpoints:

### **GET /**

* Render HTML template
* Display all embeddings
* Simple form to add new activity

### **POST /add-activity**

Form fields:

* source_type
* text_original
* id_user (optional)

Behavior:

1. Call Gemini embeddings
2. Insert embedding into DB
3. Redirect to "/"

### **POST /delete-activity/{id}**

Deletes an embedding row.

### **POST /rag/query**

JSON:

```
{
  "id_user": 1,
  "question": "Apa rencana kuliah saya minggu ini?",
  "top_k": 5
}
```

Behavior:

1. Embed question
2. Find similar rows (`ORDER BY embedding <-> query_vec`)
3. Build augmented prompt
4. Call Gemini generate
5. Save chat history

Response:

```
{
  "answer": "...",
  "context_docs": [...]
}
```

---

# **9. RAG Logic (Gemini CLI should implement)**

### **Embedding**

Call Gemini embeddings model with:

```
POST GEMINI_EMBED_URL
{
  "input": "text..."
}
```

### **Retrieval (pgvector)**

SQL:

```sql
SELECT *
FROM rags_embeddings
ORDER BY embedding <-> :query_vec
LIMIT :top_k;
```

### **Augmentation**

Construct prompt:

```
Use the following context to answer the question.

Context:
[<source_type>#<id>] <text_original>
...

Question: <user_question>

Answer concisely and with actionable steps.
```

### **Generation**

POST Gemini generation model:

```
POST GEMINI_GEN_URL
{
  "prompt": "<augmented_prompt>"
}
```

---

# **10. Frontend Requirements**

Simple HTML with:

* Bootstrap 5
* Table listing embeddings
* Form for adding activities
* Delete button

No React, no Laravel, no SPA.

---

# **11. Unit Tests Specifications**

Gemini CLI must generate pytest tests:

### Tests must include:

* root page loads
* activity creation (monkeypatch embedding)
* rag/query returns answer (monkeypatch generation)
* DB resets between tests

Monkeypatch examples:

* Replace `embed_text_with_gemini` with fake vector
* Replace `generate_answer_with_gemini` with fake string

---

# **12. Support for Gemini CLI Agent Mode**

Gemini CLI Agent must:

### **Option A: Use REST API**

Already defined in ENV vars.

### **Option B: Use Gemini CLI subprocess**

Gemini CLI agent can generate code using:

```
gemini embed --model ... --text "..." --output json
```

Python example Gemini CLI should generate:

```python
import subprocess, json

def embed_with_cli(text):
    out = subprocess.check_output(["gemini", "embed", "--model", "embedding-001", "--text", text, "--output", "json"])
    data = json.loads(out)
    return data["embedding"]
```

### **Option C: Tools Mode**

Gemini CLI agent can expose FastAPI endpoints as tools for planning.

---

# **13. Google Calendar Integration (optional)**

Gemini CLI should create:

### Endpoint

`POST /calendar/create-event`

Fields:

```
summary
description
start_time
end_time
```

### Behavior:

1. Use Google API client
2. Create event in user’s Google Calendar
3. Return event ID

---

# **14. What the Agent Should Build**

Gemini CLI, using this file alone, must generate:

* Entire FastAPI directory structure
* Database models
* SQLAlchemy pgvector integration
* CRUD logic
* RAG logic
* Embedding + Generation functions
* Frontend HTML
* Unit tests
* Requirements.txt
* Instructions for running the server

---

# **15. Running the App**

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Set environment variables

```
export DATABASE_URL=...
export GEMINI_API_KEY=...
export GEMINI_EMBED_URL=...
export GEMINI_GEN_URL=...
```

### 3. Create tables

FastAPI auto-creates via SQLAlchemy on startup.

### 4. Run:

```
uvicorn app.main:app --reload
```

### 5. Open:

```
http://localhost:8000/
```

---

# **16. Summary**

Using this GEMINI.md, Gemini CLI agent must create an entire functional:

* FastAPI backend
* pgvector RAG pipeline
* Gemini embedding & generation system
* Simple CRUD HTML UI
* Chat history
* Optional Google Calendar integration
* Unit tests

No external docs needed.
No Laravel.
No React.
Pure FastAPI prototype.

# **16. Notes**

The system is Windows 11, so use PowerShell commands
PostgreSQL 17 and pgvector are inside a Docker, so use this command to access it:
```
docker exec -it pg17-vector psql -U admin -d ragdb
```