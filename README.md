# Cloud Cost Calculator

A desktop application for calculating and comparing cloud infrastructure costs across AWS, Azure, and GCP with support for multiple pricing scenarios (PAYG, 1-Year RI, 3-Year RI).

## 🎯 Purpose

This tool solves the problem of manually updating hundreds of VMs when comparing different reservation pricing models. Instead of changing each VM individually, you can:

1. Create a Bill of Materials (BOM) once
2. Automatically generate 3 pricing scenarios
3. Compare costs side-by-side
4. Export reports for stakeholders

## ✨ Features

- **Multi-Cloud Support**: AWS, Azure, and GCP
- **Scenario Comparison**: PAYG vs 1-Year RI vs 3-Year RI
- **Bulk Operations**: Apply discount models to all VMs at once
- **Local Desktop App**: No internet required after pricing data sync
- **Export**: CSV, Excel, PDF reports
- **Version Control**: Built with Git workflow in mind

## 🏗️ Architecture

```
├── Backend (Python FastAPI)
│   ├── Pricing Engine
│   ├── Scenario Manager
│   └── Data Storage (SQLite)
│
├── Frontend (Electron + React)
│   ├── BOM Builder UI
│   ├── Scenario Comparison View
│   └── Export Tools
│
└── External APIs
    └── Infracost Cloud Pricing API
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/cloud-cost-calculator.git
cd cloud-cost-calculator

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

### Development

```bash
# Start backend (Terminal 1)
cd backend
source venv/bin/activate
python main.py

# Start frontend (Terminal 2)
cd frontend
npm run dev
```

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)

## 🌿 Branching Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `hotfix/*` - Critical bug fixes

## 📝 License

MIT License - See [LICENSE](LICENSE) file

## 👤 Author

Anshuman Nath
