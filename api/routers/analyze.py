"""
MindWall — Analysis Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

POST /api/analyze — Primary endpoint for email analysis from both
the IMAP proxy and browser extension.
"""

import structlog
from fastapi import APIRouter, Request, HTTPException

from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_email(request: Request, payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    Submit an email for psychological manipulation analysis.

    Accepts email content and metadata from the IMAP proxy or browser extension,
    runs the full analysis pipeline, and returns manipulation scores.
    """
    pipeline = request.app.state.pipeline

    try:
        # Ensure employee record exists
        employee_repo = request.app.state.employee_repo
        await employee_repo.get_or_create(
            email=payload.recipient_email,
            display_name=None,
        )

        result = await pipeline.run(payload)

        logger.info(
            "analyze.complete",
            analysis_id=result.analysis_id,
            score=result.manipulation_score,
            severity=result.severity,
            processing_ms=result.processing_time_ms,
        )

        return result

    except Exception as e:
        logger.error("analyze.error", error=str(e), message_uid=payload.message_uid)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
