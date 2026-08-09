<div align="center">

# 🎭 TraceIQ Synthetic Environment
### Deterministic Demo Mode

</div>

---

The `demo/` directory houses the synthetic incident databases required for a flawless, deterministic presentation of TraceIQ.

When presenting at a hackathon or to stakeholders, relying on live external APIs (GitHub, Datadog) introduces unacceptable risk (rate limits, network latency, unpredictable data). 

---

## ⚙️ How Demo Mode Operates

When the `DEMO_MODE=true` flag is detected in the `.env` configuration:
1. The `InvestigationOrchestrator` bypasses all live external HTTP calls.
2. The `DemoProvider` seamlessly intercepts the request and loads the highly curated synthetic data from `scenario.json`.
3. The LLM Service bypasses the live OpenAI/Anthropic network call and returns a deterministic, pre-validated JSON structure.
4. The rest of the engine (Validation, Confidence, Recommendation) executes exactly as it would in production, proving the pipeline works end-to-end.

---

## 🧪 The "Payment 401" Scenario (`scenario.json`)

Our primary showcase incident.

**The Context:** A recent commit updated the authentication middleware to strictly enforce JWT `aud` (audience) claims. This successfully deployed to production, but immediately caused legacy checkout services (which don't send the `aud` claim) to fail with HTTP 401s.

**The Evidence Injected:**
- **`commit_123456`**: The actual code change.
- **`deploy_prod_89`**: The CI/CD deployment event.
- **`metric_401_spike`**: The Datadog metric anomaly.
- **`alert_auth_fail`**: The PagerDuty trigger.
- **`historical_inc_44`**: A simulated Qdrant vector retrieval of a remarkably similar incident from 2025.
