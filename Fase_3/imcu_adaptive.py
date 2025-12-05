from __future__ import annotations
import math
import logging
import numpy as np
import time
from typing import Dict, List, Optional, Set, Tuple, Any, cast
import sys
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
    from Fase_3.classes_adaptive import (
        AdaptiveUser, 
        TaskAdaptive, 
        REPUTATION_ABSOLUTE_MIN_THRESHOLD
    )
except ImportError as e:
    raise ImportError(f"Impossibile importare classes_adaptive: {e}")

try:
    from Fase_1.imcu import (
        IMCUAuction, 
        IMCUDiagnostics, 
        _unique_tasks,
        SelectionStepLog,
        PaymentStepLog,
        total_value_of_users
    )
    import Fase_1.imcu as imcu_base
except ImportError as e:
    raise ImportError(f"Impossibile importare fase 1 imcu: {e}")

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def _validate_user_adaptive(user: AdaptiveUser) -> None:
    imcu_base._validate_user(user)
    required_attrs = {
        'estimated_rationality': (0.0, 1.0, float),
        'reputation': (0.0, 1.0, float),
        'rho_alpha': (0.0, float('inf'), float),
        'rho_beta': (0.0, float('inf'), float),
        'reputation_reliability': (0.0, 1.0, float),
        'reputation_quality': (0.0, 1.0, float),
    }
    for attr, (min_val, max_val, expected_type) in required_attrs.items():
        if not hasattr(user, attr):
            raise AttributeError(f"Utente {user.id}: attributo '{attr}' mancante")
        val = getattr(user, attr)
        if not isinstance(val, expected_type):
            raise TypeError(f"Utente {user.id}: '{attr}' deve essere {expected_type.__name__}")
        if not (min_val <= val <= max_val):
            raise ValueError(f"Utente {user.id}: '{attr}'={val} fuori range [{min_val}, {max_val}]")
    if user.mdr_observation_count == 0 and user.reputation < 0.99:
        raise ValueError(f"Utente {user.id}: viola trust-by-default (reputazione={user.reputation:.3f})")

def _validate_users_adaptive(users: Optional[List[AdaptiveUser]]) -> List[AdaptiveUser]:
    if users is None:
        raise TypeError("users non puo essere none")
    if not isinstance(users, list):
        raise TypeError(f"users deve essere lista, ricevuto: {type(users).__name__}")
    valid_users: List[AdaptiveUser] = []
    for u in users:
        if not isinstance(u, AdaptiveUser):
            raise TypeError(f"Utente deve essere AdaptiveUser, ricevuto: {type(u).__name__}")
        _validate_user_adaptive(u)
        valid_users.append(u)
    if not valid_users:
        logger.warning("Lista users validata vuota")
    return sorted(valid_users, key=lambda u: u.id)


