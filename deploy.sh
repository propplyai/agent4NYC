#!/bin/bash
# Deployment script for Propply AI to Digital Ocean

set -e

echo "🚀 Propply AI - Digital Ocean Deployment Script"
echo "=============================================="

# Configuration
APP_NAME="propply-ai"
DOCKER_IMAGE="propply-ai:latest"
CONTAINER_NAME="propply-ai-container"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is available and running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_status "Docker Compose is available"

# Build the Docker image
print_status "Building Docker image..."
docker build -t $DOCKER_IMAGE .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Stop and remove existing containers
print_status "Stopping existing containers..."
$COMPOSE_CMD down --remove-orphans

# Create logs directory
mkdir -p logs
print_status "Created logs directory"

# Start the application
print_status "Starting Propply AI application..."
$COMPOSE_CMD up -d

if [ $? -eq 0 ]; then
    print_status "Application started successfully"
else
    print_error "Failed to start application"
    exit 1
fi

# Wait for health check
print_status "Waiting for application to be healthy..."
sleep 10

# Check health
for i in {1..12}; do
    if curl -f http://localhost/health &> /dev/null; then
        print_status "Application is healthy and ready!"
        break
    fi
    if [ $i -eq 12 ]; then
        print_error "Application failed health check"
        echo "Checking logs..."
        $COMPOSE_CMD logs --tail=20
        exit 1
    fi
    echo "Waiting... ($i/12)"
    sleep 5
done

# Show running containers
print_status "Running containers:"
$COMPOSE_CMD ps

# Show logs
print_status "Recent logs:"
$COMPOSE_CMD logs --tail=10

echo ""
print_status "🎉 Deployment completed successfully!"
echo ""
echo "📱 Application URLs:"
echo "   • Health Check: http://your-server-ip/health"
echo "   • Main App: http://your-server-ip/"
echo "   • API: http://your-server-ip/api/"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: $COMPOSE_CMD logs -f"
echo "   • Restart: $COMPOSE_CMD restart"
echo "   • Stop: $COMPOSE_CMD down"
echo "   • Update: git pull && ./deploy.sh"
echo ""
print_warning "Remember to configure your domain DNS to point to this server!"