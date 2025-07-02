@echo off
::
:: Simple Windows Batch script to add, commit, and push changes to GitHub.
::

echo "🚀 Starting Git push process..."

:: Check if there are any changes to commit
git diff-index --quiet HEAD --
if %errorlevel% equ 0 (
    echo "✅ No changes to commit. Your working directory is clean."
    goto :eof
)
set "DEFAULT_MESSAGE=Fix: Use relative URLs for API calls in customer setup form"

set /p COMMIT_MESSAGE="Enter commit message (or press Enter to use default): "

if not defined COMMIT_MESSAGE (
    set "COMMIT_MESSAGE=%DEFAULT_MESSAGE%"
)

echo "➕ Adding all changed files..."
git add .

echo "💾 Committing with message: "%COMMIT_MESSAGE%""
git commit -m "%COMMIT_MESSAGE%"

echo "📤 Pushing to origin main..."
git push origin main

echo "🎉 Successfully pushed updates to GitHub!"