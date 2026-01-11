import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class CaloriesBurnedClient:
    """Клиент для работы с Calories Burned API."""
    
    def __init__(self, api_key: str):
        """
        Инициализация клиента.
        
        Args:
            api_key: API ключ от API Ninjas
        """
        self.api_key = api_key
        self.base_url = "https://api.api-ninjas.com/v1"
        self.headers = {"X-Api-Key": api_key}
    
    async def calculate_calories_burned(
        self,
        activity: str,
        weight: Optional[float] = None,
        duration: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать калории, сожжённые при активности.
        
        Args:
            activity: Название активности (running, swimming, yoga)
            weight: Вес в кг (опционально)
            duration: Длительность в минутах (опционально)
            
        Returns:
            list: Данные о сожжённых калориях
        """
        try:
            params = {"activity": activity}
            
            if weight:
                # апи берет вес в фунтах
                weight_lbs = weight * 2.20462
                params["weight"] = int(weight_lbs)
            
            if duration:
                params["duration"] = duration
            
            logger.info(f"Requesting API Ninjas: activity={activity}, weight={weight}, duration={duration}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/caloriesburned",
                    params=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API Ninjas success: {len(data)} activities found")
                    return data
                else:
                    logger.error(f"API Ninjas error: {response.status_code} - {response.text}")
                    return []
                    
        except httpx.TimeoutException:
            logger.error("API Ninjas timeout")
            return []
        except Exception as e:
            logger.error(f"API Ninjas error: {str(e)}")
            return []
    
    async def get_activities_list(self) -> List[str]:
        """
        Получить список поддерживаемых активностей.
        
        Returns:
            list: Список доступных активностей
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/caloriesburnedactivities",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Activities list error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Activities list error: {str(e)}")
            return []
    
    def generate_exercise_recommendations(
        self,
        target_calories: float,
        weight: float,
        fitness_level: str = "intermediate"
    ) -> str:
        """
        Сгенерировать рекомендации по упражнениям для сжигания калорий.
        
        Args:
            target_calories: Целевое количество калорий для сжигания
            weight: Вес пользователя в кг
            fitness_level: Уровень подготовки (beginner, intermediate, advanced)
            
        Returns:
            str: Текст рекомендаций
        """
        # значения калорий/час для человека весом 70кг
        weight_factor = weight / 70.0
        
        activities = {
            "beginner": [
                {"name": "Ходьба (5 км/ч)", "cal_per_hour": 240 * weight_factor, "intensity": "низкая"},
                {"name": "Плавание (спокойно)", "cal_per_hour": 360 * weight_factor, "intensity": "низкая"},
                {"name": "Йога", "cal_per_hour": 180 * weight_factor, "intensity": "низкая"},
                {"name": "Велосипед (15 км/ч)", "cal_per_hour": 360 * weight_factor, "intensity": "средняя"},
            ],
            "intermediate": [
                {"name": "Бег трусцой (8 км/ч)", "cal_per_hour": 480 * weight_factor, "intensity": "средняя"},
                {"name": "Аэробика", "cal_per_hour": 420 * weight_factor, "intensity": "средняя"},
                {"name": "Велосипед (20 км/ч)", "cal_per_hour": 540 * weight_factor, "intensity": "средняя"},
                {"name": "Танцы", "cal_per_hour": 330 * weight_factor, "intensity": "средняя"},
            ],
            "advanced": [
                {"name": "Бег (12 км/ч)", "cal_per_hour": 720 * weight_factor, "intensity": "высокая"},
                {"name": "HIIT тренировка", "cal_per_hour": 660 * weight_factor, "intensity": "высокая"},
                {"name": "Плавание (быстро)", "cal_per_hour": 600 * weight_factor, "intensity": "высокая"},
                {"name": "Прыжки на скакалке", "cal_per_hour": 750 * weight_factor, "intensity": "высокая"},
            ]
        }
        
        level_activities = activities.get(fitness_level, activities["beginner"])
        
        recommendations = []
        recommendations.append(f"Для сжигания {target_calories:.0f} ккал (вес {weight:.0f} кг):\n")
        
        for activity in level_activities:
            minutes_needed = (target_calories / activity["cal_per_hour"]) * 60
            
            if minutes_needed < 120: 
                recommendations.append(
                    f"• {activity['name']}: {minutes_needed:.0f} минут "
                    f"({activity['cal_per_hour']:.0f} ккал/час, интенсивность: {activity['intensity']})"
                )
        
        recommendations.append(f"\nСовет: Комбинируйте разные виды активности для лучшего результата!")
        
        return "\n".join(recommendations)
    
    def calculate_deficit_recommendation(
        self,
        tdee: float,
        target_weight_loss: float = 0.5
    ) -> Dict[str, Any]:
        """
        Рассчитать рекомендуемый дефицит калорий для похудения.
        
        Args:
            tdee: Суточная калорийность
            target_weight_loss: Целевое снижение веса в кг/неделю (по умолчанию 0.5)
            
        Returns:
            dict: Рекомендации по дефициту калорий
        """
        # 1 кг жира = 7700 ккал
        weekly_deficit_needed = target_weight_loss * 7700
        daily_deficit = weekly_deficit_needed / 7
        
        # безопасный диапазон дефицита: 15-25% от TDEE
        max_safe_deficit = tdee * 0.25
        min_deficit = tdee * 0.15
        
        if daily_deficit > max_safe_deficit:
            recommended_deficit = max_safe_deficit
            achievable_loss = (recommended_deficit * 7) / 7700
            warning = "⚠️ Желаемый темп слишком быстрый. Рекомендуем более медленное снижение веса."
        elif daily_deficit < min_deficit:
            recommended_deficit = min_deficit
            achievable_loss = (recommended_deficit * 7) / 7700
            warning = None
        else:
            recommended_deficit = daily_deficit
            achievable_loss = target_weight_loss
            warning = None
        
        target_calories = tdee - recommended_deficit
        
        # не опускаться ниже базового метаболизма (примерно 60% от TDEE)
        min_calories = tdee * 0.60
        if target_calories < min_calories:
            target_calories = min_calories
            achievable_loss = ((tdee - target_calories) * 7) / 7700
            warning = "⚠️ Достигнут минимально безопасный уровень калорийности."
        
        return {
            "tdee": tdee,
            "target_calories": target_calories,
            "daily_deficit": recommended_deficit,
            "weekly_deficit": recommended_deficit * 7,
            "achievable_weight_loss_per_week": achievable_loss,
            "warning": warning,
            "exercise_burn_target": recommended_deficit * 0.4,  
            "diet_reduction_target": recommended_deficit * 0.6,
        }


