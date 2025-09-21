#!/bin/bash

# Deep Researcher Agent - Docker Build Script
# This script builds and runs the Deep Researcher Agent using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deep Researcher Agent - Docker Build Script${NC}"
echo "================================================"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose is not installed. Using 'docker compose' instead."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Parse command line arguments
BUILD_MODE="production"
CLEAN_BUILD=false
RUN_AFTER_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            BUILD_MODE="development"
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --run)
            RUN_AFTER_BUILD=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --dev     Build in development mode"
            echo "  --clean   Clean build (remove existing images)"
            echo "  --run     Run the container after building"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Building in $BUILD_MODE mode..."

# Clean build if requested
if [ "$CLEAN_BUILD" = true ]; then
    print_status "Cleaning existing images..."
    docker rmi deep-researcher-agent:latest 2>/dev/null || true
    docker system prune -f
fi

# Build the Docker image
print_status "Building Docker image..."
docker build -t deep-researcher-agent:latest .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully!"
else
    print_error "Docker build failed!"
    exit 1
fi

# Run the container if requested
if [ "$RUN_AFTER_BUILD" = true ]; then
    print_status "Starting container..."
    
    if [ "$BUILD_MODE" = "development" ]; then
        $COMPOSE_CMD --profile dev up deep-researcher-dev
    else
        $COMPOSE_CMD up deep-researcher
    fi
fi

print_status "Build completed successfully!"
print_status "To run the container:"
print_status "  Production: $COMPOSE_CMD up deep-researcher"
print_status "  Development: $COMPOSE_CMD --profile dev up deep-researcher-dev"
print_status "  Or use: docker run -p 8000:8000 -p 3000:3000 deep-researcher-agent:latest"
