from __future__ import annotations
import sys
import math
import logging
import time
from typing import Any, Optional, List, Dict
import numpy as np
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
    from Fase_2.classes_bounded import (
        Task as TaskBounded, 
        BoundedRationalUser,
        RATIONALITY_MIN,
        RATIONALITY_MAX,
        BETA_REPUTATION,
        DETECTION_PROBABILITY
    )
except ImportError as e:
    raise ImportError(
        f"Impossibile importare Fase_2.classes_bounded: {e}\n"
        f"Assicurarsi che Fase_2/__init__.py e Fase_2/classes_bounded.py esistano."
    )

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

BAYESIAN_RHO_PRIOR_ALPHA: float = 6.5
BAYESIAN_RHO_PRIOR_BETA: float = 3.5
RHO_OBS: float = 1.0

MDR_WEIGHT_COMPLETION: float = 0.0
MDR_WEIGHT_RELIABILITY: float = 0.60
MDR_WEIGHT_QUALITY: float = 0.40

_MDR_TOTAL_WEIGHT = (
    MDR_WEIGHT_COMPLETION + 
    MDR_WEIGHT_RELIABILITY + 
    MDR_WEIGHT_QUALITY
)
if not math.isclose(_MDR_TOTAL_WEIGHT, 1.0, abs_tol=1e-6):
    raise ValueError(
        f"Pesi MDR non normalizzati a 1.0 (somma={_MDR_TOTAL_WEIGHT:.4f})"
    )

LAMBDA_REPUTATION_DECAY: float = 0.85
KAPPA_RELIABILITY: float = 1.0
BETA_TRUST_BONUS: float = 0.50
REPUTATION_THRESHOLD_BONUS: float = 0.90
REPUTATION_THRESHOLD_MALUS: float = 0.70

PENALTY_BASE_FACTOR: float = 0.85
PENALTY_REPUTATION_DECAY: float = 0.15
MIN_PENALTY_FLOOR: float = 0.20
IR_SAFETY_MARGIN: float = 0.10

REPUTATION_ABSOLUTE_MIN_THRESHOLD: float = 0.30


class TaskAdaptive(TaskBounded):
    __slots__ = (
        "id", "position", "value", "is_community_task", 
        "quality_target", "group_id", 
        "required_reliability", "feedback_weight",
        "feedback_quality", "completion_timestamp",
        "feedback_notes"
    )
    
    def __init__(
        self,
        task_id: int, 
        x: float, 
        y: float, 
        value: Optional[float] = None,
        is_community_task: Optional[bool] = False, 
        quality_target: Optional[float] = None, 
        group_id: Optional[int] = None,
        required_reliability: float = 0.0,
        feedback_weight: float = 1.0,
        feedback_notes: str = ""
    ):
        super().__init__(
            task_id, x, y, value, is_community_task, 
            quality_target, group_id
        )
        if not (0.0 <= required_reliability <= 1.0):
            raise ValueError(
                f"required_reliability deve essere in [0, 1], "
                f"ricevuto: {required_reliability}"
            )
        self.required_reliability = float(required_reliability)
        if feedback_weight < 0:
            raise ValueError(
                f"feedback_weight non può essere negativo, "
                f"ricevuto: {feedback_weight}"
            )
        self.feedback_weight = float(feedback_weight)
        self.feedback_quality: Optional[float] = None
        self.completion_timestamp: Optional[float] = None
        self.feedback_notes = str(feedback_notes)
    
    def mark_completed_by_platform(
        self,
        quality: float,
        timestamp: Optional[float] = None,
        notes: Optional[str] = None
    ) -> None:
        if self.completion_timestamp is not None:
            logger.warning(
                f"Task {self.id} già marcato come completato, sovrascrittura del feedback"
            )
        if not (0.0 <= quality <= 1.0):
            raise ValueError(
                f"Qualità di feedback deve essere in [0, 1], ricevuto: {quality}"
            )
        self.completion_timestamp = float(timestamp) if timestamp else time.time()
        self.feedback_quality = float(quality)
        if notes:
            self.feedback_notes = notes

    def __repr__(self) -> str:
        base_repr = super().__repr__()
        quality_str = (
            f"Q_feed={self.feedback_quality:.2f}" 
            if self.feedback_quality is not None else "Q_feed=N/A"
        )
        return (
            f"{base_repr[:-1]}, "
            f"ReqR={self.required_reliability:.1f}, "
            f"Weight={self.feedback_weight:.1f}, "
            f"{quality_str})"
        )


