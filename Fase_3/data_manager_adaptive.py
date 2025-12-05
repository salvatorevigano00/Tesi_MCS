from __future__ import annotations
import sys
from typing import List, Tuple, Optional
import warnings
import logging
from pathlib import Path

_current_file = Path(__file__).resolve()
_current_dir = _current_file.parent
_parent_dir = _current_dir.parent
_fase1_dir = _parent_dir / "Fase_1"
_fase2_dir = _parent_dir / "Fase_2"
_fase3_dir = _current_dir

for p in [str(_fase1_dir), str(_fase2_dir), str(_fase3_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from Fase_2.data_manager_bounded import DataManagerRational
except ImportError as e:
    raise ImportError(f"Impossibile importare DataManager Fase 2: {e}")

try:
    from Fase_3.classes_adaptive import AdaptiveUser, TaskAdaptive
except ImportError as e:
    raise ImportError(f"Impossibile importare classi Fase 3: {e}")

try:
    from Fase_1.classes import Task as TaskBase
except ImportError as e:
    raise ImportError(f"Impossibile importare classi Fase 1: {e}")

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class DataManagerAdaptive(DataManagerRational):
    def __init__(
        self, 
        raw_txt_path: str, 
        out_dir: str = "dataset_processato", 
        bbox: Optional[Tuple[float, float, float, float]] = None, 
        random_seed: int = 42
    ):
        super().__init__(raw_txt_path, out_dir, bbox, random_seed)
        logger.info(f"DataManagerAdaptive inizializzato: seed={random_seed}")
    
    def create_tasks_adaptive(
        self, 
        day: Optional[str] = None, 
        hour: Optional[str] = None, 
        duration_hours: int = 1, 
        cell_size_m: int = 500, 
        value_mode: str = "uniform", 
        uniform_low: Optional[float] = None, 
        uniform_high: Optional[float] = None, 
        seed: Optional[int] = None,
        high_value_threshold_pct: float = 0.80,
        min_reliability_critical: float = 0.70,
        max_reliability_critical: float = 0.85,
        min_quality_target_critical: float = 0.40,
        max_quality_target_critical: float = 0.60,
        min_feedback_weight_critical: float = 1.5,
        max_feedback_weight_critical: float = 2.5,
    ) -> List[TaskAdaptive]:
        if not (0.0 <= high_value_threshold_pct <= 1.0):
            raise ValueError(
                f"high_value_threshold_pct deve essere in [0, 1], "
                f"ricevuto: {high_value_threshold_pct}"
            )
        if not (0.0 <= min_reliability_critical <= max_reliability_critical <= 1.0):
            raise ValueError(
                f"Reliability critica deve rispettare 0 <= min <= max <= 1, "
                f"ricevuto: min={min_reliability_critical}, max={max_reliability_critical}"
            )
        if not (0.0 <= min_quality_target_critical <= max_quality_target_critical <= 1.0):
            raise ValueError(
                f"Quality target critica deve rispettare 0 <= min <= max <= 1, "
                f"ricevuto: min={min_quality_target_critical}, max={max_quality_target_critical}"
            )
        if min_feedback_weight_critical < 0 or max_feedback_weight_critical < min_feedback_weight_critical:
            raise ValueError(
                f"Feedback weight critico deve rispettare 0 <= min <= max, "
                f"ricevuto: min={min_feedback_weight_critical}, max={max_feedback_weight_critical}"
            )
        tasks_f1: List[TaskBase] = super(DataManagerRational, self).create_tasks(
            day=day, 
            hour=hour, 
            duration_hours=duration_hours, 
            cell_size_m=cell_size_m, 
            value_mode=value_mode, 
            uniform_low=uniform_low, 
            uniform_high=uniform_high, 
            seed=seed
        )
        if not tasks_f1:
            warnings.warn(
                f"Nessun task generato nella finestra "
                f"[{day} {hour}:00 + {duration_hours}h], ritorno lista vuota"
            )
            return []
        if uniform_low is None: 
            uniform_low = TaskBase.VALUE_MIN
        if uniform_high is None: 
            uniform_high = TaskBase.VALUE_MAX
        value_threshold = (
            uniform_low + 
            (uniform_high - uniform_low) * high_value_threshold_pct
        )
        value_range_critical = max(1e-9, uniform_high - value_threshold)
        logger.info(
            f"Soglia valore task critici: {value_threshold:.2f} euro "
            f"({high_value_threshold_pct*100:.0f} percentile, "
            f"range [{uniform_low:.2f}, {uniform_high:.2f}])"
        )
        tasks_f3: List[TaskAdaptive] = []
        critical_tasks_count = 0
        for t_f1 in tasks_f1:
            lat_f1, lon_f1 = t_f1.position
            req_rel = 0.0
            feed_weight = 1.0
            quality_target = None
            if t_f1.value >= value_threshold:
                normalized_value = (t_f1.value - value_threshold) / value_range_critical
                normalized_value = max(0.0, min(1.0, normalized_value))
                req_rel = (
                    min_reliability_critical + 
                    (max_reliability_critical - min_reliability_critical) * normalized_value
                )
                quality_target = (
                    min_quality_target_critical + 
                    (max_quality_target_critical - min_quality_target_critical) * normalized_value
                )
                feed_weight = (
                    min_feedback_weight_critical + 
                    (max_feedback_weight_critical - min_feedback_weight_critical) * normalized_value
                )
                critical_tasks_count += 1
                required_rho = 0.3 + 0.7 * quality_target
                logger.debug(
                    f"Task {t_f1.id}: critico (v={t_f1.value:.2f} euro, norm={normalized_value:.2f}), "
                    f"req_rel={req_rel:.2f}, quality_target={quality_target:.2f} "
                    f"(rho_min={required_rho:.2f}), weight={feed_weight:.1f}"
                )
            task_f3 = TaskAdaptive(
                task_id=t_f1.id, 
                x=lon_f1,
                y=lat_f1,
                value=t_f1.value,
                quality_target=quality_target,
                required_reliability=req_rel,
                feedback_weight=feed_weight
            )
            tasks_f3.append(task_f3)
        critical_pct = (critical_tasks_count / len(tasks_f3) * 100) if tasks_f3 else 0.0
        logger.info(
            f"Creati {len(tasks_f3)} task adaptive fase 3, "
            f"{critical_tasks_count} critici ({critical_pct:.1f}%), "
            f"req_rel: [{min_reliability_critical:.2f}, {max_reliability_critical:.2f}], "
            f"quality_target: [{min_quality_target_critical:.2f}, {max_quality_target_critical:.2f}], "
            f"weight: [{min_feedback_weight_critical:.1f}, {max_feedback_weight_critical:.1f}], "
        )
        total_v_mech = sum(t.value for t in tasks_f3)
        return tasks_f3

    def create_users_adaptive(
        self, 
        day: Optional[str] = None, 
        hour: Optional[str] = None, 
        duration_hours: int = 1, 
        max_users: int = 316, 
        cost_mode: str = "uniform", 
        cost_params: Optional[Tuple[float, float]] = None, 
        sampling_strategy: str = "uniform", 
        rationality_distribution: str = "mixed", 
        tasks: Optional[List[TaskAdaptive]] = None, 
        task_radius_m: float = 2500.0,
        allow_no_tasks: bool = False,
        prefilter_quality: bool = True
    ) -> List[AdaptiveUser]:
        users_f1 = super(DataManagerRational, self).create_users(
            day=day, 
            hour=hour, 
            duration_hours=duration_hours, 
            max_users=max_users, 
            cost_mode=cost_mode, 
            cost_params=cost_params, 
            sampling_strategy=sampling_strategy
        )
        if not users_f1:
            warnings.warn(
                f"Nessun tassista attivo trovato nella finestra "
                f"[{day} {hour}:00 + {duration_hours}h], ritorno lista vuota"
            )
            return []
        if (tasks is None or not tasks) and allow_no_tasks:
            logger.info(
                f"Modalità allow_no_tasks: creazione {len(users_f1)} utenti "
                f"senza task pre-assegnati (task verranno assegnati successivamente)"
            )
            users_f3: List[AdaptiveUser] = []
            for user_f1 in users_f1:
                rationality_level = self._generate_rationality(rationality_distribution)
                user = AdaptiveUser(
                    user_id=user_f1.id, 
                    x=user_f1.position[1],
                    y=user_f1.position[0],
                    cost_per_km=user_f1.cost_per_km, 
                    rationality_level=rationality_level, 
                    global_seed=self.random_seed
                )
                user.set_tasks([])
                users_f3.append(user)
            logger.info(
                f"Creati {len(users_f3)} adaptive user fase 3 senza task, "
                f"distribuzione razionalita: {rationality_distribution}, "
                f"rho_stima_media (prior): {sum(u.estimated_rationality for u in users_f3)/len(users_f3):.3f}"
            )
            return users_f3
        if tasks is None or not tasks:
            logger.warning(
                f"Nessun task disponibile per la creazione utenti "
                f"(tasks={'none' if tasks is None else 'vuoto'}), ritorno lista vuota, "
                f"suggerimento: usa allow_no_tasks=true se i task verranno assegnati dopo"
            )
            return []
        if tasks and not all(isinstance(t, TaskAdaptive) for t in tasks):
            raise TypeError(
                f"Alcuni task non sono di tipo TaskAdaptive, "
                f"tipi trovati: {set(type(t).__name__ for t in tasks)}"
            )
        logger.info(
            f"Validati {len(tasks)} task adaptive per assegnazione utenti "
            f"(raggio={task_radius_m}m, prefilter_quality={prefilter_quality})"
        )
        users_f3: List[AdaptiveUser] = []
        excluded_no_tasks = 0
        excluded_by_quality = 0
        task_counts = []
        for user_f1 in users_f1:
            rationality_level = self._generate_rationality(rationality_distribution)
            user = AdaptiveUser(
                user_id=user_f1.id, 
                x=user_f1.position[1],
                y=user_f1.position[0],
                cost_per_km=user_f1.cost_per_km, 
                rationality_level=rationality_level, 
                global_seed=self.random_seed
            )
            candidate_tasks: List[TaskAdaptive] = []
            tasks_filtered_quality = 0
            for task in tasks:
                dist_m = user.calculate_distance_to(task)
                if dist_m > task_radius_m:
                    continue
                if prefilter_quality and task.quality_target is not None:
                    required_rho = 0.3 + 0.7 * task.quality_target
                    if user.estimated_rationality < required_rho:
                        tasks_filtered_quality += 1
                        logger.debug(
                            f"Utente {user.id}: task {task.id} pre-filtrato "
                            f"(rho_stima={user.estimated_rationality:.2f} < {required_rho:.2f} richiesto)"
                        )
                        continue
                candidate_tasks.append(task)
            if tasks_filtered_quality > 0:
                excluded_by_quality += tasks_filtered_quality
            if not candidate_tasks:
                excluded_no_tasks += 1
                logger.debug(
                    f"Utente {user_f1.id}: escluso "
                    f"(nessun task nel raggio {task_radius_m}m o tutti pre-filtrati)"
                )
                continue
            user.set_tasks(candidate_tasks)
            task_counts.append(len(candidate_tasks))
            users_f3.append(user)
        if users_f3:
            import numpy as np
            avg_tasks = np.mean(task_counts)
            std_tasks = np.std(task_counts)
            min_tasks = int(np.min(task_counts))
            max_tasks = int(np.max(task_counts))
            logger.info(
                f"Creati {len(users_f3)} adaptive user fase 3 "
                f"({excluded_no_tasks} esclusi per mancanza task, "
                f"{excluded_by_quality} task pre-filtrati per qualita), "
                f"distribuzione razionalita: {rationality_distribution}, "
                f"task candidati: media={avg_tasks:.1f}, std={std_tasks:.1f}, "
                f"range=[{min_tasks}, {max_tasks}]"
            )
        else:
            logger.warning(
                f"Nessun utente creato, "
                f"tutti i {len(users_f1)} tassisti erano fuori dal raggio "
                f"({task_radius_m}m) di tutti i {len(tasks)} task, "
                f"o non avevano rho sufficiente per i task disponibili"
            )
        return users_f3
