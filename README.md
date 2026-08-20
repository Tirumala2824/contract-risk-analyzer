# Contract Risk Analyzer

An enterprise-oriented contract risk analysis platform that combines deterministic scoring, multi-agent review, confidence calibration, and auditable decisioning. The application provides a browser-based workflow for uploading a contract, running category-level analysis, reviewing evidence and recommendations, and inspecting prior analysis history.

> **Project status:** This repository is an organized source snapshot prepared from the supplied project archive. It is intended for further engineering, integration, and validation; it is not legal advice and should not be used as the sole basis for a contractual decision.

## What the system does

The platform evaluates contracts across six independent risk categories defined by the supplied enterprise scoring policy: **Legal, Compliance, Financial, Operational, Security, and Fraud**. Each category combines deterministic rules with several judging strategies, produces a score from 0 to 100, calculates model-agreement confidence, and maps the result to an actionable review recommendation.

The bundled frontend is a static HTML/CSS/JavaScript interface. The backend is a FastAPI service responsible for upload handling, document ingestion, orchestration, risk scoring, persistence, audit records, and health checks.

## Repository layout

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI application, agents, routes, services, repositories, scoring engine, and data models |
| `frontend/` | Static browser interface for upload, status, results, summary, and history views |
| `docs/assets/` | Supplied enterprise scoring policy PDF and Contract Risk Analyzer demo video |
| `uploads/` | Runtime upload directory; only `.gitkeep` is versioned |
| `.env.example` | Configuration template for Azure OpenAI, MongoDB, and application settings |
| `requirements.txt` | Python dependencies |

The scoring model is summarized in [`docs/scoring-policy-summary.md`](docs/scoring-policy-summary.md), while the application flow is described in [`docs/architecture.md`](docs/architecture.md).

## Prerequisites

Use Python 3.10 or newer, a MongoDB deployment reachable by the backend, and an Azure OpenAI deployment if LLM-backed judging is enabled. The dependency list also includes document-processing, FastAPI, persistence, and test packages.

## Local setup

```bash
git clone <private-repository-url>
cd contract-risk-analyzer

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# Edit .env with the MongoDB and Azure OpenAI values for your environment.

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/> after the service starts. The health endpoint is available at <http://127.0.0.1:8000/health>.

For a deployment-specific Azure OpenAI connectivity check, use:

```bash
python -m backend.scripts.verify_azure_connection
```

## Configuration

The application reads environment variables from `.env`. Never commit populated credentials. The repository includes only blank configuration placeholders in `.env.example`.

| Variable group | Main settings |
| --- | --- |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_URL`, `AZURE_OPENAI_MODEL`, `AZURE_EMBEDDING_MODEL`, `AZURE_OPENAI_API_VERSION` |
| MongoDB | `MONGODB_USERNAME`, `MONGODB_PASSWORD`, `MONGODB_HOST`, `MONGODB_DATABASE`, `MONGODB_USE_SRV` |
| Application | `APP_NAME`, `APP_VERSION`, `DEBUG` |
| Uploads | `MAX_FILE_SIZE_MB`, `ALLOWED_EXTENSIONS`, `UPLOAD_DIR` |

## Risk-scoring policy

The supplied policy defines a deterministic and auditable scoring framework:

1. Each category calculates weighted sub-risk scores and a category base score.
2. Four judges produce category scores: rule-based, template-based, Bayesian, and LLM-based.
3. The final score uses the policy weights `0.30 / 0.30 / 0.25 / 0.15`.
4. Confidence is derived from judge-score spread, with larger disagreement producing lower confidence.
5. Risk bands range from **Low** through **Critical**, and category actions determine the overall contract status.

The complete source policy is preserved at [`docs/assets/enterprise-contract-risk-scoring-policy.pdf`](docs/assets/enterprise-contract-risk-scoring-policy.pdf). The policy summary in this repository is a navigation aid, not a replacement for that source document.

## Demo

The supplied walkthrough video is available at [`docs/assets/contract-risk-analyzer-demo.mp4`](docs/assets/contract-risk-analyzer-demo.mp4).

## Development notes

The project is currently delivered as a source snapshot rather than a production deployment. Before production use, validate the database configuration, authentication and authorization boundaries, CORS policy, file-validation behavior, observability, retention rules, and legal/compliance controls. Add automated tests for the scoring engine and API routes as the next engineering step.

## Data and privacy

Contract files can contain confidential information. Runtime uploads are intentionally excluded from Git history by `.gitignore`. Use a controlled storage system, apply appropriate access controls, and confirm retention and deletion requirements before connecting real enterprise data.

## License

No open-source license has been supplied with the project. All rights remain with the project owner unless a separate written license is provided.
