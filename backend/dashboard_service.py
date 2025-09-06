import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger
from pathlib import Path

class DashboardService:
    """Dashboard service for system monitoring and analytics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
    def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.utcnow().isoformat() + "Z"
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        uptime = datetime.utcnow() - self.start_time
        
        dashboard_data = {
            "system": {
                "status": "running",
                "uptime": str(uptime),
                "uptime_seconds": int(uptime.total_seconds()),
                "start_time": self.start_time.isoformat() + "Z",
                "current_time": self.get_current_time(),
                "environment": os.getenv("APP_ENV", "production")
            },
            "metrics": {
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate": round((self.error_count / max(self.request_count, 1)) * 100, 2),
                "requests_per_hour": self.calculate_requests_per_hour()
            },
            "services": await self.get_services_status(),
            "environment": self.get_environment_info(),
            "recent_activity": await self.get_recent_activity(),
            "system_resources": self.get_system_resources()
        }
        
        return dashboard_data
    
    async def get_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        services = {}
        
        # Telegram Bot
        services["telegram"] = {
            "name": "Telegram Bot",
            "configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "status": "active" if os.getenv("TELEGRAM_BOT_TOKEN") else "not_configured",
            "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", "")
        }
        
        # Bitrix24 
        services["bitrix24"] = {
            "name": "Bitrix24 CRM",
            "configured": bool(os.getenv("BITRIX24_WEBHOOK_URL")),
            "status": "active" if os.getenv("BITRIX24_WEBHOOK_URL") else "not_configured",
            "portal": self.extract_portal_from_webhook(os.getenv("BITRIX24_WEBHOOK_URL", ""))
        }
        
        # AI Service
        services["ai"] = {
            "name": "AI Service (Emergent LLM)",
            "configured": bool(os.getenv("EMERGENT_LLM_KEY")),
            "status": "active" if os.getenv("EMERGENT_LLM_KEY") else "not_configured",
            "model": "gpt-4o-mini"
        }
        
        # Database
        services["database"] = {
            "name": "MongoDB",
            "configured": bool(os.getenv("MONGO_URL")),
            "status": "active" if os.getenv("MONGO_URL") else "not_configured",
            "url": self.mask_sensitive_url(os.getenv("MONGO_URL", ""))
        }
        
        return services
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.name,
            "environment": os.getenv("APP_ENV", "production"),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "port": os.getenv("PORT", "8000"),
            "timezone": str(datetime.now().astimezone().tzinfo)
        }
    
    async def get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        activities = [
            {
                "timestamp": self.get_current_time(),
                "type": "system",
                "message": "Dashboard data requested",
                "level": "info"
            }
        ]
        
        # Add some sample activities (in production, this would come from logs/database)
        if self.request_count > 0:
            activities.append({
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
                "type": "api",
                "message": f"Total API requests: {self.request_count}",
                "level": "info"
            })
        
        if self.error_count > 0:
            activities.append({
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z",
                "type": "error",
                "message": f"Total errors encountered: {self.error_count}",
                "level": "warning"
            })
        
        return activities[-10:]  # Last 10 activities
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get basic system resource info"""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
        except ImportError:
            return {
                "cpu_percent": "N/A (psutil not available)",
                "memory": {"total": "N/A", "available": "N/A", "percent": "N/A"},
                "disk": {"total": "N/A", "free": "N/A", "percent": "N/A"}
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_recent_logs(self, lines: int = 100) -> List[str]:
        """Get recent log entries"""
        logs = []
        
        try:
            log_file = self.logs_dir / "app.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = f.readlines()[-lines:]
            else:
                logs = ["Log file not found"]
        except Exception as e:
            logs = [f"Error reading logs: {str(e)}"]
        
        return [log.strip() for log in logs]
    
    def calculate_requests_per_hour(self) -> float:
        """Calculate requests per hour"""
        uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        if uptime_hours == 0:
            return 0.0
        return round(self.request_count / uptime_hours, 2)
    
    def extract_portal_from_webhook(self, webhook_url: str) -> str:
        """Extract Bitrix24 portal from webhook URL"""
        if not webhook_url:
            return ""
        
        try:
            if "/rest/" in webhook_url:
                return webhook_url.split("/rest/")[0]
            return "Unknown portal"
        except:
            return "Invalid URL"
    
    def mask_sensitive_url(self, url: str) -> str:
        """Mask sensitive parts of URL"""
        if not url:
            return ""
        
        try:
            if "mongodb" in url.lower():
                # Hide password in MongoDB URL
                if "@" in url:
                    parts = url.split("@")
                    if len(parts) >= 2:
                        credentials_part = parts[0]
                        if ":" in credentials_part:
                            user_pass = credentials_part.split(":")
                            if len(user_pass) >= 3:  # mongodb://user:pass
                                user_pass[-1] = "****"  # Mask password
                                return ":".join(user_pass) + "@" + "@".join(parts[1:])
            return url
        except:
            return "Invalid URL"
    
    def increment_request_count(self):
        """Increment request counter"""
        self.request_count += 1
    
    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1
    
    async def log_activity(self, activity_type: str, message: str, level: str = "info"):
        """Log activity for dashboard"""
        activity = {
            "timestamp": self.get_current_time(),
            "type": activity_type,
            "message": message,
            "level": level
        }
        
        # In production, save to database or proper logging system
        logger.info(f"📊 Dashboard activity: {activity}")
    
    async def get_analytics_data(self, period: str = "24h") -> Dict[str, Any]:
        """Get analytics data for specified period"""
        # This is a placeholder - in production, you'd query actual analytics data
        analytics = {
            "period": period,
            "telegram_messages": {
                "total": 150,
                "today": 25,
                "trend": "+15%"
            },
            "bitrix24_deals": {
                "total": 50,
                "new_today": 3,
                "trend": "+8%"
            },
            "ai_requests": {
                "total": 120,
                "today": 20,
                "trend": "+22%"
            },
            "top_user_intents": [
                {"intent": "cleaning_request", "count": 45},
                {"intent": "price_inquiry", "count": 30},
                {"intent": "support_request", "count": 25},
                {"intent": "general_info", "count": 20}
            ],
            "response_times": {
                "avg_ai_response": "1.2s",
                "avg_bitrix24_api": "0.8s",
                "avg_telegram_webhook": "0.3s"
            }
        }
        
        return analytics
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        services = await self.get_services_status()
        
        healthy_services = sum(1 for s in services.values() if s["status"] == "active")
        total_services = len(services)
        
        health_score = (healthy_services / total_services) * 100
        
        return {
            "overall_health": "healthy" if health_score > 75 else "warning" if health_score > 50 else "critical",
            "health_score": round(health_score, 1),
            "healthy_services": healthy_services,
            "total_services": total_services,
            "uptime": str(datetime.utcnow() - self.start_time),
            "last_check": self.get_current_time()
        }