class AdaptiveUser(BoundedRationalUser):
    __slots__ = (
        "id", "position", "cost_per_km", "tasks", "cost", "bid", "payment", 
        "utility", "is_winner",
        "rationality_level", "reputation", "honesty_profile",
        "p_defect_base", "deviation_prob", 
        "fft_type", "cue_ranking", "soglia_distanza_km", "soglia_reward_base", 
        "prefers_community", "reward_allocation_class",
        "blacklisted_until", "blacklist_strikes", "penalty_accumulated",
        "p_defect", "completed", "actually_completed", 
        "_local_rng",
        "estimated_rationality",
        "rho_alpha",
        "rho_beta",
        "_rho_prior_alpha",
        "_rho_prior_beta",
        "rho_observation_count",
        "reputation_reliability",
        "reputation_quality",
        "mdr_observation_count"
    )
    
    def __init__(
        self,
        user_id: int,
        x: float,
        y: float,
        cost_per_km: Optional[float] = None,
        rationality_level: Optional[float] = None,
        global_seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            user_id=user_id,
            x=x, y=y,
            cost_per_km=cost_per_km,
            rationality_level=rationality_level,
            initial_reputation=1.0,
            deviation_prob=None,
            global_seed=global_seed
        )
        self._rho_prior_alpha = float(BAYESIAN_RHO_PRIOR_ALPHA)
        self._rho_prior_beta = float(BAYESIAN_RHO_PRIOR_BETA)
        self.rho_alpha = self._rho_prior_alpha
        self.rho_beta = self._rho_prior_beta
        self.rho_observation_count = 0
        self.estimated_rationality = self._compute_rationality_estimate()
        self.reputation_reliability = 1.0
        self.reputation_quality = 1.0
        self.mdr_observation_count = 0
        self.reputation = 1.0
        logger.debug(
            f"Utente adattivo {self.id} inizializzato: "
            f"ρ={self.rationality_level:.3f}, "
            f"ρ̂={self.estimated_rationality:.3f}, "
            f"R̂={self.reputation:.3f}"
        )

    def update_platform_beliefs(
        self,
        was_winner: bool,
        task_list: List[TaskAdaptive]
    ) -> None:
        if not was_winner or not task_list:
            logger.debug(
                f"Utente {self.id}: non vincitore o senza task, apprendimento skippato"
            )
            return
        self._update_rationality_belief(
            is_success=(self.actually_completed),
            strength=RHO_OBS
        )
        logger.debug(
            f"Utente {self.id}: ρ̂ aggiornato, "
            f"defezione={'no' if self.actually_completed else 'sì'}, "
            f"ρ̂={self.estimated_rationality:.3f}"
        )
        total_weight = 0.0
        observed_quality_sum = 0.0
        for task in task_list:
            if isinstance(task, TaskAdaptive) and task.feedback_quality is not None:
                weight = task.feedback_weight
                total_weight += weight
                observed_quality_sum += task.feedback_quality * weight
        avg_quality = (
            (observed_quality_sum / total_weight) if total_weight > 0 else 0.5
        )
        decay = LAMBDA_REPUTATION_DECAY
        current_weight = 1.0 - decay
        obs_reliability = 1.0 if self.actually_completed else 0.0
        self.reputation_reliability = (
            decay * self.reputation_reliability +
            current_weight * obs_reliability
        )
        obs_quality = avg_quality if self.actually_completed else 0.0
        self.reputation_quality = (
            decay * self.reputation_quality +
            current_weight * obs_quality
        )
        self.mdr_observation_count += 1
        self._recalculate_aggregate_reputation()
        logger.debug(
            f"Utente {self.id}: R̂ aggiornato, "
            f"R_r={self.reputation_reliability:.3f}, "
            f"R_q={self.reputation_quality:.3f}, "
            f"R̂_agg={self.reputation:.3f}"
        )

    def get_effective_bid(self) -> float:
        base_bid = self.bid
        if base_bid < 0:
            raise ValueError(
                f"Utente {self.id}: bid non calcolato o negativo, "
                f"chiamare generate_bid() prima"
            )
        effective_reliability = max(0.01, self.reputation)
        adjustment_factor = effective_reliability ** KAPPA_RELIABILITY
        adjusted_bid = base_bid / max(1e-9, adjustment_factor)
        logger.debug(
            f"Utente {self.id}: offerta effettiva, "
            f"base={base_bid:.2f}€, R̂={self.reputation:.3f} (κ={KAPPA_RELIABILITY}), "
            f"effettiva={adjusted_bid:.2f}€ ({(adjusted_bid/base_bid-1)*100:+.0f}%)"
        )
        return float(adjusted_bid)

    def get_incentive_payment(self, base_payment: float) -> float:
        if base_payment <= 0:
            logger.debug(
                f"Utente {self.id}: base_payment={base_payment:.2f} ≤ 0, "
                f"nessun pagamento erogato"
            )
            return 0.0
        if self.reputation >= REPUTATION_THRESHOLD_BONUS:
            trust_adjustment = base_payment * BETA_TRUST_BONUS
            adjustment_type = "bonus"
        elif self.reputation < REPUTATION_THRESHOLD_MALUS:
            reputation_gap = (
                (REPUTATION_THRESHOLD_MALUS - self.reputation) / 
                REPUTATION_THRESHOLD_MALUS
            )
            trust_adjustment = -base_payment * BETA_TRUST_BONUS * reputation_gap
            adjustment_type = "malus"
        else:
            trust_adjustment = 0.0
            adjustment_type = "neutrale"
        final_payment = max(0.0, base_payment + trust_adjustment)
        if hasattr(self, 'cost') and self.cost > 0:
            min_payment = self.cost * (1 + IR_SAFETY_MARGIN)
            if final_payment < min_payment:
                logger.warning(
                    f"Utente {self.id}: vincolo IR applicato "
                    f"(p={final_payment:.2f} < min={min_payment:.2f})"
                )
                final_payment = min_payment
        logger.debug(
            f"Utente {self.id}: gap-incentive ({adjustment_type}), "
            f"base={base_payment:.2f}€, R̂={self.reputation:.3f}, "
            f"adj={trust_adjustment:+.2f}€, finale={final_payment:.2f}€"
        )
        return float(final_payment)

    def _compute_rationality_estimate(self) -> float:
        total = self.rho_alpha + self.rho_beta
        if total <= 0:
            return RATIONALITY_MIN
        raw_estimate = self.rho_alpha / total
        rho_range = RATIONALITY_MAX - RATIONALITY_MIN
        scaled_estimate = RATIONALITY_MIN + raw_estimate * rho_range
        return float(
            np.clip(
                scaled_estimate,
                RATIONALITY_MIN,
                RATIONALITY_MAX,
            )
        )

    def _update_rationality_belief(
        self, 
        is_success: bool, 
        strength: float
    ) -> None:
        if is_success:
            self.rho_alpha += strength
        else:
            self.rho_beta += strength
        self.rho_observation_count += 1
        self.estimated_rationality = self._compute_rationality_estimate()

    def _recalculate_aggregate_reputation(self) -> None:
        if _MDR_TOTAL_WEIGHT <= 0:
            self.reputation = 0.0
            return
        weighted_sum = (
            self.reputation_reliability * MDR_WEIGHT_RELIABILITY +
            self.reputation_quality * MDR_WEIGHT_QUALITY
        )
        self.reputation = float(
            np.clip(weighted_sum / _MDR_TOTAL_WEIGHT, 0.0, 1.0)
        )

    def reset_state(
        self,
        reset_reputation: bool = False,
        reset_learning: bool = False,
    ) -> None:
        super().reset_state(reset_reputation=reset_reputation)
        if reset_learning or reset_reputation:
            self.rho_alpha = self._rho_prior_alpha
            self.rho_beta = self._rho_prior_beta
            self.rho_observation_count = 0
            self.estimated_rationality = self._compute_rationality_estimate()
            self.reputation_reliability = 1.0
            self.reputation_quality = 1.0
            self.mdr_observation_count = 0
            self.reputation = 1.0
            logger.debug(
                f"Utente {self.id}: stato di apprendimento gap resettato ai prior"
            )

    def attempt_task_completion(self) -> bool:
        if self.rationality_level >= RATIONALITY_MAX:
            self.completed = True
            self.actually_completed = True
            self.p_defect = 0.0
            logger.debug(
                f"Utente {self.id}: razionale perfetto, "
                f"completamento garantito (ρ={self.rationality_level:.3f})"
            )
            return True
        delta_base = self.p_defect_base
        reputation_factor = 1.0 + BETA_REPUTATION * (1.0 - self.reputation)
        self.p_defect = min(0.95, delta_base * reputation_factor)
        logger.debug(
            f"Utente {self.id}: p_defect={self.p_defect:.3f} "
            f"(δ_base={delta_base:.3f}, R̂={self.reputation:.2f})"
        )
        defect_attempt = self._local_rng.random() < self.p_defect
        if not defect_attempt:
            self.completed = True
            self.actually_completed = True
            logger.debug(f"Utente {self.id}: task completato onestamente")
            return True
        detected = self._local_rng.random() < DETECTION_PROBABILITY
        if not detected:
            self.completed = True
            self.actually_completed = False
            logger.debug(
                f"Utente {self.id}: defezione non rilevata "
                f"(free-riding riuscito, p_detect={DETECTION_PROBABILITY:.2f})"
            )
            return True
        base_penalty = PENALTY_BASE_FACTOR * self.payment
        reputation_multiplier = 1.0 + (1.0 - self.reputation)
        adaptive_penalty = base_penalty * reputation_multiplier
        final_penalty = max(
            MIN_PENALTY_FLOOR * self.payment,
            adaptive_penalty
        )
        self.penalty_accumulated += final_penalty
        penalty_rep = PENALTY_REPUTATION_DECAY * self.reputation
        self.reputation = max(0.0, self.reputation - penalty_rep)
        self.completed = False
        self.actually_completed = False
        utility_final = self.payment - self.cost - final_penalty
        logger.info(
            f"Utente {self.id}: defezione rilevata e sanzionata, "
            f"sanzione={final_penalty:.2f}€ "
            f"(base={base_penalty:.2f}€ × {reputation_multiplier:.2f}, min={MIN_PENALTY_FLOOR*self.payment:.2f}€), "
            f"R̂ decay: {self.reputation + penalty_rep:.2f} → {self.reputation:.2f}, "
            f"u_i finale={utility_final:.2f}€ "
            f"({'negativa, deterrente attivo' if utility_final < 0 else 'non negativa'})"
        )
        return False

    def validate_utility_after_penalty(self) -> bool:
        if not hasattr(self, 'payment') or self.payment < 0:
            return True
        if not hasattr(self, 'cost') or self.cost < 0:
            return True
        net_payment = self.payment - self.penalty_accumulated
        utility = net_payment - self.cost
        TOLERANCE = 1e-6
        if utility < -TOLERANCE:
            if self.actually_completed:
                safety_margin = max(
                    IR_SAFETY_MARGIN,
                    IR_SAFETY_MARGIN * self.payment
                )
                max_allowed_penalty = max(
                    0.0,
                    self.payment - self.cost - safety_margin
                )
                if self.penalty_accumulated > max_allowed_penalty:
                    penalty_original = self.penalty_accumulated
                    self.penalty_accumulated = max_allowed_penalty
                    net_payment_corrected = self.payment - self.penalty_accumulated
                    utility_corrected = net_payment_corrected - self.cost
                    logger.warning(
                        f"Utente {self.id} (onesto): "
                        f"sanzione cappata per garantire vincolo ir, "
                        f"sanzione: {penalty_original:.2f}€ → {self.penalty_accumulated:.2f}€, "
                        f"u_i: {utility:.2f}€ → {utility_corrected:.2f}€"
                    )
                    return True
                else:
                    logger.error(
                        f"Utente {self.id} (onesto): "
                        f"violazione ir non correggibile (payment={self.payment:.2f}, "
                        f"cost={self.cost:.2f}, penalty={self.penalty_accumulated:.2f})"
                    )
                    return False
            else:
                logger.debug(
                    f"Utente {self.id} (defezione): u_i={utility:.2f}€ < 0, "
                    f"deterrente attivo"
                )
                return True
        return True

    def __repr__(self) -> str:
        base_repr = super().__repr__()
        return (
            f"{base_repr[:-1]}, "
            f"ρ̂={self.estimated_rationality:.3f} (N_ρ={self.rho_observation_count}), "
            f"R̂={self.reputation:.3f} (N_R={self.mdr_observation_count}))"
        )
    
    def test_bayesian_convergence(self, n_rounds: int = 100) -> Dict[str, Any]:
        mae_history = []
        rho_estimated_history = []
        backup_alpha = self.rho_alpha
        backup_beta = self.rho_beta
        backup_est = self.estimated_rationality
        self.rho_alpha = self._rho_prior_alpha
        self.rho_beta = self._rho_prior_beta
        for t in range(n_rounds):
            is_success = (np.random.random() < self.rationality_level)
            self._update_rationality_belief(is_success, strength=1.0)
            mae = abs(self.estimated_rationality - self.rationality_level)
            mae_history.append(mae)
            rho_estimated_history.append(self.estimated_rationality)
        mae_first_10 = np.mean(mae_history[:10])
        mae_last_10 = np.mean(mae_history[-10:])
        convergence_rate = (mae_first_10 - mae_last_10) / mae_first_10 if mae_first_10 > 0 else 0.0
        self.rho_alpha = backup_alpha
        self.rho_beta = backup_beta
        self.estimated_rationality = backup_est
        return {
            'mae_initial': float(mae_first_10),
            'mae_final': float(mae_last_10),
            'convergence_rate': float(convergence_rate),
            'converged': bool(convergence_rate > 0.5),
            'history_mae': mae_history,
            'history_rho_est': rho_estimated_history,
            'rho_true': self.rationality_level
        }


