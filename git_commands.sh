#!/bin/bash
# Git commands to upload LOI Automation System to GitHub
# Run these commands in a terminal where git is available

echo "🚀 Setting up LOI Automation System repository..."

# Configure git (if not already done)
git config --global user.name "mattmizell"
git config --global user.email "mattmizell@gmail.com"

# Initialize repository
echo "📁 Initializing git repository..."
git init

# Create README
echo "# BDE LOI Automation System

Better Day Energy Letter of Intent Automation System with:
- Electronic signature capture with HTML5 Canvas
- PostgreSQL tamper-evident storage with HMAC integrity
- Professional PDF generation via HTML-to-PDF
- Less Annoying CRM integration
- Gmail email notifications  
- Complete audit trail and compliance
- Render deployment ready

## Features
- 🖊️ DocuSign-like signature experience
- 💾 PostgreSQL BLOB storage for signatures
- 🔐 Cryptographic integrity verification
- 📄 Browser-based PDF generation
- 📝 Automatic CRM record updates
- 📧 Professional email notifications
- 🔒 ESIGN Act compliance

## Deployment
Ready for Render deployment with included render.yaml configuration.

## Tech Stack
- Python (HTTP server, PostgreSQL, email)
- HTML5 Canvas + Signature Pad JS
- PostgreSQL with tamper-evident hashing
- Less Annoying CRM API integration
- Gmail SMTP for notifications" > README.md

# Add all files
echo "📤 Adding all files to repository..."
git add .

# Initial commit
echo "💾 Creating initial commit..."
git commit -m "Complete LOI Automation System with PostgreSQL, PDF generation, and CRM integration

Features implemented:
- Electronic signature capture with HTML5 Canvas and Signature Pad
- PostgreSQL tamper-evident storage with HMAC-SHA256 integrity hashing
- Professional PDF generation via HTML-to-PDF browser conversion
- Less Annoying CRM integration with automatic record updates
- Gmail SMTP email notifications with professional templates
- Complete audit trail with IP logging and browser fingerprinting
- ESIGN Act compliance with legal binding signatures
- Render deployment configuration with PostgreSQL database
- Security headers, CSRF protection, and SSL enforcement

Components:
- integrated_pdf_signature_server.py: Main signature server application
- signature_storage.py: PostgreSQL tamper-evident storage system
- html_to_pdf_generator.py: PDF generation and CRM integration
- render.yaml: Production deployment configuration
- requirements.txt: Python dependencies for deployment
- Supporting utilities for testing and verification

Ready for production deployment on Render platform."

# Set up remote (create repository on GitHub first)
echo "🔗 Setting up GitHub remote..."
git branch -M main
git remote add origin https://mattmizell:JNyzRxyK2MH252H@github.com/mattmizell/bde-loi-automation-system.git

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push -u origin main

echo "✅ Repository uploaded successfully!"
echo "🔗 GitHub URL: https://github.com/mattmizell/bde-loi-automation-system"
echo "🚀 Next step: Deploy to Render using this repository"