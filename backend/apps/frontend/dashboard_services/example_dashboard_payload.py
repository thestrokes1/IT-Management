
Example Dashboard Payloads

This file documents the expected output format for dashboard metrics
based on different user roles.

================================================================================
1. SUPERADMIN - Full Global Access
================================================================================

{
    "computed_at": "2024-01-15T10:30:00Z",
    "period_start": "2024-01-08T00:00:00Z",
    "period_end": "2024-01-15T00:00:00Z",
    "tickets": {
        "created_today": 12,
        "created_week": 85,
        "by_status": {
            "created": 85,
            "updated": 120,
            "resolved": 45
        },
        "by_priority": {
            "unknown": 0
        }
    },
    "assets": {
        "modified_today": 5,
        "modified_week": 23,
        "by_status": {
            "modified_week": 23,
            "assigned": 15,
            "returned": 8
        }
    },
    "security": {
        "incidents_30d": 7,
        "by_severity": {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 1,
            "UNKNOWN": 0
        },
        "by_status": {
            "open": 1,
            "resolved": 6
        },
        "open_critical": 1
    },
    "activity": {
        "total_actions": 456,
        "by_role": {
            "SUPERADMIN": 45,
            "IT_ADMIN": 120,
            "MANAGER": 89,
            "TECHNICIAN": 156,
            "VIEWER": 46
        },
        "by_category": {
            "ACTIVITY": 380,
            "SECURITY": 7,
            "SYSTEM": 45,
            "AUDIT": 24
        },
        "top_actors": [
            {"name": "john.doe", "count": 67},
            {"name": "jane.smith", "count": 54},
            {"name": "bob.wilson", "count": 42}
        ]
    },
    "users": {
        "active_today": 23,
        "active_week": 45,
        "summary": {
            "total_actions": 456,
            "unique_actors": 45,
            "most_active_role": "TECHNICIAN"
        }
    },
    "performance": {
        "cache_hit": false,
        "query_time_ms": 127
    }
}

================================================================================
2. IT_ADMIN - IT Department Scope
================================================================================

{
    "computed_at": "2024-01-15T10:30:00Z",
    "period_start": "2024-01-08T00:00:00Z",
    "period_end": "2024-01-15T00:00:00Z",
    "tickets": {
        "created_today": 8,
        "created_week": 62,
        "by_status": {
            "created": 62,
            "updated": 89,
            "resolved": 34
        },
        "by_priority": {"unknown": 0}
    },
    "assets": {
        "modified_today": 3,
        "modified_week": 18,
        "by_status": {
            "modified_week": 18,
            "assigned": 12,
            "returned": 6
        }
    },
    "security": {
        "incidents_30d": 5,
        "by_severity": {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 3,
            "LOW": 1,
            "UNKNOWN": 0
        },
        "by_status": {"open": 0, "resolved": 5},
        "open_critical": 0
    },
    "activity": {
        "total_actions": 312,
        "by_role": {
            "IT_ADMIN": 98,
            "MANAGER": 67,
            "TECHNICIAN": 112,
            "VIEWER": 35
        },
        "by_category": {
            "ACTIVITY": 265,
            "SECURITY": 5,
            "SYSTEM": 28,
            "AUDIT": 14
        },
        "top_actors": [
            {"name": "jane.smith", "count": 45},
            {"name": "bob.wilson", "count": 38}
        ]
    },
    "users": {
        "active_today": 18,
        "active_week": 32,
        "summary": {
            "total_actions": 312,
            "unique_actors": 32,
            "most_active_role": "TECHNICIAN"
        }
    },
    "performance": {
        "cache_hit": true,
        "query_time_ms": 45
    }
}

================================================================================
3. TECHNICIAN - Limited Scope (Own Actions + Assignments)
================================================================================

