from __future__ import annotations

import os, sys
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from typing import List, Set, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import time
import math
import json
import csv
import random
import logging
logger = logging.getLogger(__name__)
from classes import User, Task

@dataclass
class SelectionStepLog:
    iteration: int
    covered_count_before: int
    candidates: List[Dict[str, float]]
    chosen_user_id: Optional[int]
    chosen_gain: float
    covered_count_after: int

@dataclass
class PaymentStepLog:
    winner_id: int
    steps: List[Dict[str, float]]
    after_threshold: float
    final_payment: float
    k_last: int = 0
    vi_sequence: List[float] = field(default_factory=list)
    vj_sequence: List[float] = field(default_factory=list)
    bj_sequence: List[float] = field(default_factory=list)
    cand_sequence: List[float] = field(default_factory=list)

@dataclass
class IMCUDiagnostics:
    winners_count: int
    covered_tasks_count: int
    payments_sum: float
    platform_value_vS: float
    platform_utility_u0: float
    selection_time_s: float
    payment_time_s: float
    total_time_s: float
    mv_calls_selection: int
    mv_calls_payment: int
    logs_selection: List[SelectionStepLog] = field(default_factory=list)
    logs_payment: List[PaymentStepLog] = field(default_factory=list)
    property_checks: Dict[str, Any] = field(default_factory=dict)

def _validate_task(task: Task) -> None:
    if task is None:
        raise TypeError("Task fornito è None")
    if not hasattr(task, "id") or not isinstance(task.id, int):
        raise TypeError("Task.id deve essere un intero")
    if not hasattr(task, "value"):
        raise TypeError("Task.value non presente")
    try:
        val = float(task.value)
    except Exception as exc:
        raise TypeError("Task.value deve essere float") from exc
    if val < 0:
        raise ValueError(f"Task.value deve essere non negativo, ricevuto: {val}")

def _validate_user(user: User) -> None:
    if user is None:
        raise TypeError("Utente fornito è None")
    if not hasattr(user, "id") or not isinstance(user.id, int):
        raise TypeError("User.id deve essere un intero")
    if not hasattr(user, "bid"):
        raise TypeError("User.bid non presente")
    try:
        b = float(user.bid)
    except Exception as exc:
        raise TypeError("User.bid deve essere float") from exc
    if b < 0:
        raise ValueError(f"User.bid deve essere non negativo, ricevuto: {b}")
    if not hasattr(user, "tasks") or user.tasks is None:
        raise TypeError("User.tasks non presente o None")
    if not isinstance(user.tasks, list):
        raise TypeError(f"User.tasks deve essere lista, ricevuto: {type(user.tasks)}")
    for t in user.tasks:
        _validate_task(t)

def _validate_users(users: Optional[List[User]]) -> List[User]:
    if users is None:
        raise TypeError("Parametro 'users' è None")
    if not isinstance(users, list):
        raise TypeError(f"'users' deve essere lista, ricevuto: {type(users)}")
    for u in users:
        _validate_user(u)
    return sorted(users, key=lambda u: u.id)

def _unique_tasks(tasks: List[Task]) -> List[Task]:
    return list({t.id: t for t in tasks}.values())

def total_value_of_users(users: List[User]) -> float:
    covered: Dict[int, Task] = {}
    for u in users:
        for t in _unique_tasks(u.tasks):
            covered.setdefault(t.id, t)
    return float(sum(float(t.value) for t in covered.values()))

def _delta_v_for_user(user: User, covered_ids: Set[int]) -> float:
    seen = set()
    mv = 0.0
    for t in user.tasks:
        if t.id in seen:
            continue
        seen.add(t.id)
        if t.id not in covered_ids:
            mv += float(t.value)
    return float(mv)