def check_adaptive_eligibility(
    user: AdaptiveUser, 
    task: TaskAdaptive, 
    current_time: float
) -> bool:
    if not user.is_eligible_at_time(current_time):
        logger.debug(
            f"Utente {user.id}: non idoneo (in blacklist) "
            f"fino a {user.blacklisted_until:.0f}"
        )
        return False
    if user.reputation < REPUTATION_ABSOLUTE_MIN_THRESHOLD:
        logger.debug(
            f"Utente {user.id}: escluso da hard filter, "
            f"R̂={user.reputation:.3f} < soglia minima {REPUTATION_ABSOLUTE_MIN_THRESHOLD:.3f}, "
            f"recidività eccessiva"
        )
        return False
    if task.quality_target is not None:
        required_rationality = 0.3 + 0.7 * task.quality_target
        if user.rationality_level < required_rationality:
            logger.debug(
                f"Utente {user.id} non idoneo per task {task.id} "
                f"(ρ={user.rationality_level:.2f} < "
                f"{required_rationality:.2f})"
            )
            return False
    if user.reputation < task.required_reliability:
        logger.debug(
            f"Utente {user.id} non idoneo per task {task.id} "
            f"(R̂={user.reputation:.3f} < "
            f"{task.required_reliability:.3f})"
        )
        return False
    return True


