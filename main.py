from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search
import uvicorn

app = FastAPI(
    title="drp.ai",
    description="AI-powered fashion visual search engine",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "drp.ai is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)