def empirical_submodularity_check(users: List[User], trials: int = 100, seed: int = 42) -> Dict[str, Any]:
    TOLERANCE = 1e-9
    rnd = random.Random(seed)
    violations = 0
    examples = []
    if len(users) < 3:
        return {"violations": 0, "trials": 0, "examples": []}
    all_ids = [u.id for u in users]
    task_map = {u.id: set(t.id for t in _unique_tasks(u.tasks)) for u in users}
    def covered_of(S_ids: Set[int]) -> Set[int]:
        cov = set()
        for uid in S_ids:
            cov |= task_map[uid]
        return cov
    for _ in range(trials):
        T_size = rnd.randint(1, max(1, len(users) - 1))
        T_ids = set(rnd.sample(all_ids, T_size))
        i_id = rnd.choice([x for x in all_ids if x not in T_ids])
        if len(T_ids) == 1:
            continue
        S_size = rnd.randint(1, len(T_ids) - 1)
        S_ids = set(rnd.sample(list(T_ids), S_size))
        cov_S = covered_of(S_ids)
        cov_T = covered_of(T_ids)
        u_i = next(u for u in users if u.id == i_id)
        dvS = _delta_v_for_user(u_i, cov_S)
        dvT = _delta_v_for_user(u_i, cov_T)
        if dvS < dvT - TOLERANCE:
            violations += 1
            if len(examples) < 5:
                examples.append({"user_id": int(i_id), "S_size": int(len(S_ids)), "T_size": int(len(T_ids)), "delta_v_S": float(dvS), "delta_v_T": float(dvT)})
    return {"violations": int(violations), "trials": int(trials), "examples": examples}