def test_convergence_all_profiles():
    profiles = [0.30, 0.50, 0.70, 0.90]
    results = []
    logger.info("Avvio test di convergenza bayesiana...")
    all_converged = True
    for rho in profiles:
        user = AdaptiveUser(user_id=1, x=0, y=0, cost_per_km=0.50, rationality_level=rho)
        res = user.test_bayesian_convergence(n_rounds=100)
        results.append((rho, res))
        if not res['converged']:
            logger.error(f"Convergenza fallita per ρ={rho}: rate={res['convergence_rate']:.2f}, mae={res['mae_final']:.3f}")
            all_converged = False
        if res['mae_final'] >= 0.15:
            logger.error(f"Mae troppo alto per ρ={rho}: {res['mae_final']:.3f}")
            all_converged = False
    if all_converged:
        logger.info("Test convergenza bayesiana superato per tutti i profili")
    else:
        logger.error("Test convergenza bayesiana fallito")
    return results


def diagnose_completion_paradox(results_phase2: Dict, results_phase3: Dict) -> Dict:
    logger.info("Diagnostica paradosso completion rate")
    if 'users' not in results_phase3 or not results_phase3['users']:
        logger.warning("Diagnostica paradosso: users non presente o vuoto in results_phase3")
        return {}
    if 'winners' not in results_phase3:
        logger.warning("Diagnostica paradosso: winners non presente in results_phase3")
        return {}
    all_users = results_phase3['users']
    all_winners = results_phase3['winners']
    excluded_users = sum(1 for u in all_users if u.reputation < 0.35)
    excluded_pct = excluded_users / len(all_users) * 100 if all_users else 0.0
    winner_reps = [u.reputation for u in all_winners]
    if not winner_reps:
        logger.warning("Diagnostica paradosso: lista vincitori vuota")
        winner_rep_mean = np.nan
        winner_rep_min = np.nan
        opp_winners_pct = np.nan
        defections_by_profile = {}
    else:
        winner_rep_mean = np.mean(winner_reps)
        winner_rep_min = np.min(winner_reps)
        opp_winners = sum(1 for u in all_winners if u.rationality_level < 0.45)
        opp_winners_pct = opp_winners / len(all_winners) * 100 if all_winners else 0.0
        defections_by_profile = {}
        for u in all_winners:
            profile = u.honesty_profile
            if not u.actually_completed:
                defections_by_profile[profile] = defections_by_profile.get(profile, 0) + 1
    tasks_f2 = results_phase2['total_tasks_allocated']
    tasks_f3 = results_phase3['total_tasks_allocated']
    results = {
        'excluded_pct': excluded_pct,
        'winner_rep_mean': winner_rep_mean,
        'winner_rep_min': winner_rep_min,
        'opportunistic_pct': opp_winners_pct,
        'defections_by_profile': defections_by_profile,
        'tasks_f2': tasks_f2,
        'tasks_f3': tasks_f3,
        'gap': tasks_f3 - tasks_f2
    }
    logger.info(f"  Hard filter: {excluded_pct:.1f}% utenti esclusi")
    logger.info(f"  Reputazione vincitori: media={winner_rep_mean:.3f}, min={winner_rep_min:.3f}")
    logger.info(f"  Opportunisti vincitori: {opp_winners_pct:.1f}%")
    logger.info(f"  Task allocati: fase2={tasks_f2}, fase3={tasks_f3} (gap={tasks_f3-tasks_f2})")
    return results


