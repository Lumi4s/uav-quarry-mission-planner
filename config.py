"""
Конфигурация параметров БПЛА и системных констант.

Значения соответствуют типовому квадрокоптеру класса DJI Mavic 3 Enterprise,
часто применяемому для аэрофотосъёмки карьеров.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DroneSpec:
    """Технические характеристики БПЛА."""

    # Параметры камеры
    sensor_width_mm: float = 17.3          # ширина матрицы
    sensor_height_mm: float = 13.0         # высота матрицы
    focal_length_mm: float = 12.29         # фокусное расстояние
    image_width_px: int = 5280             # ширина снимка в пикселях
    image_height_px: int = 3956            # высота снимка в пикселях

    # Параметры полёта
    max_flight_time_min: float = 45.0      # максимальное время полёта на одной батарее
    battery_capacity_mah: int = 5000       # ёмкость батареи
    cruise_power_w: float = 90.0           # средняя потребляемая мощность в крейсерском режиме
    battery_voltage_v: float = 17.6        # напряжение батареи

    # Безопасность
    safety_reserve_percent: float = 15.0   # резерв % батареи на возврат


@dataclass(frozen=True)
class MissionLimits:
    """Предельные значения параметров миссии для валидации."""

    min_altitude_m: float = 30.0
    max_altitude_m: float = 500.0
    min_speed_mps: float = 1.0
    max_speed_mps: float = 25.0
    min_overlap_percent: float = 30.0
    max_overlap_percent: float = 95.0


DRONE = DroneSpec()
LIMITS = MissionLimits()

# Каталоги вывода
OUTPUT_DIR = "output"
MISSIONS_DIR = "missions"