import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from models import HealthResponse, MissionRequest, MissionResponse
from services.mission_generator import generate_mission

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("uav.mission")

# Приложение 
app = FastAPI(
    title="UAV Quarry Mission Planner",
    description=(
        "Сервис автоматической подготовки миссии БПЛА "
        "для аэрофотосъёмки карьеров. Принимает границы карьера, "
        "параметры полёта и возвращает оптимизированный маршрут, "
        "файл миссии и визуализацию."
    ),
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Проверка состояния сервиса."""
    return HealthResponse(
        status="ok",
        service="uav-quarry-mission-planner",
        version=app.version,
    )


@app.post(
    "/mission/generate",
    response_model=MissionResponse,
    tags=["mission"],
    summary="Сгенерировать полётную миссию",
)
def mission_generate(request: MissionRequest) -> MissionResponse:
    """
    Принимает параметры съёмки и возвращает готовую миссию:
    - точки маршрута,
    - длину маршрута,
    - время полёта,
    - расход батареи,
    - количество снимков,
    - путь к mission.json,
    - путь к route.png.
    """
    logger.info(
        "Запрос на генерацию миссии: вершин=%d, H=%.1f м, V=%.1f м/с, overlap=%.0f%%",
        len(request.quarry_polygon),
        request.flight_altitude,
        request.flight_speed,
        request.photo_overlap,
    )
    try:
        response = generate_mission(request)
    except ValueError as exc:
        logger.warning("Ошибка валидации: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Внутренняя ошибка генерации миссии")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

    logger.info(
        "Миссия готова: точек=%d, дистанция=%.1f м, время=%.2f мин, батарея=%.1f%%",
        response.photos_count,
        response.distance_meters,
        response.flight_time_minutes,
        response.battery_usage_percent,
    )
    return response


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request, exc: Exception):  # noqa: D401
    """Глобальный обработчик неожиданных ошибок."""
    logger.exception("Необработанная ошибка: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)