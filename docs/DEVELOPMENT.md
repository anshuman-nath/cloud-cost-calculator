# Development Guide

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/cloud-cost-calculator.git
   cd cloud-cost-calculator
   ```

2. **Run setup script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Configure environment**
   ```bash
   # Edit backend/.env
   nano backend/.env

   # Add your API keys:
   INFRACOST_API_KEY=your_key_here
   ```

4. **Initialize database**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "from app.utils.database import init_db; init_db()"
   ```

## Development Workflow

### Running the Application

**Option 1: Manual (recommended for debugging)**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option 2: Automated**
```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

### Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Git Workflow

### Branching Strategy

- `main` - Production branch
- `develop` - Development branch
- `feature/feature-name` - Feature branches
- `hotfix/bug-name` - Hotfix branches

### Creating a Feature

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/bulk-discount

# Make changes, commit regularly
git add .
git commit -m "feat: add bulk discount application"

# Push to remote
git push origin feature/bulk-discount

# Create Pull Request on GitHub to merge into develop
```

### Releasing to Production

```bash
# Merge develop into main
git checkout main
git merge develop

# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

### Hotfix Workflow

```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix the bug
git add .
git commit -m "fix: correct pricing calculation"

# Merge to main
git checkout main
git merge hotfix/critical-bug
git tag v1.0.1
git push origin main --tags

# Also merge to develop
git checkout develop
git merge hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_pricing_engine.py -v

# Run specific test
pytest tests/test_pricing_engine.py::TestPricingEngine::test_payg_calculation -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Code Quality

### Linting

```bash
# Backend
cd backend
pylint app/ tests/

# Frontend
cd frontend
npm run lint
```

### Code Formatting

```bash
# Backend - format code
cd backend
black app/ tests/

# Backend - check formatting
black --check app/ tests/
```

## Database Management

### Viewing Data

```bash
cd backend
sqlite3 cloud_cost_calculator.db

# SQLite commands
.tables
.schema bill_of_materials
SELECT * FROM bill_of_materials;
.quit
```

### Resetting Database

```bash
cd backend
rm cloud_cost_calculator.db
python -c "from app.utils.database import init_db; init_db()"
```

## API Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Create BOM
curl -X POST http://localhost:8000/api/v1/bom/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test BOM",
    "cloud_provider": "aws",
    "services": []
  }'

# Generate scenarios
curl -X POST http://localhost:8000/api/v1/scenarios/1/generate
```

### Using httpie (easier)

```bash
# Install httpie
pip install httpie

# Create BOM
http POST http://localhost:8000/api/v1/bom/ \
  name="Test BOM" \
  cloud_provider="aws" \
  services:='[]'
```

## Debugging

### Backend

1. Add breakpoints in PyCharm or VS Code
2. Or use ipdb:
   ```python
   import ipdb; ipdb.set_trace()
   ```

### Logs

```bash
# View logs
tail -f backend/logs/app.log

# Search logs
grep "ERROR" backend/logs/app.log
```

## Building for Production

### Backend

```bash
cd backend
pip freeze > requirements.txt
```

### Frontend

```bash
cd frontend

# Build React app
npm run build

# Package Electron app
npm run package:mac    # macOS
npm run package:win    # Windows
npm run package:linux  # Linux
```

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version

# Reinstall dependencies
cd backend
pip install -r requirements-dev.txt

# Check for port conflicts
lsof -i :8000
```

### Frontend won't start

```bash
# Clear node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version
```

### Database issues

```bash
# Check database file
ls -lh backend/cloud_cost_calculator.db

# Recreate database
cd backend
rm cloud_cost_calculator.db
python -c "from app.utils.database import init_db; init_db()"
```

## Performance Tips

1. Use pricing cache to avoid repeated API calls
2. Run pricing refresh weekly, not on every request
3. Index database queries appropriately
4. Profile slow endpoints with `time curl`

## Contributing

1. Follow conventional commits format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `test:` - Tests
   - `refactor:` - Code refactoring

2. Write tests for new features
3. Update documentation
4. Create PR with clear description

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [Infracost API](https://www.infracost.io/docs/cloud_pricing_api/overview/)
