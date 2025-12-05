from __future__ import annotations
import os
import sys
import math
from typing import List, Tuple, Dict, Optional
import random
import warnings
import logging
from pathlib import Path

_current_file = Path(__file__).resolve()
_current_dir = _current_file.parent
_parent_dir = _current_dir.parent
_fase1_dir = _parent_dir / "Fase_1"
_fase2_dir = _parent_dir / "Fase_2"

for p in [str(_fase1_dir), str(_fase2_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from Fase_1.data_manager import DataManager as DataManagerBase
except ImportError as e:
    raise ImportError(f"Impossibile importare DataManager dalla Fase 1. Controlla che esistano {_fase1_dir}/data_manager.py e {_fase1_dir}/__init__.py. Dettagli tecnici: {e}")

try:
    from Fase_2.classes_bounded import BoundedRationalUser, Task
except ImportError as e:
    raise ImportError(f"Impossibile importare le classi della Fase 2. Controlla che esista il file {_fase2_dir}/classes_bounded.py. Dettagli tecnici: {e}")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class RationalityDistributions:
    ALTA = {"high": (0.825, 0.90)}
    MISTA = {
        "quasi_rational": (0.825, 0.90, 0.25),
        "bounded_honest": (0.65, 0.825, 0.25),
        "bounded_moderate": (0.475, 0.65, 0.30),
        "bounded_opportunistic": (0.30, 0.475, 0.20),
    }
    BASSA = {"low": (0.30, 0.65)}

class DataManagerRational(DataManagerBase):
    def __init__(self, raw_txt_path: str, out_dir: str = "dataset_out", bbox: Optional[Tuple[float, float, float, float]] = None, random_seed: int = 42):
        super().__init__(raw_txt_path, out_dir, bbox, random_seed)
        self.random_seed = random_seed
        random.seed(random_seed)
        logger.info(f"DataManagerRational pronto: seed={random_seed}, riquadro={bbox if bbox else 'predefinito'}")

    def create_users_bounded(self, day: Optional[str] = None, hour: Optional[str] = None, duration_hours: int = 1, max_users: int = 316, cost_mode: str = "uniform", cost_params: Optional[Tuple[float, float]] = None, sampling_strategy: str = "uniform", rationality_distribution: str = "mixed", tasks: Optional[List[Task]] = None, task_radius_m: float = 2500.0) -> List[BoundedRationalUser]:
        if task_radius_m <= 0:
            raise ValueError(f"Il raggio massimo dei task deve essere maggiore di zero. Valore ricevuto: {task_radius_m} metri")
        if not math.isfinite(task_radius_m):
            warnings.warn("Raggio dei task infinito: ogni utente vedrà tutti i task come candidati. Le prestazioni potrebbero risentirne.")
        if cost_mode not in ("uniform",):
            raise ValueError(f"Modalità di costo non valida: {cost_mode}. Al momento è supportata solo la modalità 'uniform'.")
        if sampling_strategy not in ("uniform", "stratified"):
            raise ValueError(f"Strategia di campionamento non valida: {sampling_strategy}. Valori ammessi: 'uniform' o 'stratified'.")
        if rationality_distribution not in ("high", "mixed", "low"):
            raise ValueError(f"Distribuzione di razionalità non valida: {rationality_distribution}. Valori ammessi: high, mixed o low. La modalità perfect è solo teorica e non disponibile in Fase 2.")
        if cost_params is None:
            try:
                cost_min_default = BoundedRationalUser.COST_PER_KM_MIN
                cost_max_default = BoundedRationalUser.COST_PER_KM_MAX
            except AttributeError:
                logger.warning("Impossibile leggere COST_PER_KM_MIN e COST_PER_KM_MAX da BoundedRationalUser. Si useranno 0.5 e 1.5 €/km come valori di ripiego.")
                cost_min_default = 0.5
                cost_max_default = 1.5
            cost_params = (cost_min_default, cost_max_default)
        cost_min, cost_max = cost_params
        if cost_min < 0 or cost_max < 0 or cost_min > cost_max:
            raise ValueError(f"Intervallo di costo non valido: minimo={cost_min}, massimo={cost_max}. Il minimo deve essere non negativo e non superiore al massimo.")
        if day is None or hour is None:
            partitions = sorted([f for f in os.listdir(self.part_dir) if f.endswith(".csv")])
            if not partitions:
                raise FileNotFoundError(f"Nessuna partizione dati trovata in {self.part_dir}. Prima va eseguito il parsing dei dati grezzi.")
            first_partition = partitions[0]
            day = first_partition[:10]
            hour = first_partition[11:13] if len(first_partition) > 10 else "00"
            logger.info(f"Parametri temporali rilevati automaticamente: giorno={day}, ora={hour}")
        last_positions: Dict[int, Tuple[float, float, int]] = {}
        for row in self.get_window_records(day=day, hour=hour, duration_hours=duration_hours):
            driver_id = int(row["driver_id"])
            epoch_ms = int(row["epoch_ms"])
            lat, lon = float(row["lat"]), float(row["lon"])
            if driver_id not in last_positions or epoch_ms > last_positions[driver_id][2]:
                last_positions[driver_id] = (lat, lon, epoch_ms)
        if not last_positions:
            warnings.warn(f"Nessun tassista attivo nella finestra specificata: giorno {day}, ora {hour}:00, durata {duration_hours} ore. Ritorno una lista vuota di utenti.")
            return []
        driver_items = [(did, (lat, lon)) for did, (lat, lon, _) in last_positions.items()]
        if len(driver_items) > max_users:
            if sampling_strategy == "uniform":
                driver_items = random.sample(driver_items, k=max_users)
            else:
                driver_items = self._stratified_sampling(driver_items, max_users)
        driver_items.sort(key=lambda item: item[0])
        users: List[BoundedRationalUser] = []
        for driver_id, (lat, lon) in driver_items:
            cost_per_km = random.uniform(cost_min, cost_max)
            rationality_level = self._generate_rationality(rationality_distribution)
            user = BoundedRationalUser(user_id=driver_id, x=lon, y=lat, cost_per_km=cost_per_km, rationality_level=rationality_level, initial_reputation=1.0, deviation_prob=None, global_seed=self.random_seed)
            candidate_tasks: List[Task] = []
            if tasks is not None:
                for task in tasks:
                    dist_m = user.calculate_distance_to(task)
                    if dist_m <= task_radius_m:
                        candidate_tasks.append(task)
            desired_tasks: List[Task] = user.select_task_set_bounded(candidate_tasks)
            user.set_tasks(desired_tasks)
            user.generate_bid()
            users.append(user)
        logger.info(f"Creati {len(users)} utenti con razionalità limitata (distribuzione={rationality_distribution})")
        return users

    def _stratified_sampling(self, driver_items: List[Tuple[int, Tuple[float, float]]], max_users: int) -> List[Tuple[int, Tuple[float, float]]]:
        lat0, lat1, lon0, lon1 = self.bbox
        n_stratum = 5
        strata: Dict[Tuple[int, int], List[Tuple[int, Tuple[float, float]]]] = {}
        for did, (lat, lon) in driver_items:
            sy = int(min(n_stratum - 1, (lat - lat0) / (lat1 - lat0 + 1e-9) * n_stratum))
            sx = int(min(n_stratum - 1, (lon - lon0) / (lon1 - lon0 + 1e-9) * n_stratum))
            strata.setdefault((sy, sx), []).append((did, (lat, lon)))
        sampled: List[Tuple[int, Tuple[float, float]]] = []
        total_drivers = len(driver_items)
        for _, drivers_in_stratum in strata.items():
            n_sample_stratum = max(1, int(len(drivers_in_stratum) / total_drivers * max_users))
            n_sample_stratum = min(n_sample_stratum, len(drivers_in_stratum))
            sampled.extend(random.sample(drivers_in_stratum, k=n_sample_stratum))
        if len(sampled) < max_users:
            remaining = [item for item in driver_items if item not in sampled]
            if remaining:
                additional = random.sample(remaining, k=min(max_users - len(sampled), len(remaining)))
                sampled.extend(additional)
        return sampled[:max_users]

    def _generate_rationality(self, distribution: str) -> float:
        if distribution == "high":
            return random.uniform(0.825, 0.90)
        elif distribution == "mixed":
            rand = random.random()
            if rand < 0.25:
                return random.uniform(0.825, 0.90)
            elif rand < 0.50:
                return random.uniform(0.65, 0.825)
            elif rand < 0.80:
                return random.uniform(0.475, 0.65)
            else:
                return random.uniform(0.30, 0.475)
        elif distribution == "low":
            return random.uniform(0.30, 0.65)
        else:
            raise ValueError(f"Distribuzione di razionalità non riconosciuta: {distribution}")

    def create_tasks(self, day: Optional[str] = None, hour: Optional[str] = None, duration_hours: int = 1, cell_size_m: int = 500, value_mode: str = "uniform", uniform_low: Optional[float] = None, uniform_high: Optional[float] = None, seed: Optional[int] = None) -> List[Task]:
        tasks_f1 = super().create_tasks(day=day, hour=hour, duration_hours=duration_hours, cell_size_m=cell_size_m, value_mode=value_mode, uniform_low=uniform_low, uniform_high=uniform_high, seed=seed)
        if not tasks_f1:
            warnings.warn(f"Nessun task generato nella finestra specificata: giorno {day}, ora {hour}:00, durata {duration_hours} ore. Ritorno una lista vuota di task.")
            return []
        tasks_f2: List[Task] = []
        for t_f1 in tasks_f1:
            lat_f1, lon_f1 = t_f1.position
            task_f2 = Task(task_id=t_f1.id, x=lon_f1, y=lat_f1, value=t_f1.value)
            tasks_f2.append(task_f2)
        return tasks_f2