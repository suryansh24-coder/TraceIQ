<div align="center">

# 🤖 AI Usage Disclosure
### StarForge Hackathon 2026

</div>

---

In adherence to the StarForge Hackathon 2026 rules and guidelines regarding artificial intelligence and synthetic generation, we proudly disclose the methodologies used during the creation of **TraceIQ**.

---

## 🛠️ Code Generation & Architecture

The core backend architecture, rigorous schema designs, and foundational boilerplate were rapidly scaffolded using advanced AI coding assistants. This allowed our engineering team to focus on the high-value logic: the orchestration pipeline, deterministic evidence validation, and the voice integration layer.

**Tools utilized:**
- GitHub Copilot / Cursor
- Gemini Advanced Agentic Coding

**Impact:** Accelerated initial API routing, Pydantic data model generation, and Dockerization.

## 🗣️ Voice Generation

The entire premise of TraceIQ relies on delivering actionable intelligence back to the engineer seamlessly. We utilize the **Rime API** for ultra-realistic Text-to-Speech (TTS) generation. The voices heard in the application demo are entirely synthetic, crafted dynamically from the LLM's analytical output.

## 🧠 LLM Reasoning Node

At the heart of TraceIQ's investigation engine sits a Large Language Model (e.g., GPT-4/Anthropic). 
**Crucially, we do not use the LLM to generate code or act as an autonomous agent in production.** 
Instead, we strictly confine it to act as a *Reasoning Node*. It receives a chronologically ordered array of facts and is programmatically constrained by the `EvidenceValidator` to ensure it cannot hallucinate beyond the provided incident data.
