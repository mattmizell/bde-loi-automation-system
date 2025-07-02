#!/usr/bin/env python3
"""
DEAD SIMPLE TEST - If this doesn't work, we have a Python/dependency issue
"""
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "🚨 SIMPLE TEST IS WORKING!",
        "port": os.getenv("PORT", "NO PORT SET"),
        "environment_vars": len(os.environ),
        "python_working": True
    }

@app.get("/test")
def test():
    return {"status": "SIMPLE FASTAPI IS WORKING"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚨 STARTING SIMPLE TEST ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)