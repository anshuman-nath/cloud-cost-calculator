# GitHub Setup Visual Workflow

## 🎯 Complete Setup Process

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Choose Your Setup Method                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ├──────────────────────┬────────────────────────
                          │                      │
                    ┌─────▼─────┐          ┌───▼────┐
                    │ AUTOMATED │          │ MANUAL │
                    │  (Easy)   │          │(Control)│
                    └─────┬─────┘          └───┬────┘
                          │                    │
                          │                    │
┌─────────────────────────▼────────┐  ┌────────▼──────────────────────┐
│ AUTOMATED PATH                   │  │ MANUAL PATH                   │
├──────────────────────────────────┤  ├───────────────────────────────┤
│                                  │  │                               │
│ 1. Install GitHub CLI            │  │ 1. Go to github.com/new       │
│    brew install gh (Mac)         │  │                               │
│                                  │  │ 2. Create repository          │
│ 2. Authenticate                  │  │    Name: cloud-cost-calculator│
│    gh auth login                 │  │    Visibility: Private/Public │
│                                  │  │    ❌ Don't initialize repo   │
│ 3. Run script                    │  │                               │
│    cd cloud-cost-calculator      │  │ 3. Initialize Git locally     │
│    chmod +x scripts/github_*.sh  │  │    cd cloud-cost-calculator   │
│    ./scripts/github_setup.sh     │  │    git init                   │
│                                  │  │    git add .                  │
│ 4. Follow prompts                │  │    git commit -m "Initial"    │
│    - Choose visibility           │  │    git branch -M main         │
│    - Enter API key (optional)    │  │                               │
│    - Create project (optional)   │  │ 4. Connect to GitHub          │
│                                  │  │    git remote add origin ...  │
│ ✅ Done automatically!           │  │    git push -u origin main    │
│                                  │  │                               │
│                                  │  │ 5. Create develop branch      │
│                                  │  │    git checkout -b develop    │
│                                  │  │    git push -u origin develop │
│                                  │  │                               │
│                                  │  │ 6. Configure branch protection│
│                                  │  │    (See GITHUB_SETUP.md)      │
│                                  │  │                               │
│                                  │  │ ✅ Done manually!             │
└──────────────────┬───────────────┘  └───────────────┬───────────────┘
                   │                                   │
                   └───────────────┬───────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │  STEP 2: Verify Setup          │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │ Visit GitHub Repository        │
                    │ Check:                         │
                    │ ✓ main branch exists          │
                    │ ✓ develop branch exists       │
                    │ ✓ Actions tab shows workflows │
                    │ ✓ README.md is visible        │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │  STEP 3: Start Developing      │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │ git checkout develop           │
                    │ git checkout -b feature/name   │
                    │ # Make changes                 │
                    │ git push origin feature/name   │
                    │ # Create PR on GitHub          │
                    └────────────────────────────────┘
