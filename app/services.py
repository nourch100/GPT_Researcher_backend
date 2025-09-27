import time
import logging

from typing import Optional
from sqlalchemy.orm import Session

from app.utils.date import extract_published_date
from .models import RunResult
from .gptr_client import get_researcher
from app.utils.export import append_ndjson
from .schemas import RunRequest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RunService:
    @staticmethod
    async def run_research_and_store(req: RunRequest, db: Session):
        """
        Run research using the specified provider and model, store the results in the DB
        """
        logger.info(f"Starting research run | provider={req.provider}, model={req.model}, query={req.query}")
        start = time.time()
        errors = None
        try:
            researcher = get_researcher(query=req.query, provider=req.provider, model=req.model, **req.run_config)
            await researcher.conduct_research()
            report = await researcher.write_report()
            source_urls = researcher.get_source_urls()
            research_costs = researcher.get_costs()
            research_images = researcher.get_research_images()
            research_sources = researcher.get_research_sources()

            if report is None:
                    logger.error("Researcher returned an empty report")
                    raise ValueError("Empty response from researcher")

            latency_ms = (time.time() - start) * 1000

            filtered_sources=[]
            for src in research_sources : 
                published = extract_published_date(src.get("raw_content",""))
                filtered_sources.append({
                    "url": src.get("url"),
                    "published": published,
                })

            run = RunResult(
                provider=req.provider,
                model=req.model,
                query=req.query,
                report=report,
                source_urls=source_urls,
                research_sources=filtered_sources,
                num_images= len(research_images),
                num_sources=len(research_sources),
                research_costs= research_costs,
                latency_ms= latency_ms,
                errors= errors,
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            logger.info(f"Finished research and stored run id={run.id} for query='{req.query}'")
            append_ndjson(run)
            return run
        
        except Exception as e:
            logger.error(f"Error during research run: {str(e)}")
            raise
    
    @staticmethod
    async def fetch_results_service(db:Session, provider: Optional[str]=None, model: Optional[str]=None,query_text: Optional[str]=None)-> list[RunResult]:
        """
        Fetch run results from DB.
        If provider or model or query is specified, filter accordingly.
        Otherwise return all results.
        """
        q =db.query(RunResult)
        if provider:
            q = q.filter(RunResult.provider == provider)
        if model:
            q = q.filter(RunResult.model == model)  
        if query_text:
            q = q.filter(RunResult.query == query_text)  
        results = q.all()
        return results
        

    @staticmethod
    async def delete_result_service(db: Session, run_id: int) -> dict:
        """
        Delete run results from DB by ID.
        Returns a status dict.
        """
        obj = db.query(RunResult).filter(RunResult.id == run_id).first()
        if not obj:
            return {"status": "error", "message": f"Row {run_id} not found"}

        db.delete(obj)
        db.commit()
        return {"status": "success", "message": f"Deleted row {run_id}"}
        
    