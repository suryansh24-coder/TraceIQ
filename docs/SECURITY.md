<div align="center">

# 🛡️ Security Posture
### TraceIQ Application Security

</div>

---

While TraceIQ is a hackathon prototype, we treat security and data integrity as first-class citizens. Incident data is highly sensitive, and our architecture reflects enterprise-grade precautions.

---

## 🛑 1. Minimum Hallucination Guarantee

The most significant security risk of integrating LLMs into DevOps is the generation of fabricated facts (hallucinations), which could lead an engineer to take destructive actions.

**Our Mitigation:** The `EvidenceValidator`.
The LLM output is intercepted before it ever reaches the user. The Validator strictly checks every `supporting_evidence_id` cited by the LLM against the IDs of the actual evidence fetched during the request. If the LLM invents a commit hash or log entry, that recommendation is entirely stripped from the payload.

## 🔑 2. Secret Management

- **Absolute Zero Hardcoding:** No API keys (OpenAI, GitHub, Qdrant, Rime) are permitted in the source code.
- **Environment Driven:** All secrets are managed via `pydantic_settings` reading from `.env` or CI/CD environment variables.
- **No Log Leakage:** The `secrets.py` utility safely checks for the presence of keys without ever evaluating or logging their contents.

## 🧹 3. Input Sanitization

Voice-to-text can occasionally produce malformed strings, and API endpoints are vulnerable to injection.
- The `sanitization.py` utility aggressively strips null bytes (`\x00`) and malicious control characters from the user query while preserving legitimate technical content (like URLs or code snippets).

## 🚦 4. Rate Limiting & Abuse Prevention

- **MVP In-Memory Limiting:** The `rate_limit.py` middleware tracks IP addresses and enforces a strict window (e.g., 60 requests per 60 seconds) to prevent brute force or DDoS attempts on the expensive LLM endpoints.
- *(Production Ready)*: The architecture is designed to swap the in-memory dictionary for Redis effortlessly.

## 🌐 5. Network Security

- **CORS:** Strictly controlled via the `CORS_ORIGINS` environment variable.
- **Headers:** The `security.py` middleware injects foundational protections:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
