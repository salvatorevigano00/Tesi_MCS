from __future__ import annotations
import sys
import math
import random
import logging
from enum import Enum, auto
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
from pathlib import Path

_current_file = Path(__file__).resolve()
_current_dir = _current_file.parent
_parent_dir = _current_dir.parent
_fase1_dir = _parent_dir / "Fase_1"
if str(_fase1_dir) not in sys.path:
    sys.path.insert(0, str(_fase1_dir))

try:
    from Fase_1.classes import Task as TaskBase, User as UserBase
except ImportError as e:
    raise ImportError(f"Impossibile importare Fase_1.classes: {e}\nVerifica che esista Fase_1/__init__.py e che contenga Task e User")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

URBAN_CORRECTION_FACTOR_BASE: float = 1.30
ROUTING_INEFFICIENCY_MAX: float = 0.40
ROUTING_GAMMA: float = 3.0

RATIONALITY_MIN: float = 0.30
RATIONALITY_MAX: float = 0.90
RATIONALITY_THRESHOLD_HIGH: float = 0.825
RATIONALITY_THRESHOLD_MEDIUM: float = 0.65
RATIONALITY_THRESHOLD_LOW: float = 0.475

THETA_R_MIN_EURO: float = 10.0
THETA_R_MAX_EURO: float = 120.0
THETA_D_MIN_KM: float = 0.5
THETA_D_MAX_KM: float = 4.0
EXPECTED_PAYMENT_FACTOR: float = 0.7

ALPHA_DEVIATION_MIN: float = 0.02
ALPHA_DEVIATION_MAX: float = 0.20
KAPPA_ATTENTION: float = 0.5

DELTA_EXOGENOUS: float = 0.00
DELTA_ENDOGENOUS_MAX: float = 0.35
GAMMA_RATIONALITY: float = 2.0

BETA_REPUTATION: float = 0.6
LAMBDA_REPUTATION_DECAY: float = 0.85
DETECTION_PROBABILITY: float = 0.50
PENALTY_FACTOR: float = 2.0
ENFORCEMENT_COST: float = 0.5

BLACKLIST_STRIKES_THRESHOLD: int = 3
BLACKLIST_BASE_DURATION_H: float = 2.0
BLACKLIST_MAX_DURATION_H: float = 24.0

PAYMENT_REPUTATION_WEIGHT: float = 0.5
PAYMENT_RATIONALITY_WEIGHT: float = 0.3
PAYMENT_MIN_FACTOR: float = 0.3

EFFICIENCY_BASELINE_FASE1: float = 0.3157
IR_VIOLATION_BASELINE_FASE1: float = 0.0
COMPLETION_BASELINE_FASE1: float = 1.0

class Cue(Enum):
    DISTANZA = auto()
    RICOMPENSA = auto()
    COMMUNITY = auto()

class FFTType(Enum):
    LENIENT_PECTINATE = auto()
    STRICT_PECTINATE = auto()
    ZIGZAG_1 = auto()
    ZIGZAG_2 = auto()

def set_random_seed(seed: int) -> None:
    if seed < 0:
        raise ValueError(f"Il seed deve essere >= 0, ricevuto: {seed}")
    random.seed(int(seed))
    np.random.seed(int(seed))
    logger.info(f"Seed casuale globale impostato: {seed}")

def compute_defection_baseline(rho: float) -> float:
    if not (RATIONALITY_MIN <= rho <= RATIONALITY_MAX):
        raise ValueError(f"Livello di razionalità (rho) fuori dall'intervallo ammissibile [{RATIONALITY_MIN}, {RATIONALITY_MAX}]: {rho:.4f}\nVerificare la generazione degli utenti in `data_manager_bounded.py`")
    delta_endo = DELTA_ENDOGENOUS_MAX * math.exp(-GAMMA_RATIONALITY * rho)
    delta_baseline = DELTA_EXOGENOUS + delta_endo
    return float(delta_baseline)

