"""
AIP444 Lab 4: Structured Outputs & Code Reading
Student Name: Wenjun Wei
Student ID:169010238
Date: 10/09/2026

General Overview:
This file establishes a production-grade asynchronous HTTP API server using the FastAPI framework.
It acts as the backend bridge for an AI-powered flashcard generator, handling incoming POST requests,
enforcing strict payload validation via Pydantic, executing cross-origin resource sharing, and
tracking request execution times through custom middleware before delegating logic to the AI generator.
"""

import time
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from flashcard_generator import generate_flashcards

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

class GenerateRequest(BaseModel):
    notes: str
    cards: int = 3

@app.post("/api/generate")
async def generate_cards(request: GenerateRequest):
    try:
        result = await generate_flashcards(request.notes, request.cards)
        return result
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Server running on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)