# 📧 MailLens.AI  

**Your AI-powered email lens** — MailLens.AI syncs with your email account, processes messages incrementally, embeds and indexes them with Pinecone, and lets you **search** and **chat** with your emails using OpenAI models.  

---

## 🚀 Features  

- 🔄 **Incremental Email Sync** – Fetches and updates emails continuously with Celery workers.  
- 🧩 **Smart Chunking & Embedding** – Splits messages into chunks, embeds them with `text-embedding-large`, and stores them in Pinecone for semantic search.  
- 🔍 **Semantic Email Search** – Find relevant messages beyond simple keyword search.  
- 💬 **Chat With Your Inbox** – Interact with your email history using GPT-4o-mini for contextual conversations.  
- 🌐 **Modern Frontend** – Next.js frontend with Context API for global state management.  
- ⚡ **Scalable Backend** – FastAPI + Celery pipeline for ingestion, embedding, and querying.  
- ☁️ **Cloud Deployment** – Runs on AWS infrastructure for reliability and scalability.  

---

## 🛠️ Installation  

### Prerequisites  
- Python 3.10+  
- Node.js 18+  
- PostgreSQL (for metadata storage)  
- AWS SQS (for Celery task queue in production)  
- Redis (optional, for local development)  
- Pinecone account (for vector embeddings)  
- OpenAI API key  

### Backend Setup  
```bash
# Clone repository
git clone https://github.com/s3847243/MailLens.git
cd maillens.ai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e.

```

### Environment Variables
Create a .env file in the backend directory and fill in the required values:
```bash
 ---- Core
DATABASE_URL=
REDIS_URL= 
ALLOW_ORIGIN=
SESSION_COOKIE_NAME= 

 ---- Auth / Google (placeholders)
JWT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
GOOGLE_OAUTH_SCOPES="openid email profile https://www.googleapis.com/auth/gmail.readonly"

 ---- Vector / LLM
PINECONE_API_KEY=
PINECONE_INDEX=
EMBEDDING_MODEL=
EMBEDDING_DIM=
OPENAI_API_KEY=
ENCRYPTION_KEY= 
APP_BASE_URL=
OPENAI_CHAT_MODEL=gpt-4o-mini

 ---- Celery
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
CELERY_TIMEZONE=
CELERY_BEAT_ENABLED=
CELERY_SCHEDULE_MINUTES=
```
### Run Services locally
```bash
#### Start Celery workers
celery -A app.celery worker --loglevel=info

#### Run FastAPI server
uvicorn app.main:app --reload

### Frontend Setup

cd ../frontend

#### Install dependencies
npm install

#### Setup environment
cp .env.example .env.local
#### Add NEXT_PUBLIC_API_URL and any other keys

#### Run dev server
npm run dev
```
---


## Deployment

MailLens.AI is deployed on AWS for production use:

- EC2 → Hosts the FastAPI backend 
- Vercel → Hosts the Next.js (Typescript) frontend 
- RDS (PostgreSQL) → Stores metadata, email headers, and indexing state.  
- SQS (Amazon Simple Queue Service) → Powers Celery task queues for reliable distributed processing of email sync and embeddings.  
- Pinecone → Manages semantic vector embeddings for search.  
- OpenAI APIs → Used for embeddings (text-embedding-large) and chat responses (gpt-4o-mini).  

This architecture ensures scalability, reliability, and cost-efficiency while handling large volumes of emails.

---
## License

This project is licensed under the MIT License – see the LICENSE file for details.
