from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import RunResult
from .schemas import RunRequest, RunResponse
from .database import get_session
from .services import RunService

router = APIRouter()

@router.post("/run", response_model=RunResponse)
async def run_research(req: RunRequest, db: Session = Depends(get_session)):
    try:
        response = await RunService.run_research_and_store(req, db)
        if not response or not response.report:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate report. Empty response from researcher.",
            )
        result = RunResponse(
            provider=response.provider,
            model=response.model,
            query=response.query,
            report=response.report,
            citations=response.research_sources or [],
            metrics={
                "research_costs": response.research_costs,
                "latency_ms": response.latency_ms,
                "errors": response.errors,
                "num_images" : response.num_images,
                "num_sources" : response.num_sources,
            },
            )
        return result
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except Exception:
        raise

@router.get("/results", response_model=List[RunResponse])
async def get_results(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    model: Optional[str] = Query(None, description="Filter by model"),
    query: Optional[str] = Query(None, description="Filter by query"),
    db: Session = Depends(get_session)
):
    try: 
        results = await RunService.fetch_results_service(db, provider, model, query_text=query)
        if not results:
            if provider and model and query:
                raise HTTPException(
                    status_code=404,
                    detail=f"No results found for provider='{provider}' and model='{model}' and query='{query}'"
                )
            elif provider:
                raise HTTPException(
                    status_code=404,
                    detail=f"No results found for provider='{provider}'"
                )
            elif model:
                raise HTTPException(
                    status_code=404,
                    detail=f"No results found for model='{model}'"
                )
            elif query:
                raise HTTPException(
                    status_code=404,
                    detail=f"No results found for query='{query}'"
                )
        else:
            final_results = []
            for res in results:
                final_results.append(RunResponse(
                    provider=res.provider,
                    model=res.model,
                    query=res.query,
                    report=res.report,
                    citations=res.research_sources or [],
                    metrics={
                        "research_costs": res.research_costs,
                        "latency_ms": res.latency_ms,
                        "errors": res.errors,
                        "num_images" : res.num_images,
                        "num_sources" : res.num_sources,
                    },
                ))
            return final_results
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except HTTPException:
        raise

@router.delete("/results/{run_id}")
async def delete_result(run_id: int, db: Session = Depends(get_session)):
    return await RunService.delete_result_service(db, run_id)


@router.get("/queries", response_model=List[str])
def get_queries(db: Session = Depends(get_session)):
    rows = db.query(RunResult.query).distinct().all()
    return [row[0] for row in rows if row[0]]