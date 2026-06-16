"""
Алгоритмы построения и оптимизации маршрута облёта точек съёмки.

Реализованы:
 - Nearest Neighbor (NN) — жадное построение начального маршрута.
 - 2-opt — локальная оптимизация маршрута, устраняющая пересечения.
"""

from typing import List, Tuple

import numpy as np

Point = Tuple[float, float]


def _distance_matrix(points: List[Point]) -> np.ndarray:
    """Полная матрица евклидовых расстояний между точками."""
    arr = np.asarray(points, dtype=float)
    diff = arr[:, np.newaxis, :] - arr[np.newaxis, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


def nearest_neighbor_route(points: List[Point], start_index: int = 0) -> List[Point]:
    """
    Построение маршрута по правилу ближайшего соседа.

    :param points: список точек съёмки
    :param start_index: индекс стартовой точки
    :return: упорядоченный список точек маршрута
    """
    n = len(points)
    if n == 0:
        return []
    if n == 1:
        return [points[0]]

    dist = _distance_matrix(points)
    visited = [False] * n
    order = [start_index]
    visited[start_index] = True

    current = start_index
    for _ in range(n - 1):
        # Маскируем посещённые
        candidates = np.where(~np.array(visited), dist[current], np.inf)
        nxt = int(np.argmin(candidates))
        order.append(nxt)
        visited[nxt] = True
        current = nxt

    return [points[i] for i in order]


def _route_length(route: List[Point]) -> float:
    if len(route) < 2:
        return 0.0
    arr = np.asarray(route)
    diffs = np.diff(arr, axis=0)
    return float(np.sqrt((diffs ** 2).sum(axis=1)).sum())


def two_opt(route: List[Point], max_iterations: int = 200) -> List[Point]:
    """
    Алгоритм 2-opt: на каждой итерации ищется пара рёбер, разворот участка между
    которыми сокращает суммарную длину маршрута. Останавливается при отсутствии
    улучшений или достижении лимита итераций.

    :param route: исходный маршрут
    :param max_iterations: максимальное число полных проходов
    :return: оптимизированный маршрут
    """
    n = len(route)
    if n < 4:
        return list(route)

    best = list(route)
    best_len = _route_length(best)
    improved = True
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(1, n - 2):
            # Локальный кэш ради скорости
            a = best[i - 1]
            b = best[i]
            for j in range(i + 1, n):
                c = best[j]
                d = best[j + 1] if j + 1 < n else None

                # Длина двух текущих рёбер
                d_ab = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
                d_cd = (
                    ((c[0] - d[0]) ** 2 + (c[1] - d[1]) ** 2) ** 0.5
                    if d is not None
                    else 0.0
                )
                # Длина новых рёбер после разворота сегмента [i..j]
                d_ac = ((a[0] - c[0]) ** 2 + (a[1] - c[1]) ** 2) ** 0.5
                d_bd = (
                    ((b[0] - d[0]) ** 2 + (b[1] - d[1]) ** 2) ** 0.5
                    if d is not None
                    else 0.0
                )

                delta = (d_ac + d_bd) - (d_ab + d_cd)
                if delta < -1e-9:
                    best[i : j + 1] = list(reversed(best[i : j + 1]))
                    best_len += delta
                    improved = True
                    b = best[i]

    return best