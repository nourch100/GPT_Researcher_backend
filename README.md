
# GPTR Backend (FastAPI)

This is the **backend API** of the GPTR Research Dashboard — a benchmark and evaluation platform for LLMs like Mistral, OpenAI, and Gemini.

It’s built using **FastAPI**, **SQLAlchemy**, and **SQLite** for simplicity.


## Features
- REST API with FastAPI
- Stores benchmark results in SQLite
- Routes for research runs, queries, and model metrics
- Tested using pytest
- Lightweight and Dockerized


1. create a .env file and add the variables : 
    ```     
    DATABASE_URL="sqlite:///./research.db"
    TAVILY_API_KEY=""
    OPENAI_API_KEY=""
    GOOGLE_API_KEY=""
    MISTRAL_API_KEY=""
    
    ```

2. For Testing
```bash
pytest --cov=app --cov-report=term-missing
```
(reached 91% coverage)

## Project Structure ( important parts)
```
app/
 ├── main.py          # FastAPI entrypoint
 ├── routes.py        # API endpoints
 ├── services.py      # Business logic layer
 ├── models.py        # SQLAlchemy models
 ├── schemas.py       # Pydantic models
 ├── gptr_client.py   # GPT Researcher init
 ├── utils/           # Helpers (date, export)
 ├── tests/           # Unit & integration tests
```


