<div align="center">

# 🤖 Chatapplicatie AI  
_Een complete AI-chatapplicatie met FastAPI, Amazon Bedrock, React & AWS hosting._

[![Tech](https://img.shields.io/badge/Built%20with-FastAPI%20•%20React%20•%20AWS-10B981?style=for-the-badge)](#)

</div>

---

## 📦 Over dit project

Dit project is een moderne AI-chatapplicatie bestaande uit:

- **Frontend** – React (Vite) + TailwindCSS  
- **Backend** – FastAPI (Python) + Amazon Bedrock (Claude 3 Haiku)  
- **Conversatielogs** – Amazon S3 (1 JSON-bestand per bericht)  
- **Hosting**  
  - Backend → AWS App Runner (Docker image vanuit ECR)  
  - Frontend → S3 Static Website Hosting  

---

## 🧱 Architectuur

```text
[ Browser (React UI) ]
          │
          ▼
[ Frontend @ S3 / CloudFront ]
          │
          ▼
[ Backend @ App Runner (FastAPI, Docker) ]
          │
          ├── Bedrock: Claude 3 Haiku
          └── S3: Conversatielogs opslaan

📁 Projectstructuur
.
├── backend/
│   ├── main.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
└── README.md

🔐 Environment variabelen
Backend (backend/.env)

(niet committen)

AWS_REGION=eu-west-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
CHAT_LOG_BUCKET=<jouw-s3-bucketnaam>

App Runner environment variables

Voeg dezelfde variabelen toe in App Runner onder Environment variables.

🧪 Backend lokaal starten

Vereist: Python 3.11+ en uv package manager

cd backend
uv sync
uv run uvicorn main:app --reload --port 8000


Endpoints:

Docs → http://localhost:8000/docs

Health → http://localhost:8000/health

Chat → POST /chat

💬 Chat endpoint voorbeeld
Request
{
  "message": "Hallo!",
  "conversation_id": "optioneel-uuid"
}

Response
{
  "reply": "Antwoord van Claude…",
  "conversation_id": "uuid-blijft-consistent"
}

S3 log structuur
s3://<CHAT_LOG_BUCKET>/conversations/<conversation_id>/
    2024-05-12T15:22:11_user.json
    2024-05-12T15:22:12_assistant.json

🧪 Frontend lokaal starten

Vereist: Node 18+

cd frontend
npm install
npm run dev


Frontend draait op:

http://localhost:5173


De backend-URL staat in:

frontend/src/App.jsx

🐳 Backend Docker builden
cd backend
docker build -t chat-backend .
docker run -p 8000:8000 chat-backend

☁️ AWS Deployment (korte stappen)
1. Backend → ECR → App Runner

Bouw & push Docker image:

aws ecr get-login-password --region eu-west-1 \
 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com

docker tag chat-backend:latest <ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chat-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chat-backend:latest


Maak App Runner service:

Source: ECR

Port: 8000

Environment vars: zie boven

IAM:

ECR access role

Instance role met:

bedrock:InvokeModel

s3:GetObject, PutObject, ListBucket

Je krijgt een URL zoals:

https://abcd1234.eu-west-1.awsapprunner.com

2. Frontend → S3 Static Website

Build:

npm run build


Upload dist/ naar je S3 bucket

Zet static website hosting aan

Voeg bucket policy toe:

{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::<bucketnaam>/*"
}

👥 Werken met deze repo (voor developers)
Repo clonen
git clone https://github.com/DeanNieuwerfv2/chatapplicatie-ai.git
cd chatapplicatie-ai

Lokaal starten
cd backend
uv run uvicorn main:app --reload --port 8000

cd ../frontend
npm install
npm run dev

🔮 Toekomstige uitbreidingen

Historiek ophalen uit S3 en tonen in de UI

Ondersteuning voor meerdere modellen

Deploy pipeline via GitHub Actions

API-key beveiliging

🧑‍💻 Credits

Ontwikkeling: Dean

AI Pair Programming: ChatGPT (GPT-5.1)