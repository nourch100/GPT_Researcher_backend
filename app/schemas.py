from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class RunRequest(BaseModel):
    provider: str
    model: str
    query: str
    run_config: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    provider: str
    model: str
    query: str
    report: str
    citations: List[Dict[str, Any]]
    metrics: Dict[str, Any]

