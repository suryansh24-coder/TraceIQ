<div align="center">

# 🎬 Live Demonstration Script
### Experiencing TraceIQ

*Step-by-step guide to showcasing the power of voice-first DevOps intelligence.*

</div>

---

This script is designed for judging panels and product demonstrations. It utilizes `DEMO_MODE` to ensure a flawless, deterministic presentation without relying on live external APIs that could rate-limit or timeout during a pitch.

---

## 🎯 The Scenario

An engineer receives a PagerDuty alert at 2:00 AM. The legacy Payment API is throwing a massive spike of HTTP 401 Unauthorized errors. Instead of booting up Datadog, GitHub, and Jira, the engineer opens TraceIQ.

## 🚀 Execution Steps

### 1. Boot the Engine
Ensure the backend is running in deterministic mode. Check the `.env` file for `DEMO_MODE=true`.
```bash
make dev
```

### 2. Enter the Interface
Open the API documentation to simulate the frontend payload submission:
**`http://localhost:8000/docs`**

### 3. The Voice Query
Navigate to `POST /api/v1/investigate`. Simulate the transcription of the engineer's frantic voice request:

**Payload:**
```json
{
    "query": "TraceIQ, why is the Payment API returning authentication errors for legacy clients?",
    "service": "payment-api",
    "severity": "high"
}
```

### 4. The Magic (Observe the Response)
Execute the request. TraceIQ completes its orchestration in under 2 seconds. Point out the following to the audience:

- **The Timeline:** Note how TraceIQ chronologically ordered the GitHub deployment *before* the 401 metric spike.
- **The Evidence Validator:** Explain that the `likely_causes` are not hallucinated guesses; they explicitly cite `supporting_evidence_ids` like `commit_123456` and `metric_401_spike`.
- **The Recommendation:** Highlight the actionable output ("Revert strict audience checking") which is now being sent to the Rime TTS engine to be spoken aloud to the engineer.
