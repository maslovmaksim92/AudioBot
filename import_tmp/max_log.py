p = '/opt/audiobot/backend/app/services/max_service.py'
s = open(p, encoding='utf-8').read()

# 1) send_message: тело + статус
OLD1 = '''    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] send_message {r.status_code}: {r.text[:300]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] send_message error: {e}")
        return None'''
NEW1 = '''    n_rows = len(buttons) if buttons else 0
    logger.debug(f"[MAX] send_message → chat={chat_id} text={text[:80]!r} rows={n_rows}")
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] send_message {r.status_code} chat={chat_id} rows={n_rows} body={r.text[:300]}")
            else:
                logger.info(f"[MAX] send_message ok chat={chat_id} rows={n_rows} status={r.status_code}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] send_message error chat={chat_id} rows={n_rows}: {e}")
        return None'''
assert OLD1 in s
s = s.replace(OLD1, NEW1)

# 2) answer_callback: тело + статус + кол-во рядов
OLD2 = '''    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/answers",
                params={"callback_id": callback_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] answer_callback {r.status_code}: {r.text[:300]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] answer_callback error: {e}")
        return None'''
NEW2 = '''    n_rows = len(buttons) if buttons else 0
    logger.debug(f"[MAX] answer_callback → cb={callback_id[:12]} new_text={(new_text or text or '')[:80]!r} rows={n_rows}")
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/answers",
                params={"callback_id": callback_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] answer_callback {r.status_code} cb={callback_id[:12]} rows={n_rows} body={r.text[:300]}")
            else:
                logger.info(f"[MAX] answer_callback ok cb={callback_id[:12]} rows={n_rows} status={r.status_code}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] answer_callback error cb={callback_id[:12]} rows={n_rows}: {e}")
        return None'''
assert OLD2 in s
s = s.replace(OLD2, NEW2)

open(p, 'w', encoding='utf-8').write(s)
print("OK: MAX-обмен логируется детально (rows, status, ошибки с контекстом)")
