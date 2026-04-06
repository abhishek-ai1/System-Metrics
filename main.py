import psutil
import platform
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

app = FastAPI(
    title="System Observability API",
    version="1.0.0",
    description="Production-ready system monitoring API"
)

# ------------------------------
# Prometheus Metrics
# ------------------------------

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API Requests",
    ["method", "endpoint"]
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency"
)

# ------------------------------
# Helper Functions
# ------------------------------

def cpu_metrics():
    freq = psutil.cpu_freq()

    return {
        "usage_percent": psutil.cpu_percent(interval=1),
        "logical_cores": psutil.cpu_count(),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": {
            "current": freq.current if freq else None,
            "min": freq.min if freq else None,
            "max": freq.max if freq else None
        }
    }


def memory_metrics():
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "virtual_memory": {
            "total_gb": round(vm.total / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "percent": vm.percent
        },
        "swap_memory": {
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
            "free_gb": round(swap.free / (1024**3), 2),
            "percent": swap.percent
        }
    }


def disk_metrics():
    disk = psutil.disk_usage('/')

    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "percent": disk.percent
    }


def network_metrics():
    net = psutil.net_io_counters()

    return {
        "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv
    }


def system_info():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "boot_time": datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": str(timedelta(seconds=int(uptime_seconds)))
    }

# ------------------------------
# Health Endpoints
# ------------------------------

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def readiness():
    return {"status": "ready"}


@app.get("/live")
def liveness():
    return {"status": "alive"}

# ------------------------------
# Prometheus Endpoint
# ------------------------------

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

# ------------------------------
# Observability API
# ------------------------------

@app.get("/api/v1/observability")
def observability():

    REQUEST_COUNT.labels(method="GET", endpoint="/observability").inc()

    start = time.time()

    data = {
        "system_info": system_info(),
        "cpu": cpu_metrics(),
        "memory": memory_metrics(),
        "disk": disk_metrics(),
        "network": network_metrics()
    }

    REQUEST_LATENCY.observe(time.time() - start)

    return data

# ------------------------------
# Run Server
# ------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)