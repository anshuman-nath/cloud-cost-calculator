# Contributing to Cloud Cost Calculator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🎯 How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker
- Use the bug report template
- Include detailed steps to reproduce
- Provide system information
- Include relevant logs

### Suggesting Features

- Use the GitHub issue tracker
- Use the feature request template
- Explain the use case clearly
- Consider alternative solutions

### Code Contributions

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes
4. Write/update tests
5. Update documentation
6. Submit a pull request

## 🌿 Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch (base for features)
- `feature/*` - New features
- `hotfix/*` - Critical production fixes

## 💻 Development Setup

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

Quick start:
```bash
git clone https://github.com/YOUR_USERNAME/cloud-cost-calculator.git
cd cloud-cost-calculator
./scripts/setup.sh
```

## 📝 Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions focused and small
- Maximum line length: 100 characters

**Formatting:**
```bash
black app/ tests/
```

**Linting:**
```bash
pylint app/ tests/
```

### JavaScript (Frontend)

- Use ES6+ features
- Follow Airbnb style guide
- Use meaningful variable names
- Keep components small and focused

**Formatting:**
```bash
npm run format
```

### General Principles

- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)
- Write self-documenting code
- Comment complex logic

## ✅ Testing Requirements

### Backend

- Write unit tests for new features
- Maintain test coverage above 80%
- Test edge cases
- Mock external API calls

**Running tests:**
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend

- Write component tests
- Test user interactions
- Test API integration

**Running tests:**
```bash
cd frontend
npm test
```

## 📋 Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(pricing): add Azure pricing API integration

- Implement Azure Retail Prices API client
- Add caching for pricing data
- Update pricing engine to support Azure

Closes #45
```

```
fix(scenario): correct 3-year RI discount calculation

The discount rate was set to 65% instead of 72%
for 3-year reserved instances.

Fixes #67
```

## 🔄 Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests
   - Update documentation

3. **Test Locally**
   ```bash
   # Backend
   cd backend
   pytest tests/ -v

   # Frontend
   cd frontend
   npm test
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select `develop` as base branch
   - Fill out PR template completely
   - Link related issues

7. **Code Review**
   - Address reviewer feedback
   - Make requested changes
   - Update PR

8. **Merge**
   - Squash and merge when approved
   - Delete feature branch after merge

## 🚀 Release Process

Only maintainers can create releases.

1. Merge `develop` into `main`
2. Tag the release:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
3. GitHub Actions will build and publish

## 📚 Documentation

- Update README.md for user-facing changes
- Update API.md for API changes
- Update DEVELOPMENT.md for setup changes
- Add inline code comments for complex logic
- Update CHANGELOG.md

## ❓ Questions?

- Open a GitHub Discussion
- Check existing issues
- Read documentation in `/docs`

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Cloud Cost Calculator! 🎉
