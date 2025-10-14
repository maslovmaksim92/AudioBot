"""
API для управления статьями расходов и их маппингом на категории
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncpg
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["finance_articles"])


class ArticleMapping(BaseModel):
    article: str
    category: str
    description: Optional[str] = None


class UpdateArticlesRequest(BaseModel):
    mappings: List[ArticleMapping]


# Маппинг статей расходов на категории
ARTICLE_MAPPING = {
    "1.001": "Аренда",
    "1.101": "Покупка авто",
    "1.104": "Продукты питания",
    "1.109": "Цифровая техника",
    "1.006": "Мобильная связь",
    "1.007": "Мобильная связь",
    "3.001": "Реклама и маркетинг",
    "3.004": "Реклама и маркетинг",
    "3.005": "Реклама и маркетинг",
    "4.001": "Аутсорсинг",
    "4.102": "Канцтовары",
    "4.103": "Юридические услуги",
    "9.001": "Транспорт",
    "9.007": "Транспорт",
    "9.008": "Транспорт",
    "9.009": "Транспорт",
    "9.011": "Страхование",
    "9.012": "Транспорт",
    "9.013": "Реклама и маркетинг",
    "11.002": "Материалы",
    "11.003": "Материалы",
    "11.004": "Материалы",
    "11.005": "Коммунальные услуги",
    "11.006": "Коммунальные услуги",
    "13.002": "Филиал Ленинск-Кузнецкий",
    "16.001": "Зарплата",
    "16.002": "Зарплата",
    "16.003": "Зарплата",
    "16.004": "Зарплата",
    "16.005": "Зарплата",
    "17.001": "Лизинг",
    "17.003": "Кредиты",
}


async def get_db_connection():
    """Получить прямое соединение с БД"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        return await asyncpg.connect(db_url)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.get("/finances/articles")
async def get_articles():
    """
    Получить все статьи расходов и их маппинг на категории
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем все уникальные статьи из транзакций
            query = """
                SELECT DISTINCT tags[1] as article, 
                       category,
                       COUNT(*) as transaction_count,
                       SUM(amount) as total_amount
                FROM financial_transactions
                WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
                AND type = 'expense'
                GROUP BY tags[1], category
                ORDER BY tags[1]
            """
            rows = await conn.fetch(query)
            
            articles = []
            for row in rows:
                article = row['article']
                if not article or article == '----------':
                    continue
                    
                articles.append({
                    "article": article,
                    "category": row['category'],
                    "mapped_category": ARTICLE_MAPPING.get(article, "Прочие расходы"),
                    "transaction_count": row['transaction_count'],
                    "total_amount": float(row['total_amount']),
                    "is_mapped": article in ARTICLE_MAPPING
                })
            
            return {
                "articles": articles,
                "total_articles": len(articles),
                "unmapped_count": len([a for a in articles if not a['is_mapped']])
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finances/articles/unmapped")
async def get_unmapped_articles():
    """
    Получить все статьи, которые не замаплены на категории
    """
    try:
        conn = await get_db_connection()
        try:
            query = """
                SELECT DISTINCT tags[1] as article,
                       category,
                       COUNT(*) as transaction_count,
                       SUM(amount) as total_amount,
                       array_agg(DISTINCT description) as sample_descriptions
                FROM financial_transactions
                WHERE tags IS NOT NULL 
                AND array_length(tags, 1) > 0
                AND type = 'expense'
                AND category = 'Прочие расходы'
                GROUP BY tags[1], category
                HAVING tags[1] != '----------'
                ORDER BY SUM(amount) DESC
            """
            rows = await conn.fetch(query)
            
            unmapped = []
            for row in rows:
                article = row['article']
                if article not in ARTICLE_MAPPING:
                    unmapped.append({
                        "article": article,
                        "current_category": row['category'],
                        "transaction_count": row['transaction_count'],
                        "total_amount": float(row['total_amount']),
                        "sample_descriptions": row['sample_descriptions'][:5] if row['sample_descriptions'] else []
                    })
            
            return {
                "unmapped_articles": unmapped,
                "total_unmapped": len(unmapped)
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching unmapped articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finances/articles/update-mapping")
async def update_article_mapping(request: UpdateArticlesRequest):
    """
    Обновить маппинг статей на категории и пересчитать категории в транзакциях
    """
    try:
        conn = await get_db_connection()
        try:
            updated_count = 0
            
            # Создаем маппинг из запроса
            new_mapping = {m.article: m.category for m in request.mappings}
            
            # Обновляем категории для каждой статьи
            for article, category in new_mapping.items():
                result = await conn.execute("""
                    UPDATE financial_transactions
                    SET category = $1
                    WHERE tags @> ARRAY[$2]
                    AND type = 'expense'
                """, category, article)
                
                # Извлекаем количество обновленных строк
                count = int(result.split()[-1])
                updated_count += count
                
                logger.info(f"Обновлено {count} транзакций для статьи {article} -> {category}")
            
            return {
                "success": True,
                "updated_transactions": updated_count,
                "updated_articles": len(new_mapping)
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error updating article mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finances/articles/recategorize")
async def recategorize_all():
    """
    Пересчитать категории для всех транзакций на основе текущего маппинга
    """
    try:
        conn = await get_db_connection()
        try:
            updated_count = 0
            
            for article, category in ARTICLE_MAPPING.items():
                result = await conn.execute("""
                    UPDATE financial_transactions
                    SET category = $1
                    WHERE tags @> ARRAY[$2]
                    AND type = 'expense'
                """, category, article)
                
                count = int(result.split()[-1])
                updated_count += count
            
            return {
                "success": True,
                "updated_transactions": updated_count,
                "message": "Категории успешно пересчитаны"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error recategorizing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
