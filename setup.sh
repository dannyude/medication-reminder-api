#!/bin/bash

# ==============================================================================
# MEDI-MINDER API - SETUP SCRIPT (Linux/Mac)
# ==============================================================================
# This script automates the setup process for the Medi-Minder API
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================================================"
echo "    MEDI-MINDER API - AUTOMATED SETUP"
echo "========================================================================"
echo -e "${NC}"

# Step 1: Check if Docker is installed
echo -e "${YELLOW}[1/6] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed${NC}"

# Step 2: Check if Docker Compose is installed
echo -e "${YELLOW}[2/6] Checking Docker Compose installation...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose is installed${NC}"

# Step 3: Create .env file if it doesn't exist
echo -e "${YELLOW}[3/6] Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate a random SECRET_KEY
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i.bak "s/your-super-secret-jwt-key-change-this-in-production-min-32-chars/$SECRET_KEY/" .env
        rm .env.bak
        echo -e "${GREEN}✅ Generated random SECRET_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  OpenSSL not found. Please manually update SECRET_KEY in .env${NC}"
    fi
    
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual credentials before proceeding${NC}"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 4: Stop any running containers
echo -e "${YELLOW}[4/6] Stopping any running containers...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Cleaned up old containers${NC}"

# Step 5: Build Docker images
echo -e "${YELLOW}[5/6] Building Docker images...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✅ Docker images built successfully${NC}"

# Step 6: Start services
echo -e "${YELLOW}[6/6] Starting services...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Services started successfully${NC}"

# Wait for services to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check if API is responding
echo -e "${YELLOW}🔍 Checking API health...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy and responding!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo -e "${GREEN}"
echo "========================================================================"
echo "    🎉 SETUP COMPLETE!"
echo "========================================================================"
echo -e "${NC}"
echo "Your Medi-Minder API is now running!"
echo ""
echo "📍 API Endpoint:      http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔧 Redoc:            http://localhost:8000/redoc"
echo "🗄️  PostgreSQL:       localhost:5432"
echo "⚡ Redis:            localhost:6379"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f api"
echo "  • Stop services:    docker-compose down"
echo "  • Restart API:      docker-compose restart api"
echo "  • View all logs:    docker-compose logs -f"
echo ""
echo -e "${YELLOW}⚠️  Remember to configure your email and SMS credentials in .env${NC}"
echo ""
