#!/bin/bash
# Setup script for Cloud Cost Calculator

echo "🚀 Setting up Cloud Cost Calculator..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
echo "✅ Backend dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file (please configure your API keys)"
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"

cd ..

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend

# Check Node version
node_version=$(node --version)
echo "✅ Node version: $node_version"

# Install dependencies
npm install
echo "✅ Frontend dependencies installed"

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your API keys"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Start frontend: cd frontend && npm run dev"
echo ""
echo "📚 Documentation: docs/DEVELOPMENT.md"
