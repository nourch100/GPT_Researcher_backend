from fastapi import FastAPI
from .routes import router
from dotenv import load_dotenv
import uvicorn
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine

Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="Research Runner (GPTR)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)