class IMCUAuctionAdaptive(IMCUAuction):
    def __init__(
        self,
        all_users: List[AdaptiveUser],
        all_tasks: List[TaskAdaptive],
        current_time: float,
        debug: bool = True
    ):
        self._original_users: List[AdaptiveUser] = _validate_users_adaptive(all_users)
        self._all_tasks_map: Dict[int, TaskAdaptive] = {t.id: t for t in all_tasks}
        self._current_time: float = current_time
        self._eligible_users: List[AdaptiveUser] = self._filter_eligible_users(
            self._original_users,
            self._all_tasks_map,
            self._current_time
        )
        self._logs_payment_base: Dict[int, float] = {}
        self._logs_payment_final: Dict[int, float] = {}
        logger.info(
            f"Asta imcu adaptive: {len(self._eligible_users)}/{len(self._original_users)} "
            f"utenti idonei per {len(all_tasks)} task"
        )
        super().__init__(users=self._eligible_users, debug=debug, verify_properties=True)

    def _filter_eligible_users(
        self, 
        users: List[AdaptiveUser], 
        tasks_map: Dict[int, TaskAdaptive],
        current_time: float
    ) -> List[AdaptiveUser]:
        import copy
        eligible_auction_users: List[AdaptiveUser] = []
        total_tasks_before = 0
        total_tasks_after = 0
        for u in users:
            candidate_tasks = _unique_tasks(u.tasks)
            total_tasks_before += len(candidate_tasks)
            eligible_tasks_for_user: List[TaskAdaptive] = []
            for task in candidate_tasks:
                task_obj = tasks_map.get(task.id)
                if not task_obj or not isinstance(task_obj, TaskAdaptive):
                    continue
                if not u.is_eligible_at_time(current_time):
                    continue
                if task_obj.quality_target is not None:
                    required_rationality = 0.3 + 0.7 * task_obj.quality_target
                    if u.estimated_rationality < required_rationality:
                        logger.debug(
                            f"Utente {u.id}: task {task_obj.id} filtrato "
                            f"(rho_stima={u.estimated_rationality:.2f} < {required_rationality:.2f})"
                        )
                        continue
                if u.reputation < REPUTATION_ABSOLUTE_MIN_THRESHOLD:
                    logger.debug(
                        f"Utente {u.id} escluso: reputazione={u.reputation:.2f} < {REPUTATION_ABSOLUTE_MIN_THRESHOLD}"
                    )
                    continue
                eligible_tasks_for_user.append(task_obj)
            total_tasks_after += len(eligible_tasks_for_user)
            if eligible_tasks_for_user:
                u_copy = copy.copy(u)
                u_copy.set_tasks(eligible_tasks_for_user)
                eligible_auction_users.append(u_copy)
        logger.info(
            f"Filtro eligibilita: {len(eligible_auction_users)}/{len(users)} utenti ammessi, "
            f"{total_tasks_after}/{total_tasks_before} task idonei"
        )
        return eligible_auction_users

    def _selection_phase(self) -> List[AdaptiveUser]:
        winners: List[AdaptiveUser] = []
        remaining: List[AdaptiveUser] = list(self.users)
        covered: Set[int] = set()
        iteration = 0
        logger.info(f"Selezione gap: {len(remaining)} utenti idonei in competizione")
        while True:
            iteration += 1
            best_candidate: Optional[AdaptiveUser] = None
            best_gain = float("-inf")
            candidates_log: List[Dict[str, float]] = []
            for u in remaining:
                mv = self._marginal_value(u, covered, count_for="sel")
                effective_bid = u.get_effective_bid()
                gain = mv - effective_bid
                if self.debug:
                    candidates_log.append({
                        "id": float(u.id),
                        "mv": float(mv),
                        "bid_base": float(u.bid),
                        "effective_bid": float(effective_bid),
                        "reputation": float(u.reputation),
                        "gain": float(gain)
                    })
                should_update = (
                    (gain > best_gain) or
                    (best_candidate is None) or
                    (math.isclose(gain, best_gain, abs_tol=self.EPSILON) and u.id < best_candidate.id)
                )
                if should_update:
                    best_candidate = u
                    best_gain = gain
            if best_candidate is None:
                if self.debug:
                    self._logs_selection.append(SelectionStepLog(
                        iteration=iteration, covered_count_before=len(covered),
                        candidates=candidates_log, chosen_user_id=None,
                        chosen_gain=float(best_gain), covered_count_after=len(covered)
                    ))
                break
            if best_gain > self.EPSILON:
                winners.append(best_candidate)
                remaining.remove(best_candidate)
                self._add_user_tasks_to_covered(best_candidate, covered)
                if self.debug:
                    self._logs_selection.append(SelectionStepLog(
                        iteration=iteration,
                        covered_count_before=len(covered) - len(_unique_tasks(best_candidate.tasks)),
                        candidates=candidates_log,
                        chosen_user_id=best_candidate.id,
                        chosen_gain=float(best_gain),
                        covered_count_after=len(covered)
                    ))
            else:
                if self.debug:
                    self._logs_selection.append(SelectionStepLog(
                        iteration=iteration,
                        covered_count_before=len(covered),
                        candidates=candidates_log,
                        chosen_user_id=None,
                        chosen_gain=float(best_gain),
                        covered_count_after=len(covered)
                    ))
                break
        logger.info(f"Selezione completata: {len(winners)} vincitori")
        return winners

    def _payment_phase(self, winners: List[AdaptiveUser]) -> Dict[int, float]:
        payments: Dict[int, float] = {}
        logger.info(f"Pagamento gap: calcolo per {len(winners)} vincitori")
        self._logs_payment_base.clear()
        self._logs_payment_final.clear()
        for w in winners:
            others: List[AdaptiveUser] = [u for u in self.users if u.id != w.id]
            critical_base = w.get_effective_bid()
            temp_covered: Set[int] = set()
            prefix_T: List[AdaptiveUser] = []
            steps_log: List[Dict[str, float]] = []
            k_last = 0
            vi_seq, vj_seq, bj_seq, cand_seq = [], [], [], []
            while True:
                best_competitor: Optional[AdaptiveUser] = None
                best_competitor_gain = float("-inf")
                for c in others:
                    if c in prefix_T:
                        continue
                    mv_c = self._marginal_value(c, temp_covered, count_for="pay")
                    effective_bid_c = c.get_effective_bid()
                    gain_c = mv_c - effective_bid_c
                    should_update = (
                        (gain_c > best_competitor_gain) or
                        (best_competitor is None) or
                        (math.isclose(gain_c, best_competitor_gain, abs_tol=self.EPSILON) and 
                         c.id < best_competitor.id)
                    )
                    if should_update:
                        best_competitor = c
                        best_competitor_gain = gain_c
                if best_competitor is None or best_competitor_gain <= self.EPSILON:
                    v_i_after = self._marginal_value(w, temp_covered, count_for="pay")
                    critical_base = max(critical_base, v_i_after)
                    if self.debug:
                        self._logs_payment.append(PaymentStepLog(
                            winner_id=w.id, steps=steps_log,
                            after_threshold=float(v_i_after),
                            final_payment=critical_base,
                            k_last=k_last, vi_sequence=vi_seq,
                            vj_sequence=vj_seq, bj_sequence=bj_seq,
                            cand_sequence=cand_seq
                        ))
                    break
                v_i_T = self._marginal_value(w, temp_covered, count_for="pay")
                v_j_T = self._marginal_value(best_competitor, temp_covered, count_for="pay")
                effective_bid_j = best_competitor.get_effective_bid()
                cand_j = min(v_i_T - v_j_T + effective_bid_j, v_i_T)
                critical_base = max(critical_base, cand_j)
                if best_competitor_gain > self.EPSILON:
                    k_last = len(prefix_T) + 1
                if self.debug:
                    steps_log.append({
                        "pos": float(len(prefix_T) + 1), "v_i_T": float(v_i_T),
                        "comp_id": float(best_competitor.id), "v_j_T": float(v_j_T),
                        "b_j_eff": float(effective_bid_j),
                        "cand_j": float(cand_j), "critical_so_far": float(critical_base)
                    })
                    vi_seq.append(float(v_i_T))
                    vj_seq.append(float(v_j_T))
                    bj_seq.append(float(effective_bid_j))
                    cand_seq.append(float(cand_j))
                prefix_T.append(best_competitor)
                self._add_user_tasks_to_covered(best_competitor, temp_covered)
            max_budget = float('inf')
            for task in _unique_tasks(w.tasks):
                if hasattr(task, 'budget') and task.budget is not None:
                    max_budget = min(max_budget, task.budget)
            if max_budget < float('inf') and critical_base > max_budget:
                logger.warning(
                    f"Utente {w.id}: pagamento limitato da budget task "
                    f"({critical_base:.2f} -> {max_budget:.2f})"
                )
                critical_base = max_budget
            final_payment = w.get_incentive_payment(critical_base)
            payments[w.id] = final_payment
            self._logs_payment_base[w.id] = critical_base
            self._logs_payment_final[w.id] = final_payment
        logger.info("Pagamento completato")
        return payments

    def _extended_diagnostics_adaptive(
        self, 
        winners: List[AdaptiveUser], 
        payments: Dict[int, float]
    ) -> Dict[str, Any]:
        diag: Dict[str, Any] = {}
        all_eligible = self.users
        rho_true: List[float] = [float(u.rationality_level) for u in all_eligible]
        rho_est: List[float] = [float(u.estimated_rationality) for u in all_eligible]
        if rho_true:
            diag['avg_rho_true_eligible'] = float(np.mean(rho_true))
            diag['avg_rho_estimated_eligible'] = float(np.mean(rho_est))
            mae_rho = np.mean(np.abs(np.array(rho_true) - np.array(rho_est)))
            diag['mae_rho_estimation'] = float(mae_rho)
            variances: List[float] = []
            for u in all_eligible:
                alpha, beta = float(u.rho_alpha), float(u.rho_beta)
                total = alpha + beta
                if total > 0:
                    variance = (alpha * beta) / ((total ** 2) * (total + 1))
                    variances.append(variance)
            if variances:
                diag['avg_rho_estimation_variance'] = float(np.mean(variances))
                diag['avg_rho_estimation_std'] = float(np.mean(np.sqrt(variances)))
        rep_agg: List[float] = [float(u.reputation) for u in all_eligible]
        rep_r: List[float] = [float(u.reputation_reliability) for u in all_eligible]
        rep_q: List[float] = [float(u.reputation_quality) for u in all_eligible]
        if rep_agg:
            diag['avg_reputation_agg_eligible'] = float(np.mean(rep_agg))
            diag['avg_reputation_reliability_eligible'] = float(np.mean(rep_r))
            diag['avg_reputation_quality_eligible'] = float(np.mean(rep_q))
            diag['std_reputation_agg_eligible'] = float(np.std(rep_agg))
            diag['min_reputation_agg_eligible'] = float(np.min(rep_agg))
            diag['max_reputation_agg_eligible'] = float(np.max(rep_agg))
        base_p: List[float] = list(self._logs_payment_base.values())
        final_p: List[float] = list(self._logs_payment_final.values())
        if base_p:
            diag['sum_payment_base'] = float(np.sum(base_p))
            diag['sum_payment_final'] = float(np.sum(final_p))
            total_incentive = diag['sum_payment_final'] - diag['sum_payment_base']
            diag['total_incentive_bonus_malus'] = float(total_incentive)
            diag['avg_incentive_pct_change'] = float(
                (total_incentive / max(1e-9, diag['sum_payment_base']))
            )
            incentives = [final_p[i] - base_p[i] for i in range(len(base_p))]
            diag['avg_incentive_per_winner'] = float(np.mean(incentives))
            diag['std_incentive_per_winner'] = float(np.std(incentives))
            diag['max_bonus'] = float(max(incentives))
            diag['max_malus'] = float(min(incentives))
        completed_tasks: List[TaskAdaptive] = []
        seen_task_ids: Set[int] = set()
        for w in winners:
            if w.actually_completed:
                for t in _unique_tasks(w.tasks):
                    if t.id not in seen_task_ids:
                        completed_tasks.append(cast(TaskAdaptive, t))
                        seen_task_ids.add(t.id)
        v_eff_expost = sum(float(t.value) for t in completed_tasks)
        sumP_final = sum(payments.values())
        u0_expost = v_eff_expost - sumP_final
        eligible_task_ids = {t.id for u in self.users for t in _unique_tasks(u.tasks)}
        eligible_tasks_value = sum(float(t.value) for t in self._all_tasks_map.values() if t.id in eligible_task_ids)
        diag['v_eff_expost'] = float(v_eff_expost)
        diag['sumP_final_expost'] = float(sumP_final)
        diag['u0_expost'] = float(u0_expost)
        diag['profitability_expost'] = bool(u0_expost >= -1e-9)
        diag['v_mech'] = float(eligible_tasks_value)
        ir_violations = 0
        ir_violation_details: List[Dict[str, float]] = []
        for w in winners:
            final_payment = payments.get(w.id, w.payment)
            u_i = final_payment - w.cost - w.penalty_accumulated
            if u_i < -1e-6:
                ir_violations += 1
                ir_violation_details.append({
                    'user_id': w.id,
                    'final_payment': float(final_payment),
                    'cost': float(w.cost),
                    'penalty': float(w.penalty_accumulated),
                    'utility': float(u_i),
                    'reputation': float(w.reputation)
                })
        ir_violation_rate = ir_violations / max(1, len(winners))
        diag['ir_violations_expost'] = int(ir_violations)
        diag['ir_violation_rate_expost'] = float(ir_violation_rate)
        diag['ir_violation_details'] = ir_violation_details
        actual_compl = sum(1 for w in winners if w.actually_completed)
        actual_rate_winners = actual_compl / max(1, len(winners))
        diag['actual_completion_rate_winners'] = float(actual_rate_winners)
        total_tasks_available = len(
            {t.id for u in all_eligible for t in _unique_tasks(u.tasks)}
        )
        completion_rate_tasks = len(seen_task_ids) / max(1, total_tasks_available)
        diag['completion_rate_tasks'] = float(completion_rate_tasks)
        deficit = (u0_expost < 0)
        ir_breakdown = (ir_violation_rate > 0.05)
        service_breakdown = (completion_rate_tasks < 0.90)
        severity = (
            4.0 * deficit +
            3.0 * ir_breakdown +
            1.0 * service_breakdown
        )
        diag['mechanism_health_expost'] = {
            'deficit_breakdown': bool(deficit),
            'ir_breakdown': bool(ir_breakdown),
            'service_breakdown': bool(service_breakdown),
            'severity_weighted': float(severity),
            'severity_max': 8.0,
            'health_score': float((8.0 - severity) / 8.0),
            'u0_eff': float(u0_expost),
            'ir_violation_rate': float(ir_violation_rate),
            'completion_rate_tasks': float(completion_rate_tasks),
        }
        completed_tasks_map: Dict[int, List[int]] = {}
        for w in winners:
            if w.actually_completed:
                task_ids = [t.id for t in _unique_tasks(w.tasks)]
                if task_ids:
                    completed_tasks_map[w.id] = task_ids
        diag['completed_tasks_by_winner'] = completed_tasks_map
        logger.info(
            f"Diagnostica gap: u0={u0_expost:.2f} euro, violazioni ir={ir_violation_rate*100:.1f}%, "
            f"completamento={completion_rate_tasks*100:.1f}%, salute={(8-severity)/8*100:.1f}%"
        )
        return diag

    def run(self) -> Tuple[Set[int], Dict[int, float], IMCUDiagnostics]:
        t_start = time.perf_counter()
        logger.info("Step 1: selezione gap-select")
        t0 = time.perf_counter()
        winners = self._selection_phase()
        t1 = time.perf_counter()
        logger.info(f"  Selezionati {len(winners)} vincitori ({t1-t0:.3f}s)")
        logger.info("Step 2: pagamento gap-incentive")
        payments = self._payment_phase(winners)
        t2 = time.perf_counter()
        logger.info(f"  Pagamenti calcolati ({t2-t1:.3f}s)")
        winners_set: Set[int] = {u.id for u in winners}
        logger.info("Step 3: simulazione completamento")
        completion_stats = {
            'completed': 0,
            'defected_detected': 0,
            'defected_undetected': 0
        }
        for w in winners:
            w.payment = payments.get(w.id, 0.0)
            w.utility = w.payment - w.cost
            w.is_winner = True
            w.attempt_task_completion()
            if w.actually_completed:
                completion_stats['completed'] += 1
            elif w.completed and not w.actually_completed:
                completion_stats['defected_undetected'] += 1
            elif not w.completed:
                completion_stats['defected_detected'] += 1
        logger.info(
            f"  Completati: {completion_stats['completed']}, "
            f"defezioni rilevate: {completion_stats['defected_detected']}, "
            f"free-riding: {completion_stats['defected_undetected']}"
        )
        logger.info("Step 4: validazione vincolo ir")
        ir_violations = 0
        for w in winners:
            final_payment = payments.get(w.id, 0.0)
            utility_after_all = final_payment - w.cost - w.penalty_accumulated
            if utility_after_all < -1e-6:
                logger.warning(
                    f"  Utente {w.id}: violazione ir (utilita={utility_after_all:.2f} euro)"
                )
                ir_violations += 1
        if ir_violations > 0:
            logger.warning(
                f"  {ir_violations}/{len(winners)} violazioni ir "
                f"({ir_violations/len(winners)*100:.1f}%)"
            )
        else:
            logger.info("  Nessuna violazione ir rilevata")
        logger.info("Step 5: apprendimento delegato a orchestratore fase 3")
        logger.info("Step 6: diagnostica estesa")
        vS_exante = total_value_of_users(winners)
        sumP_final = sum(payments.values())
        diagnostics = IMCUDiagnostics(
            winners_count=len(winners),
            covered_tasks_count=len({t.id for u in winners for t in _unique_tasks(u.tasks)}),
            payments_sum=sumP_final,
            platform_value_vS=vS_exante,
            platform_utility_u0=vS_exante - sumP_final,
            selection_time_s=(t1 - t0),
            payment_time_s=(t2 - t1),
            total_time_s=(time.perf_counter() - t_start),
            mv_calls_selection=self._mv_calls_selection,
            mv_calls_payment=self._mv_calls_payment,
            logs_selection=self._logs_selection if self.debug else [],
            logs_payment=self._logs_payment if self.debug else []
        )
        diagnostics.property_checks['AdaptiveGAPMetrics'] = \
            self._extended_diagnostics_adaptive(winners, payments)
        logger.info(f"Asta imcu adaptive completata ({time.perf_counter() - t_start:.3f}s)")
        return winners_set, payments, diagnostics


