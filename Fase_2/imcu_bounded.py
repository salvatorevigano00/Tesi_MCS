from __future__ import annotations
import math
import logging
import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any, TypedDict
import sys
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
    from Fase_2.classes_bounded import BoundedRationalUser as User, compute_anomaly_threshold
except ImportError:
    try:
        from Fase_1.classes import User
        logging.warning("Utilizzo `User`/`Task` dalla Fase 1 (classes_bounded.py non disponibile)")
    except ImportError as e:
        raise ImportError(f"Impossibile importare User/Task dalla Fase 2 o Fase 1: {e}\nVerificare che esista classes_bounded.py o Fase_1/classes.py")

try:
    from Fase_1.imcu import IMCUAuction, IMCUDiagnostics, _unique_tasks
    import Fase_1.imcu as imcu_base
except ImportError as e:
    raise ImportError(f"Impossibile importare Fase_1.imcu: {e}\nVerificare che esista Fase_1/__init__.py e Fase_1/imcu.py")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class IMCURationalConfig:
    BID_DEVIATION_WARNING_PCT: float = 15.0
    SIMULATE_MORAL_HAZARD: bool = True

class BoundedRationalityMetrics(TypedDict, total=False):
    avg_rationality_all: float
    avg_rationality_winners: float
    std_rationality_all: float
    std_rationality_winners: float
    min_rationality_all: float
    max_rationality_all: float
    bid_deviation_max_abs_pct: float
    bid_deviation_mean_pct: float
    bid_deviation_p95_pct: float
    bid_deviation_status: str
    bid_deviation_warning: bool
    bid_deviation_anomaly: bool
    profile_distribution_all: Dict[str, int]
    profile_distribution_winners: Dict[str, int]
    expected_defections_sum: float
    expected_completion_rate: float
    expected_completion_rate_ci95_lower: float
    expected_completion_rate_ci95_upper: float
    expected_completion_rate_stderr: float
    expected_quality_loss: float
    actual_completions: int
    actual_completion_rate: float
    completion_rate_prediction_error: float
    v_eff_expost: float
    u0_expost: float
    ir_violations_expost: int
    ir_violation_rate_expost: float
    profitability_expost: bool
    mechanism_breakdown_expost: Dict[str, Any]
    total_penalties_accumulated: float
    avg_penalty_per_winner: float
    avg_utility_winners: float
    std_utility_winners: float
    min_utility_winners: float
    max_utility_winners: float
    positive_utility_rate: float
    avg_payment_cost_ratio: float
    median_payment_cost_ratio: float
    original_users_count: int
    eligible_users_count: int

def _validate_user_rational(user: User) -> None:
    imcu_base._validate_user(user)
    required_attrs = {'rationality_level': (0.30, 0.90, float), 'p_defect': (0.0, 1.0, float), 'p_defect_base': (0.0, 1.0, float), 'reputation': (0.0, 1.0, float), 'honesty_profile': (None, None, str), 'completed': (None, None, bool), 'actually_completed': (None, None, bool), 'penalty_accumulated': (0.0, float('inf'), float), 'deviation_prob': (0.0, 1.0, float), 'reward_allocation_class': (None, None, str)}
    for attr, (min_val, max_val, expected_type) in required_attrs.items():
        if not hasattr(user, attr):
            raise AttributeError(f"Utente {user.id} manca l'attributo obbligatorio '{attr}'.\nVerificare l'inizializzazione di `BoundedRationalUser` in classes_bounded.py")
        val = getattr(user, attr)
        if not isinstance(val, expected_type):
            raise TypeError(f"Utente {user.id}: l'attributo '{attr}' deve essere di tipo {expected_type.__name__}, ricevuto: {type(val).__name__} = {val}")
        if min_val is not None and max_val is not None:
            if not (min_val <= val <= max_val):
                raise ValueError(f"Utente {user.id}: '{attr}'={val} è fuori dall'intervallo ammissibile [{min_val}, {max_val}].\nVerificare la generazione dei parametri in data_manager_bounded.py")
    if not hasattr(user, 'blacklisted_until'):
        raise AttributeError(f"Utente {user.id} manca 'blacklisted_until'.\nAttributo obbligatorio per il sistema di idoneità della Fase 2.")
    val = user.blacklisted_until
    if val is not None and not isinstance(val, (float, int)):
        raise TypeError(f"Utente {user.id}: 'blacklisted_until' deve essere None, float o int, ricevuto: {type(val).__name__} = {val}")
    if not hasattr(user, 'blacklist_strikes'):
        raise AttributeError(f"Utente {user.id} manca 'blacklist_strikes'.\nAttributo obbligatorio per il sistema di idoneità della Fase 2.")
    strikes = user.blacklist_strikes
    if not isinstance(strikes, int):
        raise TypeError(f"Utente {user.id}: 'blacklist_strikes' deve essere int, ricevuto: {type(strikes).__name__} = {strikes}")
    if strikes < 0:
        raise ValueError(f"Utente {user.id}: 'blacklist_strikes'={strikes} non può essere negativo.")

