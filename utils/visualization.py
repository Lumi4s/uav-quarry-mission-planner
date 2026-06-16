"""
Визуализация маршрута БПЛА с помощью Matplotlib.

Создаёт PNG, на котором отображены:
  - граница карьера (полигон),
  - точки съёмки (waypoints),
  - стартовая точка (зелёный маркер),
  - конечная точка (красный маркер),
  - линия маршрута облёта со стрелками направления.
"""

from typing import List, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


Point = Tuple[float, float]


def render_route(
    polygon_points: List[Point],
    photo_points: List[Point],
    route: List[Point],
    output_path: str,
    title: str = "Маршрут БПЛА",
) -> None:
    """
    Сохраняет PNG-визуализацию маршрута.

    :param polygon_points: вершины полигона карьера
    :param photo_points:   все точки съёмки (узлы сетки)
    :param route:          упорядоченный маршрут
    :param output_path:    путь для сохранения PNG
    :param title:          заголовок графика
    """
    fig, ax = plt.subplots(figsize=(11, 9), dpi=120)

    # Полигон карьера
    poly_patch = MplPolygon(
        polygon_points,
        closed=True,
        facecolor="#f5e6c8",
        edgecolor="#8b5a2b",
        linewidth=2.0,
        alpha=0.55,
        label="Карьер",
    )
    ax.add_patch(poly_patch)

    # Точки съёмки
    if photo_points:
        xs = [p[0] for p in photo_points]
        ys = [p[1] for p in photo_points]
        ax.scatter(
            xs, ys,
            s=22, c="#1f77b4", marker="o",
            edgecolors="white", linewidths=0.5,
            label=f"Точки съёмки ({len(photo_points)})",
            zorder=3,
        )

    # Линия маршрута 
    if len(route) >= 2:
        rx = [p[0] for p in route]
        ry = [p[1] for p in route]
        ax.plot(
            rx, ry,
            color="#d62728", linewidth=1.6, alpha=0.85,
            label="Маршрут облёта", zorder=2,
        )

        # Стрелки направления каждые N сегментов
        step = max(1, len(route) // 25)
        for i in range(0, len(route) - 1, step):
            x0, y0 = route[i]
            x1, y1 = route[i + 1]
            dx, dy = x1 - x0, y1 - y0
            ax.annotate(
                "",
                xy=(x0 + dx * 0.6, y0 + dy * 0.6),
                xytext=(x0 + dx * 0.4, y0 + dy * 0.4),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
            )

    # Старт и финиш 
    if route:
        sx, sy = route[0]
        ex, ey = route[-1]
        ax.scatter([sx], [sy], s=180, c="#2ca02c", marker="*",
                   edgecolors="black", linewidths=0.8,
                   label="Старт", zorder=5)
        ax.scatter([ex], [ey], s=140, c="#d62728", marker="X",
                   edgecolors="black", linewidths=0.8,
                   label="Финиш", zorder=5)

    # Оформление
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X, м")
    ax.set_ylabel("Y, м")
    ax.set_title(title, fontsize=12, pad=12)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    # Авто-расширение границ
    all_x = [p[0] for p in polygon_points] + [p[0] for p in route]
    all_y = [p[1] for p in polygon_points] + [p[1] for p in route]
    if all_x and all_y:
        pad_x = (max(all_x) - min(all_x)) * 0.08 + 5
        pad_y = (max(all_y) - min(all_y)) * 0.08 + 5
        ax.set_xlim(min(all_x) - pad_x, max(all_x) + pad_x)
        ax.set_ylim(min(all_y) - pad_y, max(all_y) + pad_y)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)