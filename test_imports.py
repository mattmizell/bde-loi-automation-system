#!/usr/bin/env python3
"""
Test script to check all imports and identify issues
"""

import sys
import os

def test_imports():
    print("🔍 Testing imports...")
    
    try:
        print("Testing basic imports...")
        import fastapi
        print("✅ FastAPI imported")
        
        import uvicorn
        print("✅ Uvicorn imported")
        
        import psycopg2
        print("✅ psycopg2 imported")
        
        print("\nTesting main module imports...")
        
        # Test forms_api import
        try:
            from api.forms_api import router as forms_router
            print("✅ forms_api imported")
        except Exception as e:
            print(f"❌ forms_api failed: {e}")
        
        # Test database imports
        try:
            from database.connection import DatabaseManager
            print("✅ database.connection imported")
        except Exception as e:
            print(f"❌ database.connection failed: {e}")
        
        # Test main app import
        try:
            from main import app
            print("✅ Main app imported successfully")
            print(f"✅ App type: {type(app)}")
        except Exception as e:
            print(f"❌ Main app failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports()