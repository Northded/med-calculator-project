from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database.db import get_session
from backend.database.repository import CalculatorRepository
from backend.database.schemas import (     
    IMTInput,
    CaloriesInput,
    BloodPressureInput,
    CalculationResponse
)
from backend.utils.calculators import (
    calculate_imt,
    calculate_calories,
    calculate_blood_pressure_category
)

router = APIRouter()


@router.post(
    "/calculations/imt",
    response_model=CalculationResponse,
    summary="Расчёт ИМТ",
    description="Расчёт Индекса Массы Тела с классификацией по ВОЗ"
)
async def calculate_imt_endpoint(
    data: IMTInput,
    user_id: str = Query(..., description="ID пользователя из localStorage"),
    session: AsyncSession = Depends(get_session)
):
    try:
        result = calculate_imt(data.weight, data.height)
        repo = CalculatorRepository(session)
        calculation = await repo.create_calculation(
            user_id=user_id,
            calculation_type="imt",
            input_data={
                "weight": data.weight,
                "height": data.height
            },
            result=result
        )

        return CalculationResponse(
            id=calculation.id,
            calculation_type="imt",
            result=result,
            created_at=calculation.created_at,
            message="ИМТ рассчитан успешно"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при расчёте: {str(e)}")


@router.post(
    "/calculations/calories",
    response_model=CalculationResponse,
    summary="Расчёт суточной калорийности",
    description="Расчёт по формуле Харриса-Бенедикта (1984)"
)
async def calculate_calories_endpoint(
    data: CaloriesInput,
    user_id: str = Query(..., description="ID пользователя"),
    session: AsyncSession = Depends(get_session)
):
    try:
        result = calculate_calories(
            weight=data.weight,
            height=data.height,
            age=data.age,
            gender=data.gender,
            activity_level=data.activity_level
        )
        repo = CalculatorRepository(session)
        calculation = await repo.create_calculation(
            user_id=user_id,
            calculation_type="calories",
            input_data={
                "weight": data.weight,
                "height": data.height,
                "age": data.age,
                "gender": data.gender,
                "activity_level": data.activity_level
            },
            result=result
        )

        return CalculationResponse(
            id=calculation.id,
            calculation_type="calories",
            result=result,
            created_at=calculation.created_at,
            message="Калорийность рассчитана успешно"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при расчёте: {str(e)}")


@router.post(
    "/calculations/blood-pressure",
    response_model=CalculationResponse,
    summary="Оценка артериального давления",
    description="Классификация по стандарту ACC/AHA 2017"
)
async def calculate_blood_pressure_endpoint(
    data: BloodPressureInput,
    user_id: str = Query(..., description="ID пользователя"),
    session: AsyncSession = Depends(get_session)
):
    try:
        result = calculate_blood_pressure_category(
            systolic=data.systolic,
            diastolic=data.diastolic
        )
        repo = CalculatorRepository(session)
        calculation = await repo.create_calculation(
            user_id=user_id,
            calculation_type="blood_pressure",
            input_data={
                "systolic": data.systolic,
                "diastolic": data.diastolic
            },
            result=result
        )

        return CalculationResponse(
            id=calculation.id,
            calculation_type="blood_pressure",
            result=result,
            created_at=calculation.created_at,
            message="Давление оценено успешно"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при расчёте: {str(e)}")


@router.get(
    "/calculations/history",
    summary="История расчётов",
    description="Получить историю всех расчётов пользователя"
)
async def get_history(
    user_id: str = Query(..., description="ID пользователя"),
    limit: int = Query(10, ge=1, le=100, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    calculation_type: Optional[str] = Query(None, description="Тип расчёта (imt, calories, blood_pressure)"),
    session: AsyncSession = Depends(get_session)
):
    try:
        repo = CalculatorRepository(session)
        calculations = await repo.get_user_calculations(
            user_id=user_id,
            calculation_type=calculation_type,
            limit=limit,
            offset=offset
        )

        total = await repo.count_user_calculations(
            user_id=user_id,
            calculation_type=calculation_type
        )

        return {
            "calculations": [...],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении истории: {str(e)}")


@router.get(
    "/calculations/stats",
    summary="Статистика показателей",
    description="Общая статистика показателей здоровья пользователя"
)
async def get_stats(
    user_id: str = Query(..., description="ID пользователя"),
    session: AsyncSession = Depends(get_session)
):
    try:
        repo = CalculatorRepository(session)

        stats = await repo.get_user_stats(user_id)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")


@router.delete(
    "/calculations/{calculation_id}",
    summary="Удалить расчёт",
    description="Удаление конкретного расчёта из истории"
)
async def delete_calculation(
    calculation_id: int,
    user_id: str = Query(..., description="ID пользователя для проверки"),
    session: AsyncSession = Depends(get_session)
):
    try:
        repo = CalculatorRepository(session)
 
        calculation = await repo.get_calculation_by_id(calculation_id)

        if not calculation:
            raise HTTPException(status_code=404, detail="Расчёт не найден")

        if calculation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому расчёту")

        await repo.delete_calculation(calculation_id)

        return {
            "message": "Расчёт успешно удалён",
            "calculation_id": calculation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")