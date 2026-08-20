# Application Architecture

## High-level flow

The application follows a browser-to-API workflow. A user selects a contract in the frontend, the FastAPI backend stores and extracts the document, the orchestration layer dispatches analysis across category agents, the scoring engine combines judge outputs, and the result is persisted for later review and audit.

```text
Browser UI
   |
   | upload / status / results / history requests
   v
FastAPI application (`backend/main.py`)
   |
   +--> Upload routes ------------------> document storage and ingestion
   +--> Analysis routes -----------------> orchestration service
   +--> Audit routes --------------------> audit repository
   |
   v
Agent factory and category agents
   |
   +--> Legal
   +--> Compliance
   +--> Financial
   +--> Operational
   +--> Security
   +--> Fraud
   |
   v
Scoring engine
   |
   +--> rule judge
   +--> template judge
   +--> Bayesian judge
   +--> LLM judge
   |
   v
MongoDB repositories + audit trail
```

## Main components

| Component | Responsibility |
| --- | --- |
| `backend/main.py` | Creates the FastAPI application, configures middleware, mounts frontend assets, exposes page routes, and provides the health endpoint |
| `backend/routes/` | HTTP endpoints for uploads, analysis status/results, and audit/history operations |
| `backend/services/` | Document ingestion, analysis orchestration, and service-level coordination |
| `backend/agents/` | Category-specific prompts and analysis behaviors for the six policy domains |
| `backend/services/scoring/` | Rule, template, Bayesian, and LLM judge implementations plus weighted consensus calculation |
| `backend/repositories/` | Persistence abstractions for documents, analyses, and audit records |
| `backend/models.py` | Pydantic/domain models used for validation and API data exchange |
| `backend/core/` | Settings, dependency container, and shared database/runtime initialization |
| `frontend/` | Static UI pages and browser-side modules for upload and result presentation |

## Scoring flow

For each category, the system first calculates policy-defined sub-risk values and a weighted base score. The four judge strategies then provide independent scores. The scoring engine applies the policy weights, calculates confidence from the spread among judges, maps the final score to a risk band, and selects an action. Actions are aggregated into an overall contract state such as auto-approved, pending review, or blocked.

## External dependencies

The service is designed to use MongoDB for persistence and Azure OpenAI for LLM and embedding capabilities. Document extraction relies on the PDF, DOCX, and spreadsheet libraries listed in `requirements.txt`. These integrations require environment-specific credentials and should be configured outside Git.

## Runtime boundaries and hardening priorities

The source snapshot does not provide an authentication layer. A production deployment should place the service behind enterprise identity and authorization controls before it accepts confidential contracts. The default development CORS setting is permissive and should be restricted to approved frontend origins. Upload validation, malware scanning, storage encryption, audit retention, secrets management, and rate limiting should be reviewed before production use.
