from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Annotated

# USER SCHEMAS
class UserBase(BaseModel):
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CALCULATION SCHEMAS
class CalculationBase(BaseModel):
    user_id: str
    calc_type: str
    input_data: str
    result: float
    interpretation: Optional[str] = None

class CalculationCreate(CalculationBase):
    pass

class CalculationResponse(CalculationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# MEDICAL CALCULATION INPUTS 
class IMTInput(BaseModel):
    user_id: str = Field(..., description="ID пользователя из localStorage")
    weight: Annotated[float, Field(gt=0, description="Вес в кг")]
    height: Annotated[float, Field(gt=0, description="Рост в см")]

class CaloriesInput(BaseModel):
    user_id: str = Field(..., description="ID пользователя из localStorage")
    age: Annotated[int, Field(gt=0, le=150)]
    weight: Annotated[float, Field(gt=0)]
    height: Annotated[float, Field(gt=0)]
    gender: Annotated[str, Field(pattern="^(м|ж)$")]
    activity_level: Annotated[float, Field(default=1.5, ge=1.2, le=1.9)]

class BloodPressureInput(BaseModel):
    user_id: str = Field(..., description="ID пользователя из localStorage")
    systolic: Annotated[int, Field(ge=50, le=250)]
    diastolic: Annotated[int, Field(ge=30, le=150)]

# HEALTH METRICS
class HealthMetricBase(BaseModel):
    metric_type: str
    value: float
    unit: str
    notes: Optional[str] = None

class HealthMetricCreate(HealthMetricBase):
    user_id: str

class HealthMetricResponse(HealthMetricCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
