from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.app.integrations.monitoring import parse_alert_payload

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

class AlertPayload(BaseModel):
    service: str
    error_type: str
    message: str
    stack_trace: Optional[str] = ""

@router.post("/webhook")
def receive_monitoring_alert(payload: AlertPayload):
    parsed_data = parse_alert_payload(payload.model_dump())
    return {
        "status": "received",
        "alert": parsed_data
    }