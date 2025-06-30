#!/bin/bash

# Enhanced Intelligent Store Migration Assistant - Production Deployment Script
# Following DevOps best practices for enterprise deployment

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ================================
# Configuration & Environment
# ================================

# Script metadata
SCRIPT_NAME="Enhanced Migration Assistant Deployment"
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
DEFAULT_ENVIRONMENT="staging"
DEFAULT_REGION="us-east-1"
DEFAULT_CLUSTER_NAME="migration-assistant-cluster"
DEFAULT_NAMESPACE="migration-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ================================
# Utility Functions
# ================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1" >&2
}

# Display help information
show_help() {
    cat << EOF
${SCRIPT_NAME} v${SCRIPT_VERSION}

USAGE:
    $0 [OPTIONS] COMMAND

COMMANDS:
    build           Build Docker images
    test            Run comprehensive test suite
    deploy          Deploy to Kubernetes cluster
    rollback        Rollback to previous version
    status          Check deployment status
    logs            View application logs
    cleanup         Clean up resources
    validate        Validate deployment configuration
    migrate         Run database migrations
    backup          Create database backup
    restore         Restore from backup
    scale           Scale the deployment
    update          Update the deployment
    health          Check application health

OPTIONS:
    -e, --environment ENV    Target environment (dev|staging|prod) [default: ${DEFAULT_ENVIRONMENT}]
    -r, --region REGION      AWS region [default: ${DEFAULT_REGION}]
    -c, --cluster CLUSTER    Kubernetes cluster name [default: ${DEFAULT_CLUSTER_NAME}]
    -n, --namespace NS       Kubernetes namespace [default: ${DEFAULT_NAMESPACE}]
    -v, --verbose           Enable verbose output
    -d, --dry-run           Show what would be done without executing
    -f, --force             Force operation without confirmation
    -h, --help              Show this help message
    --version               Show version information

EXAMPLES:
    $0 deploy --environment prod --region us-west-2
    $0 build --verbose
    $0 test --environment staging
    $0 rollback --environment prod --force
    $0 scale --replicas 5 --environment prod

EOF
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT="${DEFAULT_ENVIRONMENT}"
    REGION="${DEFAULT_REGION}"
    CLUSTER_NAME="${DEFAULT_CLUSTER_NAME}"
    NAMESPACE="${DEFAULT_NAMESPACE}"
    VERBOSE=false
    DRY_RUN=false
    FORCE=false
    COMMAND=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -c|--cluster)
                CLUSTER_NAME="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                echo "${SCRIPT_NAME} v${SCRIPT_VERSION}"
                exit 0
                ;;
            --replicas)
                REPLICAS="$2"
                shift 2
                ;;
            --*)
                log_error "Unknown option: $1"
                exit 1
                ;;
            *)
                if [[ -z "$COMMAND" ]]; then
                    COMMAND="$1"
                else
                    log_error "Multiple commands not supported: $COMMAND, $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    if [[ -z "$COMMAND" ]]; then
        log_error "No command specified"
        show_help
        exit 1
    fi
}

# Validate environment
validate_environment() {
    case "$ENVIRONMENT" in
        dev|development)
            ENVIRONMENT="development"
            ;;
        staging|stage)
            ENVIRONMENT="staging"
            ;;
        prod|production)
            ENVIRONMENT="production"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT (must be dev/staging/prod)"
            exit 1
            ;;
    esac
}

# Check required tools
check_prerequisites() {
    log "Checking prerequisites..."
    
    local required_tools=(
        "docker"
        "kubectl"
        "helm"
        "aws"
        "git"
        "jq"
        "curl"
    )
    
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again"
        exit 1
    fi
    
    log_success "All prerequisites are available"
}

# Load environment-specific configuration
load_config() {
    local config_file="${PROJECT_ROOT}/config/${ENVIRONMENT}.env"
    
    if [[ -f "$config_file" ]]; then
        log "Loading configuration from $config_file"
        # shellcheck source=/dev/null
        source "$config_file"
    else
        log_warning "Configuration file not found: $config_file"
    fi
    
    # Set defaults if not provided
    export IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
    export IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-migration-assistant}"
    export REPLICAS="${REPLICAS:-3}"
    export CPU_REQUEST="${CPU_REQUEST:-100m}"
    export CPU_LIMIT="${CPU_LIMIT:-500m}"
    export MEMORY_REQUEST="${MEMORY_REQUEST:-256Mi}"
    export MEMORY_LIMIT="${MEMORY_LIMIT:-1Gi}"
}

