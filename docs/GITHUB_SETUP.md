# GitHub Repository Setup Guide

## 🎯 Objective
Set up the cloud-cost-calculator repository on GitHub with proper branch structure, CI/CD workflows, and branch protection rules.

## Prerequisites
- GitHub account
- Git installed locally
- GitHub CLI (optional, but recommended): `brew install gh` (Mac) or download from https://cli.github.com/

## Option 1: Automated Setup (Using GitHub CLI - Recommended)

### Step 1: Install GitHub CLI (if not installed)
```bash
# macOS
brew install gh

# Linux
sudo apt install gh

# Windows
winget install --id GitHub.cli
```

### Step 2: Authenticate with GitHub
```bash
gh auth login
# Follow the prompts to authenticate
```

### Step 3: Run the automated setup script
```bash
cd cloud-cost-calculator
chmod +x scripts/github_setup.sh
./scripts/github_setup.sh
```

This script will:
- Create the repository on GitHub
- Set up main and develop branches
- Configure branch protection rules
- Push initial code
- Set up GitHub Actions secrets

---

## Option 2: Manual Setup (Step-by-Step)

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `cloud-cost-calculator`
3. Description: `Multi-cloud cost calculator with scenario comparison (PAYG, 1-Yr RI, 3-Yr RI)`
4. Visibility: **Private** or **Public** (your choice)
5. ❌ **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **Create repository**

### Step 2: Initialize Local Git Repository

```bash
cd cloud-cost-calculator

# Initialize Git (if not already done)
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Project structure and boilerplate

- Backend API with FastAPI
- Frontend skeleton with Electron + React
- Scenario manager for bulk pricing model application
- Unit tests with pytest
- CI/CD workflows with GitHub Actions
- Complete documentation"

# Set default branch to main
git branch -M main
```

### Step 3: Connect to GitHub and Push

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cloud-cost-calculator.git

# Push main branch
git push -u origin main
```

### Step 4: Create and Push Develop Branch

```bash
# Create develop branch
git checkout -b develop

# Push develop branch
git push -u origin develop

# Return to main
git checkout main
```

### Step 5: Configure Branch Protection Rules

#### Protect Main Branch
1. Go to repository on GitHub
2. Click **Settings** → **Branches**
3. Click **Add branch protection rule**
4. Branch name pattern: `main`
5. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (set to 1 if working with team)
   - ✅ Require status checks to pass before merging
     - Add check: `test-backend`
     - Add check: `frontend-check`
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings
6. Click **Create**

#### Protect Develop Branch
1. Add another branch protection rule
2. Branch name pattern: `develop`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Add check: `test-backend`
     - Add check: `frontend-check`
4. Click **Create**

### Step 6: Set Up GitHub Actions Secrets

For Infracost API integration:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add secrets:
   - Name: `INFRACOST_API_KEY`
   - Value: `your_infracost_api_key_here`
4. Click **Add secret**

### Step 7: Verify GitHub Actions

1. Go to **Actions** tab
2. You should see workflows listed:
   - Development CI
3. Make a test commit to `develop` branch to trigger CI:

```bash
git checkout develop

# Make a small change
echo "# Test" >> test.md
git add test.md
git commit -m "test: trigger CI workflow"
git push origin develop

# Check Actions tab on GitHub to see the workflow run
```

---

## Branch Strategy Overview

```
main (production)
  ↓
  Protected branch
  Requires PR + CI pass
  Tagged releases (v1.0.0, v1.1.0...)

develop (development)
  ↓
  Integration branch
  Requires PR + CI pass
  Daily work happens here

feature/* (feature branches)
  ↓
  Created from develop
  Merged back to develop via PR
  Deleted after merge

hotfix/* (critical fixes)
  ↓
  Created from main
  Merged to both main and develop
  Deleted after merge
```

---

## Common Git Workflows

### Creating a Feature

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/pricing-api-integration

# Work on feature
# ... make changes ...

git add .
git commit -m "feat: integrate Infracost API for real-time pricing"

# Push to GitHub
git push origin feature/pricing-api-integration

# Create Pull Request on GitHub
# Go to repository → Pull requests → New pull request
# Base: develop ← Compare: feature/pricing-api-integration
# Add description and create PR
```

### Releasing to Production

```bash
# Merge develop into main via Pull Request on GitHub
# 1. Go to Pull requests → New pull request
# 2. Base: main ← Compare: develop
# 3. Review changes
# 4. Merge pull request

# After merge, tag the release locally
git checkout main
git pull origin main

git tag -a v1.0.0 -m "Release v1.0.0: Initial production release

Features:
- Multi-cloud cost calculator
- Scenario comparison (PAYG, 1-Yr RI, 3-Yr RI)
- Bulk pricing model application
- REST API with FastAPI
- Desktop app with Electron"

git push origin v1.0.0

# Create GitHub Release
# Go to Releases → Draft a new release
# Choose tag: v1.0.0
# Add release notes
# Publish release
```

### Hotfix Workflow

```bash
# Critical bug found in production!
git checkout main
git pull origin main

# Create hotfix branch
git checkout -b hotfix/discount-calculation-error

# Fix the bug
# ... make changes ...

git add .
git commit -m "fix: correct 3-year RI discount rate from 65% to 72%"

# Push and create PR to main
git push origin hotfix/discount-calculation-error

# After merging to main, also merge to develop
git checkout develop
git pull origin develop
git merge hotfix/discount-calculation-error
git push origin develop

# Tag the hotfix
git checkout main
git pull origin main
git tag -a v1.0.1 -m "Hotfix v1.0.1: Fix discount calculation"
git push origin v1.0.1

# Delete hotfix branch
git branch -d hotfix/discount-calculation-error
git push origin --delete hotfix/discount-calculation-error
```

---

## Troubleshooting

### Authentication Issues

If you get authentication errors:

```bash
# Use GitHub CLI
gh auth login

# Or use SSH instead of HTTPS
git remote set-url origin git@github.com:YOUR_USERNAME/cloud-cost-calculator.git
```

### Push Rejected (Branch Protection)

If direct push is rejected:
- This is intentional! Branch protection is working
- Create a Pull Request instead
- Or temporarily disable branch protection (not recommended)

### CI Workflow Not Running

1. Check `.github/workflows/` files are pushed
2. Go to Actions tab → Enable workflows if disabled
3. Check workflow syntax with:
   ```bash
   cat .github/workflows/dev-ci.yml
   ```

### Merge Conflicts

When merging branches with conflicts:

```bash
# Update your branch with latest develop
git checkout feature/your-feature
git pull origin develop

# Resolve conflicts in your editor
# Look for <<<<<<< and >>>>>>> markers

# After resolving
git add .
git commit -m "resolve: merge conflicts from develop"
git push origin feature/your-feature
```

---

## GitHub Repository Settings Checklist

✅ Repository created
✅ Main branch pushed
✅ Develop branch created and pushed
✅ Branch protection on main configured
✅ Branch protection on develop configured
✅ GitHub Actions enabled
✅ Secrets configured (INFRACOST_API_KEY)
✅ First CI workflow run successful
✅ README.md visible on repository home

---

## Next Steps

1. ✅ Clone repository on other machines:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cloud-cost-calculator.git
   cd cloud-cost-calculator
   git checkout develop
   ./scripts/setup.sh
   ```

2. ✅ Invite collaborators (if team project):
   - Settings → Collaborators → Add people

3. ✅ Set up project board (optional):
   - Projects → New project → Board template

4. ✅ Configure notifications:
   - Settings → Notifications → Watch repository

---

## Resources

- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Git Branching Strategy](https://nvie.com/posts/a-successful-git-branching-model/)
