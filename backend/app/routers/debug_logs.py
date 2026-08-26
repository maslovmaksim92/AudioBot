"""
Онлайн-просмотр логов из браузера: /api/debug/logs

Эндпоинты:
  GET /api/debug/logs          — таблица последних N строк (HTML)
  GET /api/debug/logs.txt      — сырой текст последних N строк
  GET /api/debug/logs/stream   — SSE-стрим новых строк в реальном времени
  GET /api/debug/logs/health   — короткая сводка (размер, последние ошибки)

Защита: токен из переменной окружения DEBUG_LOGS_TOKEN.
        Если переменная не задана — эндпоинты ВЫКЛЮЧЕНЫ (для безопасности).
        Передача: ?token=...  или  заголовок X-Debug-Token: ...
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger("debug_logs")

LOG_FILE = "/var/log/audiobot.log"
ERR_FILE = "/var/log/audiobot.err.log"


def _check_token(request: Request, token: Optional[str]):
    expected = os.environ.get("DEBUG_LOGS_TOKEN", "").strip()
    if not expected:
        raise HTTPException(503, "Debug logs disabled: set DEBUG_LOGS_TOKEN in .env")
    got = token or request.headers.get("X-Debug-Token") or ""
    if got != expected:
        raise HTTPException(403, "Bad token")


def _tail(path: str, n: int = 500) -> str:
    """Эффективный tail (читаем с конца блоками)."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 64 * 1024
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            return data.decode("utf-8", errors="replace").split("\n")[-n:].__iter__().__class__("\n".join(data.decode("utf-8", errors="replace").split("\n")[-n:]))
    except Exception as e:
        return f"[tail error: {e}]"


def _tail_lines(path: str, n: int = 500) -> list[str]:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 64 * 1024
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            return data.decode("utf-8", errors="replace").split("\n")[-n:]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [f"[tail error: {e}]"]


@router.get("/logs.txt", response_class=PlainTextResponse)
async def logs_txt(request: Request, token: Optional[str] = None,
                   n: int = 500, errors_only: bool = False):
    _check_token(request, token)
    path = ERR_FILE if errors_only else LOG_FILE
    lines = _tail_lines(path, min(max(n, 1), 5000))
    return "\n".join(lines)


@router.get("/logs", response_class=HTMLResponse)
async def logs_html(request: Request, token: Optional[str] = None,
                    n: int = 500, errors_only: bool = False, filter: str = ""):
    _check_token(request, token)
    path = ERR_FILE if errors_only else LOG_FILE
    lines = _tail_lines(path, min(max(n, 1), 5000))
    if filter:
        f = filter.lower()
        lines = [ln for ln in lines if f in ln.lower()]

    def color(ln: str) -> str:
        import html as _h
        e = _h.escape(ln)
        if " E " in ln or "ERROR" in ln or "Traceback" in ln:
            return f'<div class="e">{e}</div>'
        if " W " in ln or "WARNING" in ln:
            return f'<div class="w">{e}</div>'
        if "HTTP←" in ln or "HTTP→" in ln:
            return f'<div class="h">{e}</div>'
        if "[MAX" in ln:
            return f'<div class="m">{e}</div>'
        return f'<div>{e}</div>'

    body = "\n".join(color(l) for l in lines if l)
    title = "ERRORS" if errors_only else "LOGS"
    next_q = f"?token={token or ''}&n={n}&errors_only={str(errors_only).lower()}&filter={filter}"
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{title} · audiobot</title>
<style>
  body{{background:#0f172a;color:#e2e8f0;font-family:Menlo,Consolas,monospace;font-size:12px;margin:0;padding:8px}}
  .bar{{position:sticky;top:0;background:#1e293b;padding:8px;margin:-8px -8px 8px;border-bottom:1px solid #334155;display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
  a,a:visited{{color:#60a5fa;text-decoration:none}}
  a:hover{{text-decoration:underline}}
  input,button,select{{background:#0f172a;color:#e2e8f0;border:1px solid #475569;padding:4px 8px;border-radius:4px;font:inherit}}
  button{{cursor:pointer}}
  .e{{color:#fca5a5}} .w{{color:#fcd34d}} .h{{color:#86efac}} .m{{color:#93c5fd}}
  div{{white-space:pre-wrap;word-break:break-all;padding:1px 0}}
  .stats{{color:#94a3b8;font-size:11px}}
</style></head><body>
<div class="bar">
  <strong>📜 {title}</strong>
  <span class="stats">{len(lines)} строк</span>
  <a href='/api/debug/logs?token={token or ''}&n={n}&errors_only=false'>Все</a>
  <a href='/api/debug/logs?token={token or ''}&n={n}&errors_only=true'>Ошибки</a>
  <a href='/api/debug/logs?token={token or ''}&n={n}&filter=MAX'>MAX</a>
  <a href='/api/debug/logs?token={token or ''}&n={n}&filter=bitrix'>Bitrix</a>
  <a href='/api/debug/logs?token={token or ''}&n={n}&filter=HTTP'>HTTP</a>
  <form style="display:inline;margin-left:8px">
    <input type=hidden name=token value="{token or ''}">
    <input type=hidden name=n value="{n}">
    <input type=hidden name=errors_only value="{str(errors_only).lower()}">
    <input type=text name=filter value="{filter}" placeholder='фильтр (подстрока)' size=20>
    <button type=submit>Фильтр</button>
  </form>
  <button onclick="location.reload()">↻ Обновить</button>
  <label><input type=checkbox id=auto> авто (5с)</label>
</div>
{body}
<script>
  const auto=document.getElementById('auto');
  let t=null;
  auto.onchange=()=>{{ if(auto.checked){{ t=setInterval(()=>location.reload(),5000); }} else {{ clearInterval(t); }} }};
  window.scrollTo(0, document.body.scrollHeight);
</script>
</body></html>"""


@router.get("/logs/health")
async def logs_health(request: Request, token: Optional[str] = None):
    _check_token(request, token)
    def stat(path):
        try:
            p = Path(path)
            return {"path": path, "exists": p.exists(),
                    "size_mb": round(p.stat().st_size / 1024 / 1024, 2) if p.exists() else 0}
        except Exception:
            return {"path": path, "exists": False}
    # последние 3 ошибки
    err_lines = _tail_lines(ERR_FILE, 30)
    recent_errors = [l for l in err_lines if l.strip()][-5:]
    return {
        "main_log": stat(LOG_FILE),
        "err_log": stat(ERR_FILE),
        "recent_errors": recent_errors,
    }


@router.get("/logs/stream")
async def logs_stream(request: Request, token: Optional[str] = None):
    _check_token(request, token)

    async def gen():
        try:
            f = open(LOG_FILE, "r", encoding="utf-8", errors="replace")
            f.seek(0, 2)
            while True:
                if await request.is_disconnected():
                    break
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line.rstrip()}\n\n"
        except Exception as e:
            yield f"data: [stream error: {e}]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
