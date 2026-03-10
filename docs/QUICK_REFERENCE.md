# Quick Reference Guide

## 🚀 Initial Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/cloud-cost-calculator.git
cd cloud-cost-calculator

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp backend/.env.example backend/.env
nano backend/.env  # Add your API keys
```

## 🏃 Running the App

### Development Mode
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🌿 Git Workflow

### New Feature
```bash
git checkout develop
git pull origin develop
git checkout -b feature/feature-name
# ... make changes ...
git add .
git commit -m "feat: add feature"
git push origin feature/feature-name
# Create PR on GitHub: develop ← feature/feature-name
```

### Hotfix
```bash
git checkout main
git checkout -b hotfix/bug-name
# ... fix bug ...
git add .
git commit -m "fix: fix bug"
git push origin hotfix/bug-name
# Create PR on GitHub: main ← hotfix/bug-name
# After merge to main, also merge to develop
```

### Release
```bash
# Via PR: main ← develop
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
```

## 🛠️ Common Commands

### Backend
```bash
# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run linting
pylint app/ tests/

# Format code
black app/ tests/

# Run specific test
pytest tests/test_pricing_engine.py::TestPricingEngine::test_payg_calculation -v
```

### Frontend
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build production
npm run build

# Package app
npm run package:mac     # macOS
npm run package:win     # Windows
npm run package:linux   # Linux
```

### Database
```bash
# Access database
cd backend
sqlite3 cloud_cost_calculator.db

# View tables
.tables

# Query data
SELECT * FROM bill_of_materials;

# Exit
.quit

# Reset database
rm cloud_cost_calculator.db
python -c "from app.utils.database import init_db; init_db()"
```

## 📡 API Examples

### Create BOM
```bash
curl -X POST http://localhost:8000/api/v1/bom/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Environment",
    "cloud_provider": "aws",
    "services": [
      {
        "service_name": "Web Server",
        "service_type": "compute",
        "cloud_provider": "aws",
        "region": "us-east-1",
        "config": {
          "instance_type": "m5.large",
          "quantity": 10
        }
      }
    ]
  }'
```

### Generate Scenarios
```bash
curl -X POST http://localhost:8000/api/v1/scenarios/1/generate
```

### Compare Scenarios
```bash
curl http://localhost:8000/api/v1/scenarios/1/compare
```

### Get BOM
```bash
curl http://localhost:8000/api/v1/bom/1
```

## 📊 Project Structure

```
cloud-cost-calculator/
├── backend/           # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # Data models
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utilities
│   └── tests/        # Unit tests
├── frontend/         # Electron + React
├── scripts/          # Utility scripts
└── docs/             # Documentation
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
pip install -r requirements-dev.txt

# Check port
lsof -i :8000
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 18+

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database issues
```bash
# Check database exists
ls -lh backend/cloud_cost_calculator.db

# Recreate database
cd backend
rm cloud_cost_calculator.db
python -c "from app.utils.database import init_db; init_db()"
```

### Git issues
```bash
# Reset to last commit
git reset --hard HEAD

# Pull latest changes
git fetch origin
git pull origin develop

# View status
git status
git log --oneline -10
```

## 📚 Documentation

- [README.md](README.md) - Project overview
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development guide
- [GITHUB_SETUP.md](docs/GITHUB_SETUP.md) - GitHub setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🔗 Useful Links

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Electron: https://www.electronjs.org/
- Infracost API: https://www.infracost.io/docs/cloud_pricing_api/