{
    "computed_at": "2024-01-15T10:30:00Z",
    "period_start": "2024-01-08T00:00:00Z",
    "period_end": "2024-01-15T00:00:00Z",
    "tickets": {
        "created_today": 2,
        "created_week": 15,
        "by_status": {
            "created": 15,
            "updated": 28,
            "resolved": 12
        },
        "by_priority": {"unknown": 0}
    },
    "assets": {
        "modified_today": 1,
        "modified_week": 5,
        "by_status": {
            "modified_week": 5,
            "assigned": 3,
            "returned": 2
        }
    },
    "security": {
        "incidents_30d": 1,
        "by_severity": {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 0,
            "UNKNOWN": 0
        },
        "by_status": {"open": 0, "resolved": 1},
        "open_critical": 0
    },
    "activity": {
        "total_actions": 67,
        "by_role": {
            "TECHNICIAN": 45,
            "IT_ADMIN": 12,
            "MANAGER": 10
        },
        "by_category": {
            "ACTIVITY": 58,
            "SECURITY": 1,
            "SYSTEM": 5,
            "AUDIT": 3
        },
        "top_actors": [
            {"name": "current_user", "count": 45},
            {"name": "jane.smith", "count": 12}
        ]
    },
    "users": {
        "active_today": 5,
        "active_week": 12,
        "summary": {
            "total_actions": 67,
            "unique_actors": 12,
            "most_active_role": "TECHNICIAN"
        }
    },
    "performance": {
        "cache_hit": false,
        "query_time_ms": 34
    }
}

================================================================================
4. VIEWER - Read-Only Summaries
================================================================================

{
    "computed_at": "2024-01-15T10:30:00Z",
    "period_start": "2024-01-08T00:00:00Z",
    "period_end": "2024-01-15T00:00:00Z",
    "tickets": {
        "created_today": 0,
        "created_week": 0,
        "by_status": {"created": 0, "updated": 0, "resolved": 0},
        "by_priority": {"unknown": 0}
    },
    "assets": {
        "modified_today": 0,
        "modified_week": 0,
        "by_status": {"modified_week": 0, "assigned": 0, "returned": 0}
    },
    "security": {
        "incidents_30d": 0,
        "by_severity": {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0
        },
        "by_status": {"open": 0, "resolved": 0},
        "open_critical": 0
    },
    "activity": {
        "total_actions": 0,
        "by_role": {},
        "by_category": {},
        "top_actors": []
    },
    "users": {
        "active_today": 0,
        "active_week": 0,
        "summary": {
            "total_actions": 0,
            "unique_actors": 0,
            "most_active_role": "UNKNOWN"
        }
    },
    "performance": {
        "cache_hit": true,
        "query_time_ms": 12
    }
}

================================================================================
5. USAGE IN VIEWS
================================================================================

# views.py
from apps.frontend.services import DashboardMetricsService

def dashboard_view(request):
    service = DashboardMetricsService(user=request.user)
    metrics = service.get_all_metrics()
    
    return render(request, 'dashboard.html', {
        'metrics': metrics,
        'metrics_json': json.dumps(metrics.to_dict()),
    })

# Or for API responses
def dashboard_api(request):
    service = DashboardMetricsService(user=request.user)
    metrics = service.get_all_metrics()
    
    return JsonResponse(metrics.to_dict())

# Convenience function
from apps.frontend.services import get_dashboard_metrics

def dashboard_view(request):
    metrics = get_dashboard_metrics(user=request.user)
    return render(request, 'dashboard.html', {'metrics': metrics})

================================================================================
6. PERFORMANCE NOTES
================================================================================

- Cache TTL varies by role:
  - SUPERADMIN/IT_ADMIN: 5 minutes
  - MANAGER: 10 minutes
  - TECHNICIAN: 1 minute
  - VIEWER: 15 minutes

- Query limits (for aggregation):
  - Security by severity: 1000 logs
  - Actions by role: 10000 logs
  - Top actors: 10000 logs

- Always use indexed fields:
  - timestamp (for date filtering)
  - action (for action filtering)
  - actor_name (for actor aggregation)
  - model_name (for target filtering)

