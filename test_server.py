#!/usr/bin/env python3
"""
Minimal test server to debug connection issues
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/dashboard")
async def dashboard():
    return {"message": "Dashboard works!"}

if __name__ == "__main__":
    print("Starting minimal test server on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)