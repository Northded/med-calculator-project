from typing import Tuple


def calculate_imt(weight: float, height: float) -> Tuple[float, str]:
    """
    Рассчитать Индекс Массы Тела (ИМТ)

    Args:
        weight: Вес в килограммах
        height: Рост в сантиметрах

    Returns:
        Tuple[float, str]: (ИМТ, интерпретация)

    Формула: ИМТ = вес(кг) / (рост(м))²
    """
    if weight <= 0 or height <= 0:
        raise ValueError("Вес и рост должны быть положительными числами")

    height_m = height / 100 
    imt = weight / (height_m ** 2)

    if imt < 16:
        interpretation = "Выраженный дефицит массы тела"
    elif imt < 18.5:
        interpretation = "Недостаточная масса тела"
    elif imt < 25:
        interpretation = "Нормальная масса тела"
    elif imt < 30:
        interpretation = "Избыточная масса тела (предожирение)"
    elif imt < 35:
        interpretation = "Ожирение I степени"
    elif imt < 40:
        interpretation = "Ожирение II степени"
    else:
        interpretation = "Ожирение III степени (морбидное)"

    return round(imt, 1), interpretation


def calculate_bmr(age: int, weight: float, height: float, gender: str) -> float:
    """
    Рассчитать Базовый Метаболизм (БМО/BMR) по формуле Харриса-Бенедикта

    Args:
        age: Возраст в годах
        weight: Вес в килограммах
        height: Рост в сантиметрах
        gender: Пол ('м' или 'ж')

    Returns:
        float: БМО в ккал/день

    Формула Харриса-Бенедиктая:
    - Мужчины: BMR = 88.362 + (13.397 × вес) + (4.799 × рост) - (5.677 × возраст)
    - Женщины: BMR = 447.593 + (9.247 × вес) + (3.098 × рост) - (4.330 × возраст)
    """
    if age <= 0 or weight <= 0 or height <= 0:
        raise ValueError("Возраст, вес и рост должны быть положительными")

    if gender not in ['м', 'ж', 'm', 'f']:
        raise ValueError("Пол должен быть 'м' или 'ж'")

    if gender in ['м', 'm']:
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    return round(bmr, 1)


def calculate_tdee(bmr: float, activity_level: float) -> float:
    """
    Рассчитать суточные энергозатраты (TDEE)

    Args:
        bmr: Базовый метаболизм в ккал/день
        activity_level: Коэффициент активности

    Returns:
        float: TDEE в ккал/день

    Коэффициенты активности:
    - 1.2: Сидячий образ жизни (минимальная активность)
    - 1.375: Небольшая активность (легкие тренировки 1-3 дня/неделю)
    - 1.55: Средняя активность (умеренные тренировки 3-5 дней/неделю)
    - 1.725: Высокая активность (интенсивные тренировки 6-7 дней/неделю)
    - 1.9: Экстремальная активность (тяжелые тренировки 2 раза в день)
    """
    if bmr <= 0:
        raise ValueError("BMR должен быть положительным числом")

    if not 1.0 <= activity_level <= 2.5:
        raise ValueError("Коэффициент активности должен быть от 1.0 до 2.5")

    tdee = bmr * activity_level
    return round(tdee, 1)


def calculate_calories(
    age: int, 
    weight: float, 
    height: float, 
    gender: str, 
    activity_level: float
) -> Tuple[float, float, str]:
    """
    Полный расчёт калорийности: BMR и TDEE

    Args:
        age: Возраст
        weight: Вес (кг)
        height: Рост (см)
        gender: Пол ('м' или 'ж')
        activity_level: Коэффициент активности (1.2-1.9)

    Returns:
        Tuple[float, float, str]: (BMR, TDEE, интерпретация)
    """
    bmr = calculate_bmr(age, weight, height, gender)
    tdee = calculate_tdee(bmr, activity_level)

    # Интерпретация уровня активности
    activity_descriptions = {
        1.2: "Минимальная активность (сидячий образ жизни)",
        1.375: "Небольшая активность (1-3 дня/неделю)",
        1.55: "Средняя активность (3-5 дней/неделю)",
        1.725: "Высокая активность (6-7 дней/неделю)",
        1.9: "Экстремальная активность (2 раза/день)"
    }

    interpretation = activity_descriptions.get(
        activity_level, 
        f"Уровень активности: {activity_level}"
    )

    return bmr, tdee, interpretation