def sensitivity_analysis_quality_target():
    param_grid = [(0.2, 0.8), (0.3, 0.7), (0.4, 0.6)]
    results = []
    logger.info("Avvio sensitivity analysis (simulazione stub)")
    for intercept, slope in param_grid:
        logger.info(f"  Test parametri: intercept={intercept}, slope={slope}")
        results.append({
            'params': (intercept, slope),
            'breakdown': 0.0,
            'completion': 0.0,
            'utility': 0.0
        })
    logger.info("Sensitivity analysis completata")
    return results


def diagnose_reputation_distribution(
    users: List[AdaptiveUser], 
    winners: List[AdaptiveUser]
) -> Dict[str, Any]:
    logger.info("Avvio diagnostica distribuzione reputazioni")
    pop_reps = [u.reputation for u in users]
    win_reps = [u.reputation for u in winners]
    if not pop_reps:
        pop_reps = [np.nan]
    if not win_reps:
        win_reps = [np.nan]
    stats = {
        'pop_mean': np.nanmean(pop_reps),
        'pop_median': np.nanmedian(pop_reps),
        'pop_p25': np.nanpercentile(pop_reps, 25),
        'win_mean': np.nanmean(win_reps),
        'win_median': np.nanmedian(win_reps),
        'win_p25': np.nanpercentile(win_reps, 25),
        'raw_pop_reps': pop_reps,
        'raw_win_reps': win_reps
    }
    logger.info(f"  Popolazione: media R={stats['pop_mean']:.3f}")
    logger.info(f"  Vincitori: media R={stats['win_mean']:.3f}")
    return stats
