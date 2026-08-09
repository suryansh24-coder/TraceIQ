<div align="center">

# ☁️ Cloud Deployment
### Scaling TraceIQ via Render

</div>

---

TraceIQ is engineered for containerized, cloud-native environments. For the StarForge Hackathon 2026, we utilize **Render.com** for continuous, zero-downtime deployments.

---

## 🚀 Continuous Deployment Setup

Render automatically detects the `Dockerfile` and builds the production image on every push to the `main` branch.

### 1. Initialize the Web Service
- Navigate to the Render Dashboard and create a new **Web Service**.
- Connect the `StellarVisionAI/TraceIQ` GitHub repository.

### 2. Configure the Build Environment
- **Runtime:** `Docker`
- **Dockerfile Path:** `deployment/docker/backend.Dockerfile`
  *(Note: This Dockerfile sets the build context to the repository root to correctly copy the `backend` directory).*

### 3. Production Environment Variables
Inject the following into the Render dashboard to secure the production instance:

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables strict error handling (no stack traces). |
| `DEMO_MODE` | `true` | Ensures deterministic execution for the hackathon judging. |
| `CORS_ORIGINS` | `https://traceiq-frontend.vercel.app` | Restricts API access to the React client. |

### 4. Health & Readiness Probes
Render relies on HTTP probes to route traffic. TraceIQ natively exposes these:
- **Health Check Path:** `/health`
- **Readiness Check Path:** `/health/ready`

*Once deployed, Render will issue a secure `https://` URL for the Voice UI to connect to.*
