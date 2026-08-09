<div align="center">

# 🗂️ File Ownership & Governance
### TraceIQ Codebase Accountability

</div>

---

To prevent merge conflicts and ensure code quality during the rapid pace of the hackathon, file ownership is strictly delineated. 

**Do not heavily modify files outside your domain without consulting the owner.**

---

## 👑 Team Lead (Suryansh)

*Owns the core architecture, schemas, and deployment infrastructure.*

- `backend/app/api/*` (FastAPI routing)
- `backend/app/schemas/*` (Strict Pydantic contracts)
- `backend/app/services/orchestrator.py`
- `backend/app/services/evidence_validator.py`
- `backend/app/services/confidence.py`
- `backend/app/services/recommendation.py`
- `backend/app/services/report_generator.py`
- `backend/app/middleware/*`
- `backend/app/utils/*`
- `backend/Dockerfile`
- `docker-compose.yml`
- `docs/*`

---

## 🤝 Shared Integration Points

*These files are the connective tissue of the application. They are designed to be extended by other team members.*

- **`backend/app/integrations/*`**: Yuvraj owns populating this directory with GitHub/Datadog providers.
- **`backend/app/rag/prompts.py`**: Shared prompts. Raghav and Suryansh collaborate here.
- **`backend/app/services/demo_mode.py`**: The fallback provider. Anyone can add synthetic data handling here.
- **`demo/scenario.json`**: The synthetic incident database. Highly collaborative.

---

## 🛠️ Upcoming Ownership

- **`frontend/*`**: Sparsh maintains total ownership of the React application and Voice integrations.
- **`knowledge/*`**: Raghav maintains ownership of scripts related to populating the Qdrant database.
