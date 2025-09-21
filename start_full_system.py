#!/usr/bin/env python3
"""
Complete startup script for Deep Researcher System
This script starts both the backend API server and the React frontend.
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def check_backend_dependencies():
    """Check if backend dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        print("✅ Backend dependencies found")
        return True
    except ImportError:
        print("❌ Backend dependencies not found. Please install them:")
        print("   pip install -r requirements.txt")
        return False

def start_backend():
    """Start the FastAPI backend server."""
    print("🔧 Starting Deep Researcher Backend...")
    try:
        subprocess.run([sys.executable, 'api_server.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend: {e}")

def start_frontend():
    """Start the React frontend."""
    print("🎨 Starting Deep Researcher Frontend...")
    try:
        subprocess.run(['npm', 'start'], cwd='frontend')
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start frontend: {e}")

def main():
    """Main function to start the complete system."""
    print("🔬 Deep Researcher Complete System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('api_server.py').exists():
        print("❌ api_server.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    if not Path('frontend').exists():
        print("❌ Frontend directory not found.")
        sys.exit(1)
    
    # Check backend dependencies
    if not check_backend_dependencies():
        sys.exit(1)
    
    print("\n🚀 Starting both backend and frontend...")
    print("📡 Backend API: http://localhost:8000")
    print("🎨 Frontend UI: http://localhost:3000")
    print("\nPress Ctrl+C to stop both servers")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend (this will block)
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n👋 Shutting down complete system...")

if __name__ == '__main__':
    main()