```

## 📋 Branch Protection Visual

```
┌────────────────────────────────────────────────────────────────┐
│                    MAIN BRANCH (Production)                    │
├────────────────────────────────────────────────────────────────┤
│ Protection Rules:                                              │
│ 🔒 Require Pull Request                                        │
│ 🔒 Require 1 approval (if team)                                │
│ 🔒 Require CI to pass (test-backend, frontend-check)           │
│ 🔒 Require branch up-to-date                                   │
│ 🔒 No direct pushes (even admins)                              │
│                                                                 │
│ Merge allowed from: develop (via PR)                           │
│                    hotfix/* (via PR)                           │
└────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (PR + CI pass)
                              │
┌────────────────────────────────────────────────────────────────┐
│                  DEVELOP BRANCH (Development)                   │
├────────────────────────────────────────────────────────────────┤
│ Protection Rules:                                              │
│ 🔒 Require Pull Request                                        │
│ 🔒 Require CI to pass (test-backend, frontend-check)           │
│                                                                 │
│ Merge allowed from: feature/*                                  │
│                    bugfix/*                                    │
└────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (PR + CI pass)
                              │
                    ┌─────────┴─────────┐
                    │                   │
        ┌───────────▼────────┐   ┌─────▼──────────┐
        │  feature/pricing   │   │  feature/ui    │
        └────────────────────┘   └────────────────┘
```

## 🔄 Development Workflow Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE DEVELOPMENT FLOW                     │
└─────────────────────────────────────────────────────────────────┘

    1. Start from develop
    ────────────────────
    git checkout develop
    git pull origin develop

              │
              ▼

    2. Create feature branch
    ────────────────────────
    git checkout -b feature/pricing-api

              │
              ▼

    3. Make changes
    ───────────────
    # Edit files
    # Write tests
    # Update docs

              │
              ▼

    4. Commit changes
    ─────────────────
    git add .
    git commit -m "feat: integrate pricing API"

              │
              ▼

    5. Push to GitHub
    ─────────────────
    git push origin feature/pricing-api

              │
              ▼

    6. Create Pull Request
    ──────────────────────
    Go to GitHub → New PR
    Base: develop ← Compare: feature/pricing-api

              │
              ▼

    7. CI Runs Automatically
    ────────────────────────
    ✓ Linting
    ✓ Unit tests
    ✓ Code formatting

              │
              ▼

    8. Code Review (if team)
    ────────────────────────
    Team reviews code
    Request changes or approve

              │
              ▼

    9. Merge to develop
    ───────────────────
    Squash and merge
    Delete feature branch

              │
              ▼

    10. Test in develop
    ───────────────────
    Full integration testing

              │
              ▼

    11. Ready for production?
    ─────────────────────────
    Create PR: main ← develop

              │
              ▼

    12. Merge to main
    ─────────────────
    Create release tag
    git tag v1.0.0

              │
              ▼

    13. Release Pipeline Runs
    ─────────────────────────
    ✓ Build installers
    ✓ Create GitHub release
    ✓ Upload artifacts
```

## 🚨 Hotfix Workflow Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                      HOTFIX FLOW (URGENT!)                      │
└─────────────────────────────────────────────────────────────────┘

    1. Bug found in production!
    ───────────────────────────
    Users report critical issue

              │
              ▼

    2. Create hotfix from main
    ──────────────────────────
    git checkout main
    git checkout -b hotfix/critical-bug

              │
              ▼

    3. Fix the bug
    ──────────────
    # Fix code
    # Add test
    git commit -m "fix: correct calculation"

              │
              ▼

    4. Push and PR to main
    ──────────────────────
    git push origin hotfix/critical-bug
    Create PR: main ← hotfix/critical-bug

              │
              ▼

    5. Merge to main
    ────────────────
    After CI passes
    Tag: v1.0.1

              │
              ├──────────────────────────┐
              │                          │
              ▼                          ▼

    6. ALSO merge to develop     Deploy to production
    ────────────────────────     ───────────────────
    git checkout develop         Release pipeline runs
    git merge hotfix/...
    git push origin develop

              │
              ▼

    7. Clean up
    ───────────
    git branch -d hotfix/critical-bug
```

## 📊 CI/CD Pipeline Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                      CI/CD PIPELINE FLOW                        │
└─────────────────────────────────────────────────────────────────┘

    Push to develop branch
            │
            ▼
    ┌───────────────────┐
    │  dev-ci.yml       │
    │  (GitHub Actions) │
    └────────┬──────────┘
             │
             ├──────────────────┬──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
    ┌────────────────┐  ┌──────────────┐  ┌─────────────┐
    │ Backend Tests  │  │Frontend Tests│  │   Linting   │
    │                │  │              │  │             │
    │ • pytest       │  │ • jest       │  │ • pylint    │
    │ • coverage     │  │ • build      │  │ • black     │
    └────────┬───────┘  └──────┬───────┘  └──────┬──────┘
             │                  │                  │
             └──────────────────┴──────────────────┘
                                │
                                ▼
                          ✅ All pass?
                                │
                    ┌───────────┴───────────┐
                    │                       │
                   Yes                     No
                    │                       │
                    ▼                       ▼
            ✅ PR can merge        ❌ Fix issues


    Push to main (or tag v*)
            │
            ▼
    ┌───────────────────┐
    │  prod-ci.yml      │
    │  (GitHub Actions) │
    └────────┬──────────┘
             │
             ├──────────────┬──────────────┬──────────────┐
             │              │              │              │
             ▼              ▼              ▼              ▼
    ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐
    │ Full Tests │  │ Security │  │  Build   │  │   Build    │
    │            │  │   Scan   │  │  macOS   │  │  Windows   │
    └──────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘
           │             │             │              │
           └─────────────┴─────────────┴──────────────┘
                               │
                               ▼
                    Tagged release (v*)?
                               │
                    ┌──────────┴──────────┐
                   Yes                   No
                    │                     │
                    ▼                     ▼
           ┌─────────────────┐      ✅ Done
           │  release.yml    │
           │ (Auto Release)  │
           └────────┬────────┘
                    │
                    ├──────────┬──────────┬──────────┐
                    │          │          │          │
                    ▼          ▼          ▼          ▼
            ┌────────────┬────────┬────────┬──────────────┐
            │Create      │ Build  │ Build  │Upload        │
            │Release     │ macOS  │Windows │Installers    │
            │on GitHub   │ .dmg   │ .exe   │to Release    │
            └────────────┴────────┴────────┴──────────────┘
                               │
                               ▼
                    ✅ Release Published!
                    Users can download installers
```

## 🎯 Quick Decision Tree

```
                    Need to make changes?
                            │
                ┌───────────┴───────────┐
                │                       │
           Bug in prod?            New feature?
                │                       │
                ▼                       ▼
        ┌───────────────┐      ┌────────────────┐
        │ HOTFIX BRANCH │      │ FEATURE BRANCH │
        │ from main     │      │ from develop   │
        └───────┬───────┘      └────────┬───────┘
                │                       │
                ▼                       ▼
        Fix → PR → main          Code → PR → develop
                │                       │
                ▼                       ▼
        Tag v1.0.1               Test in develop
                │                       │
                ▼                       ▼
        Merge to develop         When ready: PR → main
```

---

## 📝 Summary

✅ **Automated Setup**: Run `./scripts/github_setup.sh`
✅ **Manual Setup**: Follow `docs/GITHUB_SETUP.md`
✅ **Quick Reference**: Use `docs/QUICK_REFERENCE.md`
✅ **Development**: Follow `docs/DEVELOPMENT.md`

**Your repository is production-ready with professional CI/CD!** 🚀
