<div align="center">

# 💻 Development Guide
### Engineering TraceIQ Locally

</div>

---

Welcome to the TraceIQ backend environment. We use a modernized Python stack emphasizing speed, type safety, and reproducibility.

---

## 🛠️ Prerequisites

- **Python**: `3.11` or higher.
- **Make**: For executing build commands.
- **Docker**: Highly recommended for consistent execution.

---

## 🚀 Quick Start (Docker - Recommended)

The most reliable way to run the backend, completely sidestepping local OS or compiler issues.

```bash
# 1. Clone and enter directory
git clone https://github.com/StellarVisionAI/TraceIQ.git
cd TraceIQ

# 2. Configure Environment
cp .env.example .env
# Edit .env and ensure DEMO_MODE=true for local testing without API keys

# 3. Build & Run
make docker-build
make docker-run
```

The API is now live at `http://localhost:8000`.

---

## 🐍 Native Setup

If you prefer to run bare-metal using `uvicorn`:

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # (On Windows: venv\Scripts\activate)

# 2. Configure Environment
cp .env.example .env

# 3. Install dependencies
make install

# 4. Start the development server
make dev
```

---

## 🧪 Testing

We use `pytest` for our test suites. Tests are configured to automatically force `DEMO_MODE=true` to prevent accidental consumption of API credits during CI/CD.

```bash
make test
```

## 💅 Linting & Formatting

We use `ruff`, an ultra-fast Rust-based linter, to maintain code quality.

```bash
# Check for errors
make lint

# Automatically fix and format code
make format
```