class IMCUAuction:
    EPSILON: float = 1e-9
    SUBMODULARITY_TEST_TRIALS: int = 100
    SUBMODULARITY_TEST_SEED: int = 42
    MONOTONICITY_TEST_DELTA_FACTOR: float = 1e-3
    MONOTONICITY_TEST_DELTA_MIN: float = 1e-6    
    TRUTHFULNESS_TEST_SAMPLES: int = 10
    
    def __init__(self, users: List[User], debug: bool = True, verify_properties: bool = True):
        self._test_rng = random.Random(self.SUBMODULARITY_TEST_SEED)
        self.users: List[User] = _validate_users(users)
        self.debug = debug
        self.verify_properties = verify_properties
        self._mv_calls_selection = 0
        self._mv_calls_payment = 0
        self._logs_selection: List[SelectionStepLog] = []
        self._logs_payment: List[PaymentStepLog] = []
    
    def _marginal_value(self, user: User, covered_task_ids: Set[int], count_for: str) -> float:
        if count_for == "sel":
            self._mv_calls_selection += 1
        elif count_for == "pay":
            self._mv_calls_payment += 1
        mv = 0.0
        seen = set()
        for t in user.tasks:
            if t.id in seen:
                continue
            seen.add(t.id)
            if t.id not in covered_task_ids:
                mv += float(t.value)
        return float(mv)
    
    def _add_user_tasks_to_covered(self, user: User, covered_task_ids: Set[int]) -> None:
        for t in _unique_tasks(user.tasks):
            covered_task_ids.add(t.id)
    
    def _selection_phase(self) -> List[User]:
        winners: List[User] = []
        remaining: List[User] = list(self.users)
        covered: Set[int] = set()
        iteration = 0
        while True:
            iteration += 1
            best_candidate = None
            best_gain = float("-inf")
            candidates_log = []
            for u in remaining:
                mv = self._marginal_value(u, covered, count_for="sel")
                gain = mv - float(u.bid)
                candidates_log.append({"id": float(u.id), "mv": float(mv), "bid": float(u.bid), "gain": float(gain)})
                should_update = ((gain > best_gain) or (best_candidate is None) or (math.isclose(gain, best_gain, rel_tol=0, abs_tol=self.EPSILON) and u.id < best_candidate.id))
                if should_update:
                    best_candidate = u
                    best_gain = gain
            if best_candidate is None:
                break
            covered_before = len(covered)
            if best_gain > self.EPSILON:
                winners.append(best_candidate)
                remaining.remove(best_candidate)
                self._add_user_tasks_to_covered(best_candidate, covered)
                covered_after = len(covered)
                if self.debug:
                    self._logs_selection.append(SelectionStepLog(iteration=iteration, covered_count_before=covered_before, candidates=candidates_log, chosen_user_id=best_candidate.id, chosen_gain=float(best_gain), covered_count_after=covered_after))
            else:
                if self.debug:
                    self._logs_selection.append(SelectionStepLog(iteration=iteration, covered_count_before=covered_before, candidates=candidates_log, chosen_user_id=None, chosen_gain=float(best_gain), covered_count_after=covered_before))
                break
        if self.debug:
            logger.info(f"  [Selezione] Completata in {iteration-1} iterazioni. Input: {len(self.users)} utenti. Output: {len(winners)} vincitori, {len(covered)} task coperti")
        return winners
    
    def _payment_phase(self, winners: List[User]) -> Dict[int, float]:
        payments: Dict[int, float] = {}
        n_winners = len(winners)
        mv_calls_start = self._mv_calls_payment 
        if self.debug:
            logger.info(f"  [Pagamento] Avvio calcolo per {n_winners} vincitori")
        for w in winners:
            others: List[User] = [u for u in self.users if u.id != w.id]
            critical = float(w.bid)
            temp_covered: Set[int] = set()
            prefix_T: List[User] = []
            steps_log: List[Dict[str, float]] = []
            k_last = 0
            vi_sequence: List[float] = []
            vj_sequence: List[float] = []
            bj_sequence: List[float] = []
            cand_sequence: List[float] = []
            while True:
                best_competitor = None
                best_competitor_gain = float("-inf")
                for c in others:
                    if c in prefix_T:
                        continue
                    mv_c = self._marginal_value(c, temp_covered, count_for="pay")
                    gain_c = mv_c - float(c.bid)
                    should_update = ((gain_c > best_competitor_gain) or (best_competitor is None) or (math.isclose(gain_c, best_competitor_gain, rel_tol=0, abs_tol=self.EPSILON) and c.id < best_competitor.id))
                    if should_update:
                        best_competitor = c
                        best_competitor_gain = gain_c
                if best_competitor is None or best_competitor_gain <= self.EPSILON:
                    v_i_after = self._marginal_value(w, temp_covered, count_for="pay")
                    critical = max(critical, v_i_after)
                    after_threshold = float(v_i_after)
                    final_payment = float(critical)
                    if self.debug:
                        self._logs_payment.append(PaymentStepLog(winner_id=w.id, steps=steps_log, after_threshold=after_threshold, final_payment=final_payment, k_last=int(k_last), vi_sequence=vi_sequence, vj_sequence=vj_sequence, bj_sequence=bj_sequence, cand_sequence=cand_sequence))
                    break
                v_i_T = self._marginal_value(w, temp_covered, count_for="pay")
                v_j_T = self._marginal_value(best_competitor, temp_covered, count_for="pay")
                cand_j = min(v_i_T - v_j_T + float(best_competitor.bid), v_i_T)
                critical = max(critical, cand_j)
                if best_competitor_gain > self.EPSILON:
                    k_last = len(prefix_T) + 1
                if self.debug:
                    steps_log.append({"pos": float(len(prefix_T) + 1), "v_i_T": float(v_i_T), "comp_id": float(best_competitor.id), "v_j_T": float(v_j_T), "b_j": float(best_competitor.bid), "cand_j": float(cand_j), "critical_so_far": float(critical)})
                vi_sequence.append(float(v_i_T))
                vj_sequence.append(float(v_j_T))
                bj_sequence.append(float(best_competitor.bid))
                cand_sequence.append(float(cand_j))
                prefix_T.append(best_competitor)
                self._add_user_tasks_to_covered(best_competitor, temp_covered)
            payments[w.id] = float(critical)
        mv_calls_end = self._mv_calls_payment
        total_payment = sum(payments.values())
        avg_payment = total_payment / n_winners if n_winners > 0 else 0
        if self.debug:
            logger.info(f"  [Pagamento] Completato. Totale: {total_payment:.2f} euro (media: {avg_payment:.2f} euro/vincitore). MV Calls: {mv_calls_end - mv_calls_start}")
        return payments
    
    def _selection_only(self, users: List[User]) -> Set[int]:
        temp_auction = IMCUAuction(users, debug=False, verify_properties=False)
        winners = temp_auction._selection_phase()
        return {u.id for u in winners}
    
    def _clone_users_with_modified_bid(self, user_id: int, new_bid: float) -> List[User]:
        cloned: List[User] = []
        for u in self.users:
            nu = User(u.id, u.position[1], u.position[0], cost_per_km=u.cost_per_km)
            nu.tasks = list(u.tasks)
            nu.cost = float(u.cost)
            nu.bid = float(max(0.0, new_bid)) if u.id == user_id else float(u.bid)
            cloned.append(nu)
        return cloned
    
    def _check_properties(self, winners: List[User], payments: Dict[int, float]) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        ir_violations = []
        for w in winners:
            if payments[w.id] + self.EPSILON < float(w.bid):
                ir_violations.append({"user_id": int(w.id), "payment": float(payments[w.id]), "bid": float(w.bid), "deficit": float(w.bid - payments[w.id])})
        if ir_violations:
            raise AssertionError(f"Violazione Individual Rationality: {len(ir_violations)} vincitori con pagamento < bid. Dettagli: {ir_violations}")
        report["IndividualRationality"] = {"passed": True, "violations": 0}
        vS = total_value_of_users(winners)
        sumP = float(sum(payments.values()))
        if vS + self.EPSILON < sumP:
            raise AssertionError(f"Violazione Profitability: v(S) = {vS:.6f} < Σp_i = {sumP:.6f}, deficit = {sumP - vS:.6f}")
        report["Profitability"] = {"passed": True, "platform_value": float(vS), "total_payments": float(sumP), "platform_utility": float(vS - sumP)}
        mono_results = {}
        for w in winners:
            delta = max(self.MONOTONICITY_TEST_DELTA_MIN, self.MONOTONICITY_TEST_DELTA_FACTOR * max(1.0, float(w.bid)))
            reduced_bid = max(0.0, float(w.bid) - delta)
            mod_users = self._clone_users_with_modified_bid(w.id, new_bid=reduced_bid)
            new_winners = self._selection_only(mod_users)
            still_wins = (w.id in new_winners)
            mono_results[str(w.id)] = {"original_bid": float(w.bid), "reduced_bid": float(reduced_bid), "still_wins": bool(still_wins)}
            if not still_wins:
                raise AssertionError(f"Violazione Monotonicity: utente {w.id} perde dopo riduzione bid da {w.bid:.6f} a {reduced_bid:.6f}")
        report["Monotonicity"] = mono_results
        crit_results = {}
        for w in winners:
            p_i = payments[w.id]
            delta = max(self.MONOTONICITY_TEST_DELTA_MIN, self.MONOTONICITY_TEST_DELTA_FACTOR * max(1.0, p_i))
            above_bid = p_i + delta
            mod_high = self._clone_users_with_modified_bid(w.id, new_bid=above_bid)
            win_high = self._selection_only(mod_high)
            wins_above = (w.id in win_high)
            below_bid = max(0.0, p_i - delta)
            mod_low = self._clone_users_with_modified_bid(w.id, new_bid=below_bid)
            win_low = self._selection_only(mod_low)
            wins_below = (w.id in win_low)
            crit_results[str(w.id)] = {"payment": float(p_i), "bid_above": float(above_bid), "wins_above": bool(wins_above), "bid_below": float(below_bid), "wins_below": bool(wins_below)}
            if wins_above:
                raise AssertionError(f"Violazione Critical Value (sopra): utente {w.id} vince ancora con bid = {above_bid:.6f} > p_i = {p_i:.6f}")
            if not wins_below:
                raise AssertionError(f"Violazione Critical Value (sotto): utente {w.id} perde con bid = {below_bid:.6f} < p_i = {p_i:.6f}")
        report["CriticalValue"] = crit_results
        if self.debug and self._logs_payment:
            bound_results = {}
            for pl in self._logs_payment:
                winner = next(u for u in winners if u.id == pl.winner_id)
                empty_covered: Set[int] = set()
                v_i_empty = self._marginal_value(winner, empty_covered, count_for="pay")
                if pl.final_payment > v_i_empty + self.EPSILON:
                    raise AssertionError(f"Violazione bound pagamento: winner {pl.winner_id}, p_i = {pl.final_payment:.6f} > v_i(∅) = {v_i_empty:.6f}")
                bound_results[str(int(pl.winner_id))] = {"payment": float(pl.final_payment), "v_i_empty": float(v_i_empty), "satisfies_bound": True}
            report["PaymentBound"] = bound_results
        else:
            report["PaymentBound"] = {"skipped": "log non disponibili"}
        truth_results = {}
        for w in winners:
            true_cost = float(w.cost)
            true_utility = max(0.0, float(payments[w.id] - true_cost))            
            fake_utilities = []
            violations = []
            for _ in range(self.TRUTHFULNESS_TEST_SAMPLES):
                multiplier = self._test_rng.uniform(0.5, 2.0)
                if math.isclose(multiplier, 1.0):
                    continue 
                fake_bid = true_cost * multiplier
                mod_users = self._clone_users_with_modified_bid(w.id, new_bid=fake_bid)
                temp_auction = IMCUAuction(mod_users, debug=False, verify_properties=False)
                fake_winners_ids = temp_auction._selection_only(mod_users)
                if w.id in fake_winners_ids:
                    fake_winners_obj = [u for u in mod_users if u.id in fake_winners_ids]
                    fake_payments = temp_auction._payment_phase(fake_winners_obj)
                    fake_utility = float(fake_payments[w.id] - true_cost)
                else:
                    fake_utility = 0.0
                fake_utilities.append({"bid_multiplier": float(multiplier), "fake_bid": float(fake_bid), "utility": float(fake_utility)})
                if fake_utility > true_utility + self.EPSILON:
                    violations.append({'multiplier': multiplier, 'utility_gain': fake_utility - true_utility, 'fake_utility': fake_utility})
            truth_results[str(w.id)] = {"true_utility": float(true_utility), "fake_bids_tested": len(fake_utilities), "dominating_bids_count": len(violations), "dominating_bids_examples": violations[:5]}
            if violations:
                raise AssertionError(f"Violazione Truthfulness: utente {w.id} guadagna mentendo. Utilità vera = {true_utility:.6f}, Trovati {len(violations)}/{self.TRUTHFULNESS_TEST_SAMPLES} bid mendaci migliori. Esempio: {violations[0]}")
        report["Truthfulness"] = truth_results
        return report
    
    def run(self) -> Tuple[Set[int], Dict[int, float], IMCUDiagnostics]:
        t0 = time.perf_counter()
        winners = self._selection_phase()
        t1 = time.perf_counter()
        payments = self._payment_phase(winners)
        t2 = time.perf_counter()
        winners_set: Set[int] = {u.id for u in winners}
        for u in self.users:
            u.is_winner = (u.id in winners_set)
            u.payment = float(payments.get(u.id, 0.0))
            base_cost = float(u.cost) if hasattr(u, "cost") and u.cost > 0 else float(u.bid)
            u.utility = float(u.payment - base_cost)
        vS = total_value_of_users(winners)
        sumP = float(sum(payments.values()))
        diagnostics = IMCUDiagnostics(winners_count=len(winners), covered_tasks_count=len({t.id for u in winners for t in _unique_tasks(u.tasks)}), payments_sum=sumP, platform_value_vS=vS, platform_utility_u0=vS - sumP, selection_time_s=(t1 - t0), payment_time_s=(t2 - t1), total_time_s=(t2 - t0), mv_calls_selection=self._mv_calls_selection, mv_calls_payment=self._mv_calls_payment, logs_selection=self._logs_selection if self.debug else [], logs_payment=self._logs_payment if self.debug else [])
        if self.verify_properties:
            prop_report = self._check_properties(winners, payments)
            diagnostics.property_checks = prop_report
            subm = empirical_submodularity_check(self.users, trials=self.SUBMODULARITY_TEST_TRIALS, seed=self.SUBMODULARITY_TEST_SEED)
            diagnostics.property_checks["Submodularity"] = subm
        return winners_set, payments, diagnostics

