from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class RunResult(Base):
    __tablename__ = "run_results_research"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    model = Column(String)
    query = Column(Text)
    report = Column(Text)
    source_urls = Column(JSON, nullable=True)  
    research_sources = Column(JSON, nullable=True)  
    num_images = Column(Integer, default=0)         
    num_sources = Column(Integer, default=0)      
    research_costs = Column(Float, nullable=True)    
    latency_ms = Column(Float)
    errors = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
