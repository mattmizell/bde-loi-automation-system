#!/usr/bin/env python3
"""
Simple GitHub repository creator and uploader
Creates repo via web interface simulation
"""

import os
import subprocess
import sys

def create_git_repo():
    """Create local git repository and prepare for upload"""
    
    print("🚀 Simple GitHub Upload Helper")
    print("=" * 50)
    
    # Check if git is available
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Git is not installed. Please install git first.")
            return False
    except FileNotFoundError:
        print("❌ Git command not found. Please install git.")
        return False
    
    print("✅ Git is available")
    
    # Initialize repository
    print("\n📁 Initializing git repository...")
    subprocess.run(['git', 'init'], check=True)
    
    # Configure git
    print("🔧 Configuring git...")
    subprocess.run(['git', 'config', 'user.name', 'mattmizell'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'mattmizell@gmail.com'], check=True)
    
    # Add all files
    print("📤 Adding all files...")
    subprocess.run(['git', 'add', '.'], check=True)
    
    # Create commit
    print("💾 Creating commit...")
    commit_message = """Complete LOI Automation System

Features:
- Electronic signature capture with HTML5 Canvas
- PostgreSQL tamper-evident storage
- PDF generation via HTML
- Less Annoying CRM integration
- Email notifications
- Complete audit trail
- Render deployment ready"""
    
    subprocess.run(['git', 'commit', '-m', commit_message], check=True)
    
    # Set main branch
    subprocess.run(['git', 'branch', '-M', 'main'], check=True)
    
    print("\n✅ Local repository ready!")
    print("\n📋 Next steps:")
    print("1. Go to https://github.com/new")
    print("2. Create repository: bde-loi-automation-system")
    print("3. Don't initialize with README")
    print("4. Run these commands:")
    print()
    print("git remote add origin https://github.com/mattmizell/bde-loi-automation-system.git")
    print("git push -u origin main")
    print()
    print("Or with authentication:")
    print("git remote add origin https://mattmizell:JNyzRxyK2MH252H@github.com/mattmizell/bde-loi-automation-system.git")
    print("git push -u origin main")
    
    return True

def create_upload_instructions():
    """Create simple upload instructions"""
    
    instructions = """
# BDE LOI Automation - GitHub Upload Instructions

## Quick Upload Steps:

### 1. Create GitHub Repository
- Go to: https://github.com/new
- Repository name: `bde-loi-automation-system`
- Keep it PUBLIC
- DON'T initialize with README, .gitignore, or license
- Click "Create repository"

### 2. Upload Using GitHub Web Interface
Since the OAuth flow had issues, use the web interface:

1. On the new repository page, click "uploading an existing file"
2. Open this folder in your file manager: `/media/sf_PycharmProjects/bde_customer_onboarding/loi_automation_system/`
3. Select ALL files (Ctrl+A) except hidden folders
4. Drag and drop into GitHub web interface
5. Commit message: "Complete LOI Automation System"
6. Click "Commit changes"

### 3. Or Use Command Line (if git works)
```bash
cd /media/sf_PycharmProjects/bde_customer_onboarding/loi_automation_system
git init
git add .
git commit -m "Complete LOI Automation System"
git remote add origin https://github.com/mattmizell/bde-loi-automation-system.git
git push -u origin main
```

### 4. Deploy to Render
Once uploaded:
1. Go to render.com
2. New Web Service
3. Connect GitHub repository
4. It will auto-detect render.yaml
5. Add environment variables

## Files Being Uploaded:
- integrated_pdf_signature_server.py - Main application
- signature_storage.py - PostgreSQL storage
- html_to_pdf_generator.py - PDF generation
- render.yaml - Deployment config
- requirements.txt - Dependencies
- All supporting files

Ready for production deployment!
"""
    
    with open("GITHUB_UPLOAD_INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)
    
    print(f"\n📄 Created: GITHUB_UPLOAD_INSTRUCTIONS.txt")
    print("Follow these instructions to complete the upload.")

if __name__ == "__main__":
    print("🔧 Preparing repository for GitHub upload...")
    
    # Try to create git repo
    git_success = create_git_repo()
    
    # Create upload instructions
    create_upload_instructions()
    
    if git_success:
        print("\n✅ Repository prepared successfully!")
        print("📋 See GITHUB_UPLOAD_INSTRUCTIONS.txt for next steps")
    else:
        print("\n⚠️ Git initialization failed")
        print("📋 Use web upload method in GITHUB_UPLOAD_INSTRUCTIONS.txt")