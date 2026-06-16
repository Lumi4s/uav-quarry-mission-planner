"""
Расчёт расхода батареи БПЛА на основании времени полёта.

Используется упрощённая энергетическая модель:
  - известна средняя потребляемая мощность в крейсерском режиме (Вт);
  - известна ёмкость батареи (мА·ч) и напряжение (В);
  - вычисляется доля от полной энергоёмкости, израсходованная за время полёта,
    с учётом обязательного резерва на возврат.
"""

from config import DRONE


def battery_energy_wh() -> float:
    """Полная энергоёмкость батареи в ватт-часах."""
    return (DRONE.battery_capacity_mah / 1000.0) * DRONE.battery_voltage_v


def estimate_battery_usage(flight_time_minutes: float) -> float:
    """
    Возвращает прогнозируемый расход батареи (%) на миссию.

    Формула:
        E_used   = P_cruise * t_h               [Вт·ч]
        E_full   = C_mah/1000 * U               [Вт·ч]
        usage_%  = E_used / E_full * 100 + reserve

    Резерв безопасности добавляется как требование на возврат / посадку.

    :param flight_time_minutes: общее время полёта, мин
    :return: расход батареи в процентах (может превышать 100% — это сигнал,
             что миссию нужно разбить на несколько вылетов)
    """
    if flight_time_minutes < 0:
        raise ValueError("Время полёта не может быть отрицательным")

    t_hours = flight_time_minutes / 60.0
    energy_used_wh = DRONE.cruise_power_w * t_hours
    energy_full_wh = battery_energy_wh()

    usage_percent = (energy_used_wh / energy_full_wh) * 100.0
    return usage_percent + DRONE.safety_reserve_percent