def compute_deviation_probability(rho: float) -> float:
    if not (RATIONALITY_MIN <= rho <= RATIONALITY_MAX):
        raise ValueError(f"Livello di razionalità (rho) fuori dall'intervallo ammissibile [{RATIONALITY_MIN}, {RATIONALITY_MAX}]: {rho}")
    alpha_range = ALPHA_DEVIATION_MAX - ALPHA_DEVIATION_MIN
    deviation = ALPHA_DEVIATION_MIN + alpha_range * ((1.0 - rho) ** KAPPA_ATTENTION)
    return float(np.clip(deviation, 0.0, ALPHA_DEVIATION_MAX))

def routing_inefficiency_factor(rho: float) -> float:
    return 1.0 + ROUTING_INEFFICIENCY_MAX * math.exp(-ROUTING_GAMMA * max(0.0, rho))

def compute_anomaly_threshold(users: List[UserBase]) -> float:
    deviations = []
    for u in users:
        if hasattr(u, "cost") and hasattr(u, "bid") and u.cost > 1e-6:
            dev = abs(u.bid - u.cost) / u.cost
            deviations.append(dev)
    if not deviations:
        return 0.15
    mean_dev = float(np.mean(deviations))
    std_dev = float(np.std(deviations))
    threshold = mean_dev + 3 * std_dev
    final_threshold = float(np.clip(threshold, 0.10, 0.25))
    logger.debug(f"Soglia anomalia dinamica calcolata: {final_threshold:.3f} (media={mean_dev:.3f}, dev_std={std_dev:.3f}, 3sigma_raw={threshold:.3f})")
    return final_threshold

class Task(TaskBase):
    __slots__ = ("id", "position", "value", "is_community_task", "quality_target", "group_id")

    def __init__(self, task_id: int, x: float, y: float, value: Optional[float] = None, is_community_task: Optional[bool] = False, quality_target: Optional[float] = None, group_id: Optional[int] = None):
        super().__init__(task_id, x, y, value)
        self.is_community_task = bool(is_community_task if is_community_task is not None else random.choice([True, False]))
        if quality_target is not None:
            if not (0.0 <= quality_target <= 1.0):
                raise ValueError(f"Il target di qualità (quality_target) è fuori dall'intervallo [0, 1]: {quality_target}\nValori ammessi: [0.0 = nessun vincolo, 1.0 = massima qualità]")
            self.quality_target = float(quality_target)
        else:
            self.quality_target = None
        self.group_id = group_id

    def __repr__(self) -> str:
        tipo = "Comunitario" if self.is_community_task else "Commerciale"
        return f"Task({self.id}, {tipo}, v={self.value:.2f})"

