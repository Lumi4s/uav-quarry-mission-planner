"""
Геометрические утилиты:
 - расчёт наземного покрытия снимка (footprint),
 - расчёт шага сетки исходя из перекрытия,
 - построение регулярной сетки точек внутри полигона.
"""

from typing import List, Tuple

import numpy as np
from shapely.geometry import Polygon, Point

from config import DRONE


def compute_ground_footprint(altitude_m: float) -> Tuple[float, float]:
    """
    Вычисляет линейные размеры наземного покрытия одного кадра (м).

    Используется модель тонкой линзы:
        GSD_x = (sensor_width  * altitude) / focal_length
        GSD_y = (sensor_height * altitude) / focal_length

    :param altitude_m: высота полёта над поверхностью, м
    :return: (ширина_кадра_м, высота_кадра_м)
    """
    if altitude_m <= 0:
        raise ValueError("Высота полёта должна быть положительной")

    width_m = (DRONE.sensor_width_mm * altitude_m) / DRONE.focal_length_mm
    height_m = (DRONE.sensor_height_mm * altitude_m) / DRONE.focal_length_mm
    return width_m, height_m


def compute_grid_step(altitude_m: float, overlap_percent: float) -> Tuple[float, float]:
    """
    Рассчитывает шаг сетки точек съёмки с учётом продольного и поперечного перекрытия.

    Шаг = размер_кадра * (1 - overlap/100).

    :param altitude_m: высота полёта (м)
    :param overlap_percent: перекрытие снимков (%) — применяется к обеим осям
    :return: (шаг_по_X_м, шаг_по_Y_м)
    """
    fp_w, fp_h = compute_ground_footprint(altitude_m)
    factor = 1.0 - overlap_percent / 100.0
    step_x = max(fp_w * factor, 0.5)   # защита от нулевого шага
    step_y = max(fp_h * factor, 0.5)
    return step_x, step_y


def build_polygon(points: List[Tuple[float, float]]) -> Polygon:
    """Создаёт shapely-полигон, корректируя ориентацию обхода."""
    poly = Polygon(points)
    if not poly.is_valid:
        # Попытка восстановить валидность (например, самопересечения)
        poly = poly.buffer(0)
    if poly.is_empty:
        raise ValueError("Полигон карьера некорректен или вырожден")
    return poly


def generate_grid_points(
    polygon: Polygon,
    step_x: float,
    step_y: float,
) -> List[Tuple[float, float]]:
    """
    Строит регулярную сетку точек, попадающих внутрь полигона.

    Точки выкладываются по узлам решётки, начиная от минимального угла bounding box.
    Граничные точки также включаются (используется covers).

    :return: список (x, y) точек съёмки
    """
    min_x, min_y, max_x, max_y = polygon.bounds

    # Сдвигаем стартовую точку на половину шага внутрь, чтобы избежать пустых краёв
    start_x = min_x + step_x / 2.0
    start_y = min_y + step_y / 2.0

    xs = np.arange(start_x, max_x + 1e-9, step_x)
    ys = np.arange(start_y, max_y + 1e-9, step_y)

    points: List[Tuple[float, float]] = []
    for y in ys:
        for x in xs:
            if polygon.covers(Point(x, y)):
                points.append((float(x), float(y)))

    if not points:
        c = polygon.centroid
        points.append((float(c.x), float(c.y)))

    return points


def route_length(route: List[Tuple[float, float]]) -> float:
    """Суммарная длина ломаной маршрута, м."""
    if len(route) < 2:
        return 0.0
    arr = np.array(route)
    diffs = np.diff(arr, axis=0)
    return float(np.sqrt((diffs ** 2).sum(axis=1)).sum())