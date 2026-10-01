#!/bin/bash

set -e

echo "GitHub setup"

read -rp "GitHub repo URL: " REPO

if [ -z "$REPO" ]; then
    echo "No repository URL provided."
    exit 1
fi

echo "Initializing Git..."
git init

echo "Setting branch to main..."
git branch -M main

echo "Adding files..."
git add .

echo "Creating commit..."
git commit -m "Initial commit"

echo "Adding remote..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO"

echo "Pushing to GitHub..."
git push -u origin main

echo "Done. Your project is now on GitHub."
