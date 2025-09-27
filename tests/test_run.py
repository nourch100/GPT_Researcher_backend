import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.main import app
from app.models import Base, RunResult
from app.database import get_session

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture
def async_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_run_research_and_store_success(monkeypatch, async_client):
    """
    Test /run works with a fake researcher
    """
    class FakeResearcher:
        async def conduct_research(self): return None
        async def write_report(self): return "This is a fake report"
        def get_source_urls(self): return ["http://example.com"]
        def get_costs(self): return 0.01
        def get_research_images(self): return []
        def get_research_sources(self):
            return [{"url": "http://example.com", "raw_content": "Published 2025"}]

    monkeypatch.setattr("app.services.get_researcher", lambda **kwargs: FakeResearcher())

    payload = {"provider": "openai", "model": "gpt-4.1", "query": "Test query", "run_config": {}}

    async with async_client as ac:
        response = await ac.post("/run", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4.1"
    assert data["query"] == "Test query"
    assert data["report"] == "This is a fake report"
    assert "metrics" in data
    assert "citations" in data

@pytest.mark.asyncio
async def test_run_research_empty_report_failure(monkeypatch):
    """
    Simulate researcher failure that generates empty report
    """
    class FakeRunResponse:
        provider = "openai"
        model = "gpt-5"
        query = "bad query"
        report = None  
        research_sources = []
        research_costs = 0.01
        latency_ms = 10
        errors = None
        num_images = 0
        num_sources = 0

    async def fake_run_research_and_store(req, db):
        return FakeRunResponse()
    
    monkeypatch.setattr("app.routes.RunService.run_research_and_store", fake_run_research_and_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/run", json={
            "provider": "openai",
            "model": "gpt-5",
            "query": "bad query",
            "run_config": {}
        })
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate report. Empty response from researcher."


@pytest.mark.asyncio
async def test_run_research_db_error(monkeypatch, async_client):
    """
    Simulate a DB error during /run
    """
    async def fake_run_research_and_store(*args, **kwargs):
        raise SQLAlchemyError("DB down")

    monkeypatch.setattr("app.routes.RunService.run_research_and_store", fake_run_research_and_store)

    payload = {"provider": "openai", "model": "gpt-9", "query": "test", "run_config": {}}
    async with async_client as ac:
        res = await ac.post("/run", json=payload)

    assert res.status_code == 500
    assert "Database error" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_results(async_client):
    """
    Fetch all results
    """
    async with async_client as ac:
        res = await ac.get("/results")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_provider_nonexistent(async_client):
    """
    Request results with a nonexistent provider
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"provider": "nonexistent"})
    assert res.status_code == 404
    assert "No results found for provider" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_results_model_nonexistent(async_client):
    """
    Request results with a nonexistent model
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"model": "nonexistent"})
    assert res.status_code == 404
    assert "No results found for model" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_results_query_nonexistent(async_client):
    """
    Request results with a nonexistent query
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"query": "nonexistent"})
    assert res.status_code == 404
    assert "No results found for query" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_results_filter_by_model_success(async_client):
    """
    Filter results by model
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"model": "gpt-4.1"})
    assert res.status_code == 200
    data = res.json()
    assert all(item["model"] == "gpt-4.1" for item in data)

@pytest.mark.asyncio
async def test_get_results_filter_by_provider_success(async_client):
    """
    Filter results by provider
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"provider": "openai"})
    assert res.status_code == 200
    data = res.json()
    assert all(item["provider"] == "openai" for item in data)


@pytest.mark.asyncio
async def test_get_results_filter_by_query_success(async_client):
    """
    Filter results by query
    """
    async with async_client as ac:
        res = await ac.get("/results", params={"query": "Test query"})
    assert res.status_code == 200
    data = res.json()
    assert all(item["query"] == "Test query" for item in data)


@pytest.mark.asyncio
async def test_get_queries_success(async_client):
    """
    Fetch distinct queries
    """
    async with async_client as ac:
        res = await ac.get("/queries")
    assert res.status_code == 200
    queries = res.json()
    assert "Test query" in queries


@pytest.mark.asyncio
async def test_delete_result_success(async_client):
    """
    Delete an existing row
    """
    db = next(get_session())
    run = db.query(RunResult).first()
    run_id = run.id
    async with async_client as ac:
        delete_res = await ac.delete(f"/results/{run_id}")
        assert delete_res.status_code == 200






