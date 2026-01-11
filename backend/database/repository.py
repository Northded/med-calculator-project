from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from . import models, schemas
from ..deps import SessionDep
import logging

logger = logging.getLogger(__name__)

class CalculatorRepository():
    def __init__(self, session: SessionDep):
        self.session = session

    # ===== USER OPERATIONS =====      
    async def get_or_create_user(self, user_id: str):
        """Получить существующего пользователя или создать нового"""
        try:
            result = await self.session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = models.User(user_id=user_id)
                self.session.add(user)
                await self.session.commit()
                await self.session.refresh(user)
                logger.info(f"Создан новый пользователь: {user_id}")
            
            return user
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Ошибка целостности при создании пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким ID уже существует"
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при создании пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Ошибка базы данных"
            )

    async def get_user(self, user_id: str):
        """Получить пользователя по ID"""
        try:
            result = await self.session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Пользователь {user_id} не найден"
                )

            return user

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def update_user(
        self, 
        user_id: str, 
        email: str = None,
        first_name: str = None,
        last_name: str = None
    ):
        """Обновить данные пользователя"""
        try:
            result = await self.session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Пользователь {user_id} не найден"
                )

            if email is not None:
                user.email = email
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name

            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Обновлены данные пользователя: {user_id}")

            return user

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при обновлении пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def delete_user(self, user_id: str):
        """Удалить пользователя и все его расчёты"""
        try:
            result = await self.session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Пользователь {user_id} не найден"
                )

            await self.session.delete(user)
            await self.session.commit()
            logger.info(f"Удалён пользователь: {user_id}")

            return {"message": f"Пользователь {user_id} успешно удалён"}

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при удалении пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    # ===== CALCULATION OPERATIONS =====

    async def create_calculation(self, calc: schemas.CalculationCreate):
        """Создать новый расчёт"""
        try:
            db_calc = models.Calculation(
                user_id=calc.user_id,
                calc_type=calc.calc_type,
                input_data=calc.input_data,
                result=calc.result,
                interpretation=calc.interpretation
            )
            self.session.add(db_calc)
            await self.session.commit()
            await self.session.refresh(db_calc)
            logger.info(f"Создан расчёт {db_calc.calc_type} для пользователя {calc.user_id}")
            return db_calc
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при создании расчёта: {e}")
            raise HTTPException(
                status_code=500,
                detail="Ошибка при сохранении расчёта"
            )

    async def get_calculation(self, calculation_id: int):
        """Получить расчёт по ID"""
        try:
            result = await self.session.execute(
                select(models.Calculation).where(models.Calculation.id == calculation_id)
            )
            calc = result.scalar_one_or_none()

            if not calc:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Расчёт {calculation_id} не найден"
                )

            return calc

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении расчёта {calculation_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def get_user_calculations(
        self, 
        user_id: str, 
        limit: int = 100,
        offset: int = 0,
        calc_type: str = None
    ):
        """Получить расчёты пользователя с фильтрацией и пагинацией"""
        try:
            query = select(models.Calculation).where(
                models.Calculation.user_id == user_id
            )
            if calc_type:
                query = query.where(models.Calculation.calc_type == calc_type)

            query = (
                query.order_by(desc(models.Calculation.created_at))
                     .limit(limit)
                     .offset(offset)
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении расчётов пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def update_calculation(
        self, 
        calculation_id: int, 
        interpretation: str = None
    ):
        """Обновить интерпретацию расчёта"""
        try:
            result = await self.session.execute(
                select(models.Calculation).where(models.Calculation.id == calculation_id)
            )
            calc = result.scalar_one_or_none()

            if not calc:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Расчёт {calculation_id} не найден"
                )

            if interpretation is not None:
                calc.interpretation = interpretation

            await self.session.commit()
            await self.session.refresh(calc)
            logger.info(f"Обновлён расчёт {calculation_id}")

            return calc

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при обновлении расчёта {calculation_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def delete_calculation(self, calculation_id: int):
        """Удалить расчёт по ID"""
        try:
            result = await self.session.execute(
                select(models.Calculation).where(models.Calculation.id == calculation_id)
            )
            calc = result.scalar_one_or_none()

            if not calc:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Расчёт {calculation_id} не найден"
                )

            await self.session.delete(calc)
            await self.session.commit()
            logger.info(f"Удалён расчёт {calculation_id}")

            return {"message": f"Расчёт {calculation_id} успешно удалён"}

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при удалении расчёта {calculation_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def delete_user_calculations(self, user_id: str, calc_type: str = None):
        """Удалить все расчёты пользователя (или определённого типа)"""
        try:
            query = select(models.Calculation).where(
                models.Calculation.user_id == user_id
            )

            if calc_type:
                query = query.where(models.Calculation.calc_type == calc_type)

            result = await self.session.execute(query)
            calculations = result.scalars().all()

            if not calculations:
                raise HTTPException(
                    status_code=404, 
                    detail="Расчёты не найдены"
                )

            for calc in calculations:
                await self.session.delete(calc)

            await self.session.commit()
            count = len(calculations)
            logger.info(f"Удалено {count} расчётов пользователя {user_id}")

            return {"message": f"Удалено расчётов: {count}"}

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при удалении расчётов пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def get_calculation_stats(self, user_id: str):
        """Получить статистику расчётов пользователя"""
        try:
            result = await self.session.execute(
                select(models.Calculation).where(
                    models.Calculation.user_id == user_id
                )
            )
            calculations = result.scalars().all()

            if not calculations:
                return {
                    "total": 0,
                    "by_type": {},
                    "message": "Нет данных для статистики"
                }

            stats = {}
            for calc in calculations:
                if calc.calc_type not in stats:
                    stats[calc.calc_type] = {
                        "count": 0,
                        "results": [],
                        "avg": 0
                    }
                stats[calc.calc_type]["count"] += 1
                stats[calc.calc_type]["results"].append(calc.result)

            for calc_type in stats:
                results = stats[calc_type]["results"]
                stats[calc_type]["avg"] = round(sum(results) / len(results), 2)

            return {
                "total": len(calculations),
                "by_type": stats
            }

        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении статистики для {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    # ===== HEALTH METRICS OPERATIONS =====

    async def create_health_metric(self, metric: schemas.HealthMetricCreate):
        """Создать новую метрику здоровья"""
        try:
            db_metric = models.HealthMetric(**metric.model_dump())
            self.session.add(db_metric)
            await self.session.commit()
            await self.session.refresh(db_metric)
            logger.info(f"Создана метрика {db_metric.metric_type} для пользователя {metric.user_id}")

            return db_metric

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при создании метрики: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка при сохранении метрики"
            )

    async def get_user_metrics(
        self, 
        user_id: str, 
        metric_type: str = None,
        limit: int = 100
    ):
        """Получить метрики здоровья пользователя"""
        try:
            query = select(models.HealthMetric).where(
                models.HealthMetric.user_id == user_id
            )

            if metric_type:
                query = query.where(models.HealthMetric.metric_type == metric_type)

            query = query.order_by(desc(models.HealthMetric.created_at)).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении метрик пользователя {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def delete_health_metric(self, metric_id: int):
        """Удалить метрику здоровья"""
        try:
            result = await self.session.execute(
                select(models.HealthMetric).where(models.HealthMetric.id == metric_id)
            )
            metric = result.scalar_one_or_none()

            if not metric:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Метрика {metric_id} не найдена"
                )

            await self.session.delete(metric)
            await self.session.commit()
            logger.info(f"Удалена метрика {metric_id}")

            return {"message": f"Метрика {metric_id} успешно удалена"}

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка БД при удалении метрики {metric_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Ошибка базы данных"
            )

    async def check_user_exists(self, user_id: str) -> bool:
        """Проверить существует ли пользователь с таким ID"""
        try:
            result = await self.session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            return user is not None
        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при проверке пользователя {user_id}: {e}")
            return False