# ================================
# Core Functions
# ================================

# Build Docker images
build_images() {
    log "Building Docker images for environment: $ENVIRONMENT"
    
    local backend_image="${IMAGE_REPOSITORY}-backend:${IMAGE_TAG}"
    local frontend_image="${IMAGE_REPOSITORY}-frontend:${IMAGE_TAG}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would build images:"
        log_info "  Backend: $backend_image"
        log_info "  Frontend: $frontend_image"
        return 0
    fi
    
    # Build backend image
    log "Building backend image: $backend_image"
    docker build \
        --file "${PROJECT_ROOT}/backend/Dockerfile" \
        --tag "$backend_image" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        --target production \
        "$PROJECT_ROOT"
    
    # Build frontend image
    log "Building frontend image: $frontend_image"
    docker build \
        --file "${PROJECT_ROOT}/frontend/Dockerfile" \
        --tag "$frontend_image" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        --target production \
        "$PROJECT_ROOT"
    
    # Security scanning
    if command -v trivy &> /dev/null; then
        log "Running security scans on images..."
        trivy image --exit-code 1 "$backend_image"
        trivy image --exit-code 1 "$frontend_image"
    else
        log_warning "Trivy not found, skipping security scan"
    fi
    
    # Push images if not local environment
    if [[ "$ENVIRONMENT" != "development" ]]; then
        log "Pushing images to registry..."
        docker push "$backend_image"
        docker push "$frontend_image"
    fi
    
    log_success "Images built successfully"
}

# Run comprehensive test suite
run_tests() {
    log "Running comprehensive test suite for environment: $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would run test suite"
        return 0
    fi
    
    # Backend tests
    log "Running backend tests..."
    cd "${PROJECT_ROOT}/backend"
    
    # Install dependencies
    pip install -r requirements_enhanced.txt
    
    # Run tests with coverage
    pytest \
        tests/ \
        --verbose \
        --cov=app \
        --cov-report=html \
        --cov-report=term \
        --cov-fail-under=80 \
        --junit-xml=test-results.xml
    
    # Frontend tests
    log "Running frontend tests..."
    cd "${PROJECT_ROOT}/frontend"
    
    # Install dependencies
    npm ci
    
    # Run tests
    npm run test:ci
    npm run lint
    npm run type-check
    
    # Integration tests
    log "Running integration tests..."
    cd "$PROJECT_ROOT"
    python tests/test_enhanced_system.py
    
    # Security tests
    if command -v bandit &> /dev/null; then
        log "Running security tests..."
        bandit -r backend/app -f json -o security-report.json
    fi
    
    # Performance tests
    log "Running performance tests..."
    pytest tests/test_performance.py --benchmark-only
    
    log_success "All tests passed"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    log "Deploying to Kubernetes cluster: $CLUSTER_NAME (namespace: $NAMESPACE)"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would deploy to Kubernetes"
        return 0
    fi
    
    # Ensure we're connected to the right cluster
    aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy using Helm
    local chart_path="${PROJECT_ROOT}/helm/migration-assistant"
    local values_file="${PROJECT_ROOT}/helm/values-${ENVIRONMENT}.yaml"
    
    if [[ ! -f "$values_file" ]]; then
        log_error "Values file not found: $values_file"
        exit 1
    fi
    
    # Pre-deployment health check
    if ! check_cluster_health; then
        log_error "Cluster health check failed"
        exit 1
    fi
    
    # Deploy with Helm
    helm upgrade --install \
        "migration-assistant-${ENVIRONMENT}" \
        "$chart_path" \
        --namespace "$NAMESPACE" \
        --values "$values_file" \
        --set image.tag="$IMAGE_TAG" \
        --set environment="$ENVIRONMENT" \
        --set replicaCount="$REPLICAS" \
        --wait \
        --timeout=600s
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/migration-assistant-backend -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/migration-assistant-frontend -n "$NAMESPACE" --timeout=300s
    
    # Run post-deployment health checks
    if ! run_health_checks; then
        log_error "Post-deployment health checks failed"
        exit 1
    fi
    
    log_success "Deployment completed successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations for environment: $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would run database migrations"
        return 0
    fi
    
    # Create migration job
    local migration_job="${PROJECT_ROOT}/k8s/migration-job.yaml"
    
    # Apply migration job with environment-specific values
    envsubst < "$migration_job" | kubectl apply -f - -n "$NAMESPACE"
    
    # Wait for migration to complete
    kubectl wait --for=condition=complete job/migration-job -n "$NAMESPACE" --timeout=300s
    
    # Check if migration was successful
    if kubectl get job migration-job -n "$NAMESPACE" -o jsonpath='{.status.succeeded}' | grep -q "1"; then
        log_success "Database migration completed successfully"
    else
        log_error "Database migration failed"
        kubectl logs job/migration-job -n "$NAMESPACE"
        exit 1
    fi
    
    # Clean up migration job
    kubectl delete job migration-job -n "$NAMESPACE"
}

