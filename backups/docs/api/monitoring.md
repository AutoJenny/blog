# Monitoring API

## Overview
The Monitoring API provides endpoints for system health checks, performance monitoring, and dependency status tracking.

## Health Checks

### System Health
```http
GET /api/v1/health
```

#### Response
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2025-04-23T15:34:10Z",
    "version": "1.0.0",
    "uptime": 345600,
    "components": {
      "database": {
        "status": "healthy",
        "latency": 5,
        "connections": 10
      },
      "cache": {
        "status": "healthy",
        "hit_rate": 0.95,
        "memory_usage": 0.45
      },
      "storage": {
        "status": "healthy",
        "space_used": "45GB",
        "space_available": "155GB"
      }
    }
  }
}
```

### Dependency Status
```http
GET /api/v1/health/dependencies
```

#### Response
```json
{
  "status": "success",
  "data": {
    "services": {
      "openai": {
        "status": "operational",
        "latency": 150,
        "quota": {
          "used": 15000,
          "limit": 100000
        }
      },
      "s3": {
        "status": "operational",
        "latency": 45,
        "errors": []
      },
      "email": {
        "status": "degraded",
        "latency": 250,
        "errors": ["High latency"]
      }
    },
    "databases": {
      "postgres": {
        "status": "operational",
        "version": "15.2",
        "connections": {
          "active": 5,
          "idle": 3,
          "max": 20
        }
      },
      "redis": {
        "status": "operational",
        "version": "7.0.11",
        "memory": {
          "used": "256MB",
          "peak": "512MB",
          "limit": "1GB"
        }
      }
    }
  }
}
```

### Queue Status
```http
GET /api/v1/health/queues
```

#### Response
```json
{
  "status": "success",
  "data": {
    "queues": {
      "default": {
        "status": "operational",
        "jobs": {
          "waiting": 5,
          "processing": 2,
          "failed": 1
        },
        "workers": 3
      },
      "media": {
        "status": "operational",
        "jobs": {
          "waiting": 10,
          "processing": 4,
          "failed": 0
        },
        "workers": 5
      }
    },
    "workers": {
      "active": 8,
      "idle": 2,
      "total": 10
    }
  }
}
```

## Performance Monitoring

### System Metrics
```http
GET /api/v1/metrics/system
```

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| start | datetime | Start timestamp |
| end | datetime | End timestamp |
| interval | string | Aggregation interval |

#### Response
```json
{
  "status": "success",
  "data": {
    "cpu": {
      "usage": [
        {
          "timestamp": "2025-04-23T15:30:00Z",
          "value": 45.5
        }
      ],
      "average": 42.3
    },
    "memory": {
      "usage": [
        {
          "timestamp": "2025-04-23T15:30:00Z",
          "value": 2048
        }
      ],
      "average": 1843
    },
    "disk": {
      "reads": 1500,
      "writes": 500,
      "latency": 5
    }
  }
}
```

### Application Metrics
```http
GET /api/v1/metrics/application
```

#### Response
```json
{
  "status": "success",
  "data": {
    "requests": {
      "total": 15000,
      "success": 14850,
      "failed": 150,
      "by_endpoint": {
        "/api/v1/posts": {
          "count": 5000,
          "average_latency": 120
        }
      }
    },
    "database": {
      "queries": 25000,
      "average_latency": 15,
      "slow_queries": 25
    },
    "cache": {
      "hits": 12000,
      "misses": 3000,
      "hit_rate": 0.8
    }
  }
}
```

### LLM Performance
```http
GET /api/v1/metrics/llm
```

#### Response
```json
{
  "status": "success",
  "data": {
    "requests": {
      "total": 1000,
      "success": 980,
      "failed": 20
    },
    "latency": {
      "average": 2500,
      "p95": 3500,
      "p99": 4500
    },
    "tokens": {
      "total": 150000,
      "prompt": 50000,
      "completion": 100000
    },
    "costs": {
      "total": 15.50,
      "by_model": {
        "gpt-4": 12.50,
        "gpt-3.5-turbo": 3.00
      }
    }
  }
}
```

## Alerts

### List Alerts
```http
GET /api/v1/alerts
```

#### Response
```json
{
  "status": "success",
  "data": {
    "active": [
      {
        "id": 1,
        "severity": "high",
        "message": "High CPU usage",
        "created_at": "2025-04-23T15:34:10Z",
        "status": "triggered",
        "metadata": {
          "threshold": 90,
          "current": 95
        }
      }
    ],
    "resolved": [
      {
        "id": 2,
        "severity": "medium",
        "message": "High latency",
        "created_at": "2025-04-23T14:34:10Z",
        "resolved_at": "2025-04-23T15:00:00Z",
        "status": "resolved"
      }
    ]
  }
}
```

### Configure Alert
```http
POST /api/v1/alerts/configure
```

#### Request Body
```json
{
  "name": "CPU Alert",
  "condition": {
    "metric": "cpu_usage",
    "operator": ">",
    "threshold": 90,
    "duration": "5m"
  },
  "severity": "high",
  "notifications": {
    "email": ["admin@blog.com"],
    "slack": "#monitoring"
  }
}
```

## Error Responses

### Service Unavailable
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service is not responding",
    "details": {
      "service": "database",
      "last_check": "2025-04-23T15:34:10Z"
    }
  }
}
```

### Rate Limit
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 100,
      "reset_at": "2025-04-23T15:35:00Z"
    }
  }
}
```

## Best Practices

### Health Checks
1. Regular intervals
2. Quick response time
3. Meaningful status
4. Detailed errors

### Metrics Collection
1. Appropriate sampling
2. Efficient storage
3. Data retention
4. Access control

### Alerting
1. Avoid noise
2. Clear thresholds
3. Actionable alerts
4. Proper routing

### Performance
1. Minimal overhead
2. Efficient queries
3. Data aggregation
4. Cache results

## Usage Examples

### Check System Health
```bash
curl -H "Authorization: Bearer <token>" \
     https://api.blog.com/v1/health
```

### Get System Metrics
```bash
curl -H "Authorization: Bearer <token>" \
     "https://api.blog.com/v1/metrics/system?interval=5m"
```

### Configure Alert
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Memory Alert", "threshold": 90}' \
     https://api.blog.com/v1/alerts/configure
``` 