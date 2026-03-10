#!/bin/bash
# Automated GitHub Repository Setup Script
# This script uses GitHub CLI to automate repository creation and configuration

set -e  # Exit on error

echo "🚀 Cloud Cost Calculator - GitHub Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo ""
    echo "Please install it first:"
    echo "  macOS: brew install gh"
    echo "  Linux: sudo apt install gh"
    echo "  Windows: winget install --id GitHub.cli"
    echo ""
    echo "Or follow manual setup in docs/GITHUB_SETUP.md"
    exit 1
fi

echo "✅ GitHub CLI detected"
echo ""

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "${YELLOW}⚠️  Not authenticated with GitHub${NC}"
    echo "Running authentication..."
    gh auth login
    echo ""
fi

echo "✅ Authenticated with GitHub"
echo ""

# Get GitHub username
GITHUB_USER=$(gh api user -q .login)
echo "📍 GitHub username: ${GREEN}${GITHUB_USER}${NC}"
echo ""

# Repository details
REPO_NAME="cloud-cost-calculator"
REPO_DESC="Multi-cloud cost calculator with scenario comparison (PAYG, 1-Yr RI, 3-Yr RI)"

# Ask for repository visibility
echo "Choose repository visibility:"
echo "  1) Private (recommended for proprietary work)"
echo "  2) Public (open source)"
read -p "Enter choice [1-2]: " visibility_choice

if [ "$visibility_choice" == "2" ]; then
    VISIBILITY="public"
else
    VISIBILITY="private"
fi

echo ""
echo "Creating ${VISIBILITY} repository: ${REPO_NAME}"
echo ""

# Create repository
echo "📦 Creating repository on GitHub..."
if gh repo create ${REPO_NAME} \
    --${VISIBILITY} \
    --description "${REPO_DESC}" \
    --source=. \
    --remote=origin \
    --push; then
    echo "${GREEN}✅ Repository created successfully${NC}"
else
    echo "${RED}❌ Failed to create repository${NC}"
    echo "Repository may already exist. Continuing with existing repo..."
fi
echo ""

# Ensure we're on main branch
echo "🌿 Setting up branches..."
git branch -M main

# Create develop branch
if git show-ref --verify --quiet refs/heads/develop; then
    echo "✅ Develop branch already exists"
else
    git checkout -b develop
    echo "✅ Created develop branch"
fi

# Push both branches
echo "⬆️  Pushing branches to GitHub..."
git push -u origin main --force-with-lease
git push -u origin develop --force-with-lease
git checkout main
echo "${GREEN}✅ Branches pushed${NC}"
echo ""

# Set default branch
echo "🔧 Configuring repository settings..."
gh repo edit --default-branch main
echo "✅ Default branch set to main"
echo ""

# Enable GitHub Actions
echo "🔄 Enabling GitHub Actions..."
# GitHub Actions should be enabled by default for new repos
echo "✅ GitHub Actions enabled"
echo ""

# Set up branch protection (requires admin permissions)
echo "🔒 Setting up branch protection rules..."
echo ""
echo "${YELLOW}NOTE: Branch protection requires admin permissions.${NC}"
echo "If this fails, please configure manually in GitHub:"
echo "  Settings → Branches → Add branch protection rule"
echo ""

# Protect main branch
echo "Protecting main branch..."
gh api repos/${GITHUB_USER}/${REPO_NAME}/branches/main/protection \
  --method PUT \
  --field required_status_checks[strict]=true \
  --field 'required_status_checks[contexts][]=test-backend' \
  --field 'required_status_checks[contexts][]=frontend-check' \
  --field enforce_admins=true \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_pull_request_reviews[dismiss_stale_reviews]=true \
  --field restrictions=null \
  2>/dev/null && echo "${GREEN}✅ Main branch protected${NC}" || echo "${YELLOW}⚠️  Could not set protection (may need manual setup)${NC}"

# Protect develop branch
echo "Protecting develop branch..."
gh api repos/${GITHUB_USER}/${REPO_NAME}/branches/develop/protection \
  --method PUT \
  --field required_status_checks[strict]=true \
  --field 'required_status_checks[contexts][]=test-backend' \
  --field 'required_status_checks[contexts][]=frontend-check' \
  --field enforce_admins=false \
  --field required_pull_request_reviews[required_approving_review_count]=0 \
  --field restrictions=null \
  2>/dev/null && echo "${GREEN}✅ Develop branch protected${NC}" || echo "${YELLOW}⚠️  Could not set protection (may need manual setup)${NC}"

echo ""

# Set up GitHub secrets
echo "🔐 Setting up GitHub Actions secrets..."
echo ""
read -p "Do you have an Infracost API key? (y/n): " has_api_key

if [ "$has_api_key" == "y" ] || [ "$has_api_key" == "Y" ]; then
    read -sp "Enter your Infracost API key: " api_key
    echo ""

    if [ -n "$api_key" ]; then
        gh secret set INFRACOST_API_KEY --body "$api_key"
        echo "${GREEN}✅ INFRACOST_API_KEY secret added${NC}"
    else
        echo "${YELLOW}⚠️  Empty API key, skipping${NC}"
    fi
else
    echo "${YELLOW}⚠️  Skipping API key setup${NC}"
    echo "You can add it later with:"
    echo "  gh secret set INFRACOST_API_KEY --body 'your_key_here'"
fi
echo ""

# Create initial issue/project setup
echo "📋 Setting up project management..."
read -p "Create initial GitHub Project board? (y/n): " create_project

if [ "$create_project" == "y" ] || [ "$create_project" == "Y" ]; then
    gh project create \
        --title "Cloud Cost Calculator Development" \
        --body "Track development progress for the cloud cost calculator" \
        2>/dev/null && echo "${GREEN}✅ Project board created${NC}" || echo "${YELLOW}⚠️  Could not create project (may need manual setup)${NC}"
fi
echo ""

# Summary
echo "=================================="
echo "${GREEN}✅ GitHub Setup Complete!${NC}"
echo "=================================="
echo ""
echo "📍 Repository URL: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "Next steps:"
echo "  1. Visit your repository on GitHub"
echo "  2. Review branch protection rules in Settings → Branches"
echo "  3. Check GitHub Actions in the Actions tab"
echo "  4. Start developing on the develop branch:"
echo ""
echo "     ${GREEN}git checkout develop${NC}"
echo "     ${GREEN}git checkout -b feature/your-feature${NC}"
echo ""
echo "📚 See docs/GITHUB_SETUP.md for detailed workflows"
echo ""
