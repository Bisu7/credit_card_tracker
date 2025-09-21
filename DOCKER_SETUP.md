# Docker Setup for Deep Researcher Agent

This guide explains how to build and run the Deep Researcher Agent using Docker.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (usually included with Docker Desktop)
- At least 4GB of available RAM
- At least 2GB of free disk space

## Quick Start

### 1. Build the Docker Image

**Windows (PowerShell):**
```powershell
.\docker-build.ps1
```

**Linux/Mac (Bash):**
```bash
./docker-build.sh
```

**Manual build:**
```bash
docker build -t deep-researcher-agent:latest .
```

### 2. Run the Container

**Using Docker Compose (Recommended):**
```bash
# Production mode
docker-compose up deep-researcher

# Development mode
docker-compose --profile dev up deep-researcher-dev
```

**Using Docker directly:**
```bash
# Production mode
docker run -p 8000:8000 -p 3000:3000 -v $(pwd)/data:/app/data deep-researcher-agent:latest

# Development mode
docker run -p 8001:8000 -p 3001:3000 -v $(pwd):/app -v $(pwd)/data:/app/data deep-researcher-agent:latest
```

## Build Options

### Clean Build
Remove existing images and build from scratch:
```bash
# PowerShell
.\docker-build.ps1 -Clean

# Bash
./docker-build.sh --clean
```

### Development Mode
Build and run in development mode with live code reloading:
```bash
# PowerShell
.\docker-build.ps1 -Dev -Run

# Bash
./docker-build.sh --dev --run
```

### Build and Run
Build the image and immediately start the container:
```bash
# PowerShell
.\docker-build.ps1 -Run

# Bash
./docker-build.sh --run
```

## Service Configuration

### Production Service
- **Ports:** 8000 (API), 3000 (Frontend)
- **Volumes:** `./data:/app/data`
- **Environment:** Production
- **Command:** `python api_server_final.py`

### Development Service
- **Ports:** 8001 (API), 3001 (Frontend)
- **Volumes:** `.:/app` (live code reloading)
- **Environment:** Development
- **Command:** `python api_server.py`

## Environment Variables

You can customize the container behavior using environment variables:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - ENVIRONMENT=production
  - LOG_LEVEL=INFO
  - MAX_WORKERS=4
```

## Data Persistence

The Docker setup includes volume mounts for data persistence:

- `./data:/app/data` - Stores logs, sessions, and vector indices
- `./sample_documents:/app/sample_documents` - Sample documents for testing

## Health Checks

The container includes health checks that monitor the API endpoint:

- **Endpoint:** `http://localhost:8000/health`
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Retries:** 3

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   
   # Kill the process or use different ports
   docker run -p 8001:8000 -p 3001:3000 deep-researcher-agent:latest
   ```

2. **Permission Denied (Linux/Mac)**
   ```bash
   # Make scripts executable
   chmod +x docker-build.sh
   chmod +x docker-build.sh
   ```

3. **Out of Memory**
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or use the lite version
   docker build -f Dockerfile.lite -t deep-researcher-agent:lite .
   ```

4. **Build Fails**
   ```bash
   # Clean build
   docker system prune -a
   docker build --no-cache -t deep-researcher-agent:latest .
   ```

### Logs

View container logs:
```bash
# Using Docker Compose
docker-compose logs -f deep-researcher

# Using Docker directly
docker logs -f <container_id>
```

### Debug Mode

Run container in debug mode:
```bash
docker run -it --entrypoint /bin/bash deep-researcher-agent:latest
```

## Multi-Architecture Support

The Dockerfile supports multiple architectures:

```bash
# Build for specific architecture
docker buildx build --platform linux/amd64 -t deep-researcher-agent:latest .
docker buildx build --platform linux/arm64 -t deep-researcher-agent:latest .
```

## Security Considerations

- The container runs as a non-root user when possible
- Sensitive data should be mounted as volumes, not copied into the image
- Use secrets management for production deployments
- Regularly update base images for security patches

## Performance Optimization

- Use multi-stage builds to reduce image size
- Leverage Docker layer caching
- Use `.dockerignore` to exclude unnecessary files
- Consider using Alpine Linux base images for smaller size

## Production Deployment

For production deployment, consider:

1. **Using a reverse proxy** (nginx, traefik)
2. **Setting up SSL/TLS certificates**
3. **Implementing proper logging and monitoring**
4. **Using container orchestration** (Docker Swarm, Kubernetes)
5. **Setting up health checks and auto-restart policies**

## Support

For issues related to Docker setup, please check:

1. Docker logs: `docker logs <container_id>`
2. Container status: `docker ps -a`
3. Image details: `docker inspect deep-researcher-agent:latest`
4. System resources: `docker stats`
