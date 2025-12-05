from __future__ import annotations
from typing import List, Tuple, Optional, Iterable
import math
import random
import numpy as np
import os, sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

def set_random_seed(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))

class Task:
    __slots__ = ("id", "position", "value")
    VALUE_LOG_MEAN: float = 1.8
    VALUE_LOG_STD: float = 0.6
    VALUE_MIN: float = 1.8
    VALUE_MAX: float = 15.0

    def __init__(self, task_id: int, x: float, y: float, value: Optional[float] = None):
        if not isinstance(task_id, int):
            raise TypeError("task_id deve essere un intero")
        self.id: int = task_id
        try:
            lon = float(x)
            lat = float(y)
        except Exception as exc:
            raise TypeError("x e y devono essere numerici (float)") from exc
        if not (math.isfinite(lon) and math.isfinite(lat)):
            raise ValueError("Coordinate devono essere valori finiti")
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Coordinate fuori range EPSG:4326: lon={lon}, lat={lat}. Range ammessi: lon ∈ [-180, 180], lat ∈ [-90, 90]")
        self.position: Tuple[float, float] = (lat, lon)
        if value is None:
            value = np.random.lognormal(mean=self.VALUE_LOG_MEAN, sigma=self.VALUE_LOG_STD)
            value = max(self.VALUE_MIN, min(self.VALUE_MAX, value))
        try:
            value = float(value)
        except Exception as exc:
            raise TypeError("value deve essere numerico (float)") from exc
        if not math.isfinite(value):
            raise ValueError("Valore task deve essere finito")
        if value < 0:
            raise ValueError(f"Valore task deve essere non negativo, ricevuto: {value}")
        self.value: float = value

    def __repr__(self) -> str:
        lat, lon = self.position
        return f"Task(ID={self.id}, Posizione=({lat:.5f}°N, {lon:.5f}°E), Valore={self.value:.2f})"

class User:
    __slots__ = ("id", "position", "cost_per_km", "tasks", "cost", "bid", "payment", "utility", "is_winner")
    EARTH_RADIUS_M: float = 6_371_000.0
    URBAN_CORRECTION_FACTOR: float = 1.30
    COST_PER_KM_MIN: float = 0.45
    COST_PER_KM_MAX: float = 0.70

    def __init__(self, user_id: int, x: float, y: float, cost_per_km: Optional[float] = None):
        if not isinstance(user_id, int):
            raise TypeError("user_id deve essere un intero")
        self.id: int = user_id
        try:
            lon = float(x)
            lat = float(y)
        except Exception as exc:
            raise TypeError("x e y devono essere numerici (float)") from exc
        if not (math.isfinite(lon) and math.isfinite(lat)):
            raise ValueError("Coordinate devono essere valori finiti")
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Coordinate fuori range EPSG:4326: lon={lon}, lat={lat}. Range ammessi: lon ∈ [-180, 180], lat ∈ [-90, 90]")
        self.position: Tuple[float, float] = (lat, lon)
        if cost_per_km is None:
            cost_per_km = random.uniform(self.COST_PER_KM_MIN, self.COST_PER_KM_MAX)
        try:
            cost_per_km = float(cost_per_km)
        except Exception as exc:
            raise TypeError("cost_per_km deve essere numerico (float)") from exc
        if not math.isfinite(cost_per_km):
            raise ValueError("cost_per_km deve essere finito")
        if cost_per_km <= 0:
            raise ValueError(f"cost_per_km deve essere positivo, ricevuto: {cost_per_km}")
        self.cost_per_km: float = cost_per_km
        self.tasks: List[Task] = []
        self.cost: float = 0.0
        self.bid: float = 0.0
        self.payment: float = 0.0
        self.utility: float = 0.0
        self.is_winner: bool = False

    def set_tasks(self, tasks: Iterable[Task], dedupe: bool = True) -> None:
        if tasks is None:
            self.tasks = []
            return
        if dedupe:
            seen: dict[int, Task] = {}
            for t in tasks:
                if not isinstance(t, Task):
                    raise TypeError(f"Elementi di tasks devono essere Task. Ricevuto: {type(t)}")
                seen[t.id] = t
            self.tasks = list(seen.values())
        else:
            self.tasks = list(tasks)
            for t in self.tasks:
                if not isinstance(t, Task):
                    raise TypeError(f"Elementi di tasks devono essere Task. Ricevuto: {type(t)}")

    def _calculate_travel_distance_km(self) -> float:
        if not self.tasks:
            return 0.0
        haversine_sum_m = sum(self.calculate_distance_to(t) for t in self.tasks)
        distance_m = haversine_sum_m * 2.0 * self.URBAN_CORRECTION_FACTOR
        return distance_m / 1000.0

    def calculate_cost_and_bid(self) -> None:
        travel_km = self._calculate_travel_distance_km()
        self.cost = float(self.cost_per_km * travel_km)
        if not math.isfinite(self.cost) or self.cost < 0:
            raise ValueError(f"Costo non valido per User {self.id}: cost={self.cost}, travel_km={travel_km}, cost_per_km={self.cost_per_km}")
        self.bid = float(self.cost)

    def calculate_distance_to(self, task: Task) -> float:
        lat1, lon1 = map(math.radians, self.position)
        lat2, lon2 = map(math.radians, task.position)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = float(self.EARTH_RADIUS_M * c)
        return d if math.isfinite(d) and d >= 0.0 else 0.0

    def reset_state(self) -> None:
        self.cost = 0.0
        self.bid = 0.0
        self.payment = 0.0
        self.utility = 0.0
        self.is_winner = False
        
    def __repr__(self) -> str:
        status = "Vincitore" if self.is_winner else "Non vincitore"
        lat, lon = self.position
        return f"User(ID={self.id}, Posizione=({lat:.5f}°N, {lon:.5f}°E), Costo/km={self.cost_per_km:.2f} €/km, Bid={self.bid:.2f} €, Stato={status})"
