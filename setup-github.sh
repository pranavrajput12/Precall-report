#!/bin/bash

# GitHub Repository Setup Script
echo "🚀 GitHub Repository Setup for CrewAI Workflow Platform"
echo "======================================================="
echo ""

# Prompt for GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter repository name (default: crewai-workflow-platform): " REPO_NAME

# Use default if empty
REPO_NAME=${REPO_NAME:-crewai-workflow-platform}

# Construct the repository URL
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo "📝 Repository URL: $REPO_URL"
echo ""

# Add remote
echo "Adding remote origin..."
git remote add origin "$REPO_URL"

# Verify remote
echo ""
echo "Verifying remote..."
git remote -v

echo ""
echo "✅ Remote added successfully!"
echo ""
echo "To push your code to GitHub, run:"
echo "  git push -u origin main"
echo ""
echo "If you haven't created the repository on GitHub yet:"
echo "  1. Go to: https://github.com/new"
echo "  2. Repository name: $REPO_NAME"
echo "  3. DON'T initialize with README, .gitignore, or license"
echo "  4. Click 'Create repository'"
echo "  5. Then run: git push -u origin main"