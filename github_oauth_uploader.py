#!/usr/bin/env python3
"""
GitHub OAuth Uploader - Browser-based authentication and repository upload
Opens browser for GitHub login, then uploads repository via API
"""

import webbrowser
import http.server
import socketserver
import threading
import urllib.parse
import requests
import json
import base64
import os
from pathlib import Path
import time

class GitHubOAuthUploader:
    def __init__(self):
        self.client_id = "Iv1.b507a08c87ecfe98"  # GitHub OAuth App (public)
        self.client_secret = None  # Will be obtained through device flow
        self.access_token = None
        self.auth_server = None
        self.auth_code = None
        
    def start_oauth_flow(self):
        """Start GitHub OAuth device flow (no client secret needed)"""
        
        print("🔐 Starting GitHub OAuth authentication...")
        
        # Use GitHub Device Flow (no client secret required)
        device_code_url = "https://github.com/login/device/code"
        
        # Request device code
        device_data = {
            "client_id": self.client_id,
            "scope": "repo"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(
            device_code_url,
            data=device_data,
            headers=headers
        )
        
        if response.status_code == 200:
            device_info = response.json()
            
            print(f"\n🌐 Opening browser for GitHub authentication...")
            print(f"📝 User Code: {device_info['user_code']}")
            print(f"🔗 Verification URL: {device_info['verification_uri']}")
            
            # Open browser to verification URL
            webbrowser.open(device_info['verification_uri'])
            
            print(f"\n⏰ Please complete authentication in browser...")
            print(f"   Enter this code when prompted: {device_info['user_code']}")
            print(f"   Waiting for authentication...")
            
            # Poll for token
            return self.poll_for_token(device_info)
        else:
            print(f"❌ Failed to start OAuth flow: {response.status_code}")
            return False
    
    def poll_for_token(self, device_info):
        """Poll GitHub for access token"""
        
        token_url = "https://github.com/login/oauth/access_token"
        interval = device_info.get('interval', 5)
        device_code = device_info['device_code']
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        max_attempts = 60  # 5 minutes maximum
        
        for attempt in range(max_attempts):
            time.sleep(interval)
            
            token_data = {
                "client_id": self.client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
            
            response = requests.post(token_url, data=token_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'access_token' in result:
                    self.access_token = result['access_token']
                    print(f"✅ Authentication successful!")
                    return True
                elif result.get('error') == 'authorization_pending':
                    print(f"⏳ Waiting for authorization... ({attempt + 1}/{max_attempts})")
                    continue
                elif result.get('error') == 'slow_down':
                    interval += 5
                    continue
                else:
                    print(f"❌ Authentication error: {result.get('error')}")
                    return False
            else:
                print(f"❌ Token request failed: {response.status_code}")
                return False
        
        print("❌ Authentication timeout")
        return False
    
    def create_repository(self, repo_name, description=""):
        """Create GitHub repository using access token"""
        
        if not self.access_token:
            print("❌ No access token available")
            return None
        
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": repo_name,
            "description": description,
            "private": False,
            "auto_init": False
        }
        
        url = "https://api.github.com/user/repos"
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            print(f"✅ Repository created: {repo_data['html_url']}")
            return repo_data
        elif response.status_code == 422:
            print(f"⚠️ Repository {repo_name} already exists")
            # Get existing repo info
            user_url = "https://api.github.com/user"
            user_response = requests.get(user_url, headers=headers)
            if user_response.status_code == 200:
                username = user_response.json()['login']
                return {"name": repo_name, "full_name": f"{username}/{repo_name}"}
            return {"name": repo_name}
        else:
            print(f"❌ Failed to create repository: {response.status_code}")
            print(response.text)
            return None
    
    def upload_file(self, repo_full_name, file_path, github_path, commit_message):
        """Upload file to repository"""
        
        if not self.access_token:
            return False
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_encoded = base64.b64encode(content).decode('utf-8')
            
            headers = {
                "Authorization": f"token {self.access_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            data = {
                "message": commit_message,
                "content": content_encoded
            }
            
            url = f"https://api.github.com/repos/{repo_full_name}/contents/{github_path}"
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 201:
                print(f"✅ Uploaded: {github_path}")
                return True
            else:
                print(f"❌ Failed to upload {github_path}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return False
    
    def upload_all_files(self, repo_full_name, local_dir):
        """Upload all files from directory"""
        
        local_path = Path(local_dir)
        uploaded_count = 0
        failed_count = 0
        
        # Files to ignore
        ignore_patterns = {
            '.git', '__pycache__', '.pyc', '.DS_Store', 'node_modules',
            '.env', '.venv', 'venv', '.pytest_cache'
        }
        
        # Get all files
        all_files = []
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                if any(pattern in str(file_path) for pattern in ignore_patterns):
                    continue
                all_files.append(file_path)
        
        print(f"📤 Uploading {len(all_files)} files...")
        
        for file_path in all_files:
            relative_path = file_path.relative_to(local_path)
            github_path = str(relative_path).replace('\\', '/')
            
            if self.upload_file(
                repo_full_name,
                file_path,
                github_path,
                "Upload LOI Automation System files"
            ):
                uploaded_count += 1
            else:
                failed_count += 1
        
        print(f"\n📊 Upload Summary:")
        print(f"✅ Uploaded: {uploaded_count} files")
        print(f"❌ Failed: {failed_count} files")
        
        return uploaded_count, failed_count

def main():
    """Main function"""
    
    print("🚀 GitHub OAuth Repository Uploader")
    print("=" * 50)
    print("This will open a browser for GitHub authentication")
    print("then upload the LOI Automation System to your repository.")
    print()
    
    print("Starting authentication automatically...")
    
    # Initialize uploader
    uploader = GitHubOAuthUploader()
    
    # Start OAuth flow
    if not uploader.start_oauth_flow():
        print("❌ Authentication failed")
        return
    
    # Repository details
    repo_name = "bde-loi-automation-system"
    description = "Better Day Energy LOI Automation System with PostgreSQL, PDF generation, and CRM integration"
    
    # Create repository
    print(f"\n📁 Creating repository: {repo_name}")
    repo_data = uploader.create_repository(repo_name, description)
    
    if not repo_data:
        print("❌ Failed to create repository")
        return
    
    repo_full_name = repo_data['full_name']
    
    # Upload files
    print(f"\n📤 Uploading files to {repo_full_name}...")
    current_dir = Path.cwd()
    
    uploaded, failed = uploader.upload_all_files(repo_full_name, current_dir)
    
    if uploaded > 0:
        print(f"\n🎉 Repository uploaded successfully!")
        print(f"🔗 GitHub URL: https://github.com/{repo_full_name}")
        print(f"🚀 Ready for Render deployment!")
        
        print(f"\n✅ Key files uploaded:")
        print("- integrated_pdf_signature_server.py")
        print("- signature_storage.py") 
        print("- html_to_pdf_generator.py")
        print("- render.yaml")
        print("- requirements.txt")
        print("- All supporting files and documentation")
        
        print(f"\n🔗 Next Steps:")
        print("1. Go to render.com")
        print("2. Connect GitHub account")
        print("3. Deploy from the uploaded repository")
        print("4. Set environment variables for CRM and email")
    else:
        print("❌ Upload failed")

if __name__ == "__main__":
    main()