def _validate_users_rational(users: Optional[List[User]]) -> List[User]:
    if users is None:
        raise TypeError("La lista 'users' è None.\nÈ necessario passare una lista (anche vuota) di `BoundedRationalUser`.")
    if not isinstance(users, list):
        raise TypeError(f"L'input 'users' deve essere una lista, ricevuto: {type(users).__name__}.\nVerificare la chiamata: run_imcu_auction_bounded(users=[...])")
    if not users:
        logger.warning("Lista 'users' vuota. L'asta non può essere eseguita.")
    for u in users:
        _validate_user_rational(u)
    return sorted(users, key=lambda u: u.id)

class IMCUAuctionRational(IMCUAuction):
    def __init__(self, users: List[User], debug: bool = True, verify_properties: bool = True, check_truthfulness_acceptance: bool = True, simulate_moral_hazard: bool = None):
        validated = _validate_users_rational(users)
        super().__init__(validated, debug, verify_properties)
        self.check_truthfulness_acceptance = check_truthfulness_acceptance
        if simulate_moral_hazard is None:
            simulate_moral_hazard = IMCURationalConfig.SIMULATE_MORAL_HAZARD
        self.simulate_moral_hazard = simulate_moral_hazard
        self._original_users = validated
        self._eligible_users = validated
        logger.info(f"IMCUAuctionRational inizializzata: {len(validated)} utenti, simula_azzardo_morale={self.simulate_moral_hazard}, controlla_accettazione_fft={self.check_truthfulness_acceptance}")
    
    def _check_properties(self, winners: List[User], payments: Dict[int, float]) -> Dict[str, Any]:
        report = super()._check_properties(winners, payments)
        if "Truthfulness" in report:
            report["TruthfulnessBidding (Veridicità Offerta)"] = report.pop("Truthfulness")
            report["TruthfulnessBidding (Veridicità Offerta)"]["note"] = "Verifica che le offerte (bid) siano veritiere (b_i ≈ c_i), come garantito dal meccanismo IMCU (Teorema 4, Yang 2015). Questa verifica è ex-ante e indipendente dalle defezioni."
        if self.check_truthfulness_acceptance:
            logger.info("Quantificazione della selezione sub-ottimale (FFT) tramite euristica CV...")
            report["TruthfulnessAcceptance (Selezione FFT)"] = self._check_suboptimal_acceptance_fft(winners)
        else:
            report["TruthfulnessAcceptance (Selezione FFT)"] = {"verificato": False, "motivo": "Controllo disabilitato (costoso, check_truthfulness_acceptance=False)", "nota": "L'euristica FFT può causare una selezione sub-ottimale (15-25% vs selezione greedy) (Karaliopoulos & Bakali 2019). Questo è un comportamento atteso, non un difetto dell'IMCU."}
        return report
    
    def _check_suboptimal_acceptance_fft(self, winners: List[User]) -> Dict[str, Any]:
        if not winners:
            return {"verificato": True, "metodo": "euristica_cv_proxy", "conteggio_subottimale": 0, "totale_verificati": 0, "tasso_subottimale": 0.0, "nei_limiti_letteratura": True, "intervallo_atteso": (0.15, 0.25), "soglia_cv": 0.5, "nota": "Nessun vincitore da verificare (lista vuota)."}
        suboptimal_count = 0
        total_checked = 0
        for w in winners:
            if not w.tasks or len(w.tasks) < 2:
                continue
            total_checked += 1
            task_values = [float(t.value) for t in w.tasks]
            value_mean = np.mean(task_values)
            value_std = np.std(task_values)
            cv = value_std / value_mean if value_mean > 1e-9 else 0
            if cv > 0.5:
                suboptimal_count += 1
        suboptimal_rate = suboptimal_count / total_checked if total_checked > 0 else 0.0
        within_bounds = (0.10 <= suboptimal_rate <= 0.30)
        logger.info(f"Verifica selezione sub-ottimale (FFT): {suboptimal_count}/{total_checked} vincitori ({suboptimal_rate:.1%}), nei limiti attesi={within_bounds}")
        return {"verificato": True, "metodo": "euristica_cv_proxy", "conteggio_subottimale": suboptimal_count, "totale_verificati": total_checked, "tasso_subottimale": float(suboptimal_rate), "nei_limiti_letteratura": within_bounds, "intervallo_atteso": (0.15, 0.25), "soglia_cv": 0.5, "nota": "Euristica 'proxy': Un CV alto (>0.5) suggerisce una selezione sub-ottimale. Limitazione: Un confronto rigoroso richiederebbe l'elenco dei task candidati originali (non disponibile all'asta).", "limitazione": "Confronto rigoroso richiede l'elenco dei task candidati (vincolo architetturale)."}
    
    def _extended_diagnostics_rational(self, winners: List[User], payments: Dict[int, float]) -> Dict[str, Any]:
        diag = {}
        all_rho = [u.rationality_level for u in self._original_users]
        win_rho = [u.rationality_level for u in winners]
        if all_rho:
            diag['avg_rationality_all'] = float(np.mean(all_rho))
            diag['std_rationality_all'] = float(np.std(all_rho))
            diag['min_rationality_all'] = float(np.min(all_rho))
            diag['max_rationality_all'] = float(np.max(all_rho))
        if win_rho:
            diag['avg_rationality_winners'] = float(np.mean(win_rho))
            diag['std_rationality_winners'] = float(np.std(win_rho))
        bid_devs_pct = []
        for u in self._eligible_users:
            if hasattr(u, 'cost') and u.cost > 1e-9:
                dev_raw = abs(u.bid - u.cost) / u.cost
                bid_devs_pct.append(dev_raw * 100.0)
        if bid_devs_pct:
            max_abs_dev_pct = max(bid_devs_pct)
            diag['bid_deviation_max_abs_pct'] = float(max_abs_dev_pct)
            diag['bid_deviation_mean_pct'] = float(np.mean(bid_devs_pct))
            diag['bid_deviation_p95_pct'] = float(np.percentile(bid_devs_pct, 95))
            dynamic_threshold_raw = compute_anomaly_threshold(self._eligible_users)
            dynamic_threshold_pct = dynamic_threshold_raw * 100.0
            diag['dynamic_anomaly_threshold_pct'] = dynamic_threshold_pct
            if max_abs_dev_pct > dynamic_threshold_pct:
                logger.error(f"FIX 5.1: Rilevate offerte anomale: deviazione massima assoluta={max_abs_dev_pct:.2f}% > soglia dinamica 3-sigma={dynamic_threshold_pct:.2f}%")
                diag['bid_deviation_anomaly'] = True
                diag['bid_deviation_status'] = "anomale (oltre 3-sigma)"
            elif max_abs_dev_pct > IMCURationalConfig.BID_DEVIATION_WARNING_PCT:
                logger.warning(f"Rilevate offerte con alta deviazione: deviazione massima assoluta={max_abs_dev_pct:.2f}% > soglia avviso={IMCURationalConfig.BID_DEVIATION_WARNING_PCT:.2f}% (2-sigma)")
                diag['bid_deviation_warning'] = True
                diag['bid_deviation_status'] = "alte (oltre 2-sigma)"
            else:
                diag['bid_deviation_anomaly'] = False
                diag['bid_deviation_warning'] = False
                diag['bid_deviation_status'] = "veritiere (entro limiti)"
        else:
            diag['bid_deviation_status'] = "N/A (no bid deviations)"
            diag['bid_deviation_anomaly'] = False
            diag['bid_deviation_warning'] = False
        prof_all = {}
        prof_win = {}
        for u in self._eligible_users:
            prof_all[u.honesty_profile] = prof_all.get(u.honesty_profile, 0) + 1
        for u in winners:
            prof_win[u.honesty_profile] = prof_win.get(u.honesty_profile, 0) + 1
        diag['profile_distribution_all'] = prof_all
        diag['profile_distribution_winners'] = prof_win
        exp_defect = 0.0
        var_defect = 0.0
        exp_qloss = 0.0
        for u in winners:
            p = float(u.p_defect)
            exp_defect += p
            var_defect += p * (1 - p)
            if u.tasks:
                v_i = sum(float(t.value) for t in _unique_tasks(u.tasks))
                exp_qloss += p * v_i
        n_winners = len(winners)
        exp_compl_rate = 1.0 - (exp_defect / n_winners) if n_winners else 1.0
        std_err_compl = math.sqrt(var_defect) / n_winners if n_winners else 0.0
        ci_95_lower = max(0.0, exp_compl_rate - 1.96 * std_err_compl)
        ci_95_upper = min(1.0, exp_compl_rate + 1.96 * std_err_compl)
        diag['expected_defections_sum'] = float(exp_defect)
        diag['expected_completion_rate'] = float(exp_compl_rate)
        diag['expected_completion_rate_ci95_lower'] = float(ci_95_lower)
        diag['expected_completion_rate_ci95_upper'] = float(ci_95_upper)
        diag['expected_completion_rate_stderr'] = float(std_err_compl)
        diag['expected_quality_loss'] = float(exp_qloss)
        completed_winners = [w for w in winners if hasattr(w, 'actually_completed')]
        if completed_winners:
            actual_compl = sum(1 for w in completed_winners if w.actually_completed)
            actual_rate = actual_compl / len(completed_winners) if completed_winners else 1.0
            diag['actual_completions'] = int(actual_compl)
            diag['actual_completion_rate'] = float(actual_rate)
            if len(completed_winners) == len(winners):
                pred_err = abs(actual_rate - exp_compl_rate)
                diag['completion_rate_prediction_error'] = float(pred_err)
        if self.simulate_moral_hazard and completed_winners:
            completed_tasks = []
            seen_task_ids = set()
            for w in winners:
                if hasattr(w, 'actually_completed') and w.actually_completed:
                    for t in _unique_tasks(w.tasks):
                        if t.id not in seen_task_ids:
                            completed_tasks.append(t)
                            seen_task_ids.add(t.id)
            v_eff_expost = sum(float(t.value) for t in completed_tasks)
            sumP = sum(payments.values())
            u0_expost = v_eff_expost - sumP
            diag['v_eff_expost'] = float(v_eff_expost)
            diag['u0_expost'] = float(u0_expost)
            diag['profitability_expost'] = bool(u0_expost >= -1e-9)
            ir_violations_expost = 0
            for w in winners:
                if hasattr(w, 'penalty_accumulated'):
                    u_i_expost = w.payment - w.cost - w.penalty_accumulated
                    if u_i_expost < -1e-6:
                        ir_violations_expost += 1
            ir_violation_rate_expost = ir_violations_expost / max(1, len(winners))
            diag['ir_violations_expost'] = int(ir_violations_expost)
            diag['ir_violation_rate_expost'] = float(ir_violation_rate_expost)
            deficit_expost = (u0_expost < 0)
            ir_breakdown_expost = (ir_violation_rate_expost > 0.05)
            diag['mechanism_breakdown_expost'] = {'deficit': deficit_expost, 'ir_violation': ir_breakdown_expost, 'severity': int(deficit_expost) + int(ir_breakdown_expost), 'note': "Diagnosi di rottura ex-post (dopo defezioni). Estensione oltre l'Assunzione 2.1 di Yang (2015)."}
        tot_penalty = sum(u.penalty_accumulated for u in winners if hasattr(u, 'penalty_accumulated'))
        diag['total_penalties_accumulated'] = float(tot_penalty)
        if winners:
            diag['avg_penalty_per_winner'] = float(tot_penalty / len(winners))
        utils = []
        p_c_ratios = []
        for w in winners:
            p_i = payments.get(w.id, 0.0)
            c_i = float(w.cost)
            if c_i > 1e-9:
                u_i = p_i - c_i
                utils.append(u_i)
                p_c_ratios.append(p_i / c_i)
        if utils:
            diag['avg_utility_winners'] = float(np.mean(utils))
            diag['std_utility_winners'] = float(np.std(utils))
            diag['min_utility_winners'] = float(np.min(utils))
            diag['max_utility_winners'] = float(np.max(utils))
            diag['positive_utility_rate'] = float(sum(1 for u in utils if u > 0) / len(utils))
        if p_c_ratios:
            diag['avg_payment_cost_ratio'] = float(np.mean(p_c_ratios))
            diag['median_payment_cost_ratio'] = float(np.median(p_c_ratios))
        diag['original_users_count'] = len(self._original_users)
        diag['eligible_users_count'] = len(self._eligible_users)
        return diag
    
    def run(self) -> Tuple[Set[int], Dict[int, float], IMCUDiagnostics]:
        logger.info("Esecuzione asta IMCU base (selezione e pagamento)...")
        winners_set, payments, diagnostics = super().run()
        winners = [u for u in self._eligible_users if u.id in winners_set]
        for w in winners:
            w.payment = payments.get(w.id, 0.0)
            w.utility = w.payment - w.cost
            w.is_winner = True
        logger.info(f"Asta (ex-ante) completata: {len(winners)} vincitori, somma pagamenti={sum(payments.values()):.2f} euro")
        if self.simulate_moral_hazard:
            logger.info("Simulazione azzardo morale (defezioni probabilistiche)...")
            for w in winners:
                w.attempt_task_completion()
        logger.info("Calcolo diagnostica estesa (ex-ante vs ex-post)...")
        extended = self._extended_diagnostics_rational(winners, payments)
        extended['platform_value_vS_exante'] = diagnostics.platform_value_vS
        diagnostics.property_checks['BoundedRationalityMetrics'] = extended
        logger.info("Asta IMCU razionale (Fase 2) completata con successo.")
        return winners_set, payments, diagnostics

