<div align="center">

# 🚑 Troubleshooting
### Diagnostics & Resolution

</div>

---

If the TraceIQ engine fails to start or process investigations, consult the following diagnostic steps.

---

## 1. Application Fails to Start

**Symptom:** `uvicorn` crashes immediately or Docker container exits.

- **Cause A: Missing Environment Variables.**
  Ensure you have copied `.env.example` to `.env`. The `pydantic_settings` module is extremely strict; if a required variable is completely missing from the `.env` file, the application will refuse to boot.
- **Cause B: Port Collision.**
  Ensure port `8000` is free. 
  *Fix:* Edit `.env` and `docker-compose.yml` to use port `8080` instead.

## 2. Pydantic Core Installation Failure (Windows Native)

**Symptom:** `pip install -r requirements.txt` fails with `linker link.exe not found` or Rust compilation errors.

- **Cause:** You are running a bleeding-edge Python version (like 3.14) that lacks pre-built wheels for `pydantic-core`, requiring local compilation which fails due to missing MSVC C++ Build Tools.
  *Fix:* Do not run natively. Use the provided Docker configuration:
  ```bash
  make docker-build
  make docker-run
  ```

## 3. Investigation Returns "Insufficient Evidence"

**Symptom:** The API returns `200 OK`, but the summary states the LLM could not determine a root cause.

- **Cause A: LLM API Failure.**
  If `DEMO_MODE=false`, ensure `LLM_API_KEY` is valid and the provider (e.g., OpenAI) is reachable. Check the terminal logs for `llm_call_failed` emitted by `structlog`.
- **Cause B: Evidence Validator Triggered.**
  The LLM hallucinated, and the `EvidenceValidator` stripped the response for safety. Check the terminal for `hallucinated_evidence_id_in_cause`.

## 4. Demo Mode Not Returning Data

**Symptom:** API returns empty evidence arrays during demo.

- **Cause:** The `demo/scenario.json` file is missing, malformed, or contains invalid JSON. The `DemoProvider` will catch the error and return an empty set to prevent crashing. Check the logs for `demo_scenario_load_failed`.