# Check cluster health
check_cluster_health() {
    log "Checking cluster health..."
    
    # Check node status
    local unhealthy_nodes
    unhealthy_nodes=$(kubectl get nodes --no-headers | grep -v " Ready " | wc -l)
    
    if [[ "$unhealthy_nodes" -gt 0 ]]; then
        log_warning "$unhealthy_nodes unhealthy nodes found"
        return 1
    fi
    
    # Check system pods
    local system_pods_not_ready
    system_pods_not_ready=$(kubectl get pods -n kube-system --no-headers | grep -v "Running\|Completed" | wc -l)
    
    if [[ "$system_pods_not_ready" -gt 0 ]]; then
        log_warning "$system_pods_not_ready system pods not ready"
        return 1
    fi
    
    log_success "Cluster health check passed"
    return 0
}

# Run health checks
run_health_checks() {
    log "Running application health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        # Get service endpoint
        local service_ip
        service_ip=$(kubectl get service migration-assistant-backend -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        
        if [[ -n "$service_ip" ]]; then
            # Check health endpoint
            if curl -sf "http://${service_ip}/health" &>/dev/null; then
                log_success "Health check passed (attempt $attempt)"
                return 0
            fi
        fi
        
        log_info "Health check failed, retrying in 10 seconds (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment in environment: $ENVIRONMENT"
    
    if [[ "$FORCE" != "true" ]]; then
        echo -n "Are you sure you want to rollback? This action cannot be undone. (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Rollback cancelled"
            exit 0
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would rollback deployment"
        return 0
    fi
    
    # Rollback using Helm
    helm rollback "migration-assistant-${ENVIRONMENT}" -n "$NAMESPACE"
    
    # Wait for rollback to complete
    kubectl rollout status deployment/migration-assistant-backend -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/migration-assistant-frontend -n "$NAMESPACE" --timeout=300s
    
    log_success "Rollback completed successfully"
}

# Check deployment status
check_status() {
    log "Checking deployment status for environment: $ENVIRONMENT"
    
    # Check Helm release status
    helm status "migration-assistant-${ENVIRONMENT}" -n "$NAMESPACE"
    
    # Check pod status
    kubectl get pods -n "$NAMESPACE" -l app=migration-assistant
    
    # Check service status
    kubectl get services -n "$NAMESPACE" -l app=migration-assistant
    
    # Check ingress status
    kubectl get ingress -n "$NAMESPACE" -l app=migration-assistant
    
    # Check recent events
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
}

# View application logs
view_logs() {
    log "Viewing logs for environment: $ENVIRONMENT"
    
    local component="${1:-backend}"
    local follow="${2:-false}"
    
    local log_args=()
    if [[ "$follow" == "true" ]]; then
        log_args+=("--follow")
    fi
    
    # Get pod name
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app=migration-assistant,component=$component" -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$pod_name" ]]; then
        kubectl logs "$pod_name" -n "$NAMESPACE" "${log_args[@]}"
    else
        log_error "No pods found for component: $component"
    fi
}

