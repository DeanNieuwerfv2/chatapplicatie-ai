from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from dotenv import load_dotenv

# ---------------------------------------------------------
# .env inladen
# ---------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------
# FastAPI applicatie + CORS
# ---------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Request / Response modellen
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None  # mag leeg zijn


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# AWS / Bedrock / S3 configuratie
# ---------------------------------------------------------
REGION = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-haiku-20240307-v1:0",  # standaard
)

CHAT_LOG_BUCKET = os.getenv("CHAT_LOG_BUCKET")

# Bedrock client
try:
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    print("✅ Bedrock client aangemaakt")
except Exception as e:
    print("⚠️ Kon Bedrock client niet aanmaken:", repr(e))
    bedrock = None

# S3 client
s3 = boto3.client("s3", region_name=REGION)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def log_message_to_s3(conversation_id: str, role: str, content: str) -> None:
    """
    Slaat één bericht op als JSON in S3:
    conversations/<conversation_id>/<timestamp>-<role>.json
    """
    if not CHAT_LOG_BUCKET:
        print("⚠️ CHAT_LOG_BUCKET niet gezet; sla niet op in S3.")
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    key = f"conversations/{conversation_id}/{timestamp}-{role}.json"

    payload = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "timestamp": timestamp,
    }

    try:
        s3.put_object(
            Bucket=CHAT_LOG_BUCKET,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )
        print(f"✅ Message opgeslagen in s3://{CHAT_LOG_BUCKET}/{key}")
    except Exception as e:
        print("❌ Fout bij log_message_to_s3:", repr(e))


@app.get("/s3-test")
def s3_test():
    """
    Snelle test of S3 werkt.
    """
    try:
        bucket = CHAT_LOG_BUCKET
        print("CHAT_LOG_BUCKET =", bucket)

        if not bucket:
            return {"status": "ERROR", "message": "CHAT_LOG_BUCKET is niet gezet"}

        test_key = "test-folder/s3-test.txt"
        test_body = "S3 test werkt!"

        s3.put_object(
            Bucket=bucket,
            Key=test_key,
            Body=test_body.encode("utf-8"),
            ContentType="text/plain",
        )

        return {"status": "OK", "message": f"Bestand opgeslagen als {test_key}"}

    except Exception as e:
        print("❌ S3 TEST ERROR:", repr(e))
        return {"status": "ERROR", "message": repr(e)}


# ---------------------------------------------------------
# /chat endpoint
# ---------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Simpele chat:
    - Optional conversation_id ontvangen (anders nieuwe maken)
    - User-bericht loggen naar S3
    - Bedrock aanroepen (Claude 3 Haiku)
    - AI-antwoord loggen naar S3
    - reply + conversation_id teruggeven
    """
    # conversation_id bepalen
    conversation_id = req.conversation_id or str(uuid.uuid4())

    # user-bericht loggen
    log_message_to_s3(conversation_id, "user", req.message)

    if bedrock is None:
        reply = f"(DEBUG) Bedrock client is None, echo: {req.message}"
        log_message_to_s3(conversation_id, "system", reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id)

    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": req.message,
                        }
                    ],
                }
            ],
        }

        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        data = json.loads(response["body"].read().decode("utf-8"))
        print("Bedrock response JSON:", data)

        # Tekst uit de Claude 3 response halen
        ai_text = ""
        for part in data.get("content", []):
            if part.get("type") == "text":
                ai_text += part.get("text", "")

        if not ai_text:
            ai_text = f"(DEBUG) Geen tekst gevonden in response: {data}"

        # AI-antwoord loggen
        log_message_to_s3(conversation_id, "assistant", ai_text)

        return ChatResponse(reply=ai_text, conversation_id=conversation_id)

    except NoCredentialsError:
        err = (
            "(ERROR) AWS credentials niet gevonden. "
            "Run 'aws configure' of zet AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY."
        )
        log_message_to_s3(conversation_id, "system", err)
        return ChatResponse(reply=err, conversation_id=conversation_id)

    except BotoCoreError as e:
        err = f"(ERROR) Bedrock fout: {e}"
        print("❌ Bedrock/BotoCore fout:", repr(e))
        log_message_to_s3(conversation_id, "system", err)
        return ChatResponse(reply=err, conversation_id=conversation_id)

    except Exception as e:
        import traceback

        print("❌ Onbekende fout in /chat:", repr(e))
        print(traceback.format_exc())
        err = f"(ERROR) Onbekende fout: {repr(e)}"
        log_message_to_s3(conversation_id, "system", err)
        return ChatResponse(reply=err, conversation_id=conversation_id)
