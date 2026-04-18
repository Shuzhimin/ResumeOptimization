# AGENTS.md

## Project Overview

This repository implements a **Resume Optimization Agent Application**.

The system helps users:
1. Input or upload a resume
2. Provide a target job description (JD)
3. Analyze the match between resume and JD
4. Generate:
   - matching strengths
   - major gaps
   - actionable suggestions
5. After user confirmation, generate an optimized resume
6. Allow users to view and export results

This is a **full-stack application** with strict technical and delivery requirements.

---

## Tech Stack (MANDATORY)

- Python backend with:
  - FastAPI
  - Pydantic
  - uv (for dependency management)
- Frontend:
  - Vue 3
- Deployment:
  - Docker

---

## Non-Negotiable Requirements

All contributors MUST follow:

1. A runnable application must be delivered
2. Root directory MUST contain:
   - `Dockerfile`
   - `README.md`
3. Application must run via Docker
4. LLM API key:
   - MUST be read from environment variables
   - MUST NOT be hardcoded anywhere
5. README must allow a reviewer to:
   - configure environment
   - build image
   - run service
   - access system
   - complete a basic test flow

---

## Core Product Flow (REQUIRED)

The system must implement this full workflow:

1. Input Resume
2. Input JD
3. Analyze match
4. Show:
   - strengths
   - gaps
   - suggestions
5. User confirms optimization
6. Generate optimized resume
7. Display and export result

---

## Repository Structure (Recommended)

```text
.
├── AGENTS.md
├── README.md
├── Dockerfile
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── prompts/
│   │   └── core/
│   ├── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
└── examples/