#!/usr/bin/env python3
"""
GitHub Repository Uploader - Create repo and upload files via API
Since git command is not available, use GitHub API directly
"""

import requests
import json
import base64
import os
from pathlib import Path

class GitHubUploader:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        # Use basic auth
        import base64
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers["Authorization"] = f"Basic {encoded_credentials}"
    
    def create_repository(self, repo_name, description=""):
        """Create a new GitHub repository"""
        
        data = {
            "name": repo_name,
            "description": description,
            "private": False,
            "auto_init": False
        }
        
        url = f"{self.base_url}/user/repos"
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            print(f"✅ Repository created: {repo_data['html_url']}")
            return repo_data
        elif response.status_code == 422:
            print(f"⚠️ Repository {repo_name} already exists")
            return {"name": repo_name, "full_name": f"{self.username}/{repo_name}"}
        else:
            print(f"❌ Failed to create repository: {response.status_code}")
            print(response.text)
            return None
    
    def upload_file(self, repo_name, file_path, github_path, commit_message):
        """Upload a single file to GitHub repository"""
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Encode as base64
            content_encoded = base64.b64encode(content).decode('utf-8')
            
            # Prepare API request
            data = {
                "message": commit_message,
                "content": content_encoded
            }
            
            url = f"{self.base_url}/repos/{self.username}/{repo_name}/contents/{github_path}"
            response = requests.put(url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                print(f"✅ Uploaded: {github_path}")
                return True
            else:
                print(f"❌ Failed to upload {github_path}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return False
    
    def upload_directory(self, repo_name, local_dir, commit_message="Upload files"):
        """Upload all files from a directory to GitHub"""
        
        local_path = Path(local_dir)
        uploaded_count = 0
        failed_count = 0
        
        # Get all files (excluding .git and other unwanted files)
        ignore_patterns = {'.git', '__pycache__', '.pyc', '.DS_Store', 'node_modules'}
        
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Skip ignored files
                if any(pattern in str(file_path) for pattern in ignore_patterns):
                    continue
                
                # Calculate relative path for GitHub
                relative_path = file_path.relative_to(local_path)
                github_path = str(relative_path).replace('\\', '/')
                
                # Upload file
                if self.upload_file(repo_name, file_path, github_path, commit_message):
                    uploaded_count += 1
                else:
                    failed_count += 1
        
        print(f"\n📊 Upload Summary:")
        print(f"✅ Uploaded: {uploaded_count} files")
        print(f"❌ Failed: {failed_count} files")
        
        return uploaded_count, failed_count

def main():
    """Main upload function"""
    
    # GitHub credentials 
    username = "mattmizell"
    password = "JNyzRxyK2MH252H"
    repo_name = "bde-loi-automation-system"
    
    print("🚀 GitHub Repository Upload via API")
    print("=" * 50)
    
    # Initialize uploader
    uploader = GitHubUploader(username, password)
    
    # Create repository
    print("📁 Creating GitHub repository...")
    repo_data = uploader.create_repository(
        repo_name,
        "Better Day Energy LOI Automation System with PostgreSQL, PDF generation, and CRM integration"
    )
    
    if not repo_data:
        print("❌ Failed to create repository")
        return
    
    # Upload all files from current directory
    print(f"\n📤 Uploading files to {repo_name}...")
    current_dir = Path.cwd()
    
    uploaded, failed = uploader.upload_directory(
        repo_name,
        current_dir,
        "Complete LOI signature system with PostgreSQL, PDF generation, and CRM integration"
    )
    
    if uploaded > 0:
        print(f"\n🎉 Repository ready for Render deployment!")
        print(f"🔗 GitHub URL: https://github.com/{username}/{repo_name}")
        print(f"🚀 Next: Deploy to Render using this repository")
        
        print(f"\n✅ Files uploaded:")
        print("- integrated_pdf_signature_server.py (Main application)")
        print("- signature_storage.py (PostgreSQL storage)")  
        print("- html_to_pdf_generator.py (PDF generation)")
        print("- render.yaml (Render deployment config)")
        print("- requirements.txt (Python dependencies)")
        print("- Supporting utilities and documentation")
    else:
        print("❌ No files were uploaded successfully")

if __name__ == "__main__":
    main()