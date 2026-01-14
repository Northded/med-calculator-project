from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import json
import logging

from backend.integrations.calories_burned import get_weight_loss_plan, CaloriesBurnedClient
from backend.config import settings
from backend.database.repository import CalculatorRepository
from backend.database.schemas import (
    IMTInput,
    CaloriesInput,
    BloodPressureInput,
    CalculationResponse,
    CalculationCreate
)
from backend.utils.calculators import (
    calculate_imt,
    calculate_calories,
    calculate_blood_pressure_category,
)
from ..deps import SessionDep


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/calculations/imt",
    response_model=CalculationResponse,
    summary="Расчёт ИМТ",
    description="Расчёт Индекса Массы Тела с классификацией по ВОЗ",
)
async def calculate_imt_endpoint(
    data: IMTInput,
    session: SessionDep,
):
    """Расчёт ИМТ + автоматическое создание пользователя + сохранение в БД."""
    user_id = data.user_id
    logger.info(f"IMT calc request for user_id: {user_id}")
    
    try:
        repo = CalculatorRepository(session)
        await repo.get_or_create_user(user_id=user_id)
        
        result, interpretation = calculate_imt(data.weight, data.height)
        
        calc = CalculationCreate(
            user_id=user_id,
            calc_type="imt",
            input_data=json.dumps({"weight": data.weight, "height": data.height}),
            result=result,
            interpretation=interpretation,
        )
        
        calculation = await repo.create_calculation(calc)
        
        return CalculationResponse(
            id=calculation.id,
            user_id=calculation.user_id,
            calc_type=calculation.calc_type,
            input_data=calculation.input_data,
            result=calculation.result,
            interpretation=calculation.interpretation,
            created_at=calculation.created_at,
        )
        
    except ValueError as e:
        logger.error(f"IMT validation error for {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"IMT error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при расчёте ИМТ: {str(e)}")


@router.post(
    "/calculations/calories",
    response_model=CalculationResponse,
    summary="Расчёт суточной калорийности",
    description="Расчёт по формуле Харриса-Бенедикта с рекомендациями по упражнениям от API Ninjas",
)
async def calculate_calories_endpoint(
    data: CaloriesInput,
    session: SessionDep,
):
    """Расчёт калорий с РЕАЛЬНЫМИ рекомендациями по упражнениям от API Ninjas."""
    user_id = data.user_id
    logger.info(f"Calories calculation request for user_id: {user_id}")

    try:
        repo = CalculatorRepository(session)
        await repo.get_or_create_user(user_id=user_id)

        # расчёт BMR и TDEE
        bmr, tdee, activity_desc = calculate_calories(
            weight=data.weight,
            height=data.height,
            age=data.age,
            gender=data.gender,
            activity_level=data.activity_level,
        )

        interpretation = f"""Результаты расчёта метаболизма:

• Базовый метаболизм (БМР): {bmr:.0f} ккал/день
  (это калории, необходимые организму в покое)

• Суточная калорийность (ТДЕЕ): {tdee:.0f} ккал/день
  (с учётом вашей активности: {activity_desc})"""

        # рекомендации от апи
        if settings.API_NINJAS_ENABLED and settings.API_NINJAS_KEY:
            try:
                # рассчет ИМТ для определения стратегии
                imt, _ = calculate_imt(data.weight, data.height)

                if imt >= 25:  # избыточный вес - план похудения
                    logger.info(f"BMI {imt:.1f} >= 25, generating weight loss plan with API")
                    weight_loss_plan = get_weight_loss_plan(
                        tdee=tdee,
                        target_kg_per_week=0.5,
                        weight=data.weight,
                        api_key=settings.API_NINJAS_KEY
                    )
                    interpretation += f"\n\n{weight_loss_plan}"
                    logger.info(f"Weight loss plan with API data added for {user_id}")

                else:  # нормальный/недостаточный вес - поддержание здоровья
                    logger.info(f"BMI {imt:.1f} < 25, fetching real exercises from API Ninjas")
                    
                    client = CaloriesBurnedClient(settings.API_NINJAS_KEY)
                    
                    # вызываем апи
                    activities_to_try = ["running", "cycling", "swimming", "yoga"]
                    api_results = []
                    
                    for activity in activities_to_try:
                        try:
                            result = await client.calculate_calories_burned(
                                activity=activity,
                                weight=data.weight,
                                duration=30 
                            )
                            if result and len(result) > 0:
                                api_results.append(result[0])  # 1 резщультат
                                if len(api_results) >= 4:  # 4 активности макс
                                    break
                        except Exception as ex:
                            logger.warning(f"Failed to fetch {activity} from API: {ex}")
                            continue
                    
                    if api_results:
                        # форматирование данных апи
                        exercises_text = "💪 Рекомендации по физической активности (от API Ninjas):\n\n"
                        exercises_text += f"🔥 Примеры 30-минутных тренировок для вашего веса ({data.weight:.0f} кг):\n\n"
                        
                        for ex in api_results:
                            exercises_text += (
                                f"• {ex['name']}\n"
                                f"  Сожжёте: ~{ex['total_calories']:.0f} ккал за 30 минут\n"
                                f"  ({ex['calories_per_hour']:.0f} ккал/час)\n\n"
                            )
                        
                        exercises_text += "💡 Совет: Комбинируйте разные виды активности для лучшего результата!"
                        interpretation += f"\n\n{exercises_text}"
                        logger.info(f"Real API Ninjas data added for {user_id} ({len(api_results)} activities)")
                    
                    else:
                        # лок генерацию, если апи не сработал
                        logger.warning(f"API returned no data, using local recommendations")
                        exercises = client.generate_exercise_recommendations(
                            target_calories=300,
                            weight=data.weight,
                            fitness_level="intermediate"
                        )
                        interpretation += f"\n\n💪 Рекомендации по физической активности:\n{exercises}"

            except Exception as e:
                logger.warning(f"Failed to get API Ninjas recommendations: {str(e)}")

        calc = CalculationCreate(
            user_id=user_id,
            calc_type="calories",
            input_data=json.dumps({
                "weight": data.weight,
                "height": data.height,
                "age": data.age,
                "gender": data.gender,
                "activity_level": data.activity_level,
            }),
            result=tdee,
            interpretation=interpretation,
        )

        calculation = await repo.create_calculation(calc)
        logger.info(f"Создан расчёт calories для пользователя {user_id}")

        return CalculationResponse(
            id=calculation.id,
            user_id=calculation.user_id,
            calc_type=calculation.calc_type,
            input_data=calculation.input_data,
            result=calculation.result,
            interpretation=calculation.interpretation,
            created_at=calculation.created_at,
        )

    except ValueError as e:
        logger.error(f"Validation error for {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calories calculation error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении расчёта")


@router.post(
    "/calculations/blood-pressure",
    response_model=CalculationResponse,
    summary="Оценка артериального давления",
    description="Классификация по стандарту ACC/AHA 2017",
)
async def calculate_blood_pressure_endpoint(
    data: BloodPressureInput,
    session: SessionDep,
):
    """Анализ давления + автоматическое создание пользователя + сохранение в БД."""
    user_id = data.user_id
    logger.info(f"Blood pressure calc request for user_id: {user_id}")
    
    try:
        repo = CalculatorRepository(session)
        await repo.get_or_create_user(user_id=user_id)
        
        category, interpretation = calculate_blood_pressure_category(
            systolic=data.systolic,
            diastolic=data.diastolic,
        )
        
        from backend.database.schemas import CalculationCreate
        calc = CalculationCreate(
            user_id=user_id,
            calc_type="blood_pressure",
            input_data=json.dumps({
                "systolic": data.systolic,
                "diastolic": data.diastolic,
            }),
            result=float(data.systolic), 
            interpretation=f"{category}: {interpretation}",
        )
        
        calculation = await repo.create_calculation(calc)

        return CalculationResponse(
            id=calculation.id,
            user_id=calculation.user_id,
            calc_type=calculation.calc_type,
            input_data=calculation.input_data,
            result=calculation.result,
            interpretation=calculation.interpretation,
            created_at=calculation.created_at,
        )
        
    except ValueError as e:
        logger.error(f"Blood pressure validation error for {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Blood pressure error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе давления: {str(e)}")


@router.get(
    "/calculations/history",
    summary="История расчётов",
    description="Получить историю всех расчётов пользователя",
)
async def get_history(
    session: SessionDep,
    user_id: str = Query(description="ID пользователя"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    calc_type: Optional[str] = Query(None),
):
    logger.info(f"History request for {user_id}")
    try:
        repo = CalculatorRepository(session)
        all_calculations = await repo.get_user_calculations(
            user_id=user_id,
            calc_type=calc_type,
            limit=9999,  
            offset=0,
        )
        calculations = await repo.get_user_calculations(
            user_id=user_id,
            calc_type=calc_type,
            limit=limit,
            offset=offset,
        )
        
        return {
            "user_id": user_id,
            "total": len(all_calculations),  
            "limit": limit,
            "offset": offset,
            "calculations": [
                {
                    "id": c.id,
                    "calc_type": c.calc_type, 
                    "input_data": c.input_data,
                    "result": c.result,
                    "interpretation": c.interpretation,
                    "created_at": c.created_at,
                }
                for c in calculations
            ],
        }
    except Exception as e:
        logger.error(f"History error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки истории: {str(e)}")


@router.get(
    "/calculations/stats",
    summary="Статистика показателей",
    description="Общая статистика показателей здоровья пользователя",
)
async def get_stats(
    session: SessionDep,
    user_id: str = Query(description="Уникальный ID пользователя"),
):
    """Получить статистику расчётов по user_id."""
    logger.info(f"Stats request for user_id: {user_id}")
    try:
        repo = CalculatorRepository(session)
        stats = await repo.get_calculation_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats,
        }
        
    except Exception as e:
        logger.error(f"Stats error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")


@router.delete(
    "/calculations/{calculation_id}",
    summary="Удалить расчёт",
    description="Удаление конкретного расчёта из истории",
)
async def delete_calculation(
    session: SessionDep,
    calculation_id: int,
    user_id: str = Query(description="ID пользователя для проверки доступа"),
):
    """Удалить расчёт по ID с проверкой владельца."""
    logger.info(f"Delete request for calculation_id: {calculation_id}, user_id: {user_id}")
    try:
        repo = CalculatorRepository(session)
        

        calculation = await repo.get_calculation(calculation_id)
        
        if not calculation:
            raise HTTPException(status_code=404, detail="Расчёт не найден")
        
        if calculation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому расчёту")
        
        await repo.delete_calculation(calculation_id)
        
        return {
            "message": "Расчёт успешно удалён",
            "calculation_id": calculation_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error for {calculation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")
