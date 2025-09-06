"""
Rating and Performance Service - Employee and house rating system
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from db import db_manager
from bitrix24_service import get_bitrix24_service
import uuid

logger = logging.getLogger(__name__)

class RatingService:
    """Service for rating employees and houses"""
    
    def __init__(self):
        self.db = db_manager
    
    async def rate_employee(self, employee_id: str, rating: float, category: str, 
                           comment: str = "", rated_by: str = "system") -> Dict[str, Any]:
        """Rate an employee in specific category"""
        try:
            collection = self.db.get_collection("employee_ratings")
            
            rating_data = {
                "id": str(uuid.uuid4()),
                "employee_id": employee_id,
                "rating": max(1, min(5, rating)),  # Ensure 1-5 scale
                "category": category,  # quality, punctuality, efficiency, communication
                "comment": comment,
                "rated_by": rated_by,
                "created_at": datetime.utcnow().isoformat(),
                "month": datetime.utcnow().strftime('%Y-%m')
            }
            
            await collection.insert_one(rating_data)
            
            # Update employee overall rating
            await self._update_employee_overall_rating(employee_id)
            
            return {"success": True, "rating_id": rating_data["id"]}
            
        except Exception as e:
            logger.error(f"Error rating employee: {e}")
            return {"success": False, "error": str(e)}
    
    async def rate_house(self, house_id: str, rating: float, category: str,
                        comment: str = "", rated_by: str = "system") -> Dict[str, Any]:
        """Rate a house/cleaning object"""
        try:
            collection = self.db.get_collection("house_ratings")
            
            rating_data = {
                "id": str(uuid.uuid4()),
                "house_id": house_id,
                "rating": max(1, min(5, rating)),
                "category": category,  # cleanliness, difficulty, client_satisfaction
                "comment": comment,
                "rated_by": rated_by,
                "created_at": datetime.utcnow().isoformat(),
                "month": datetime.utcnow().strftime('%Y-%m')
            }
            
            await collection.insert_one(rating_data)
            
            # Update house overall rating
            await self._update_house_overall_rating(house_id)
            
            return {"success": True, "rating_id": rating_data["id"]}
            
        except Exception as e:
            logger.error(f"Error rating house: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_employee_ratings(self, employee_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get employee ratings"""
        try:
            collection = self.db.get_collection("employee_ratings")
            
            filter_query = {}
            if employee_id:
                filter_query["employee_id"] = employee_id
            
            cursor = collection.find(filter_query).sort("created_at", -1).limit(limit)
            ratings = await cursor.to_list(length=limit)
            
            return ratings
            
        except Exception as e:
            logger.error(f"Error getting employee ratings: {e}")
            return []
    
    async def get_top_employees(self, category: str = "overall", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-rated employees"""
        try:
            collection = self.db.get_collection("employee_overall_ratings")
            
            # Get employees sorted by rating
            cursor = collection.find({}).sort(f"ratings.{category}", -1).limit(limit)
            top_employees = await cursor.to_list(length=limit)
            
            return top_employees
            
        except Exception as e:
            logger.error(f"Error getting top employees: {e}")
            return []
    
    async def get_employee_performance_report(self, employee_id: str) -> Dict[str, Any]:
        """Get comprehensive employee performance report"""
        try:
            # Get ratings
            ratings = await self.get_employee_ratings(employee_id)
            
            if not ratings:
                return {"success": False, "error": "No ratings found"}
            
            # Calculate statistics
            categories = {}
            for rating in ratings:
                cat = rating["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(rating["rating"])
            
            category_averages = {
                cat: sum(values) / len(values) 
                for cat, values in categories.items()
            }
            
            overall_average = sum(category_averages.values()) / len(category_averages)
            
            # Get recent trend (last 30 days vs previous 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            sixty_days_ago = (datetime.utcnow() - timedelta(days=60)).isoformat()
            
            recent_ratings = [r for r in ratings if r["created_at"] > thirty_days_ago]
            previous_ratings = [r for r in ratings if sixty_days_ago < r["created_at"] <= thirty_days_ago]
            
            recent_avg = sum(r["rating"] for r in recent_ratings) / max(len(recent_ratings), 1)
            previous_avg = sum(r["rating"] for r in previous_ratings) / max(len(previous_ratings), 1)
            
            trend = "improving" if recent_avg > previous_avg else "declining" if recent_avg < previous_avg else "stable"
            
            return {
                "success": True,
                "employee_id": employee_id,
                "overall_rating": round(overall_average, 2),
                "category_ratings": {k: round(v, 2) for k, v in category_averages.items()},
                "total_ratings": len(ratings),
                "trend": trend,
                "trend_change": round(recent_avg - previous_avg, 2),
                "recent_ratings_count": len(recent_ratings),
                "recommendations": self._generate_employee_recommendations(category_averages, trend)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance report: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_house_difficulty_ranking(self) -> List[Dict[str, Any]]:
        """Get houses ranked by difficulty/complexity"""
        try:
            bx24 = await get_bitrix24_service()
            houses = await bx24.get_cleaning_houses_deals()
            
            house_rankings = []
            
            for house in houses:
                house_id = house.get("ID")
                title = house.get("TITLE", "")
                
                # Calculate difficulty score based on various factors
                difficulty_score = await self._calculate_house_difficulty(house_id, title)
                
                house_rankings.append({
                    "house_id": house_id,
                    "title": title,
                    "difficulty_score": difficulty_score,
                    "difficulty_level": self._get_difficulty_level(difficulty_score),
                    "recommended_team_size": self._get_recommended_team_size(difficulty_score),
                    "estimated_time": self._get_estimated_time(difficulty_score)
                })
            
            # Sort by difficulty score (highest first)
            house_rankings.sort(key=lambda x: x["difficulty_score"], reverse=True)
            
            return house_rankings
            
        except Exception as e:
            logger.error(f"Error getting house rankings: {e}")
            return []
    
    async def _update_employee_overall_rating(self, employee_id: str):
        """Update employee's overall rating"""
        try:
            ratings = await self.get_employee_ratings(employee_id)
            
            if not ratings:
                return
            
            # Calculate averages by category
            categories = {}
            for rating in ratings:
                cat = rating["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(rating["rating"])
            
            category_averages = {
                cat: sum(values) / len(values) 
                for cat, values in categories.items()
            }
            
            overall_average = sum(category_averages.values()) / len(category_averages)
            
            # Save overall rating
            collection = self.db.get_collection("employee_overall_ratings")
            
            overall_data = {
                "employee_id": employee_id,
                "ratings": category_averages,
                "overall_rating": overall_average,
                "total_ratings": len(ratings),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await collection.replace_one(
                {"employee_id": employee_id},
                overall_data,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating overall rating: {e}")
    
    async def _update_house_overall_rating(self, house_id: str):
        """Update house's overall rating"""
        try:
            collection = self.db.get_collection("house_ratings")
            
            cursor = collection.find({"house_id": house_id})
            ratings = await cursor.to_list(length=None)
            
            if not ratings:
                return
            
            # Calculate averages by category
            categories = {}
            for rating in ratings:
                cat = rating["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(rating["rating"])
            
            category_averages = {
                cat: sum(values) / len(values) 
                for cat, values in categories.items()
            }
            
            overall_average = sum(category_averages.values()) / len(category_averages)
            
            # Save overall rating
            overall_collection = self.db.get_collection("house_overall_ratings")
            
            overall_data = {
                "house_id": house_id,
                "ratings": category_averages,
                "overall_rating": overall_average,
                "total_ratings": len(ratings),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await overall_collection.replace_one(
                {"house_id": house_id},
                overall_data,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating house overall rating: {e}")
    
    async def _calculate_house_difficulty(self, house_id: str, title: str) -> float:
        """Calculate house difficulty score"""
        base_score = 3.0  # Base difficulty
        
        # Factors that increase difficulty
        title_lower = title.lower()
        
        if "многоэтажный" in title_lower or "этаж" in title_lower:
            base_score += 1.0
        
        if "торговый" in title_lower or "офис" in title_lower:
            base_score += 0.5
        
        if "центр" in title_lower:
            base_score += 0.3
        
        # Get ratings if available
        try:
            collection = self.db.get_collection("house_ratings")
            cursor = collection.find({"house_id": house_id, "category": "difficulty"})
            difficulty_ratings = await cursor.to_list(length=None)
            
            if difficulty_ratings:
                avg_difficulty = sum(r["rating"] for r in difficulty_ratings) / len(difficulty_ratings)
                base_score = (base_score + avg_difficulty) / 2
        except:
            pass
        
        return min(5.0, max(1.0, base_score))
    
    def _get_difficulty_level(self, score: float) -> str:
        """Get difficulty level description"""
        if score >= 4.5:
            return "Very High"
        elif score >= 3.5:
            return "High"
        elif score >= 2.5:
            return "Medium"
        else:
            return "Low"
    
    def _get_recommended_team_size(self, difficulty_score: float) -> int:
        """Get recommended team size based on difficulty"""
        if difficulty_score >= 4.5:
            return 4
        elif difficulty_score >= 3.5:
            return 3
        else:
            return 2
    
    def _get_estimated_time(self, difficulty_score: float) -> float:
        """Get estimated time in hours"""
        base_time = 1.5
        return base_time * (difficulty_score / 3.0)
    
    def _generate_employee_recommendations(self, category_ratings: Dict[str, float], trend: str) -> List[str]:
        """Generate recommendations for employee improvement"""
        recommendations = []
        
        # Check each category
        for category, rating in category_ratings.items():
            if rating < 3.5:
                if category == "quality":
                    recommendations.append("Требуется дополнительное обучение по стандартам качества")
                elif category == "punctuality":
                    recommendations.append("Необходимо улучшить пунктуальность и соблюдение графика")
                elif category == "efficiency":
                    recommendations.append("Рекомендуется оптимизация рабочих процессов")
                elif category == "communication":
                    recommendations.append("Нужно развивать навыки коммуникации с клиентами")
        
        # Trend-based recommendations
        if trend == "declining":
            recommendations.append("Провести индивидуальную беседу для выявления проблем")
        elif trend == "improving":
            recommendations.append("Отметить положительную динамику и мотивировать к дальнейшему росту")
        
        return recommendations

# Global service instance
rating_service = RatingService()

# Utility functions
async def rate_employee_performance(employee_id: str, rating: float, category: str, comment: str = "") -> Dict[str, Any]:
    """Rate employee performance"""
    return await rating_service.rate_employee(employee_id, rating, category, comment)

async def get_employee_performance_report(employee_id: str) -> Dict[str, Any]:
    """Get employee performance report"""
    return await rating_service.get_employee_performance_report(employee_id)

async def get_top_performers(category: str = "overall", limit: int = 10) -> List[Dict[str, Any]]:
    """Get top performing employees"""
    return await rating_service.get_top_employees(category, limit)