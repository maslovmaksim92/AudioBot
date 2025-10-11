TESTING PROTOCOL SUMMARY
- This file is created to track automated testing runs.
- Backend first, frontend optional per user instruction.
- All backend API routes are prefixed with /api.

RUN 2025-09-XX: Planned tests
- Health: GET /api/health should return 200 { ok: true }
- AI Assistant:
  * POST /api/ai-assistant/chat with { message: "Тест" } should return 200 and JSON (may depend on OPENAI_API_KEY)
  * POST /api/ai-assistant/analyze with { analysis_type: "financial" } should return 200 and JSON
  * GET /api/ai-assistant/context should return 200 and JSON

Notes
- If external API keys are missing, AI-related endpoints may return error payloads. Record and proceed.
- Do not modify URLs or .env values.
