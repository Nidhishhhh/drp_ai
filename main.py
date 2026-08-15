import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search, auth
from database.session import init_db
import uvicorn
from fastapi.staticfiles import StaticFiles



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[drp.ai] App started ✅")
    yield
    print("[drp.ai] App shutting down")


app = FastAPI(
    title="drp.ai",
    description="AI-powered fashion visual search engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")
app.mount("/products", StaticFiles(directory="data/products"), name="products")


@app.get("/")
async def root():
    return {"message": "drp.ai is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)