"""
Meetings API: диктофон (загрузка аудио), транскрибация через OpenAI Whisper, саммари встречи
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
import logging

router = APIRouter(prefix="/meetings", tags=["Meetings"])
logger = logging.getLogger("meetings_router")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

class SummaryRequest(BaseModel):
    text: str
    style: Optional[str] = "Кратко, по пунктам"

class TaskItem(BaseModel):
    title: str
    owner: Optional[str] = None
    due: Optional[str] = None

class TasksFromMeetingRequest(BaseModel):
    items: List[TaskItem]

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), language: Optional[str] = "ru"):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    try:
        content = await file.read()
        # Отправляем напрямую в OpenAI Whisper v1
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        data = {"model": "whisper-1", "language": language or "ru"}
        files = {"file": (file.filename or "audio.wav", content, file.content_type or "audio/wav")}
        async with httpx.AsyncClient(timeout=120) as cli:
            resp = await cli.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, data=data, files=files)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"OpenAI STT error: {resp.text}")
            j = resp.json()
            return {"text": j.get("text", "")}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"transcribe_audio error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")

@router.post("/summary")
async def meeting_summary(req: SummaryRequest):
    if not OPENAI_API_KEY:
        return {"summary": req.text[:1000]}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        system = "Ты помощник VasDom. Суммируй встречу кратко, структурировано: итоги, поручения, сроки."
        user = f"Текст встречи:\n{req.text}\n\nСформируй краткое саммари ({req.style})."
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return {"summary": (resp.choices[0].message.content or "").strip()}
    except Exception as e:
        logger.error(f"meeting_summary error: {e}")
        return {"summary": req.text[:1000]}

@router.post("/tasks")
async def tasks_from_meeting(req: TasksFromMeetingRequest):
    # TODO: интеграция с Bitrix24 или локальным Task CRUD. Пока возвращаем echo-список как созданные задачи.
    created = []
    for it in req.items or []:
        created.append({"id": f"tmp_{abs(hash(it.title))%100000}", "title": it.title, "owner": it.owner, "due": it.due})
    return {"ok": True, "created": created}