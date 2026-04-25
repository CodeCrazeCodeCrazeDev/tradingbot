#!/bin/bash
# Deployment script for Trading Bot
# Handles blue-green deployment with health checks

set -e

# Configuration
PROJECT_NAME="trading-bot"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
COMPOSE_FILE="docker-compose.production.yml"
HEALTH_CHECK_TIMEOUT=60
ROLLBACK_ON_FAILURE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { log_error "Docker Compose is required but not installed."; exit 1; }
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file $COMPOSE_FILE not found!"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    docker build -f Dockerfile.production -t "$DOCKER_IMAGE" .
    log_info "Image built successfully"
}

# Run health check on deployment
health_check() {
    log_info "Running health checks..."
    
    local retries=0
    local max_retries=$((HEALTH_CHECK_TIMEOUT / 5))
    
    while [ $retries -lt $max_retries ]; do
        if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
            log_info "Health check passed!"
            return 0
        fi
        
        log_warn "Health check failed, retrying... ($retries/$max_retries)"
        sleep 5
        retries=$((retries + 1))
    done
    
    log_error "Health check failed after $HEALTH_CHECK_TIMEOUT seconds"
    return 1
}

# Deploy with blue-green strategy
deploy_blue_green() {
    log_info "Starting blue-green deployment..."
    
    # Check if currently running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Existing deployment found, performing rolling update..."
        
        # Scale up new instances
        docker-compose -f "$COMPOSE_FILE" up -d --scale trading-bot=2 --no-recreate
        
        # Wait for new instances to be healthy
        sleep 10
        
        # Remove old instances
        docker-compose -f "$COMPOSE_FILE" up -d --scale trading-bot=1
    else
        # Fresh deployment
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
    
    # Health check
    if ! health_check; then
        if [ "$ROLLBACK_ON_FAILURE" = true ]; then
            log_error "Deployment failed, rolling back..."
            rollback
            exit 1
        else
            log_error "Deployment failed but rollback is disabled"
            exit 1
        fi
    fi
    
    log_info "Deployment completed successfully!"
}

# Rollback to previous version
rollback() {
    log_warn "Rolling back deployment..."
    
    # Stop current deployment
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    if [ -f "docker-compose.backup.yml" ]; then
        docker-compose -f docker-compose.backup.yml up -d
        log_info "Rolled back to previous version"
    else
        log_warn "No backup compose file found"
    fi
}

# Create backup of current deployment
create_backup() {
    log_info "Creating backup of current deployment..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        cp "$COMPOSE_FILE" docker-compose.backup.yml
    fi
    
    # Backup database if running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "postgres"; then
        log_info "Backing up database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U trading_bot > backup_$(date +%Y%m%d_%H%M%S).sql
    fi
    
    log_info "Backup created"
}

# Main deployment function
deploy() {
    log_info "Starting deployment process..."
    
    check_prerequisites
    create_backup
    build_image
    deploy_blue_green
    
    log_info "Deployment complete!"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old Docker resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused volumes (keep named volumes)
    docker volume prune -f
    
    log_info "Cleanup complete"
}

# Show deployment status
status() {
    log_info "Checking deployment status..."
    
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Show resource usage
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Main command handler
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    health)
        health_check
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|cleanup|health}"
        exit 1
        ;;
esac