def run_imcu_auction(users: List[User], debug: bool = True, verify_properties: bool = True) -> Tuple[Set[int], Dict[int, float], Dict[str, Any]]:
    auction = IMCUAuction(users, debug=debug, verify_properties=verify_properties)
    winners_set, payments, diag = auction.run()
    all_task_ids = {t.id for u in auction.users for t in _unique_tasks(u.tasks)}
    diagnostics = {"winners_count": diag.winners_count, "covered_tasks_count": diag.covered_tasks_count, "payments_sum": diag.payments_sum, "platform_value_vS": diag.platform_value_vS, "platform_utility_u0": diag.platform_utility_u0, "selection_time_s": diag.selection_time_s, "payment_time_s": diag.payment_time_s, "total_time_s": diag.total_time_s, "mv_calls_selection": diag.mv_calls_selection, "mv_calls_payment": diag.mv_calls_payment, "property_checks": diag.property_checks, "n_users": len(auction.users), "m_tasks": len(all_task_ids)}
    if debug:
        diagnostics["logs_selection"] = [s.__dict__ for s in diag.logs_selection]
        diagnostics["logs_payment"] = [s.__dict__ for s in diag.logs_payment]
    return winners_set, payments, diagnostics

def pretty_print_diagnostics(dx: dict, title: str = "") -> None:
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}")
    print(f"\nRisultati principali:")
    print(f"  Vincitori: {dx.get('winners_count')}")
    print(f"  Task coperti: {dx.get('covered_tasks_count')}")
    print(f"  Valore piattaforma v(S): {dx.get('platform_value_vS', 0):.4f}")
    print(f"  Pagamenti totali Σp_i: {dx.get('payments_sum', 0):.4f}")
    print(f"  Utilità piattaforma u_0: {dx.get('platform_utility_u0', 0):.4f}")
    print(f"\nMetriche performance:")
    print(f"  Tempo selezione: {dx.get('selection_time_s', 0):.6f} s")
    print(f"  Tempo pagamenti: {dx.get('payment_time_s', 0):.6f} s")
    print(f"  Tempo totale: {dx.get('total_time_s', 0):.6f} s")
    print(f"  Chiamate marginal_value (selezione): {dx.get('mv_calls_selection', 0)}")
    print(f"  Chiamate marginal_value (pagamenti): {dx.get('mv_calls_payment', 0)}")
    print(f"\nDimensione problema:")
    print(f"  Numero utenti: {dx.get('n_users', 0)}")
    print(f"  Numero task: {dx.get('m_tasks', 0)}")
    prop_checks = dx.get("property_checks", {})
    if prop_checks:
        print(f"\nVerifiche proprietà:")
        for prop_name, prop_result in prop_checks.items():
            if isinstance(prop_result, dict):
                if "passed" in prop_result:
                    status = "PASS" if prop_result["passed"] else "FAIL"
                    print(f"  {prop_name}: {status}")
                elif "violations" in prop_result:
                    violations = prop_result["violations"]
                    trials = prop_result.get("trials", 0)
                    print(f"  {prop_name}: {violations}/{trials} violazioni")
                else:
                    print(f"  {prop_name}: {prop_result}")
            else:
                print(f"  {prop_name}: {prop_result}")
    sel_logs = dx.get("logs_selection", [])
    if sel_logs:
        print(f"\nLog selezione (totale: {len(sel_logs)}):")
        for step in sel_logs[:5]:
            chosen = step.get('chosen_user_id')
            chosen_str = f"User {chosen}" if chosen is not None else "STOP"
            print(f"  Iterazione {step['iteration']}: {chosen_str}, gain = {step['chosen_gain']:.4f}, task coperti = {step['covered_count_after']}")
        if len(sel_logs) > 5:
            print(f"  ... (altre {len(sel_logs) - 5} iterazioni)")
    pay_logs = dx.get("logs_payment", [])
    if pay_logs:
        print(f"\nLog pagamenti (totale: {len(pay_logs)}):")
        for pl in pay_logs[:5]:
            print(f"  Winner {pl['winner_id']}: pagamento = {pl['final_payment']:.4f}, competitor utili (K) = {pl.get('k_last', 0)}")
        if len(pay_logs) > 5:
            print(f"  ... (altri {len(pay_logs) - 5} vincitori)")

