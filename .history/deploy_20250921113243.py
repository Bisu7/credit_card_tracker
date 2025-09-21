#!/usr/bin/env python3
"""
Deployment helper script for Deep Researcher
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Deep Researcher Deployment Helper")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("api_server_final.py").exists():
        print("❌ api_server_final.py not found. Please run from project root.")
        sys.exit(1)
    
    # Check git status
    if not run_command("git status", "Checking git status"):
        print("❌ Not a git repository or git not available")
        sys.exit(1)
    
    # Add all files
    if not run_command("git add .", "Adding files to git"):
        sys.exit(1)
    
    # Commit changes
    commit_message = input("Enter commit message (or press Enter for default): ").strip()
    if not commit_message:
        commit_message = "Update deployment configuration and fix requirements"
    
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("⚠️ No changes to commit or commit failed")
    
    # Push to GitHub
    if not run_command("git push origin main", "Pushing to GitHub"):
        print("❌ Failed to push to GitHub")
        sys.exit(1)
    
    print("\n🎉 Deployment files updated and pushed to GitHub!")
    print("📡 Your Vercel deployment should now work correctly.")
    print("\n📋 Changes made:")
    print("  ✅ Fixed requirements.txt (removed dev dependencies)")
    print("  ✅ Added vercel.json configuration")
    print("  ✅ Added runtime.txt (Python 3.9)")
    print("  ✅ Added .gitignore")
    print("  ✅ Fixed frontend unused import warning")

if __name__ == "__main__":
    main()
