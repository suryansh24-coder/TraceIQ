<div align="center">

# 🔌 API Contract
### TraceIQ Backend Interfaces

*Strictly typed, asynchronously executed, securely delivered.*

</div>

---

## 📡 Base URL
All API requests are made against the configured TraceIQ backend base URL. During local development, the default base URL is `http://localhost:8000`.

---

## 🟢 System Endpoints

### 1. Health Check
Verifies the application is running and the ASGI server is accepting connections.

- **Endpoint:** `GET /health`
- **Response `200 OK`:**
  ```json
  {
      "status": "ok",
      "service": "TraceIQ"
  }
  ```

### 2. Readiness Probe
Verifies that the application is ready to serve investigation requests and can be used by deployment or runtime health checks.

- **Endpoint:** `GET /health/ready`
- **Response `200 OK`:**
  ```json
  {
      "status": "ready",
      "service": "TraceIQ",
      "mode": "demo" 
  }
  ```

---

## 🧠 Investigation Engine

### `POST /api/v1/investigate`
This is the primary investigation endpoint. It accepts a structured request containing a natural-language investigation query (which may originate from the voice interaction layer after transcription) and optional incident context.

#### Request Headers
- `Content-Type: application/json`

#### Request Body Schema
```json
{
    "query": "Why is the Payment API returning authentication errors?",
    "incident_id": "INC-2026-001",
    "service": "payment-api",
    "severity": "high",
    "conversation_id": "session-89",
    "context": {}
}
```

#### Request Fields Contract

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | The natural-language investigation query. |
| `incident_id` | string | No | An optional identifier for the incident being investigated. |
| `service` | string | No | The specific service or microservice involved in the incident. |
| `severity` | string | No | The incident severity. Allowed values: `low`, `medium`, `high`, `critical`. |
| `conversation_id` | string | No | An identifier to correlate investigation requests within a continuous session. |
| `context` | object | No | Additional key-value pairs representing unstructured context about the incident. |

#### Response `200 OK`
A structured investigation result detailing the incident timeline, validated causes, and recommended next steps.

```json
{
    "request_id": "a1b2c3d4-e5f6...",
    "incident_id": "INC-2026-001",
    "service": "payment-api",
    "summary": "Based on the evidence, the recent authentication middleware update likely caused a spike in 401 errors for legacy clients.",
    "timeline": [
        {
            "timestamp": "2026-08-09T14:02:00Z",
            "description": "Update authentication middleware logic",
            "evidence_ids": ["commit_123456"]
        }
    ],
    "evidence": [
        {
            "id": "commit_123456",
            "source": "github",
            "title": "Update authentication middleware logic",
            "content": "Refactored JWT validation to use strict audience checking...",
            "timestamp": "2026-08-09T14:02:00Z",
            "relevance_score": 0.95,
            "metadata": {"repo": "payment-api"},
            "evidence_type": "commit"
        }
    ],
    "likely_causes": [
        {
            "cause": "Authentication middleware update caused audience mismatch.",
            "explanation": "Commit 123456 introduced strict audience checking...",
            "supporting_evidence_ids": ["commit_123456", "metric_401_spike"],
            "confidence": "high"
        }
    ],
    "confidence": {
        "level": "high",
        "score": 0.85,
        "basis": [
            "Multiple pieces of evidence available",
            "Evidence corroborated across multiple independent sources"
        ]
    },
    "recommendations": [
        {
            "action": "Revert the strict audience checking in payment-api.",
            "reason": "Restores access for legacy clients while a proper migration path is designed.",
            "priority": "high",
            "supporting_evidence_ids": ["commit_123456", "metric_401_spike"]
        }
    ],
    "follow_up_questions": [
        "Which clients are currently failing authentication?"
    ],
    "sources": [
        "github",
        "monitoring",
        "qdrant"
    ],
    "processing_metadata": {
        "llm_used": true,
        "duration_ms": 1245,
        "demo_mode": true
    }
}
```

#### Response Field Contracts

**Timeline Object**
- `timestamp`: The chronological timestamp of the event.
- `description`: A description of what occurred.
- `evidence_ids`: An array of IDs referencing evidence objects returned in the evidence collection.

**Evidence Object**
- `id`: Uniquely identifies the evidence item within the investigation result.
- `source`: The provider of the evidence (e.g., `github`, `monitoring`).
- `title`: A short title for the evidence.
- `content`: The raw or processed evidence content.
- `timestamp`: When the evidence occurred or was collected.
- `relevance_score`: A numeric relevance value determining the evidence's importance to the query.
- `metadata`: Additional properties related to the evidence item.
- `evidence_type`: The classification of the evidence (e.g., `commit`, `log`, `metric`).

**Likely Cause Object**
- `cause`: A short description of the probable cause.
- `explanation`: A detailed explanation of why this cause is likely.
- `supporting_evidence_ids`: An array referencing evidence IDs present in the collected evidence context. This connects the cause to the validated evidence, reflecting TraceIQ's evidence-grounded reasoning.
- `confidence`: The assessed confidence level of this specific cause.

**Confidence Object**
- `level`: The qualitative confidence level. Allowed values: `low`, `medium`, `high`.
- `score`: A numeric value from `0` to `1`. This score represents the deterministic confidence assessment produced by TraceIQ's confidence logic.
- `basis`: An array of text explanations detailing why this confidence score was given.

**Recommendation Object**
- `action`: The recommended mitigation or remediation step.
- `reason`: The justification for taking this action.
- `priority`: The urgency of the action (e.g., `high`).
- `supporting_evidence_ids`: An array tied directly to returned evidence IDs, providing the rationale for the recommendation.

**Sources Array**
An array of source identifiers that contributed to the investigation context. Valid identifiers in the current contract include: `github`, `monitoring`, `qdrant`.

**Processing Metadata Object**
- `llm_used`: Boolean indicating if the LLM was utilized for reasoning.
- `duration_ms`: Numeric processing duration. *(Note: The value 1245 in the example is strictly illustrative and does not represent a guaranteed performance benchmark).*
- `demo_mode`: Boolean indicating if deterministic synthetic incident data was used.

#### Error Responses
- **`400 Bad Request`**: The investigation payload is malformed or missing the required `query` field.
- **`429 Too Many Requests`**: The rate limit for the API has been exceeded.
- **`500 Internal Server Error`**: An unexpected failure occurred during the investigation orchestration.

---

## 🏗️ Frontend Consumer Clarity

This API contract serves as the primary interface consumed by the TraceIQ frontend. 

When visualizing an investigation, the frontend must rely on the explicit relationships defined by the `evidence_ids`. Specifically:
- `likely_causes[].supporting_evidence_ids` → `evidence[].id`
- `recommendations[].supporting_evidence_ids` → `evidence[].id`
- `timeline[].evidence_ids` → `evidence[].id`

By mapping these IDs, the frontend can render an interactive and verifiable investigation result where every claim traces back to collected engineering context.

---

## 📐 API Design Principles

- **Validated Inputs**: Requests are validated for schema correctness before any investigation begins.
- **Structured Outputs**: Investigation results are structured deterministically.
- **Evidence-Grounded**: Evidence IDs connect causes and recommendations directly to collected engineering evidence. Unsupported evidence references should not be returned as validated conclusions.
- **Frontend-Driven Interface**: The API contract is the formal interface consumed by the frontend, strictly defining the boundaries of data delivery without exposing internal architectural transitions.
