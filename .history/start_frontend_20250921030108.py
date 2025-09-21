#!/usr/bin/env python3
"""
Startup script for Deep Researcher Frontend
This script helps set up and run the React frontend for the Deep Researcher project.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_node():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org/")
    return False

def check_npm():
    """Check if npm is installed."""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ npm not found. Please install npm.")
    return False

def install_dependencies():
    """Install frontend dependencies."""
    print("📦 Installing frontend dependencies...")
    try:
        result = subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_frontend():
    """Start the React development server."""
    print("🚀 Starting React development server...")
    print("📱 Frontend will be available at: http://localhost:3000")
    print("🔗 Make sure the backend is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run(['npm', 'start'], cwd='frontend')
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start frontend: {e}")

def main():
    """Main function to set up and start the frontend."""
    print("🔬 Deep Researcher Frontend Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path('frontend').exists():
        print("❌ Frontend directory not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check prerequisites
    if not check_node():
        sys.exit(1)
    
    if not check_npm():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start the frontend
    start_frontend()

if __name__ == '__main__':
    main()
