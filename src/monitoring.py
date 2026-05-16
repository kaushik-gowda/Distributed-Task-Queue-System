"""
Production-ready monitoring and health check utilities
"""

import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_percent: float
    timestamp: datetime


@dataclass
class ServiceHealth:
    """Service health status."""
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: datetime = None
    
    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.utcnow()


class HealthMonitor:
    """Monitor system and service health."""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        """Initialize health monitor.
        
        Args:
            alert_thresholds: Thresholds for alerts (cpu, memory, disk percentages)
        """
        self.alert_thresholds = alert_thresholds or {
            "cpu": 90.0,
            "memory": 85.0,
            "disk": 90.0,
        }
        self.service_checks = {}
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            disk_percent=disk.percent,
            timestamp=datetime.utcnow()
        )
    
    def check_alerts(self, metrics: SystemMetrics) -> list:
        """Check metrics against alert thresholds.
        
        Returns:
            List of alert messages
        """
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds["cpu"]:
            alerts.append(
                f"High CPU usage: {metrics.cpu_percent:.1f}% "
                f"(threshold: {self.alert_thresholds['cpu']}%)"
            )
        
        if metrics.memory_percent > self.alert_thresholds["memory"]:
            alerts.append(
                f"High memory usage: {metrics.memory_percent:.1f}% "
                f"({metrics.memory_mb:.0f} MB)"
            )
        
        if metrics.disk_percent > self.alert_thresholds["disk"]:
            alerts.append(
                f"High disk usage: {metrics.disk_percent:.1f}% "
                f"(threshold: {self.alert_thresholds['disk']}%)"
            )
        
        return alerts
    
    async def check_service_health(
        self,
        service_name: str,
        check_fn,
        timeout: float = 5.0
    ) -> ServiceHealth:
        """Check individual service health.
        
        Args:
            service_name: Name of service to check
            check_fn: Async function that checks service health
            timeout: Timeout in seconds
        
        Returns:
            ServiceHealth status
        """
        start_time = time.time()
        try:
            result = await asyncio.wait_for(check_fn(), timeout=timeout)
            response_time = (time.time() - start_time) * 1000
            
            status = "healthy" if result else "degraded"
            return ServiceHealth(
                service_name=service_name,
                status=status,
                response_time_ms=response_time
            )
        except asyncio.TimeoutError:
            return ServiceHealth(
                service_name=service_name,
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message="Service check timeout"
            )
        except Exception as e:
            return ServiceHealth(
                service_name=service_name,
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        metrics = self.get_system_metrics()
        alerts = self.check_alerts(metrics)
        
        overall_status = "healthy"
        if metrics.cpu_percent > 80 or metrics.memory_percent > 80:
            overall_status = "degraded"
        if alerts:
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "status": overall_status,
            "system": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_mb": metrics.memory_mb,
                "disk_percent": metrics.disk_percent,
            },
            "alerts": alerts,
        }


class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.request_times = []
        self.error_count = 0
        self.success_count = 0
    
    def record_request(self, response_time: float, success: bool = True):
        """Record request metric.
        
        Args:
            response_time: Response time in milliseconds
            success: Whether request was successful
        """
        self.request_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Performance metrics dictionary
        """
        if not self.request_times:
            return {
                "requests": 0,
                "errors": self.error_count,
                "success_rate": 0,
            }
        
        request_times = sorted(self.request_times)
        total_requests = self.success_count + self.error_count
        
        return {
            "requests": total_requests,
            "errors": self.error_count,
            "success_rate": (self.success_count / total_requests * 100) if total_requests > 0 else 0,
            "response_time": {
                "avg_ms": sum(self.request_times) / len(self.request_times),
                "min_ms": min(self.request_times),
                "max_ms": max(self.request_times),
                "p50_ms": request_times[len(request_times) // 2],
                "p95_ms": request_times[int(len(request_times) * 0.95)],
                "p99_ms": request_times[int(len(request_times) * 0.99)],
            }
        }


# Global monitor instances
health_monitor = HealthMonitor()
performance_monitor = PerformanceMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor."""
    return health_monitor


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return performance_monitor
