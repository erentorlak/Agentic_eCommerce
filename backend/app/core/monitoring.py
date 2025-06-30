"""
Monitoring and Observability for Migration System

Following best practices for:
- Structured metrics collection
- Health checks and readiness probes
- Performance monitoring
- Business metrics tracking
- Distributed tracing
- Alerting integration
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

import structlog
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST

from ..core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetricPoint:
    """A single metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PrometheusMetrics:
    """Prometheus metrics for the application"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # HTTP Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Migration Metrics
        self.migrations_total = Counter(
            'migrations_total',
            'Total number of migrations',
            ['source_platform', 'destination_platform', 'status'],
            registry=self.registry
        )
        
        self.migration_duration = Histogram(
            'migration_duration_seconds',
            'Migration duration in seconds',
            ['source_platform', 'destination_platform'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800],  # 1m to 8h
            registry=self.registry
        )
        
        self.migration_data_volume = Histogram(
            'migration_data_volume_items',
            'Number of items migrated',
            ['source_platform', 'destination_platform', 'data_type'],
            buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000],
            registry=self.registry
        )
        
        # AI Agent Metrics
        self.ai_agent_calls_total = Counter(
            'ai_agent_calls_total',
            'Total number of AI agent calls',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.ai_agent_duration = Histogram(
            'ai_agent_duration_seconds',
            'AI agent processing duration',
            ['agent_type'],
            registry=self.registry
        )
        
        self.ai_tokens_used = Counter(
            'ai_tokens_used_total',
            'Total AI tokens consumed',
            ['model', 'agent_type'],
            registry=self.registry
        )
        
        # System Metrics
        self.active_migrations = Gauge(
            'active_migrations_count',
            'Number of currently active migrations',
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'database_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        # Business Metrics
        self.successful_migrations_24h = Gauge(
            'successful_migrations_24h',
            'Number of successful migrations in last 24 hours',
            registry=self.registry
        )
        
        self.average_migration_time = Gauge(
            'average_migration_time_seconds',
            'Average migration completion time',
            registry=self.registry
        )
        
        # Application Info
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': settings.ENVIRONMENT,
            'build_time': getattr(settings, 'BUILD_TIME', 'unknown'),
            'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}"
        })
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_migration_start(self, source_platform: str, destination_platform: str):
        """Record migration start"""
        self.migrations_total.labels(
            source_platform=source_platform,
            destination_platform=destination_platform,
            status='started'
        ).inc()
        
        # Update active migrations count
        self.active_migrations.inc()
    
    def record_migration_completion(self, source_platform: str, destination_platform: str, 
                                  duration: float, status: str, data_volumes: Dict[str, int]):
        """Record migration completion"""
        self.migrations_total.labels(
            source_platform=source_platform,
            destination_platform=destination_platform,
            status=status
        ).inc()
        
        self.migration_duration.labels(
            source_platform=source_platform,
            destination_platform=destination_platform
        ).observe(duration)
        
        # Record data volumes
        for data_type, volume in data_volumes.items():
            self.migration_data_volume.labels(
                source_platform=source_platform,
                destination_platform=destination_platform,
                data_type=data_type
            ).observe(volume)
        
        # Update active migrations count
        self.active_migrations.dec()
    
    def record_ai_agent_call(self, agent_type: str, duration: float, status: str, 
                           model: str = None, tokens_used: int = None):
        """Record AI agent call metrics"""
        self.ai_agent_calls_total.labels(agent_type=agent_type, status=status).inc()
        self.ai_agent_duration.labels(agent_type=agent_type).observe(duration)
        
        if model and tokens_used:
            self.ai_tokens_used.labels(model=model, agent_type=agent_type).inc(tokens_used)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory_usage.labels(type='used').set(memory.used)
        self.system_memory_usage.labels(type='available').set(memory.available)
        self.system_memory_usage.labels(type='total').set(memory.total)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_cpu_usage.set(cpu_percent)
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry).decode('utf-8')


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.register_default_checks()
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def register_default_checks(self):
        """Register default health checks"""
        self.register_check("database", self._check_database)
        self.register_check("memory", self._check_memory)
        self.register_check("disk", self._check_disk)
        self.register_check("external_services", self._check_external_services)
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await self._run_check(check_func)
                duration_ms = (time.time() - start_time) * 1000
                
                results[name] = HealthCheckResult(
                    name=name,
                    status=result.get('status', HealthStatus.UNHEALTHY),
                    message=result.get('message', 'No message'),
                    duration_ms=duration_ms,
                    details=result.get('details', {})
                )
                
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(exc)}",
                    duration_ms=duration_ms,
                    details={"error": str(exc)}
                )
                
                logger.error(f"Health check {name} failed", error=str(exc))
        
        return results
    
    async def _run_check(self, check_func: callable) -> Dict[str, Any]:
        """Run a single health check"""
        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Mock database check - replace with actual database connection
            await asyncio.sleep(0.01)  # Simulate DB call
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Database connection successful",
                "details": {
                    "connected": True,
                    "pool_size": 10,
                    "active_connections": 3
                }
            }
        except Exception as exc:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(exc)}",
                "details": {"error": str(exc)}
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {memory_percent:.1f}%"
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory_percent:.1f}%"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "percent": memory_percent,
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3)
            }
        }
    
    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 95:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk usage: {disk_percent:.1f}%"
        elif disk_percent > 85:
            status = HealthStatus.DEGRADED
            message = f"High disk usage: {disk_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {disk_percent:.1f}%"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "percent": disk_percent,
                "used_gb": disk.used / (1024**3),
                "total_gb": disk.total / (1024**3)
            }
        }
    
    async def _check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity"""
        try:
            # Mock external service checks
            services = {
                "openai_api": True,
                "shopify_api": True,
                "ideasoft_api": True
            }
            
            failed_services = [name for name, status in services.items() if not status]
            
            if failed_services:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"Some external services unavailable: {', '.join(failed_services)}",
                    "details": {"services": services}
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "All external services available",
                    "details": {"services": services}
                }
                
        except Exception as exc:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"External service check failed: {str(exc)}",
                "details": {"error": str(exc)}
            }
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall health status"""
        if not results:
            return HealthStatus.UNHEALTHY
        
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class PerformanceMonitor:
    """Performance monitoring and alerting"""
    
    def __init__(self):
        self.metrics_buffer: List[MetricPoint] = []
        self.alert_thresholds = {
            'response_time_p95': 5.0,  # 5 seconds
            'error_rate': 0.05,  # 5%
            'memory_usage': 0.85,  # 85%
            'cpu_usage': 0.80,  # 80%
        }
        self.performance_data = {}
    
    def record_performance_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a performance metric"""
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {}
        )
        
        self.metrics_buffer.append(metric)
        
        # Keep buffer size reasonable
        if len(self.metrics_buffer) > 10000:
            self.metrics_buffer = self.metrics_buffer[-5000:]
    
    def calculate_percentiles(self, metric_name: str, window_minutes: int = 5) -> Dict[str, float]:
        """Calculate percentiles for a metric over time window"""
        import statistics
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        values = [
            metric.value for metric in self.metrics_buffer
            if metric.name == metric_name and metric.timestamp >= cutoff_time
        ]
        
        if not values:
            return {}
        
        values.sort()
        
        return {
            'p50': statistics.median(values),
            'p90': self._percentile(values, 0.90),
            'p95': self._percentile(values, 0.95),
            'p99': self._percentile(values, 0.99),
            'min': min(values),
            'max': max(values),
            'avg': statistics.mean(values),
            'count': len(values)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        index = int(percentile * (len(values) - 1))
        return values[index]
    
    def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        # Check response time
        response_times = self.calculate_percentiles('http_response_time')
        if response_times.get('p95', 0) > self.alert_thresholds['response_time_p95']:
            alerts.append({
                'type': 'performance',
                'severity': 'warning',
                'metric': 'response_time_p95',
                'value': response_times['p95'],
                'threshold': self.alert_thresholds['response_time_p95'],
                'message': f"High response time: P95 = {response_times['p95']:.2f}s"
            })
        
        # Check system resources
        try:
            memory_percent = psutil.virtual_memory().percent / 100
            if memory_percent > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'resource',
                    'severity': 'critical' if memory_percent > 0.95 else 'warning',
                    'metric': 'memory_usage',
                    'value': memory_percent,
                    'threshold': self.alert_thresholds['memory_usage'],
                    'message': f"High memory usage: {memory_percent:.1%}"
                })
            
            cpu_percent = psutil.cpu_percent() / 100
            if cpu_percent > self.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'resource',
                    'severity': 'warning',
                    'metric': 'cpu_usage',
                    'value': cpu_percent,
                    'threshold': self.alert_thresholds['cpu_usage'],
                    'message': f"High CPU usage: {cpu_percent:.1%}"
                })
                
        except Exception as exc:
            logger.error("Failed to check system resources", error=str(exc))
        
        return alerts


# Global instances
metrics = PrometheusMetrics()
health_checker = HealthChecker()
performance_monitor = PerformanceMonitor()


async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status"""
    health_results = await health_checker.run_all_checks()
    overall_status = health_checker.get_overall_status(health_results)
    
    return {
        "status": overall_status.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            name: {
                "status": result.status.value,
                "message": result.message,
                "duration_ms": result.duration_ms,
                "details": result.details
            }
            for name, result in health_results.items()
        },
        "system": {
            "uptime_seconds": time.time() - getattr(get_health_status, '_start_time', time.time()),
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "environment": settings.ENVIRONMENT
        }
    }


def setup_monitoring():
    """Initialize monitoring system"""
    # Set start time for uptime calculation
    get_health_status._start_time = time.time()
    
    # Start background task to update system metrics
    async def update_system_metrics():
        while True:
            try:
                metrics.update_system_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as exc:
                logger.error("Failed to update system metrics", error=str(exc))
                await asyncio.sleep(30)
    
    # Start background task
    asyncio.create_task(update_system_metrics())
    
    logger.info("Monitoring system initialized")