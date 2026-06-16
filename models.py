from typing import List
from pydantic import BaseModel, Field, field_validator

from config import LIMITS


class Point2D(BaseModel):
    """Точка в локальной плоской системе координат (метры)."""

    x: float = Field(..., description="Координата X в метрах")
    y: float = Field(..., description="Координата Y в метрах")


class RoutePoint(BaseModel):
    """Точка маршрута с порядковым номером и высотой полёта."""

    seq: int = Field(..., description="Порядковый номер точки маршрута")
    x: float
    y: float
    altitude: float = Field(..., description="Высота полёта, м")
    action: str = Field(default="take_photo", description="Действие в точке")


class MissionRequest(BaseModel):
    """Входные параметры для генерации полётной миссии."""

    quarry_polygon: List[Point2D] = Field(
        ..., min_length=3, description="Границы карьера — минимум 3 точки"
    )
    flight_altitude: float = Field(..., description="Высота полёта (м)")
    flight_speed: float = Field(..., description="Скорость полёта (м/с)")
    photo_overlap: float = Field(..., description="Желаемое перекрытие снимков (%)")

    @field_validator("flight_altitude")
    @classmethod
    def _check_altitude(cls, v: float) -> float:
        if not (LIMITS.min_altitude_m <= v <= LIMITS.max_altitude_m):
            raise ValueError(
                f"flight_altitude должна быть в диапазоне "
                f"[{LIMITS.min_altitude_m}; {LIMITS.max_altitude_m}] м"
            )
        return v

    @field_validator("flight_speed")
    @classmethod
    def _check_speed(cls, v: float) -> float:
        if not (LIMITS.min_speed_mps <= v <= LIMITS.max_speed_mps):
            raise ValueError(
                f"flight_speed должна быть в диапазоне "
                f"[{LIMITS.min_speed_mps}; {LIMITS.max_speed_mps}] м/с"
            )
        return v

    @field_validator("photo_overlap")
    @classmethod
    def _check_overlap(cls, v: float) -> float:
        if not (LIMITS.min_overlap_percent <= v <= LIMITS.max_overlap_percent):
            raise ValueError(
                f"photo_overlap должно быть в диапазоне "
                f"[{LIMITS.min_overlap_percent}; {LIMITS.max_overlap_percent}] %"
            )
        return v


class MissionResponse(BaseModel):
    """Результат генерации миссии."""

    route_points: List[RoutePoint]
    distance_meters: float
    flight_time_minutes: float
    battery_usage_percent: float
    photos_count: int
    mission_file: str
    route_image: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str