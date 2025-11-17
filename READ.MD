# Chatapplicatie – AI met Amazon Bedrock & React

Dit project is een complete chatapplicatie met:

- **Frontend**: React + Vite + Tailwind (single-page chat UI)
- **Backend**: FastAPI (Python) met Amazon Bedrock (Claude 3 Haiku)
- **Opslag**: Amazon S3 (chatconversaties per bericht gelogd)
- **Hosting**:
  - Backend: AWS App Runner (Docker container uit ECR)
  - Frontend: S3 static website (optioneel achter CloudFront)

> Doel van de repo: laten zien hoe je van scratch een moderne AI-chatapp bouwt en deployt op AWS.

---

## 🏗 Architectuur

```text
[Browser] 
   │
   │  HTTPS (fetch /chat)
   ▼
[Frontend: React/Vite/Tailwind]  (S3 website / CloudFront)
   │
   │  HTTPS (REST JSON)
   ▼
[Backend: FastAPI @ App Runner]  (Docker)
   │
   ├─► [Amazon Bedrock – Claude 3 Haiku]
   │
   └─► [Amazon S3 – conversatielogs]
📁 Projectstructuur
text
Code kopiëren
.
├── backend/
│   ├── main.py              # FastAPI app (Bedrock + S3 logging)
│   ├── Dockerfile           # Container voor App Runner / ECR
│   ├── pyproject.toml       # Python project config (uv)
│   ├── uv.lock              # Dependency lockfile
│   └── .env.example         # Voorbeeld van environment-variabelen
│
├── frontend/
│   ├── src/App.jsx          # Chat UI
│   ├── src/index.css        # Tailwind + custom styles
│   ├── vite.config.js       # Vite config
│   └── package.json         # Frontend dependencies/scripts
│
└── README.md                # Dit bestand
✅ Vereisten
Lokaal ontwikkelen
Node.js 18+

npm of pnpm

Python 3.11+ (in dit project 3.12)

uv als Python package manager (https://docs.astral.sh/uv/)

Docker Desktop (voor lokaal testen van de container)

AWS CLI geconfigureerd (aws configure)

Voor productie / AWS
AWS-account (met toegang tot:

Amazon Bedrock (Claude 3 Haiku model geactiveerd)

Amazon S3

Amazon ECR

AWS App Runner

IAM permissies om:

Images naar ECR te pushen

App Runner services aan te maken

Bedrock modellen aan te roepen

S3 buckets te lezen/schrijven

🔐 Environment variables
Backend (backend/.env)
Maak backend/.env aan (voor lokaal) gebaseerd op:

env
Code kopiëren
AWS_REGION=eu-west-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
CHAT_LOG_BUCKET=je-s3-bucket-voor-conversaties
Voor App Runner zet je deze als Environment variables in de service-config.

Let op: Geen .env bestanden committen – gebruik .env.example in de repo als referentie.

▶️ Backend lokaal draaien (zonder Docker)
bash
Code kopiëren
cd backend
uv sync                     # dependencies installeren
uv run uvicorn main:app --reload --port 8000
De API is dan beschikbaar op:

Health check: http://localhost:8000/health

OpenAPI docs: http://localhost:8000/docs

Belangrijkste endpoint
POST /chat

Request:

json
Code kopiëren
{
  "message": "Hallo!",
  "conversation_id": "optioneel-uuid"
}
Response:

json
Code kopiëren
{
  "reply": "Antwoord van de AI...",
  "conversation_id": "per-conversatie-uuid"
}
Bij elke call worden:

het user-bericht (role=user)

het AI-antwoord (role=assistant)

eventuele fouten (role=system)

opgeslagen als losse JSON-bestanden in S3:

text
Code kopiëren
s3://<CHAT_LOG_BUCKET>/conversations/<conversation_id>/<timestamp>-<role>.json
🎨 Frontend lokaal draaien
bash
Code kopiëren
cd frontend
npm install
npm run dev
De app is bereikbaar op:

http://localhost:5173

De frontend stuurt fetch requests naar de backend:

js
Code kopiëren
const res = await fetch("http://localhost:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: userMessage.content,
    conversation_id: conversationId,
  }),
});
In productie moet de URL worden aangepast naar de App Runner URL (zie onder).

🐳 Backend container builden en lokaal testen
In de map backend/ staat een Dockerfile die de FastAPI-app containeriseert.

Image builden
bash
Code kopiëren
cd backend
docker build -t chat-backend .
Container runnen
bash
Code kopiëren
docker run -p 8000:8000 chat-backend
De API is dan (opnieuw) bereikbaar op http://localhost:8000 en de frontend kan daartegen praten.

☁️ Deploy naar AWS
1. Image naar ECR pushen
Maak een ECR repository, bijv. chat-backend

Login bij ECR:

bash
Code kopiëren
aws ecr get-login-password --region eu-west-1 \
  | docker login --username AWS --password-stdin <ACCOUNT-ID>.dkr.ecr.eu-west-1.amazonaws.com
Tag & push:

bash
Code kopiëren
docker tag chat-backend:latest <ACCOUNT-ID>.dkr.ecr.eu-west-1.amazonaws.com/chat-backend:latest
docker push <ACCOUNT-ID>.dkr.ecr.eu-west-1.amazonaws.com/chat-backend:latest
2. App Runner service
In AWS Console → App Runner → Create service

Source: Container registry → Amazon ECR

Kies de chat-backend:latest image

Port: 8000

Environment vars:

text
Code kopiëren
AWS_REGION=eu-west-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
CHAT_LOG_BUCKET=je-s3-bucket-voor-conversaties
IAM roles:

ECR access role (kan door App Runner automatisch worden aangemaakt)

Instance role met o.a.:

Bedrock toegang (bijv. AmazonBedrockFullAccess of beperkt beleid)

S3 toegang tot het log-bucket

CloudWatch Logs toegang

Na creation krijg je een URL zoals:

text
Code kopiëren
https://<random>.eu-west-1.awsapprunner.com
De health check (/health) moet daar {"status":"ok"} geven.

🌐 Frontend deployen naar S3
Build:

bash
Code kopiëren
cd frontend
npm run build
Maak een S3 bucket, bijv. chatapplicatie-frontend

Zet static website hosting aan, met index.html als indexdocument

Upload de inhoud van dist/:

index.html

map assets/

Maak de objects public (via bucket policy, bijv.):

json
Code kopiëren
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForStaticWebsite",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::chatapplicatie-frontend/*"
    }
  ]
}
Pas in src/App.jsx de fetch-URL aan naar je App Runner endpoint:

js
Code kopiëren
const res = await fetch("https://<your-app-runner-url>/chat", { ... })
Rebuild & opnieuw uploaden.

Optioneel: zet CloudFront vóór de S3 website voor HTTPS en betere performance.