class BoundedRationalUser(UserBase):
    __slots__ = ("id", "position", "cost_per_km", "tasks", "cost", "bid", "payment", "utility", "is_winner", "rationality_level", "reputation", "honesty_profile", "p_defect_base", "deviation_prob", "fft_type", "cue_ranking", "soglia_distanza_km", "soglia_reward_base", "prefers_community", "reward_allocation_class", "blacklisted_until", "blacklist_strikes", "penalty_accumulated", "p_defect", "completed", "actually_completed", "data_quality", "_local_rng")

    def __init__(self, user_id: int, x: float, y: float, cost_per_km: Optional[float] = None, rationality_level: Optional[float] = None, initial_reputation: float = 1.0, deviation_prob: Optional[float] = None, global_seed: Optional[int] = None, fft_type: str = "LENIENT_PECTINATE", fft_heuristic: Optional[Any] = None):
        super().__init__(user_id, x, y, cost_per_km)
        if rationality_level is None:
            rationality_level = np.random.uniform(RATIONALITY_MIN, RATIONALITY_MAX)
        else:
            if not (RATIONALITY_MIN <= rationality_level <= RATIONALITY_MAX):
                raise ValueError(f"Livello di razionalità (rho) fuori dall'intervallo ammissibile [{RATIONALITY_MIN}, {RATIONALITY_MAX}]: {rationality_level:.4f}\nUtente {user_id} generato con valore non valido.")
        self.rationality_level = float(rationality_level)
        self.reputation = float(np.clip(initial_reputation, 0.0, 1.0))
        self.penalty_accumulated = 0.0
        self.blacklisted_until = None
        self.blacklist_strikes = 0
        self.completed = False
        self.actually_completed = False
        seed_local = (user_id * 31337 + (global_seed or 0)) % (2**31)
        self._local_rng = random.Random(seed_local)
        if self.rationality_level >= RATIONALITY_THRESHOLD_HIGH:
            self.honesty_profile = "Quasi-Rational"
        elif self.rationality_level >= RATIONALITY_THRESHOLD_MEDIUM:
            self.honesty_profile = "Bounded Honest"
        elif self.rationality_level >= RATIONALITY_THRESHOLD_LOW:
            self.honesty_profile = "Bounded Moderate"
        else:
            self.honesty_profile = "Bounded Opportunistic"
        self.p_defect_base = compute_defection_baseline(self.rationality_level)
        self.p_defect = self.p_defect_base
        if deviation_prob is None:
            self.deviation_prob = compute_deviation_probability(self.rationality_level)
        else:
            if not (0.0 <= deviation_prob <= 1.0):
                raise ValueError(f"Probabilità di deviazione (deviation_prob) fuori dall'intervallo [0,1]: {deviation_prob}")
            self.deviation_prob = float(deviation_prob)
        if fft_heuristic:
            self.fft_type = fft_heuristic.fft_type
            self.cue_ranking = fft_heuristic.cue_ranking
            self.reward_allocation_class = fft_heuristic.reward_allocation_class
            logger.debug(f"Utente {self.id}: FFT assegnato da euristica pre-compilata.")
        else:
            try:
                self.fft_type = FFTType[fft_type.upper()]
            except KeyError:
                logger.warning(f"Tipo FFT '{fft_type}' non valido. Uso di default LENIENT_PECTINATE.")
                self.fft_type = FFTType.LENIENT_PECTINATE
            rank_str = self._local_rng.choice(["DCR", "DRC", "RDC", "RCD", "CRD", "CDR"])
            cue_map = {"D": Cue.DISTANZA, "R": Cue.RICOMPENSA, "C": Cue.COMMUNITY}
            self.cue_ranking = [cue_map[c] for c in rank_str if c in cue_map]
            self.reward_allocation_class = f"({rank_str},{self.fft_type.name})"
        self.soglia_distanza_km = self._local_rng.uniform(THETA_D_MIN_KM, THETA_D_MAX_KM)
        self.soglia_reward_base = self._local_rng.uniform(THETA_R_MIN_EURO, THETA_R_MAX_EURO)
        self.prefers_community = self._local_rng.choice([True, False])
        self.data_quality = 1.0
        logger.debug(f"Utente {self.id} inizializzato: rho={self.rationality_level:.2f}, profilo={self.honesty_profile}, delta_base={self.p_defect_base:.3f}, FFT={self.fft_type.name}")

    def is_eligible_at_time(self, current_time: float) -> bool:
        if self.blacklisted_until is None:
            return True
        return current_time > self.blacklisted_until

    def record_defection_detected(self, current_time: float) -> None:
        self.blacklist_strikes += 1
        if self.blacklist_strikes >= BLACKLIST_STRIKES_THRESHOLD:
            exponent = self.blacklist_strikes - BLACKLIST_STRIKES_THRESHOLD
            duration_h = min(BLACKLIST_MAX_DURATION_H, BLACKLIST_BASE_DURATION_H * (2 ** exponent))
            self.blacklisted_until = current_time + duration_h * 3600.0
            logger.warning(f"Utente {self.id} inserito in blacklist per circa {duration_h:.1f} ore (strike={self.blacklist_strikes}, rho={self.rationality_level:.2f}, fino al timestamp={self.blacklisted_until:.0f})")
        else:
            logger.info(f"Utente {self.id}: defezione rilevata (strike {self.blacklist_strikes} di {BLACKLIST_STRIKES_THRESHOLD})")

    def _assign_fft_canonical(self, fft_type: FFTType) -> None:
        rank_str = self._local_rng.choice(["DCR", "DRC", "RDC", "RCD", "CRD", "CDR"])
        cue_map = {"D": Cue.DISTANZA, "R": Cue.RICOMPENSA, "C": Cue.COMMUNITY}
        self.cue_ranking = [cue_map[c] for c in rank_str if c in cue_map]
        self.reward_allocation_class = f"({rank_str},{fft_type.name})"
        logger.debug(f"Utente {self.id}: FFT assegnato {self.reward_allocation_class}, ordine indizi={[c.name for c in self.cue_ranking]}")

    def _evaluate_cue_sequential(self, task: Task, reward: float) -> Tuple[bool, str]:
        if not isinstance(task, Task):
            raise TypeError(f"Atteso oggetto Task, ricevuto: {type(task).__name__}")
        if reward < 0:
            raise ValueError(f"Ricompensa negativa non ammessa: {reward} euro")
        for idx, cue in enumerate(self.cue_ranking):
            if cue == Cue.DISTANZA:
                dist_km = self.calculate_distance_to(task) / 1000.0
                cue_result = (dist_km <= self.soglia_distanza_km)
            elif cue == Cue.RICOMPENSA:
                cue_result = (reward >= self.soglia_reward_base)
            else:
                cue_result = (task.is_community_task == self.prefers_community)
            is_last_cue = (idx == len(self.cue_ranking) - 1)
            if self.fft_type == FFTType.LENIENT_PECTINATE:
                if cue_result:
                    return True, f"permissivo_accetta_{cue.name}"
                if is_last_cue:
                    return False, "permissivo_rifiuta_tutti"
            elif self.fft_type == FFTType.STRICT_PECTINATE:
                if not cue_result:
                    return False, f"rigoroso_rifiuta_{cue.name}"
                if is_last_cue:
                    return True, "rigoroso_accetta_tutti"
            elif self.fft_type == FFTType.ZIGZAG_1:
                if cue_result:
                    return True, f"zigzag1_esci_{cue.name}"
            else:
                if not cue_result:
                    return False, f"zigzag2_esci_{cue.name}"
        logger.warning(f"Utente {self.id}: L'euristica FFT non ha portato a una decisione esplicita, rifiuto di sicurezza.")
        return False, "rifiuto_default_finale"

    def _select_fft_heuristic(self, all_tasks: List[Task], max_tasks: int = 5) -> List[Task]:
        selected: List[Task] = []
        if self._local_rng.random() < self.deviation_prob:
            k = min(max_tasks, len(all_tasks))
            selected = self._local_rng.sample(all_tasks, k)
            logger.debug(f"Utente {self.id}: deviazione dall'euristica FFT, scelta casuale di {len(selected)} task")
            return selected
        for task in all_tasks:
            expected_reward = self._estimate_expected_payment(task)
            decision, reason = self._evaluate_cue_sequential(task, expected_reward)
            if decision:
                selected.append(task)
                logger.debug(f"Utente {self.id}: task {task.id} ACCETTATO (motivo={reason}, ricompensa_attesa={expected_reward:.2f} euro)")
                if len(selected) >= max_tasks:
                    break
            else:
                logger.debug(f"Utente {self.id}: task {task.id} rifiutato (motivo={reason})")
        return selected

    def select_task_set_bounded(self, all_tasks: List[Task], max_tasks: int = 5) -> List[Task]:
        return self._select_fft_heuristic(all_tasks, max_tasks)

    def _estimate_expected_payment(self, task: Task) -> float:
        return task.value * EXPECTED_PAYMENT_FACTOR

    def _calculate_travel_distance_km(self) -> float:
        if not self.tasks:
            return 0.0
        unique_tasks = list({t.id: t for t in self.tasks}.values())
        if len(unique_tasks) == 1:
            one_way_m = self._haversine(self.position, unique_tasks[0].position)
            total_m = 2 * one_way_m
        elif self.rationality_level >= 0.70:
            total_m = self._tsp_greedy_routing_m(unique_tasks)
        elif self.rationality_level >= 0.50:
            total_m = self._star_routing_distance_m(unique_tasks)
        else:
            total_m = self._random_routing_distance_m(unique_tasks)
        correction = URBAN_CORRECTION_FACTOR_BASE * routing_inefficiency_factor(self.rationality_level)
        distance_km = (total_m * correction) / 1000.0
        logger.debug(f"Utente {self.id}: distanza stimata {distance_km:.2f} km ({len(unique_tasks)} task, rho={self.rationality_level:.2f}, fattore_correzione={correction:.3f}x)")
        return distance_km

    def _star_routing_distance_m(self, tasks: List[Task]) -> float:
        total_m = sum(2 * self._haversine(self.position, t.position) for t in tasks)
        return total_m

    def _tsp_greedy_routing_m(self, tasks: List[Task]) -> float:
        if not tasks:
            return 0.0
        remaining = tasks.copy()
        route: List[Task] = []
        current_pos = self.position
        while remaining:
            nearest = min(remaining, key=lambda t: self._haversine(current_pos, t.position))
            route.append(nearest)
            remaining.remove(nearest)
            current_pos = nearest.position
        total = self._haversine(self.position, route[0].position)
        for i in range(len(route) - 1):
            total += self._haversine(route[i].position, route[i + 1].position)
        total += self._haversine(route[-1].position, self.position)
        return total

    def _random_routing_distance_m(self, tasks: List[Task]) -> float:
        if not tasks:
            return 0.0
        shuffled = tasks.copy()
        self._local_rng.shuffle(shuffled)
        total = self._haversine(self.position, shuffled[0].position)
        for i in range(len(shuffled) - 1):
            total += self._haversine(shuffled[i].position, shuffled[i + 1].position)
        total += self._haversine(shuffled[-1].position, self.position)
        return total

    def _haversine(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        lat1, lon1 = map(math.radians, pos1)
        lat2, lon2 = map(math.radians, pos2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = min(1.0, math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
        distance_m = self.EARTH_RADIUS_M * c
        return distance_m

    def calculate_distance_to(self, task: Task) -> float:
        if not isinstance(task, Task):
            raise TypeError(f"Atteso oggetto Task, ricevuto: {type(task).__name__}")
        return self._haversine(self.position, task.position)

    def compute_true_cost(self) -> float:
        travel_km = self._calculate_travel_distance_km()
        cost = float(self.cost_per_km * travel_km)
        if not math.isfinite(cost) or cost < 0:
            raise ValueError(f"Costo non valido calcolato per Utente {self.id}: {cost:.4f} euro\n  costo_per_km={self.cost_per_km:.2f}, km_viaggio={travel_km:.2f}\n  Controllare assegnazione dei task e calcolo del percorso.")
        return cost

    def generate_bid(self, manual_deviation: Optional[float] = None) -> float:
        try:
            c = self.compute_true_cost()
        except Exception as e:
            raise ValueError(f"Utente {self.id}: impossibile calcolare il costo effettivo: {e}") from e
        if not math.isfinite(c) or c < 0:
            raise ValueError(f"Utente {self.id}: costo non valido da compute_true_cost() = {c:.4f} euro\n  Verificare l'assegnazione dei task e il calcolo del routing.")
        if manual_deviation is not None:
            deviation = float(manual_deviation)
            logger.debug(f"Utente {self.id}: deviazione offerta impostata manualmente={deviation:.3f}")
        else:
            rho = self.rationality_level
            if rho < RATIONALITY_THRESHOLD_LOW:
                mu_dev = 0.03
                sigma_dev = 0.08 * (1.0 - rho)
            else:
                mu_dev = 0.02 + 0.06 * (1.0 - rho)
                sigma_dev = 0.03 * (1.0 - rho)
            deviation = np.random.normal(mu_dev, sigma_dev)
            deviation = float(np.clip(deviation, -0.15, 0.15))
        bid = c * (1.0 + deviation)
        bid = max(0.01, float(bid))
        self.cost = c
        self.bid = bid
        logger.debug(f"Utente {self.id}: offerta generata {bid:.2f} euro (costo={c:.2f}, deviazione_relativa={deviation:.3f}, rho={self.rationality_level:.2f})")
        return bid

    def calculate_cost_and_bid(self, strategic_deviation: float = 0.0) -> None:
        self.cost = self.compute_true_cost()
        if abs(strategic_deviation) > 1e-6:
            self.bid = self.generate_bid(manual_deviation=strategic_deviation)
        else:
            self.bid = self.generate_bid()

    def attempt_task_completion(self) -> bool:
        delta_base = self.p_defect_base
        reputation_factor = 1.0 + BETA_REPUTATION * (1.0 - self.reputation)
        self.p_defect = min(0.95, delta_base * reputation_factor)
        logger.debug(f"Utente {self.id}: probabilità di defezione stimata = {self.p_defect:.3f} (delta_base={delta_base:.3f}, reputazione={self.reputation:.2f})")
        defect_attempt = self._local_rng.random() < self.p_defect
        if defect_attempt:
            detected = self._local_rng.random() < DETECTION_PROBABILITY
            if detected:
                penalty = PENALTY_FACTOR * self.payment
                self.penalty_accumulated += penalty
                self.reputation = max(0.0, self.reputation - 0.5)
                self.completed = False
                self.actually_completed = False
                self.data_quality = 0.0
                logger.info(f"Utente {self.id}: defezione rilevata, sanzione={penalty:.2f} euro, reputazione aggiornata a {self.reputation:.2f}")
            else:
                self.completed = True
                self.actually_completed = False
                self.data_quality = float(np.random.uniform(0.1, 0.4))
                logger.debug(f"Utente {self.id}: defezione non rilevata, il task risulta completato ma con qualità bassa.")
        else:
            self.completed = True
            self.actually_completed = True
            self.data_quality = 1.0
            logger.debug(f"Utente {self.id}: task completato correttamente e senza scorciatoie.")
        return self.completed

    def update_reputation(self, completed: bool) -> None:
        if not (0.0 <= LAMBDA_REPUTATION_DECAY <= 1.0):
            raise ValueError(f"Il fattore di decadimento LAMBDA_REPUTATION_DECAY è fuori dall'intervallo [0,1]: {LAMBDA_REPUTATION_DECAY}")
        indicator = 1.0 if completed else 0.0
        self.reputation = LAMBDA_REPUTATION_DECAY * self.reputation + (1.0 - LAMBDA_REPUTATION_DECAY) * indicator
        self.reputation = float(np.clip(self.reputation, 0.0, 1.0))
        logger.debug(f"Utente {self.id}: reputazione aggiornata a {self.reputation:.3f} (completato={completed})")

    def reset_state(self, reset_reputation: bool = False) -> None:
        super().reset_state()
        self.completed = False
        self.actually_completed = False
        self.data_quality = 1.0
        if reset_reputation:
            self.reputation = 1.0
            self.penalty_accumulated = 0.0
            self.blacklist_strikes = 0
            self.blacklisted_until = None
            logger.debug(f"Utente {self.id}: stato resettato completamente, inclusa la reputazione.")
        else:
            logger.debug(f"Utente {self.id}: stato operativo resettato, reputazione mantenuta.")

    def add_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError(f"Il task deve essere un'istanza di Task, ricevuto: {type(task).__name__}")
        if task not in self.tasks:
            self.tasks.append(task)
            logger.debug(f"Utente {self.id}: task {task.id} aggiunto al bundle corrente.")

    def set_tasks(self, tasks: List[Task], dedupe: bool = True) -> None:
        if tasks is None:
            self.tasks = []
            logger.debug(f"Utente {self.id}: bundle di task svuotato.")
            return
        if dedupe:
            seen: Dict[int, Task] = {}
            for t in tasks:
                if not isinstance(t, Task):
                    raise TypeError(f"Tutti i task devono essere istanze di Task, ricevuto: {type(t).__name__}")
                seen[t.id] = t
            self.tasks = list(seen.values())
            logger.debug(f"Utente {self.id}: bundle impostato con {len(self.tasks)} task unici su {len(tasks)} proposti.")
        else:
            self.tasks = list(tasks)
            for t in self.tasks:
                if not isinstance(t, Task):
                    raise TypeError(f"Tutti i task devono essere istanze di Task, ricevuto: {type(t).__name__}")
            logger.debug(f"Utente {self.id}: bundle impostato con {len(self.tasks)} task (possibili duplicati).")

    def __repr__(self) -> str:
        blacklist_str = f", strike={self.blacklist_strikes}" if self.blacklist_strikes > 0 else ""
        return f"Utente({self.id}, rho={self.rationality_level:.2f}, {self.honesty_profile}{blacklist_str})"

def validate_mechanism_health(winners: List[BoundedRationalUser], payments: Dict[int, float], v_eff: float, all_tasks: List[Task], baseline_efficiency: float = EFFICIENCY_BASELINE_FASE1, hour_label: str = "") -> Dict:
    if v_eff < 0:
        raise ValueError(f"Il valore effettivo (v_eff) non può essere negativo: {v_eff} euro")
    if not isinstance(payments, dict):
        raise TypeError(f"`payments` deve essere un dizionario {{user_id: payment}}, ricevuto: {type(payments).__name__}")
    for user_id, p in payments.items():
        if p < 0:
            raise ValueError(f"Pagamento negativo non ammesso per utente {user_id}: {p} euro")
    sumP = sum(payments.values())
    u0_eff = v_eff - sumP
    TOLERANCE = 1e-6
    deficit_breakdown = (u0_eff < -TOLERANCE)
    ir_violations = sum(1 for w in winners if w.utility < -TOLERANCE)
    ir_violation_rate = ir_violations / max(1, len(winners))
    ir_breakdown = (ir_violation_rate > 0.05)
    efficiency = v_eff / sumP if sumP > 1e-6 else 0.0
    efficiency_breakdown = (efficiency < baseline_efficiency * 0.80)
    completed_task_ids = set()
    for w in winners:
        if w.actually_completed:
            if not w.tasks:
                logger.warning(f"Utente {w.id}: actually_completed=True ma tasks è vuoto, possibile inconsistenza di stato.")
            completed_task_ids.update(t.id for t in w.tasks)
    completion_rate = len(completed_task_ids) / max(1, len(all_tasks))
    service_breakdown = (completion_rate < 0.90)
    severity_weighted = 4.0 * deficit_breakdown + 3.0 * ir_breakdown + 2.0 * efficiency_breakdown + 1.0 * service_breakdown
    severity_binary = sum([deficit_breakdown, ir_breakdown, efficiency_breakdown, service_breakdown])
    if severity_binary > 0 and hour_label:
        breakdown_types = []
        if deficit_breakdown:
            breakdown_types.append(f"deficit (u0_eff={u0_eff:.2f} euro)")
        if ir_breakdown:
            breakdown_types.append(f"violazione IR (tasso={ir_violation_rate:.1%})")
        if efficiency_breakdown:
            breakdown_types.append(f"efficienza bassa (eta={efficiency:.2f}, baseline={baseline_efficiency:.2f})")
        if service_breakdown:
            breakdown_types.append(f"servizio insufficiente (completamento={completion_rate:.1%})")
        logger.warning(f"[{hour_label}] Rottura del meccanismo rilevata (severità={severity_binary}/4, pesata={severity_weighted:.1f}/10): {', '.join(breakdown_types)}")
    return {
        "deficit_breakdown": deficit_breakdown,
        "ir_breakdown": ir_breakdown,
        "efficiency_breakdown": efficiency_breakdown,
        "service_breakdown": service_breakdown,
        "severity_score": severity_binary,
        "severity_weighted": float(severity_weighted),
        "u0_eff": float(u0_eff),
        "ir_violation_rate": float(ir_violation_rate),
        "efficiency": float(efficiency),
        "completion_rate": float(completion_rate),
        "completed_tasks_count": len(completed_task_ids),
        "total_tasks_count": len(all_tasks),
        "winners_count": len(winners),
        "total_payments": float(sumP),
    }
