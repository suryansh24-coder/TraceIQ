from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.schemas.investigation import InvestigationRequest, InvestigationResponse
from app.services.orchestrator import InvestigationOrchestrator
from app.middleware.rate_limit import rate_limit_middleware

logger = structlog.get_logger()
router = APIRouter()

# Instantiate the orchestrator once for dependency injection
orchestrator = InvestigationOrchestrator()

def get_orchestrator():
    return orchestrator

@router.post(
    "/investigate",
    response_model=InvestigationResponse,
    dependencies=[Depends(rate_limit_middleware)]
)
async def investigate_endpoint(
    request: InvestigationRequest,
    orch: InvestigationOrchestrator = Depends(get_orchestrator)
):
    """
    Process an engineer's incident investigation request.
    Collects evidence, applies LLM reasoning, validates, and returns structured findings.
    """
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty."
            )
            
        response = await orch.investigate(request)
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error("investigation_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail="Unable to complete investigation."
        )
