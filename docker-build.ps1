# Deep Researcher Agent - Docker Build Script (PowerShell)
# This script builds and runs the Deep Researcher Agent using Docker

param(
    [switch]$Dev,
    [switch]$Clean,
    [switch]$Run,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

if ($Help) {
    Write-Host "Deep Researcher Agent - Docker Build Script" -ForegroundColor $Green
    Write-Host "Usage: .\docker-build.ps1 [OPTIONS]"
    Write-Host "Options:"
    Write-Host "  -Dev     Build in development mode"
    Write-Host "  -Clean   Clean build (remove existing images)"
    Write-Host "  -Run     Run the container after building"
    Write-Host "  -Help    Show this help message"
    exit 0
}

Write-Host "Deep Researcher Agent - Docker Build Script" -ForegroundColor $Green
Write-Host "================================================"

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Error "Docker is not installed. Please install Docker Desktop first."
    exit 1
}

# Check if Docker Compose is available
try {
    docker compose version | Out-Null
    $ComposeCmd = "docker compose"
} catch {
    try {
        docker-compose --version | Out-Null
        $ComposeCmd = "docker-compose"
    } catch {
        Write-Warning "Docker Compose is not available. You may need to install it separately."
    }
}

# Determine build mode
$BuildMode = if ($Dev) { "development" } else { "production" }

Write-Status "Building in $BuildMode mode..."

# Clean build if requested
if ($Clean) {
    Write-Status "Cleaning existing images..."
    try {
        docker rmi deep-researcher-agent:latest 2>$null
    } catch {
        # Image might not exist, continue
    }
    docker system prune -f
}

# Build the Docker image
Write-Status "Building Docker image..."
docker build -t deep-researcher-agent:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Status "Docker image built successfully!"
} else {
    Write-Error "Docker build failed!"
    exit 1
}

# Run the container if requested
if ($Run) {
    Write-Status "Starting container..."
    
    if ($Dev) {
        if ($ComposeCmd) {
            & $ComposeCmd --profile dev up deep-researcher-dev
        } else {
            Write-Warning "Docker Compose not available. Starting with docker run..."
            docker run -p 8001:8000 -p 3001:3000 -v "${PWD}/data:/app/data" deep-researcher-agent:latest
        }
    } else {
        if ($ComposeCmd) {
            & $ComposeCmd up deep-researcher
        } else {
            Write-Warning "Docker Compose not available. Starting with docker run..."
            docker run -p 8000:8000 -p 3000:3000 -v "${PWD}/data:/app/data" deep-researcher-agent:latest
        }
    }
}

Write-Status "Build completed successfully!"
Write-Status "To run the container:"
Write-Status "  Production: $ComposeCmd up deep-researcher"
Write-Status "  Development: $ComposeCmd --profile dev up deep-researcher-dev"
Write-Status "  Or use: docker run -p 8000:8000 -p 3000:3000 deep-researcher-agent:latest"
