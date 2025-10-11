# AudioBot / VasDom Cleanup & Documentation Plan

## 1) Executive Summary
- Goal: Eliminate duplicate/legacy files, align codebase with the canonical VasDom architecture, and deliver clear documentation to avoid future duplication/regression.
- Finding: Current /app is a minimal starter; the GitHub repo hosts the full VasDom application (modular backend, rich frontend, and multiple integrations). No duplicates exist in the current /app workspace.
- Outcome: Produce authoritative structure docs, migration/cleanup checklist, and guardrails (coding & branching standards) to keep the repo consistent and healthy.

## 2) Objectives
1. Document the correct, canonical application structure (backend, frontend, tasks, integrations).
2. Create comprehensive engineering docs to prevent duplication and drift.
3. Preserve environment configuration and deployment practices.
4. Define testing, linting, and CI conventions so the app works reliably end-to-end.

## 3) UI/UX Design Guidelines (placeholder)
- This section will be finalized after design system review. It will include tokens (colors, spacing, radii), typography (primary font, scale), light/dark variants, component usage (shadcn/ui), and accessibility requirements.

## 4) Implementation Steps
- Phase A: Audit & Baseline
  - Confirm canonical structure from GitHub repository and lock it in documentation.
  - Inventory environment variables and provider-specific keys.
- Phase B: Cleanup & Refactor Guardrails
  - Add duplication-prevention rules, naming conventions, and folder ownership docs.
  - Introduce code owners, review checklist, and PR templates (if applicable).
- Phase C: Observability & Testing
  - Define smoke tests (health, key endpoints), UI sanity checks, and logging standards.
  - Establish linting/formatting for both backend and frontend.
- Phase D: Handoff
  - Provide runbooks for local dev and deployment.
  - Provide an FAQs/playbook to resolve common issues quickly.

## 5) Technical Details
- Backend: FastAPI, modular routers, DB access layer, async patterns, proper CORS, timezone-aware datetimes.
- Frontend: React + Router, Tailwind, shadcn/ui, feature routes (Dashboard, Works, AI, Meetings, Training, etc.).
- Integrations: Bitrix24, Emergent LLM, OpenAI Realtime, LiveKit, Telegram, Google Maps (optional).
- Data & Time: UUIDs for identifiers where DB schema permits; all datetimes in timezone.utc on the server.

## 6) Next Actions
- Pull design guidelines and finalize Section 3.
- Produce architecture diagrams and folder-by-folder documentation.
- Write prevention policy to stop duplicate file creation.
- Validate environment variables and secrets handling against deployment targets.

## 7) Success Criteria
- Single canonical structure documented and adopted.
- No duplicate/legacy files remain after cleanup.
- Green smoke tests and no critical console/server errors.
- Clear docs enabling any contributor to set up, extend, and deploy without reintroducing duplicates.
