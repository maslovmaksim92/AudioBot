"""
API роутер для получения логов с Render
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import os
import httpx
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/render-logs", tags=["Render Logs"])

@router.get("/")
async def get_render_logs(
    service_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """
    Получить логи с Render
    
    Args:
        service_id: ID сервиса на Render (если не указан, берётся из env)
        limit: Количество строк логов (max 1000)
        start_time: Начало периода (ISO format)
        end_time: Конец периода (ISO format)
    """
    try:
        render_api_key = os.environ.get('RENDER_API_KEY')
        if not render_api_key:
            raise HTTPException(status_code=500, detail="RENDER_API_KEY not configured")
        
        # Получаем service_id
        if not service_id:
            service_id = os.environ.get('RENDER_SERVICE_ID')
        
        if not service_id:
            raise HTTPException(status_code=400, detail="service_id required")
        
        # Формируем параметры запроса
        params = {
            'limit': limit
        }
        
        # Добавляем временные фильтры если указаны
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                params['startTime'] = dt.isoformat()
            except:
                pass
        
        if end_time:
            try:
                dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                params['endTime'] = dt.isoformat()
            except:
                pass
        
        # Запрос к Render API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.render.com/v1/services/{service_id}/logs",
                headers={
                    'Authorization': f'Bearer {render_api_key}',
                    'Accept': 'application/json'
                },
                params=params
            )
            
            if response.status_code == 200:
                logs_data = response.json()
                
                # Преобразуем в удобный формат
                logs = []
                for log_entry in logs_data:
                    logs.append({
                        'timestamp': log_entry.get('timestamp'),
                        'message': log_entry.get('message'),
                        'level': log_entry.get('level', 'INFO'),
                        'service': service_id
                    })
                
                logger.info(f"✅ Retrieved {len(logs)} logs from Render")
                
                return {
                    'success': True,
                    'logs': logs,
                    'count': len(logs),
                    'service_id': service_id
                }
            
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Render API key")
            
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Service not found")
            
            else:
                logger.error(f"Render API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Render API error: {response.text}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Render logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def stream_render_logs(
    service_id: Optional[str] = None,
    tail: int = Query(default=100, le=1000)
):
    """
    Получить последние логи с Render (tail)
    
    Args:
        service_id: ID сервиса на Render
        tail: Количество последних строк
    """
    try:
        render_api_key = os.environ.get('RENDER_API_KEY')
        if not render_api_key:
            raise HTTPException(status_code=500, detail="RENDER_API_KEY not configured")
        
        if not service_id:
            service_id = os.environ.get('RENDER_SERVICE_ID')
        
        if not service_id:
            raise HTTPException(status_code=400, detail="service_id required")
        
        # Запрос к Render API для получения последних логов
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.render.com/v1/services/{service_id}/logs",
                headers={
                    'Authorization': f'Bearer {render_api_key}',
                    'Accept': 'application/json'
                },
                params={'limit': tail}
            )
            
            if response.status_code == 200:
                logs_data = response.json()
                
                # Форматируем логи в текстовый формат
                log_lines = []
                for log_entry in logs_data:
                    timestamp = log_entry.get('timestamp', '')
                    message = log_entry.get('message', '')
                    log_lines.append(f"{timestamp} {message}")
                
                return {
                    'success': True,
                    'logs_text': '\n'.join(log_lines),
                    'count': len(log_lines),
                    'service_id': service_id
                }
            
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Render API error: {response.text}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error streaming Render logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_render_services():
    """
    Получить список сервисов на Render
    """
    try:
        render_api_key = os.environ.get('RENDER_API_KEY')
        if not render_api_key:
            raise HTTPException(status_code=500, detail="RENDER_API_KEY not configured")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.render.com/v1/services",
                headers={
                    'Authorization': f'Bearer {render_api_key}',
                    'Accept': 'application/json'
                },
                params={'limit': 20}
            )
            
            if response.status_code == 200:
                data = response.json()
                services = []
                
                for service in data:
                    services.append({
                        'id': service.get('id'),
                        'name': service.get('name'),
                        'type': service.get('type'),
                        'status': service.get('status'),
                        'created_at': service.get('createdAt')
                    })
                
                return {
                    'success': True,
                    'services': services,
                    'count': len(services)
                }
            
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Render API error: {response.text}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Render services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local")
async def get_local_logs(
    log_file: str = Query(default="backend", enum=["backend", "frontend"]),
    lines: int = Query(default=100, le=1000)
):
    """
    Получить локальные логи (для разработки)
    
    Args:
        log_file: Какой лог файл читать (backend/frontend)
        lines: Количество строк с конца файла
    """
    try:
        log_paths = {
            'backend': '/var/log/supervisor/backend.err.log',
            'frontend': '/var/log/supervisor/frontend.err.log'
        }
        
        log_path = log_paths.get(log_file)
        if not log_path:
            raise HTTPException(status_code=400, detail="Invalid log_file")
        
        # Читаем последние N строк
        import subprocess
        result = subprocess.run(
            ['tail', '-n', str(lines), log_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'logs_text': result.stdout,
                'log_file': log_file,
                'lines': len(result.stdout.split('\n'))
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to read log file")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reading local logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