def run_imcu_auction_bounded(users: List[User], debug: bool = True, debug_level: str = "full", verify_properties: bool = True, check_truthfulness_acceptance: bool = True, simulate_moral_hazard: bool = None) -> Tuple[Set[int], Dict[int, float], Dict[str, Any]]:
    if debug_level not in ("none", "summary", "full"):
        raise ValueError(f"Il livello di debug (debug_level) deve essere 'none', 'summary' o 'full', ricevuto: '{debug_level}'")
    auction = IMCUAuctionRational(users, debug=debug, verify_properties=verify_properties, check_truthfulness_acceptance=check_truthfulness_acceptance, simulate_moral_hazard=simulate_moral_hazard)
    winners_set, payments, diag_obj = auction.run()
    all_task_ids = {t.id for u in auction.users for t in _unique_tasks(u.tasks)}
    diagnostics = {"winners_count": diag_obj.winners_count, "covered_tasks_count": diag_obj.covered_tasks_count, "payments_sum": diag_obj.payments_sum, "platform_value_vS": diag_obj.platform_value_vS, "platform_utility_u0": diag_obj.platform_utility_u0, "selection_time_s": diag_obj.selection_time_s, "payment_time_s": diag_obj.payment_time_s, "total_time_s": diag_obj.total_time_s, "mv_calls_selection": diag_obj.mv_calls_selection, "mv_calls_payment": diag_obj.mv_calls_payment, "property_checks": diag_obj.property_checks, "n_users": len(auction._original_users), "m_tasks": len(all_task_ids)}
    if debug:
        if debug_level == "full":
            diagnostics["logs_selection"] = [s.__dict__ for s in diag_obj.logs_selection]
            diagnostics["logs_payment"] = [s.__dict__ for s in diag_obj.logs_payment]
        elif debug_level == "summary":
            diagnostics["logs_selection_count"] = len(diag_obj.logs_selection)
            diagnostics["logs_payment_count"] = len(diag_obj.logs_payment)
            if diag_obj.logs_selection:
                diagnostics["logs_selection_sample"] = [diag_obj.logs_selection[0].__dict__, diag_obj.logs_selection[-1].__dict__]
            if diag_obj.logs_payment:
                diagnostics["logs_payment_sample"] = [diag_obj.logs_payment[0].__dict__, diag_obj.logs_payment[-1].__dict__]
    return winners_set, payments, diagnostics
