#!/bin/bash
#
# Simple script to add, commit, and push changes to the main branch on GitHub.
#

echo "🚀 Starting Git push process..."

# Check if there are any changes to commit
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to commit. Your working directory is clean."
    exit 0
fi

# Default commit message
DEFAULT_MESSAGE="Fix: Use relative URLs for API calls in customer setup form"

# Use the default message or prompt for a new one
read -p "Enter commit message (or press Enter to use default: '$DEFAULT_MESSAGE'): " COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="$DEFAULT_MESSAGE"
fi

echo "➕ Adding all changed files..."
git add .

echo "💾 Committing with message: '$COMMIT_MESSAGE'..."
git commit -m "$COMMIT_MESSAGE"

echo "📤 Pushing to origin main..."
git push origin main

echo "🎉 Successfully pushed updates to GitHub!"