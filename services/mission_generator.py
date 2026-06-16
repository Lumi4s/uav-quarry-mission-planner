"""
Сервис генерации миссии: связывает геометрию, оптимизацию маршрута,
расчёт батареи и сохранение mission.json + route.png.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from config import DRONE, MISSIONS_DIR, OUTPUT_DIR
from models import MissionRequest, MissionResponse, RoutePoint
from services.battery_estimator import estimate_battery_usage
from services.route_optimizer import nearest_neighbor_route, two_opt
from utils.geometry import (
    build_polygon,
    compute_grid_step,
    generate_grid_points,
    route_length,
)
from utils.visualization import render_route


def _ensure_dirs() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MISSIONS_DIR, exist_ok=True)


def _serialize_mission(
    request: MissionRequest,
    route: List[Tuple[float, float]],
    distance_m: float,
    flight_time_min: float,
    battery_percent: float,
) -> Dict:
    """Готовит словарь миссии в формате, удобном для наземной станции."""
    waypoints = [
        {
            "seq": i,
            "x": round(pt[0], 3),
            "y": round(pt[1], 3),
            "altitude": request.flight_altitude,
            "action": "take_photo",
        }
        for i, pt in enumerate(route)
    ]

    return {
        "mission": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "coordinate_system": "local_ENU_meters",
            "drone_profile": {
                "max_flight_time_min": DRONE.max_flight_time_min,
                "battery_capacity_mah": DRONE.battery_capacity_mah,
                "cruise_power_w": DRONE.cruise_power_w,
            },
            "parameters": {
                "flight_altitude_m": request.flight_altitude,
                "flight_speed_mps": request.flight_speed,
                "photo_overlap_percent": request.photo_overlap,
            },
            "quarry_polygon": [
                {"x": p.x, "y": p.y} for p in request.quarry_polygon
            ],
            "statistics": {
                "photos_count": len(route),
                "distance_meters": round(distance_m, 2),
                "flight_time_minutes": round(flight_time_min, 2),
                "battery_usage_percent": round(battery_percent, 2),
            },
            "waypoints": waypoints,
        }
    }


def generate_mission(request: MissionRequest) -> MissionResponse:
    """
    Полный конвейер генерации миссии:

    1. Построение полигона карьера.
    2. Расчёт шага сетки по высоте и перекрытию.
    3. Генерация точек съёмки.
    4. Построение маршрута (Nearest Neighbor).
    5. Оптимизация (2-opt).
    6. Расчёт длины, времени, расхода батареи.
    7. Сохранение mission.json и route.png.
    """
    _ensure_dirs()

    # 1. Полигон карьера
    polygon = build_polygon([(p.x, p.y) for p in request.quarry_polygon])

    # 2. Шаг сетки по продольному и поперечному перекрытию
    step_x, step_y = compute_grid_step(
        request.flight_altitude, request.photo_overlap
    )

    # 3. Точки съёмки
    grid_points = generate_grid_points(polygon, step_x, step_y)

    # 4. Начальный маршрут — ближайший сосед, старт из левого нижнего угла полигона
    min_x, min_y, _, _ = polygon.bounds
    start_idx = min(
        range(len(grid_points)),
        key=lambda i: (grid_points[i][0] - min_x) ** 2
        + (grid_points[i][1] - min_y) ** 2,
    )
    initial_route = nearest_neighbor_route(grid_points, start_index=start_idx)

    # 5. 2-opt улучшение
    optimized_route = two_opt(initial_route, max_iterations=200)

    # 6. Метрики
    distance_m = route_length(optimized_route)
    flight_time_sec = distance_m / request.flight_speed
    flight_time_min = flight_time_sec / 60.0
    battery_percent = estimate_battery_usage(flight_time_min)

    # 7. Сохранение mission.json
    mission_dict = _serialize_mission(
        request=request,
        route=optimized_route,
        distance_m=distance_m,
        flight_time_min=flight_time_min,
        battery_percent=battery_percent,
    )
    mission_path = os.path.join(MISSIONS_DIR, "mission.json")
    with open(mission_path, "w", encoding="utf-8") as f:
        json.dump(mission_dict, f, ensure_ascii=False, indent=2)

    # 8. Визуализация
    image_path = os.path.join(OUTPUT_DIR, "route.png")
    render_route(
        polygon_points=[(p.x, p.y) for p in request.quarry_polygon],
        photo_points=grid_points,
        route=optimized_route,
        output_path=image_path,
        title=(
            f"Маршрут БПЛА | H={request.flight_altitude} м, "
            f"V={request.flight_speed} м/с, перекрытие={request.photo_overlap}%"
        ),
    )

    # 9. Формирование ответа
    route_points = [
        RoutePoint(
            seq=i,
            x=round(pt[0], 3),
            y=round(pt[1], 3),
            altitude=request.flight_altitude,
            action="take_photo",
        )
        for i, pt in enumerate(optimized_route)
    ]

    return MissionResponse(
        route_points=route_points,
        distance_meters=round(distance_m, 2),
        flight_time_minutes=round(flight_time_min, 2),
        battery_usage_percent=round(battery_percent, 2),
        photos_count=len(optimized_route),
        mission_file=mission_path.replace("\\", "/"),
        route_image=image_path.replace("\\", "/"),
    )