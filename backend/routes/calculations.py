"""Маршруты для медицинских расчётов."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
import logging
import time
from uuid import uuid4

from backend.database.db import get_session
from backend.database.repository import CalculatorRepository
from backend.database.schemas import (
    IMTInput,
    CaloriesInput,
    BloodPressureInput,
    CalculationResponse,
)
from backend.utils.calculators import (
    calculate_imt,
    calculate_calories,
    calculate_blood_pressure_category,
)

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
    session: AsyncSession = Depends(get_session),
):
    """Расчёт ИМТ + автоматическое создание пользователя + сохранение в БД."""
    user_id = data.user_id
    logger.info(f"IMT calc request for user_id: {user_id}")
    
    try:
        repo = CalculatorRepository(session)
        await repo.get_or_create_user(user_id=user_id)
        
        result, interpretation = calculate_imt(data.weight, data.height)
        
        from backend.database.schemas import CalculationCreate
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
    description="Расчёт по формуле Харриса-Бенедикта (1984)",
)
async def calculate_calories_endpoint(
    data: CaloriesInput,
    session: AsyncSession = Depends(get_session),
):
    """Расчёт калорий + автоматическое создание пользователя + сохранение в БД."""
    user_id = data.user_id
    logger.info(f"Calories calc request for user_id: {user_id}")
    
    try:
        repo = CalculatorRepository(session)
        await repo.get_or_create_user(user_id=user_id)
        
        bmr, tdee, activity_desc = calculate_calories(
            weight=data.weight,
            height=data.height,
            age=data.age,
            gender=data.gender,
            activity=data.activity,
        )
        
        from backend.database.schemas import CalculationCreate
        calc = CalculationCreate(
            user_id=user_id,
            calc_type="calories",
            input_data=json.dumps({
                "weight": data.weight,
                "height": data.height,
                "age": data.age,
                "gender": data.gender,
                "activity": data.activity,
            }),
            result=tdee,
            interpretation=f"БМР: {bmr:.0f} ккал, ТДЕЕ: {tdee:.0f} ккал ({activity_desc})",
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
        logger.error(f"Calories validation error for {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calories error for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при расчёте калорий: {str(e)}")


@router.post(
    "/calculations/blood-pressure",
    response_model=CalculationResponse,
    summary="Оценка артериального давления",
    description="Классификация по стандарту ACC/AHA 2017",
)
async def calculate_blood_pressure_endpoint(
    data: BloodPressureInput,
    session: AsyncSession = Depends(get_session),
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
    user_id: str = Query(..., description="Уникальный ID пользователя"),
    limit: int = Query(10, ge=1, le=100, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    calc_type: Optional[str] = Query(None, description="Тип расчёта (imt, calories, blood_pressure)"),
    session: AsyncSession = Depends(get_session),
):
    """Получить историю расчётов по user_id."""
    logger.info(f"History request for user_id: {user_id}")
    try:
        repo = CalculatorRepository(session)
        
        calculations = await repo.get_user_calculations(
            user_id=user_id,
            calc_type=calc_type,
            limit=limit,
            offset=offset,
        )
        
        return {
            "user_id": user_id,
            "total": len(calculations),
            "limit": limit,
            "offset": offset,
            "calculations": [
                {
                    "id": c.id,
                    "type": c.calc_type,
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
        raise HTTPException(status_code=500, detail=f"Ошибка при получении истории: {str(e)}")


@router.get(
    "/calculations/stats",
    summary="Статистика показателей",
    description="Общая статистика показателей здоровья пользователя",
)
async def get_stats(
    user_id: str = Query(..., description="Уникальный ID пользователя"),
    session: AsyncSession = Depends(get_session),
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
    calculation_id: int,
    user_id: str = Query(..., description="ID пользователя для проверки доступа"),
    session: AsyncSession = Depends(get_session),
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