def dump_logs(dx: dict, run_name: str, out_dir: str = "imcu_logs") -> None:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{run_name}_diagnostics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dx, f, indent=2, ensure_ascii=False)
    sel_csv_path = os.path.join(out_dir, f"{run_name}_selection.csv")
    with open(sel_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["iter", "covered_before", "chosen_id", "chosen_gain", "cand_id", "cand_mv", "cand_bid", "cand_gain"])
        for step in dx.get("logs_selection", []):
            for cand in step.get("candidates", []):
                writer.writerow([step["iteration"], step["covered_count_before"], step.get("chosen_user_id", ""), step["chosen_gain"], int(cand["id"]), cand["mv"], cand["bid"], cand["gain"]])
    pay_csv_path = os.path.join(out_dir, f"{run_name}_payments.csv")
    with open(pay_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["winner_id", "k_last", "pos", "comp_id", "v_i_T", "v_j_T", "b_j", "cand_j", "critical_so_far", "after_threshold", "final_payment"])
        for pl in dx.get("logs_payment", []):
            if not pl.get("steps"):
                writer.writerow([int(pl["winner_id"]), int(pl.get("k_last", 0)), "", "", "", "", "", "", "", pl["after_threshold"], pl["final_payment"]])
            else:
                for step in pl["steps"]:
                    writer.writerow([int(pl["winner_id"]), int(pl.get("k_last", 0)), int(step["pos"]), int(step["comp_id"]), step["v_i_T"], step["v_j_T"], step["b_j"], step["cand_j"], step["critical_so_far"], pl["after_threshold"], pl["final_payment"]])
    print(f"\nLog esportati in '{out_dir}':")
    print(f"  - {json_path}")
    print(f"  - {sel_csv_path}")
    print(f"  - {pay_csv_path}")
