<div align="center">

# 👥 Team Workplan
### StellarVisionAI Engineering Matrix

*Orchestrating talent for the StarForge Hackathon 2026.*

</div>

---

## 🎯 The Mission

Deliver a functional, voice-first incident intelligence platform that eliminates context-switching for DevOps engineers during critical outages. 

To achieve this under hackathon constraints, our team is executing a highly parallelized, decoupled micro-architecture strategy.

---

## 👨‍💻 Engineering Roster & Responsibilities

| Engineer | Domain | Core Responsibilities |
| :--- | :--- | :--- |
| **👑 Suryansh (Team Lead)** | **Core Engine & Architecture** | • Overall System Architecture & API Design<br>• Asynchronous `InvestigationOrchestrator`<br>• LLM Reasoning Interface<br>• The `EvidenceValidator` (Anti-hallucination engine)<br>• Confidence & Recommendation logic<br>• Dockerization & Render Deployment |
| **🛠️ Yuvraj** | **Live Data Integrations** | • `EngineeringContextProvider` Implementation<br>• GitHub API integration (commits, PRs)<br>• Datadog/Prometheus API integration (metrics, alerts)<br>• Normalizing live data into the `Evidence` schema |
| **🧠 Raghav** | **Retrieval-Augmented Generation** | • `KnowledgeRetriever` Implementation<br>• Qdrant Vector Database setup & hosting<br>• Embedding generation for historical incidents/runbooks<br>• Semantic search and relevance tuning |
| **🗣️ Sparsh** | **Frontend & Voice UI** | • React.js Dashboard application<br>• Microphone/Browser STT (Speech-to-Text) capture<br>• Rime API integration for premium TTS (Text-to-Speech)<br>• Visualizing the API timeline and evidence graphically |

---

## ⏱️ Execution Timeline

> [!TIP]
> **Integration Contract:** All team members must adhere strictly to the Pydantic schemas defined in `app/schemas/`. Do not alter the `Evidence` or `InvestigationResponse` signatures without consulting the Team Lead.

1. **Phase 1: Foundation (Day 1)**
   - API Contracts finalized.
   - Core orchestrator and `DEMO_MODE` established.
   - React scaffolding and Voice UI mocking.

2. **Phase 2: Integration (Day 2)**
   - Yuvraj wires live GitHub/Monitoring data.
   - Raghav connects the live Qdrant cluster.
   - Sparsh integrates Rime TTS with the live API response.

3. **Phase 3: Polish & Demo (Day 3)**
   - Final validation of the anti-hallucination pipeline.
   - UI styling and voice latency optimization.
   - Rehearsal of the `DEMO_SCRIPT.md`.
