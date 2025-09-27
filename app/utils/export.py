import json
from pathlib import Path
from app.models import RunResult

LOG_PATH = Path("logs")
LOG_PATH.mkdir(exist_ok=True)

def append_ndjson(run: RunResult):
    p = LOG_PATH / "runs.ndjson"
    record = {
        "id": run.id,
        "provider": run.provider,
        "model": run.model,
        "query": run.query,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "report_text": run.report,  
        "source_urls": run.source_urls,
        "num_images": run.num_images,
        "num_sources": run.num_sources,
        "latency_ms": run.latency_ms,
        "research_costs": run.research_costs,
        "errors": run.errors,       
    }
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