def calculate_blood_pressure_category(
    systolic: int, 
    diastolic: int
) -> Tuple[str, str]:
    """
    Классификация артериального давления

    Args:
        systolic: Систолическое (верхнее) давление в мм рт.ст.
        diastolic: Диастолическое (нижнее) давление в мм рт.ст.

    Returns:
        Tuple[str, str]: (категория, рекомендация)

    Классификация ACC/AHA 2017:
    - Нормальное: < 120 и < 80
    - Повышенное: 120-129 и < 80
    - Гипертензия I: 130-139 или 80-89
    - Гипертензия II: ≥ 140 или ≥ 90
    - Гипертонический криз: > 180 или > 120
    """
    if systolic <= 0 or diastolic <= 0:
        raise ValueError("Давление должно быть положительным")
    if systolic < diastolic:
        raise ValueError("Систолическое давление не может быть меньше диастолического")
    if systolic > 180 or diastolic > 120:
        category = "Гипертонический криз"
        recommendation = "⚠️ СРОЧНО обратитесь к врачу! Немедленно вызовите скорую помощь."
    elif systolic >= 140 or diastolic >= 90:
        category = "Гипертензия II степени"
        recommendation = "Требуется консультация врача и медикаментозное лечение."
    elif systolic >= 130 or diastolic >= 80:
        category = "Гипертензия I степени"
        recommendation = "Рекомендуется консультация врача, изменение образа жизни."
    elif systolic >= 120 and diastolic < 80:
        category = "Повышенное АД"
        recommendation = "Следите за давлением, ведите здоровый образ жизни."
    else:
        category = "Нормальное АД"
        recommendation = "Ваше давление в норме. Продолжайте здоровый образ жизни."

    return category, recommendation


def calculate_ideal_weight(height: float, gender: str) -> Tuple[float, float]:
    """
    Рассчитать идеальный вес по формуле Devine (1974)

    Args:
        height: Рост в сантиметрах
        gender: Пол ('м' или 'ж')

    Returns:
        Tuple[float, float]: (идеальный вес, допустимый диапазон +/-)

    Формула Devine:
    - Мужчины: 50 кг + 2.3 кг × (рост в дюймах - 60)
    - Женщины: 45.5 кг + 2.3 кг × (рост в дюймах - 60)
    """
    if height <= 0:
        raise ValueError("Рост должен быть положительным")

    if gender not in ['м', 'ж', 'm', 'f']:
        raise ValueError("Пол должен быть 'м' или 'ж'")

    # Конвертируем см в дюймы
    height_inches = height / 2.54

    if gender in ['м', 'm']:
        ideal_weight = 50 + 2.3 * (height_inches - 60)
    else:
        ideal_weight = 45.5 + 2.3 * (height_inches - 60)

    # Допустимый диапазон ±10%
    range_margin = ideal_weight * 0.1

    return round(ideal_weight, 1), round(range_margin, 1)


def calculate_water_intake(weight: float, activity_level: str = "moderate") -> float:
    """
    Рассчитать рекомендуемое потребление воды в день

    Args:
        weight: Вес в килограммах
        activity_level: Уровень активности ("low", "moderate", "high")

    Returns:
        float: Рекомендуемое количество воды в литрах

    Формула: 
    - Базовая: 30-35 мл на кг веса
    - С учётом активности: +500-1000 мл
    """
    if weight <= 0:
        raise ValueError("Вес должен быть положительным")

    base_water = weight * 0.035

    activity_multipliers = {
        "low": 0,
        "moderate": 0.5,
        "high": 1.0
    }

    additional_water = activity_multipliers.get(activity_level, 0.5)
    total_water = base_water + additional_water

    return round(total_water, 1)