def run_imcu_auction_adaptive(
    users: List[AdaptiveUser],
    tasks: List[TaskAdaptive],
    current_time: float,
    debug: bool = True,
    debug_level: str = "summary"
) -> Tuple[Set[int], Dict[int, float], Dict[str, Any]]:
    if debug_level not in ("none", "summary", "full"):
        raise ValueError(f"debug_level non valido: '{debug_level}'")
    auction = IMCUAuctionAdaptive(
        all_users=users,
        all_tasks=tasks,
        current_time=current_time,
        debug=debug
    )
    winners_set, payments, diag_obj = auction.run()
    diagnostics: Dict[str, Any] = {
        "winners_count": diag_obj.winners_count,
        "covered_tasks_count": diag_obj.covered_tasks_count,
        "payments_sum": diag_obj.payments_sum,
        "platform_value_vS": diag_obj.platform_value_vS,
        "platform_utility_u0": diag_obj.platform_utility_u0,
        "selection_time_s": diag_obj.selection_time_s,
        "payment_time_s": diag_obj.payment_time_s,
        "total_time_s": diag_obj.total_time_s,
        "mv_calls_selection": diag_obj.mv_calls_selection,
        "mv_calls_payment": diag_obj.mv_calls_payment,
        "property_checks": diag_obj.property_checks,
        "n_users_original": len(auction._original_users),
        "n_users_eligible": len(auction._eligible_users),
        "m_tasks": len(auction._all_tasks_map),
    }
    if debug:
        if debug_level == "full":
            diagnostics["logs_selection"] = [s.__dict__ for s in diag_obj.logs_selection]
            diagnostics["logs_payment"] = [s.__dict__ for s in diag_obj.logs_payment]
        elif debug_level == "summary":
            diagnostics["logs_selection_count"] = len(diag_obj.logs_selection)
            diagnostics["logs_payment_count"] = len(diag_obj.logs_payment)
    return winners_set, payments, diagnostics
