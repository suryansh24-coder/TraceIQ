import os
import sys
from dotenv import load_dotenv

print("--- STARTING SCRIPT ---")

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

print(f"Token loaded: {token[:7]}..." if token else "CRITICAL: NO GITHUB_TOKEN FOUND IN .ENV!")

try:
    from backend.app.integrations.github import create_hotfix_pr
    print("Successfully imported create_hotfix_pr function!")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

REPO_NAME = "laviiyy/TraceIQ" 
FILE_PATH = "README.md"
NEW_CODE = "# TraceIQ\n\nAutomated AI Incident Response System - Live Integration Test!"

print(f"Attempting to connect to repo: {REPO_NAME}...")

try:
    res = create_hotfix_pr(
        repo_name=REPO_NAME,
        file_path=FILE_PATH,
        new_code=NEW_CODE,
        pr_title="test: TraceIQ automated PR test"
    )
    print("\n==========================================")
    print("SUCCESS! Pull Request Created:")
    print(res["pr_url"])
    print("==========================================\n")
except Exception as e:
    print(f"\nAPI Error encountered: {e}")

print("--- SCRIPT FINISHED ---")