# Scale deployment
scale_deployment() {
    log "Scaling deployment in environment: $ENVIRONMENT"
    
    local replicas="${REPLICAS:-3}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would scale to $replicas replicas"
        return 0
    fi
    
    # Scale backend
    kubectl scale deployment migration-assistant-backend --replicas="$replicas" -n "$NAMESPACE"
    
    # Scale frontend
    kubectl scale deployment migration-assistant-frontend --replicas="$replicas" -n "$NAMESPACE"
    
    # Wait for scaling to complete
    kubectl rollout status deployment/migration-assistant-backend -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/migration-assistant-frontend -n "$NAMESPACE" --timeout=300s
    
    log_success "Scaling completed successfully"
}

# Create database backup
create_backup() {
    log "Creating database backup for environment: $ENVIRONMENT"
    
    local backup_name="migration-db-backup-$(date +%Y%m%d-%H%M%S)"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would create backup: $backup_name"
        return 0
    fi
    
    # Create backup job
    local backup_job="${PROJECT_ROOT}/k8s/backup-job.yaml"
    
    # Apply backup job with environment-specific values
    BACKUP_NAME="$backup_name" envsubst < "$backup_job" | kubectl apply -f - -n "$NAMESPACE"
    
    # Wait for backup to complete
    kubectl wait --for=condition=complete job/backup-job -n "$NAMESPACE" --timeout=1800s
    
    log_success "Backup created successfully: $backup_name"
}

# Cleanup resources
cleanup_resources() {
    log "Cleaning up resources for environment: $ENVIRONMENT"
    
    if [[ "$FORCE" != "true" ]]; then
        echo -n "Are you sure you want to cleanup all resources? This action cannot be undone. (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Cleanup cancelled"
            exit 0
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would cleanup resources"
        return 0
    fi
    
    # Uninstall Helm release
    helm uninstall "migration-assistant-${ENVIRONMENT}" -n "$NAMESPACE" || true
    
    # Delete namespace if it's environment-specific
    if [[ "$ENVIRONMENT" != "production" ]]; then
        kubectl delete namespace "$NAMESPACE" || true
    fi
    
    # Clean up local Docker images
    docker image prune -f
    
    log_success "Cleanup completed successfully"
}

# Validate deployment configuration
validate_config() {
    log "Validating deployment configuration for environment: $ENVIRONMENT"
    
    local errors=0
    
    # Check Helm chart
    local chart_path="${PROJECT_ROOT}/helm/migration-assistant"
    if ! helm lint "$chart_path"; then
        log_error "Helm chart validation failed"
        ((errors++))
    fi
    
    # Check values file
    local values_file="${PROJECT_ROOT}/helm/values-${ENVIRONMENT}.yaml"
    if [[ ! -f "$values_file" ]]; then
        log_error "Values file not found: $values_file"
        ((errors++))
    fi
    
    # Check Kubernetes manifests
    if ! kubectl apply --dry-run=client --validate=true -f "${PROJECT_ROOT}/k8s/" &>/dev/null; then
        log_error "Kubernetes manifest validation failed"
        ((errors++))
    fi
    
    # Check environment variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "OPENAI_API_KEY"
        "SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable not set: $var"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log_success "Configuration validation passed"
        return 0
    else
        log_error "Configuration validation failed with $errors errors"
        return 1
    fi
}

# ================================
# Main Function
# ================================

main() {
    log "Starting ${SCRIPT_NAME} v${SCRIPT_VERSION}"
    
    # Parse command line arguments
    parse_args "$@"
    
    # Validate environment
    validate_environment
    
    # Load configuration
    load_config
    
    # Check prerequisites for most commands
    if [[ "$COMMAND" != "help" && "$COMMAND" != "version" ]]; then
        check_prerequisites
    fi
    
    # Execute command
    case "$COMMAND" in
        build)
            build_images
            ;;
        test)
            run_tests
            ;;
        deploy)
            validate_config
            run_migrations
            deploy_to_kubernetes
            ;;
        rollback)
            rollback_deployment
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "${2:-backend}" "${3:-false}"
            ;;
        cleanup)
            cleanup_resources
            ;;
        validate)
            validate_config
            ;;
        migrate)
            run_migrations
            ;;
        backup)
            create_backup
            ;;
        scale)
            scale_deployment
            ;;
        health)
            run_health_checks
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
    
    log_success "Command '$COMMAND' completed successfully"
}

# ================================
# Script Execution
# ================================

# Enable verbose mode if requested
if [[ "${VERBOSE:-false}" == "true" ]]; then
    set -x
fi

# Run main function with all arguments
main "$@"