async def get_calories_burned(
    activity: str,
    weight: float,
    duration: int,
    api_key: str
) -> List[Dict[str, Any]]:
    """
    Получить данные о сожжённых калориях.
    
    Args:
        activity: Название активности
        weight: Вес в кг
        duration: Длительность в минутах
        api_key: API ключ
        
    Returns:
        list: Данные о калориях
    """
    client = CaloriesBurnedClient(api_key)
    return await client.calculate_calories_burned(activity, weight, duration)


async def get_supported_activities(api_key: str) -> List[str]:
    """
    Получить список доступных активностей.
    
    Args:
        api_key: API ключ
        
    Returns:
        list: Список активностей
    """
    client = CaloriesBurnedClient(api_key)
    return await client.get_activities_list()


def get_weight_loss_plan(
    tdee: float,
    target_kg_per_week: float,
    weight: float,
    api_key: str
) -> str:
    """
    Сформировать план снижения веса.
    
    Args:
        tdee: Суточная калорийность
        target_kg_per_week: Целевое снижение в кг/неделю
        weight: Вес пользователя в кг
        api_key: API ключ
        
    Returns:
        str: Текст плана
    """
    client = CaloriesBurnedClient(api_key)
    
    # рассчет дефицита
    plan = client.calculate_deficit_recommendation(tdee, target_kg_per_week)
    
    # рекомендации по упражнениям
    exercise_target = plan["exercise_burn_target"]
    exercises = client.generate_exercise_recommendations(exercise_target, weight, "intermediate")
    
    # итоговый текст
    result = []
    result.append(f"План снижения веса:\n")
    result.append(f"• Ваша ТДЕЕ: {plan['tdee']:.0f} ккал/день")
    result.append(f"• Целевая калорийность: {plan['target_calories']:.0f} ккал/день")
    result.append(f"• Дефицит: {plan['daily_deficit']:.0f} ккал/день ({plan['weekly_deficit']:.0f} ккал/неделю)")
    result.append(f"• Прогнозируемое снижение веса: {plan['achievable_weight_loss_per_week']:.1f} кг/неделю")
    
    if plan["warning"]:
        result.append(f"\n{plan['warning']}")
    
    result.append(f"\nКак создать дефицит:")
    result.append(f"• Снижение калорийности питания: {plan['diet_reduction_target']:.0f} ккал (60%)")
    result.append(f"• Физическая активность: {plan['exercise_burn_target']:.0f} ккал (40%)")
    
    result.append(f"\n{exercises}")
    
    return "\n".join(result)
