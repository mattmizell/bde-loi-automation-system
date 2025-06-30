#!/usr/bin/env python3
"""
Debug server to test dashboard functionality
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Server is running", "message": "Debug server works"}

@app.get("/test")
async def test():
    return {"test": "simple test endpoint"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard test"""
    return """
    <html>
        <head>
            <title>Debug Dashboard</title>
        </head>
        <body>
            <h1>🎯 Debug Dashboard</h1>
            <p>If you can see this, the dashboard route is working!</p>
            <a href="/test">Test JSON endpoint</a>
        </body>
    </html>
    """

if __name__ == "__main__":
    print("🚀 Starting debug server...")
    print("📊 Dashboard: http://127.0.0.1:8002/dashboard")
    print("🧪 Test: http://127.0.0.1:8002/test")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="debug")