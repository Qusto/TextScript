#!/bin/bash
# AICODE-NOTE: Docker startup script with health checks and validation
# Ensures all prerequisites are met before starting services

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TextScript Docker Startup Script${NC}"
echo -e "${BLUE}================================${NC}\n"

# Function to print colored messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check Docker installation
log_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi
DOCKER_VERSION=$(docker --version)
log_success "Docker found: $DOCKER_VERSION"

# Step 2: Check Docker Compose installation
log_info "Checking Docker Compose installation..."
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not available. Please install Docker Compose V2."
    exit 1
fi
COMPOSE_VERSION=$(docker compose version)
log_success "Docker Compose found: $COMPOSE_VERSION"

# Step 3: Check if Docker daemon is running
log_info "Checking Docker daemon status..."
if ! docker ps &> /dev/null; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi
log_success "Docker daemon is running"

# Step 4: Check .env file
log_info "Checking .env file..."
if [ ! -f .env ]; then
    log_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        log_warning "Please edit .env and add your OPENAI_API_KEY"
        echo -e "\nPress Enter after you've added your API key to .env..."
        read -r
    else
        log_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Check if API key is set
if grep -q "your_api_key_here" .env; then
    log_error "OPENAI_API_KEY is not set in .env file. Please update it."
    exit 1
fi
log_success ".env file exists and configured"

# Step 5: Stop existing containers if any
log_info "Stopping existing containers (if any)..."
docker compose down 2>/dev/null || true
log_success "Previous containers stopped"

# Step 6: Build Docker images
log_info "Building Docker images (this may take a few minutes)..."
if docker compose build --progress=plain; then
    log_success "Docker images built successfully"
else
    log_error "Failed to build Docker images"
    exit 1
fi

# Step 7: Start services
log_info "Starting services..."
if docker compose up -d; then
    log_success "Services started successfully"
else
    log_error "Failed to start services"
    exit 1
fi

# Step 8: Wait for services to be ready
log_info "Waiting for services to start (30 seconds)..."
sleep 5

# Step 9: Check backend health
log_info "Checking backend health..."
MAX_RETRIES=10
RETRY_COUNT=0
BACKEND_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        BACKEND_HEALTHY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "Waiting for backend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

if [ "$BACKEND_HEALTHY" = true ]; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    log_success "Backend is healthy: $HEALTH_RESPONSE"
else
    log_error "Backend health check failed after $MAX_RETRIES attempts"
    log_info "Showing backend logs:"
    docker compose logs backend --tail 50
    exit 1
fi

# Step 10: Check frontend health
log_info "Checking frontend health..."
FRONTEND_HEALTHY=false
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        FRONTEND_HEALTHY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "Waiting for frontend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

if [ "$FRONTEND_HEALTHY" = true ]; then
    log_success "Frontend is healthy"
else
    log_error "Frontend health check failed after $MAX_RETRIES attempts"
    log_info "Showing frontend logs:"
    docker compose logs frontend --tail 50
    exit 1
fi

# Step 11: Show container status
echo -e "\n${BLUE}=== Container Status ===${NC}"
docker compose ps

# Step 12: Show access URLs
echo -e "\n${GREEN}=== Services Ready! ===${NC}"
echo -e "${GREEN}✓ Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}✓ Backend:${NC}  http://localhost:8000"
echo -e "${GREEN}✓ API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}✓ Health:${NC}   http://localhost:8000/health"

# Step 13: Show logs command
echo -e "\n${BLUE}=== Useful Commands ===${NC}"
echo -e "View logs:       ${YELLOW}docker compose logs -f${NC}"
echo -e "Stop services:   ${YELLOW}docker compose down${NC}"
echo -e "Restart:         ${YELLOW}docker compose restart${NC}"
echo -e "View containers: ${YELLOW}docker compose ps${NC}"

echo -e "\n${GREEN}Press Ctrl+C to stop following logs, services will keep running.${NC}"
echo -e "${BLUE}Following logs...${NC}\n"

# Follow logs
docker compose logs -f
