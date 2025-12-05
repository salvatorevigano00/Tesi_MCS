from __future__ import annotations
import os
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
import argparse
import datetime as dt
import numpy as np
import logging
import traceback
import math

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)

if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from Fase_1.fase_1 import (
        setup_experiment_logger, 
        save_experiment_metadata, 
        safe_csv_write
    )
    from Fase_1.classes import Task
except ImportError as e:
    raise ImportError(f"Impossibile importare moduli fase 1: {e}")

try:
    from Fase_2.fase_2 import ExperimentConfigPhase2
    from Fase_2.classes_bounded import set_random_seed
except ImportError as e:
    raise ImportError(f"Impossibile importare moduli fase 2: {e}")

try:
    from Fase_3.data_manager_adaptive import DataManagerAdaptive
    from Fase_3.classes_adaptive import AdaptiveUser, TaskAdaptive
    from Fase_3.imcu_adaptive import run_imcu_auction_adaptive
    from Fase_3.plot_adaptive import ScientificPlotterAdaptive 
except ImportError as e:
    raise ImportError(f"Impossibile importare moduli core fase 3: {e}")

logger = logging.getLogger(__name__)

PROFILE_NAMES = [
    "Perfect Rational", 
    "Quasi-Rational", 
    "Bounded Honest", 
    "Bounded Moderate", 
    "Bounded Opportunistic"
]

def validate_gap_parameters() -> None:
    try:
        from Fase_3.classes_adaptive import (
            KAPPA_RELIABILITY,
            PENALTY_REPUTATION_DECAY,
            MDR_WEIGHT_COMPLETION,
            MDR_WEIGHT_RELIABILITY,
            MDR_WEIGHT_QUALITY,
            REPUTATION_THRESHOLD_BONUS,
            REPUTATION_ABSOLUTE_MIN_THRESHOLD
        )
    except ImportError as e:
        raise AssertionError(f"Impossibile importare parametri per validazione: {e}")
    fixes = {
        "KAPPA_RELIABILITY": (KAPPA_RELIABILITY, 1.0),
        "PENALTY_REPUTATION_DECAY": (PENALTY_REPUTATION_DECAY, 0.15),
        "MDR_WEIGHT_COMPLETION": (MDR_WEIGHT_COMPLETION, 0.0),
        "MDR_WEIGHT_RELIABILITY": (MDR_WEIGHT_RELIABILITY, 0.60),
        "MDR_WEIGHT_QUALITY": (MDR_WEIGHT_QUALITY, 0.40),
        "REPUTATION_THRESHOLD_BONUS": (REPUTATION_THRESHOLD_BONUS, 0.90),
        "REPUTATION_ABSOLUTE_MIN_THRESHOLD": (REPUTATION_ABSOLUTE_MIN_THRESHOLD, 0.30)
    }
    errors = []
    for param_name, (actual, expected) in fixes.items():
        if not math.isclose(actual, expected, abs_tol=1e-6):
            errors.append(f"  {param_name}: atteso={expected}, trovato={actual}")
    if errors:
        error_msg = "\n".join([
            "=" * 80,
            "Parametri non corrispondono alla configurazione attesa",
            "=" * 80,
            "",
            "Parametri non validi:",
            *errors,
            "\nVerificare classes_adaptive.py",
            "=" * 80
        ])
        raise AssertionError(error_msg)
    logger.info("Validazione parametri superata")

@dataclass
class ExperimentConfigPhase3(ExperimentConfigPhase2):
    report_name: str = "REPORT_RIEPILOGATIVO_FASE3.txt"
    high_value_threshold_pct: float = 0.80
    min_reliability_critical: float = 0.70
    max_reliability_critical: float = 0.85
    min_quality_target_critical: float = 0.40
    max_quality_target_critical: float = 0.60
    min_feedback_weight_critical: float = 1.5
    max_feedback_weight_critical: float = 2.5

    def validate(self) -> None:
        super().validate()
        if not (0.0 <= self.high_value_threshold_pct <= 1.0):
            raise ValueError(f"high_value_threshold_pct deve essere in [0, 1]")
        if not (0.0 <= self.min_reliability_critical <= self.max_reliability_critical <= 1.0):
            raise ValueError(f"Reliability critica: 0 <= min <= max <= 1")
        if not (0.0 <= self.min_quality_target_critical <= self.max_quality_target_critical <= 1.0):
            raise ValueError(f"Quality target critica: 0 <= min <= max <= 1")
        if self.min_feedback_weight_critical < 0 or \
           self.max_feedback_weight_critical < self.min_feedback_weight_critical:
            raise ValueError(f"Feedback weight: 0 <= min <= max")

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["simulazione"] = {
            "tipo": "Fase 3 - Stateful Adattiva",
            "stato": "Persistente (utenti apprendono ora per ora)"
        }
        base_dict["gap_parametri"] = {
            "high_value_threshold_pct": self.high_value_threshold_pct,
            "reliability_range": [self.min_reliability_critical, self.max_reliability_critical],
            "quality_target_range": [self.min_quality_target_critical, self.max_quality_target_critical],
            "feedback_weight_range": [self.min_feedback_weight_critical, self.max_feedback_weight_critical]
        }
        return base_dict

def compute_effective_value(winners: List[AdaptiveUser]) -> float:
    covered_tasks: Dict[int, Task] = {}
    for user in winners:
        unique_tasks = list({t.id: t for t in user.tasks}.values())
        if not unique_tasks:
            continue
        if hasattr(user, 'actually_completed') and user.actually_completed:
            for task in unique_tasks:
                covered_tasks[task.id] = task
        elif not hasattr(user, 'actually_completed'):
            if user.completed:
                for task in unique_tasks:
                    covered_tasks[task.id] = task
    return float(sum(t.value for t in covered_tasks.values()))

def compute_winners_profile_distribution(
    users: List[AdaptiveUser], 
    winners_set: set[int]
) -> Dict[str, int]:
    distribuzione = {prof: 0 for prof in PROFILE_NAMES}
    for user in users:
        if user.id in winners_set:
            profilo = user.honesty_profile
            if profilo not in distribuzione:
                distribuzione[profilo] = 0
            distribuzione[profilo] += 1
    return distribuzione

def assign_tasks_to_users(
    users: List[AdaptiveUser], 
    tasks: List[TaskAdaptive], 
    radius_m: float,
    logger_instance: logging.Logger
) -> int:
    if not users:
        logger_instance.warning("Lista utenti vuota")
        return 0
    if not tasks:
        logger_instance.warning("Lista task vuota")
        for user in users:
            user.set_tasks([])
        return 0
    users_with_tasks = 0
    total_assignments = 0
    for user in users:
        candidate_tasks = []
        for task in tasks:
            try:
                dist_m = user.calculate_distance_to(task)
                if dist_m <= radius_m:
                    candidate_tasks.append(task)
            except Exception as e:
                logger_instance.error(f"Calcolo distanza user {user.id} - task {task.id}: {e}")
        user.set_tasks(candidate_tasks)
        if candidate_tasks:
            users_with_tasks += 1
            total_assignments += len(candidate_tasks)
    avg_tasks = total_assignments / users_with_tasks if users_with_tasks > 0 else 0.0
    logger_instance.info(
        f"Assegnazione task: {users_with_tasks}/{len(users)} utenti con task "
        f"(media={avg_tasks:.1f} task/utente)"
    )
    return users_with_tasks

def process_feedback_quality_loop(
    all_users: List[AdaptiveUser],
    tasks_for_this_hour: List[TaskAdaptive],
    diagnostics: Dict[str, Any],
    current_time_sec: float,
    config_day: str,
    hour: int,
    logger_instance: logging.Logger
) -> int:
    logger_instance.info(f"[{config_day} h{hour:02d}] Feedback quality loop")
    feedback_count = 0
    feedback_errors = 0
    gap_metrics = diagnostics.get("property_checks", {}).get("AdaptiveGAPMetrics", {})
    completed_tasks_map = gap_metrics.get("completed_tasks_by_winner", {})
    if not completed_tasks_map:
        logger_instance.warning(f"[{config_day} h{hour:02d}] Nessun task completato, feedback saltato")
        return 0
    logger_instance.debug(
        f"  Mappa task completati: {len(completed_tasks_map)} vincitori, "
        f"totale task={sum(len(v) for v in completed_tasks_map.values())}"
    )
    for winner_id, task_ids in completed_tasks_map.items():
        winner = next((u for u in all_users if u.id == winner_id), None)
        if not winner:
            logger_instance.warning(f"  Utente {winner_id} non trovato")
            continue
        for task_id in task_ids:
            task = next((t for t in tasks_for_this_hour if t.id == task_id), None)
            if not task or not isinstance(task, TaskAdaptive):
                continue
            try:
                if winner.rationality_level >= 0.75:
                    quality = 1.0
                elif winner.rationality_level >= 0.60:
                    quality = float(np.random.uniform(0.7, 1.0))
                elif winner.rationality_level >= 0.45:
                    quality = float(np.random.uniform(0.5, 0.9))
                else:
                    quality = float(np.random.uniform(0.3, 0.7))
                task.mark_completed_by_platform(
                    quality=quality,
                    timestamp=current_time_sec,
                    notes=f"User {winner.id} (rho={winner.rationality_level:.3f})"
                )
                feedback_count += 1
                logger_instance.debug(
                    f"  Task {task.id}: qualita={quality:.3f}, "
                    f"user={winner.id} (rho={winner.rationality_level:.3f})"
                )
            except Exception as e:
                feedback_errors += 1
                logger_instance.error(f"  Feedback task {task.id}: {e}", exc_info=True)
    logger_instance.info(
        f"[{config_day} h{hour:02d}] Feedback: {feedback_count} task processati, "
        f"{feedback_errors} con problemi"
    )
    return feedback_count

def save_final_user_state(
    users: List[AdaptiveUser], 
    output_path: str, 
    logger_instance: logging.Logger
) -> None:
    logger_instance.info(f"Salvataggio stato finale {len(users)} utenti: {output_path}")
    header = (
        "user_id,rho_reale,rho_stimato,rho_std,rep_aggregata,"
        "rep_affidabilita,rep_qualita,rho_alpha,rho_beta,"
        "rho_obs_count,mdr_obs_count,profilo_onesta,blacklist_strikes\n"
    )
    rows = [header]
    errors = 0
    for u in users:
        try:
            total = u.rho_alpha + u.rho_beta
            if total > 0:
                variance = (u.rho_alpha * u.rho_beta) / ((total ** 2) * (total + 1))
                rho_std = float(np.sqrt(variance))
            else:
                rho_std = float('nan')
            row = (
                f"{u.id},{u.rationality_level:.4f},{u.estimated_rationality:.4f},"
                f"{rho_std:.4f},{u.reputation:.4f},"
                f"{u.reputation_reliability:.4f},{u.reputation_quality:.4f},"
                f"{u.rho_alpha:.2f},{u.rho_beta:.2f},"
                f"{u.rho_observation_count},{u.mdr_observation_count},"
                f"{u.honesty_profile},{u.blacklist_strikes}\n"
            )
            rows.append(row)
        except Exception as e:
            errors += 1
            logger_instance.error(f"Salvataggio utente {u.id}: {e}")
    if errors > 0:
        logger_instance.warning(f"{errors}/{len(users)} utenti con problemi")
    safe_csv_write("".join(rows), output_path, logger_instance)

def generate_summary_report_phase3(
    output_dir: str, 
    day: str, 
    hourly_results: List[Dict[str, Any]], 
    config: ExperimentConfigPhase3, 
    logger_instance: logging.Logger
) -> None:
    report_path = os.path.join(output_dir, f"{day}_{config.report_name}")
    try:
        hours = [r["hour"] for r in hourly_results]
        v_mech_arr = [r.get("v_mech", 0) for r in hourly_results]
        v_eff_arr = [r.get('gap_metrics', {}).get('v_eff_expost', 0) for r in hourly_results]
        u0_eff_arr = [r.get('gap_metrics', {}).get('u0_expost', 0) for r in hourly_results]
        mae_rho_arr = [r.get('gap_metrics', {}).get('mae_rho_estimation', np.nan) for r in hourly_results]
        avg_rho_true = [r.get('gap_metrics', {}).get('avg_rho_true_eligible', np.nan) for r in hourly_results]
        avg_rho_est = [r.get('gap_metrics', {}).get('avg_rho_estimated_eligible', np.nan) for r in hourly_results]
        avg_rep = [r.get('gap_metrics', {}).get('avg_reputation_agg_eligible', np.nan) for r in hourly_results]
        payment_base_arr = [r.get('gap_metrics', {}).get('sum_payment_base', 0) for r in hourly_results]
        payment_final_arr = [r.get('gap_metrics', {}).get('sum_payment_final', 0) for r in hourly_results]
        health_reports = [r.get('gap_metrics', {}).get('mechanism_health_expost', {}) for r in hourly_results]
        completion_rate_arr = [h.get('completion_rate_tasks', 0) for h in health_reports]
        ir_violation_rate_arr = [h.get('ir_violation_rate', 0) for h in health_reports]
        health_score_arr = [h.get('health_score', 0) for h in health_reports]
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Report simulazione fase 3 - giornata {day}\n")
            f.write("Analisi meccanismo adattivo - simulazione stateful\n")
            f.write("=" * 80 + "\n\n")
            f.write("Configurazione esperimento\n")
            f.write("-" * 80 + "\n")
            f.write(f"Giorno: {config.day}\n")
            f.write(f"Finestra: {config.hour_start:02d}:00 - {config.hour_end:02d}:00\n")
            f.write(f"Seed: {config.random_seed}\n")
            f.write(f"Razionalità: {config.rationality_distribution}\n")
            f.write(f"Max utenti: {config.max_users}\n")
            f.write(f"Raggio task: {config.task_radius_m}m\n")
            f.write(f"Valore task: [{config.task_value_min}, {config.task_value_max}]€\n\n")
            f.write("Statistiche aggregate giornaliere\n")
            f.write("-" * 80 + "\n")
            v_mech_total = sum(v_mech_arr)
            v_eff_total = sum(v_eff_arr)
            u0_eff_total = sum(u0_eff_arr)
            sumP_base_total = sum(payment_base_arr)
            sumP_final_total = sum(payment_final_arr)
            f.write("Metriche ex-post:\n")
            f.write(f"  Valore effettivo v(S_eff): {v_eff_total:,.2f}€\n")
            f.write(f"  Pagamenti base: {sumP_base_total:,.2f}€\n")
            f.write(f"  Pagamenti finali (post-incentivo): {sumP_final_total:,.2f}€\n")
            f.write(f"  Utilità piattaforma (u0_eff): {u0_eff_total:,.2f}€\n")
            f.write(f"  Profittabilità: {'Sì' if u0_eff_total >= 0 else 'No'}\n\n")
            breakdown_total = v_mech_total - v_eff_total
            breakdown_pct = 100 * breakdown_total / v_mech_total if v_mech_total > 0 else 0
            f.write(f"Efficacia meccanismo:\n")
            f.write(f"  Valore teorico (v_mech): {v_mech_total:,.2f}€\n")
            f.write(f"  Valore reale (v_eff): {v_eff_total:,.2f}€\n")
            f.write(f"  Breakdown: {breakdown_total:,.2f}€ ({breakdown_pct:.2f}%)\n\n")
            total_incentive = sumP_final_total - sumP_base_total
            f.write(f"Incentivi:\n")
            f.write(f"  Costo netto: {total_incentive:,.2f}€\n")
            if sumP_base_total > 0:
                f.write(f"  Impatto: {100*total_incentive/sumP_base_total:+.2f}%\n")
            f.write("\n")
            f.write(f"Apprendimento:\n")
            mae_mean = np.nanmean(mae_rho_arr)
            mae_std = np.nanstd(mae_rho_arr)
            f.write(f"  Mae(rho): {mae_mean:.4f} ± {mae_std:.4f}\n")
            if avg_rho_true and not all(np.isnan(avg_rho_true)):
                f.write(f"  Rho medio (reale): {np.nanmean(avg_rho_true):.3f}\n")
                f.write(f"  Rho medio (stimato): {np.nanmean(avg_rho_est):.3f}\n")
            if avg_rep and not all(np.isnan(avg_rep)):
                f.write(f"  R medio: {np.nanmean(avg_rep):.3f} ± {np.nanstd(avg_rep):.3f}\n")
            f.write("\n")
            f.write(f"Salute sistema:\n")
            completion_mean = np.mean(completion_rate_arr)
            ir_viol_mean = np.mean(ir_violation_rate_arr)
            health_mean = np.mean(health_score_arr)
            f.write(f"  Completion rate: {completion_mean:.2%}\n")
            f.write(f"  Violazioni ir: {ir_viol_mean:.2%}\n")
            f.write(f"  Health score: {health_mean:.3f}\n")
            if health_mean >= 0.8:
                status = "Eccellente"
            elif health_mean >= 0.6:
                status = "Buono"
            elif health_mean >= 0.4:
                status = "Accettabile"
            else:
                status = "Critico"
            f.write(f"  Stato: {status}\n\n")
            try:
                import pandas as pd
                fase2_baseline_dir = os.path.join(
                    _parent_dir, 
                    "Fase_2", 
                    "esperimenti_fase2_baseline", 
                    f"giorno_{day}_fase2"
                )
                fase2_csv_path = os.path.join(
                    fase2_baseline_dir, 
                    f"{day}_kpi_giornalieri_fase2.csv"
                )
                if os.path.exists(fase2_csv_path):
                    df_f2 = pd.read_csv(fase2_csv_path)
                    v_mech_f2 = df_f2['v_mech_tot'].iloc[0]
                    v_eff_f2 = df_f2['v_eff_tot'].iloc[0]
                    u0_eff_f2 = df_f2['u0_eff_tot'].iloc[0]
                    eff_ratio_f2 = df_f2['eff_ratio_media'].iloc[0]
                    delta_valore = v_eff_total - v_eff_f2
                    delta_valore_pct = 100 * (v_eff_total / v_eff_f2 - 1) if v_eff_f2 > 0 else 0
                    delta_utilita = u0_eff_total - u0_eff_f2
                    delta_utilita_pct = 100 * (u0_eff_total / u0_eff_f2 - 1) if u0_eff_f2 > 0 else 0
                    breakdown_vs_f2 = 100 * (1 - v_eff_total / v_mech_f2) if v_mech_f2 > 0 else 0
                    f.write("Confronto con fase 2 (stesso giorno/seed)\n")
                    f.write("-" * 80 + "\n")
                    f.write("Metriche fase 2 (stateless, senza gap):\n")
                    f.write(f"  v_eff (f2): {v_eff_f2:,.2f}€\n")
                    f.write(f"  u0_eff (f2): {u0_eff_f2:,.2f}€\n")
                    f.write(f"  Breakdown f2: {100*(1-eff_ratio_f2):.2f}%\n\n")
                    f.write("Metriche fase 3 (stateful, con gap):\n")
                    f.write(f"  v_eff (f3): {v_eff_total:,.2f}€\n")
                    f.write(f"  u0_eff (f3): {u0_eff_total:,.2f}€\n")
                    f.write(f"  Breakdown f3 (vs baseline gap): {breakdown_pct:.2f}%\n\n")
                    f.write("Variazioni f3 vs f2:\n")
                    f.write(f"  Delta valore: {delta_valore:+,.2f}€ ({delta_valore_pct:+.1f}%)\n")
                    f.write(f"  Delta utilità: {delta_utilita:+,.2f}€ ({delta_utilita_pct:+.1f}%)\n")
                    f.write(f"  Breakdown f3 vs baseline f2: {breakdown_vs_f2:.2f}%\n\n")
                    if delta_valore < 0:
                        f.write("Nota: meccanismo sacrifica valore economico per migliorare robustezza\n")
                        f.write("      (reputazione, ir, apprendimento), comportamento atteso\n\n")
                    else:
                        f.write("Nota: meccanismo recupera valore rispetto a f2 mantenendo robustezza\n\n")
                else:
                    f.write("Confronto con fase 2\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"File baseline fase 2 non trovato: {fase2_csv_path}\n")
                    f.write("Eseguire prima fase 2 baseline per abilitare confronto\n\n")
            except Exception as e:
                logger_instance.warning(f"Confronto con fase 2: {e}")
                f.write("Confronto con fase 2: dati non disponibili\n\n")
            f.write("Dettaglio orario\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Ora':<6} {'u0_eff':<10} {'v_eff':<10} {'sumP_fin':<10} "
                   f"{'Compl%':<8} {'Ir%':<9} {'Health':<8} {'Mae(rho)':<10}\n")
            f.write("-" * 80 + "\n")
            for i, h in enumerate(hours):
                f.write(
                    f"{h:02d}h    {u0_eff_arr[i]:8,.2f}  {v_eff_arr[i]:8,.2f}  "
                    f"{payment_final_arr[i]:8,.2f}  "
                    f"{completion_rate_arr[i]:6.2%}  {ir_violation_rate_arr[i]:7.2%}  "
                    f"{health_score_arr[i]:6.3f}  {mae_rho_arr[i]:8.4f}\n"
                )
            f.write("\n" + "=" * 80 + "\n")
            f.write("Fine report fase 3\n")
            f.write("=" * 80 + "\n")
        logger_instance.info(f"Report salvato: {report_path}")
    except Exception as e:
        logger_instance.error(f"Generazione report: {e}", exc_info=True)

def run_experiment_phase3(config: ExperimentConfigPhase3) -> None:
    experiment_id = f"imcu_fase3_{config.day}_{config.hour_start:02d}-{config.hour_end:02d}"
    day_output_dir = os.path.join(config.output_dir, f"giorno_{config.day}_fase3")
    os.makedirs(day_output_dir, exist_ok=True)
    logger_exp = setup_experiment_logger(day_output_dir, experiment_id)
    logger_exp.info("=" * 80)
    logger_exp.info(f"Avvio esperimento fase 3: {experiment_id}")
    logger_exp.info("=" * 80)
    start_time = dt.datetime.now()
    try:
        config.validate()
        logger_exp.info("Configurazione validata")
    except Exception as e:
        logger_exp.error(f"Configurazione non valida: {e}")
        raise
    try:
        validate_gap_parameters()
    except AssertionError as e:
        logger_exp.error(str(e))
        raise
    set_random_seed(config.random_seed)
    logger_exp.info(f"Seed globale: {config.random_seed}")
    dm = DataManagerAdaptive(
        raw_txt_path=config.raw_data_path, 
        out_dir=os.path.join(config.output_dir, "dataset_processato"), 
        bbox=config.bbox, 
        random_seed=config.random_seed
    )
    partitions_exist = (
        os.path.exists(dm.part_dir) and 
        len([f for f in os.listdir(dm.part_dir) if f.endswith('.csv')]) > 0
    )
    if not partitions_exist:
        logger_exp.info("Avvio processo etl")
        try:
            dm.parse_raw_to_csv(
                compute_total_lines=True, 
                partition_by="day-hour", 
                write_master_sample=True
            )
            logger_exp.info("Etl completato")
        except Exception as e:
            logger_exp.error(f"Processo etl: {e}", exc_info=True)
            return
    logger_exp.info(f"Creazione popolazione {config.max_users} utenti")
    all_users = dm.create_users_adaptive(
        day=config.day, 
        hour=f"{config.hour_start:02d}", 
        duration_hours=(config.hour_end - config.hour_start), 
        max_users=config.max_users, 
        cost_params=config.cost_params,
        rationality_distribution=config.rationality_distribution, 
        tasks=None,
        allow_no_tasks=True
    )
    if not all_users:
        logger_exp.error("Nessun utente generato")
        return
    logger_exp.info(
        f"Popolazione creata: {len(all_users)} utenti, "
        f"rho medio={np.mean([u.rationality_level for u in all_users]):.3f}"
    )
    hours_range = list(range(config.hour_start, config.hour_end))
    all_hourly_diagnostics = []
    all_winner_ids_fase3 = set()
    for hour_idx, hour in enumerate(hours_range):
        current_time_sec = float(hour * 3600)
        logger_exp.info(f"\n{'='*60}")
        logger_exp.info(f"Ore {hour:02d}:00 (round {hour_idx+1}/{len(hours_range)})")
        logger_exp.info(f"{'='*60}")
        try:
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 1: generazione task")
            tasks_for_this_hour = dm.create_tasks_adaptive(
                day=config.day, 
                hour=f"{hour:02d}", 
                duration_hours=1, 
                cell_size_m=config.cell_size_m, 
                value_mode=config.value_mode, 
                uniform_low=config.task_value_min, 
                uniform_high=config.task_value_max,
                seed=(config.random_seed + hour),
                high_value_threshold_pct=config.high_value_threshold_pct,
                min_reliability_critical=config.min_reliability_critical,
                max_reliability_critical=config.max_reliability_critical,
                min_quality_target_critical=config.min_quality_target_critical,
                max_quality_target_critical=config.max_quality_target_critical,
                min_feedback_weight_critical=config.min_feedback_weight_critical,
                max_feedback_weight_critical=config.max_feedback_weight_critical
            )
            if not tasks_for_this_hour:
                logger_exp.warning(f"[{config.day} h{hour:02d}] Nessun task generato")
                continue
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 1: {len(tasks_for_this_hour)} task generati")
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 2: assegnazione task")
            users_with_tasks = assign_tasks_to_users(
                all_users, 
                tasks_for_this_hour, 
                config.task_radius_m,
                logger_exp
            )
            if users_with_tasks == 0:
                logger_exp.warning(f"[{config.day} h{hour:02d}] Nessun utente con task")
                continue
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 3: selezione bundle e generazione bid")
            PARAM_MAX_TASKS = 5
            users_ready_to_bid = []
            bid_generated_count = 0
            for user in all_users:
                if not user.tasks:
                    continue
                try:
                    selected_bundle = user.select_task_set_bounded(
                        all_tasks=user.tasks,
                        max_tasks=PARAM_MAX_TASKS
                    )
                    if selected_bundle:
                        user.set_tasks(selected_bundle)
                        user.generate_bid()
                        if user.bid >= 0:
                            users_ready_to_bid.append(user)
                            bid_generated_count += 1
                        else:
                            logger_exp.warning(f"Utente {user.id}: bid={user.bid:.2f} non valido")
                except Exception as e:
                    logger_exp.error(f"Utente {user.id}: selezione bundle: {e}", exc_info=True)
                    user.bid = -1.0
            logger_exp.info(
                f"[{config.day} h{hour:02d}] Step 3: {bid_generated_count}/{users_with_tasks} "
                f"utenti pronti (post-euristica, bid validi)"
            )
            if bid_generated_count == 0:
                logger_exp.warning(f"[{config.day} h{hour:02d}] Nessun bid valido")
                continue
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 4: esecuzione asta")
            winners_set, _, diagnostics = run_imcu_auction_adaptive(
                users=users_ready_to_bid,
                tasks=tasks_for_this_hour,
                current_time=current_time_sec,
                debug=True,
                debug_level="summary"
            )
            n_winners = diagnostics.get("winners_count", 0)
            all_winner_ids_fase3.update(winners_set)
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 4: {n_winners} vincitori")
            feedback_count = process_feedback_quality_loop(
                all_users=all_users,
                tasks_for_this_hour=tasks_for_this_hour,
                diagnostics=diagnostics,
                current_time_sec=current_time_sec,
                config_day=config.day,
                hour=hour,
                logger_instance=logger_exp
            )
            logger_exp.info(f"[{config.day} h{hour:02d}] Step 6: aggiornamento credenze")
            learning_count = 0
            for user in all_users:
                try:
                    user.update_platform_beliefs(
                        was_winner=(user.id in winners_set),
                        task_list=user.tasks
                    )
                    learning_count += 1
                    if user.id in winners_set:
                        logger_exp.debug(
                            f"  User {user.id} (vincitore): rho_stimato={user.estimated_rationality:.3f}, "
                            f"r_stimato={user.reputation:.3f}"
                        )
                except Exception as e:
                    logger_exp.error(f"Utente {user.id}: aggiornamento credenze: {e}", exc_info=True)
            logger_exp.info(
                f"[{config.day} h{hour:02d}] Step 6: {learning_count} utenti aggiornati "
                f"(vincitori={len(winners_set)}, perdenti={learning_count - len(winners_set)})"
            )
            gap_m = diagnostics.get("property_checks", {}).get("AdaptiveGAPMetrics", {})
            v_mech = gap_m.get("v_mech", sum(t.value for t in tasks_for_this_hour))
            hourly_result = {
                "day": config.day,
                "hour": hour,
                "n_tasks": len(tasks_for_this_hour),
                "n_users_eligible": diagnostics.get("n_users_eligible", 0),
                "n_winners": n_winners,
                "v_mech": v_mech,
                "sumP": diagnostics.get("payments_sum", 0.0),
                "u0_mech": diagnostics.get("platform_utility_u0", 0.0),
                "gap_metrics": gap_m,
                "diagnostics_full": diagnostics,
                "feedback_tasks_processed": feedback_count
            }
            all_hourly_diagnostics.append(hourly_result)
            logger_exp.info(
                f"[{config.day} h{hour:02d}] Completato: "
                f"v_eff={gap_m.get('v_eff_expost', 0):.2f}€, "
                f"u0_eff={gap_m.get('u0_expost', 0):.2f}€, "
                f"health={gap_m.get('mechanism_health_expost', {}).get('health_score', 0):.3f}"
            )
        except Exception as e:
            logger_exp.error(f"[{config.day} h{hour:02d}] Problema durante l'esecuzione: {e}", exc_info=True)
        finally:
            for u in all_users:
                if hasattr(u, 'reset_state'):
                    u.reset_state(reset_reputation=False, reset_learning=False)
                else:
                    u.tasks = []
                    u.bid = -1.0
                    u.completed = False
                    if hasattr(u, 'actually_completed'):
                        u.actually_completed = False
                    if hasattr(u, 'payment_base'):
                        u.payment_base = 0.0
                    if hasattr(u, 'payment_final'):
                        u.payment_final = 0.0
                if hasattr(u, 'penalty_accumulated'):
                    u.penalty_accumulated = 0.0
    if not all_hourly_diagnostics:
        logger_exp.error("Nessun risultato valido")
        return
    logger_exp.info(f"\nSimulazione completata: {len(all_hourly_diagnostics)} ore valide")
    logger_exp.info("Avvio diagnostica e aggregazione finale")
    logger_exp.info(f"\n{'='*60}")
    logger_exp.info(f"Step 8: aggregazione e reporting")
    logger_exp.info(f"{'='*60}")
    csv_header = (
        "ora,v_mech,u0_eff,v_eff,sumP_final,tasso_compl,mae_rho,incentivo_eur,"
        "vincitori,n_idonei,health_score,feedback_tasks\n"
    )
    csv_rows = []
    for r in all_hourly_diagnostics:
        gap_m = r.get('gap_metrics', {})
        health_m = gap_m.get('mechanism_health_expost', {})
        csv_rows.append(
            f"{r['hour']},{r.get('v_mech', 0):.2f},"
            f"{gap_m.get('u0_expost', 0):.2f},"
            f"{gap_m.get('v_eff_expost', 0):.2f},{gap_m.get('sum_payment_final', 0):.2f},"
            f"{health_m.get('completion_rate_tasks', 0):.4f},"
            f"{gap_m.get('mae_rho_estimation', 0):.4f},"
            f"{gap_m.get('total_incentive_bonus_malus', 0):.2f},"
            f"{r['n_winners']},{r['n_users_eligible']},"
            f"{health_m.get('health_score', 0):.4f},"
            f"{r.get('feedback_tasks_processed', 0)}\n"
        )
    safe_csv_write(
        csv_header + "".join(csv_rows), 
        os.path.join(day_output_dir, f"{config.day}_kpi_orari_fase3.csv"), 
        logger_exp
    )
    save_final_user_state(
        all_users, 
        os.path.join(day_output_dir, f"{config.day}_stato_finale_utenti_fase3.csv"),
        logger_exp
    )
    end_time = dt.datetime.now()
    generate_summary_report_phase3(
        output_dir=day_output_dir, 
        day=config.day, 
        hourly_results=all_hourly_diagnostics, 
        config=config, 
        logger_instance=logger_exp
    )
    logger_exp.info(f"\n{'='*60}\nStep 9: generazione grafici\n{'='*60}")
    try:
        plotter = ScientificPlotterAdaptive(output_dir=day_output_dir)
        hours_plot = [r['hour'] for r in all_hourly_diagnostics]
        mae_history = [r['gap_metrics'].get('mae_rho_estimation', float('nan')) for r in all_hourly_diagnostics]
        health_scores = [r['gap_metrics'].get('mechanism_health_expost', {}).get('health_score', 0.0) for r in all_hourly_diagnostics]
        ir_violations = [r['gap_metrics'].get('mechanism_health_expost', {}).get('ir_violation_rate', 0.0) for r in all_hourly_diagnostics]
        compl_rates = [r['gap_metrics'].get('mechanism_health_expost', {}).get('completion_rate_tasks', 0.0) for r in all_hourly_diagnostics]
        sum_base = [r['gap_metrics'].get('sum_payment_base', 0.0) for r in all_hourly_diagnostics]
        sum_final = [r['gap_metrics'].get('sum_payment_final', 0.0) for r in all_hourly_diagnostics]
        v_eff = [r['gap_metrics'].get('v_eff_expost', 0.0) for r in all_hourly_diagnostics]
        v_mech = [r.get('v_mech', 0.0) for r in all_hourly_diagnostics]
        plotter.plot_learning_convergence(
            hours=hours_plot,
            mae_history=mae_history,
            title=f"Convergenza apprendimento ({config.day})",
            filename=f"gap_learning_mae_{config.day}.png"
        )
        logger_exp.info("  Grafico generato: learning convergence")
        plotter.plot_health_dashboard(
            hours=hours_plot,
            health_scores=health_scores,
            ir_violations=ir_violations,
            completion_rates=compl_rates,
            title=f"Stato salute sistema ({config.day})",
            filename=f"gap_health_dashboard_{config.day}.png"
        )
        logger_exp.info("  Grafico generato: health dashboard")
        last_hour_winners = []
        try:
            if all_hourly_diagnostics:
                last_diag = all_hourly_diagnostics[-1].get("diagnostics_full", {})
                gap_metrics = last_diag.get("property_checks", {}).get("AdaptiveGAPMetrics", {})
                completed_map = gap_metrics.get("completed_tasks_by_winner", {})
                if completed_map:
                    last_hour_winners_ids = set(completed_map.keys())
                    last_hour_winners = [u for u in all_users if u.id in last_hour_winners_ids]
                    logger_exp.info(f"Ultimi vincitori: {len(last_hour_winners)}")
                else:
                    logger_exp.warning("Nessun task completato nell'ultima ora")
            else:
                logger_exp.warning("Nessuna diagnostica oraria disponibile")
        except Exception as e:
            logger_exp.error(f"Estrazione vincitori: {e}", exc_info=True)
        if last_hour_winners:
            base_list = [u.payment_base for u in last_hour_winners if hasattr(u, 'payment_base')]
            final_list = [u.payment_final for u in last_hour_winners if hasattr(u, 'payment_final')]
            if base_list and final_list and len(base_list) == len(final_list):
                plotter.plot_incentive_impact(
                    base_payments=base_list,
                    final_payments=final_list,
                    title=f"Analisi incentivi utenti (ultima ora, {config.day})",
                    filename=f"gap_incentives_scatter_{config.day}.png"
                )
                logger_exp.info("  Grafico generato: incentivi")
            else:
                logger_exp.warning("Dati pagamento individuali non disponibili per grafico incentivi")
        else:
            logger_exp.warning("Nessun vincitore per grafico incentivi")
        plotter.plot_mech_vs_eff_timeseries(
            hours=hours_plot,
            v_mech=v_mech,
            v_eff=v_eff,
            title=f"Efficienza: potenziale vs reale ({config.day})",
            filename=f"fase3_efficiency_gap_{config.day}.png",
            annotate_gap=True
        )
        logger_exp.info("  Grafico generato: efficienza")
        logger_exp.info("Tutti i grafici generati correttamente")
    except Exception as e:
        logger_exp.error(f"Generazione grafici: {e}", exc_info=True)
    save_experiment_metadata(
        output_dir=day_output_dir, 
        experiment_id=experiment_id, 
        config=config, 
        start_time=start_time, 
        end_time=end_time
    )
    duration = (end_time - start_time).total_seconds()
    logger_exp.info("=" * 80)
    logger_exp.info(f"Esperimento completato in {duration:.1f}s")
    logger_exp.info(f"Output: {day_output_dir}")
    logger_exp.info("=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description="Fase 3 (GAP)", 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--raw", required=True, help="File dati grezzo")
    parser.add_argument("--day", required=True, help="Giorno (aaaa-mm-gg)")
    parser.add_argument("--start", type=int, default=8)
    parser.add_argument("--end", type=int, default=20)
    parser.add_argument("--out", default="esperimenti_fase3")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cell", type=int, default=500)
    parser.add_argument("--radius", type=float, default=2500.0)
    parser.add_argument("--max_users", type=int, default=316)
    parser.add_argument("--cost_min", type=float, default=0.5)
    parser.add_argument("--cost_max", type=float, default=5.0)
    parser.add_argument("--value_min", type=float, default=1.0)
    parser.add_argument("--value_max", type=float, default=5.0)
    parser.add_argument("--value_mode", choices=["uniform", "demand_log"], default="uniform")
    parser.add_argument("--rationality", choices=["perfect", "high", "mixed", "low"], default="mixed")
    parser.add_argument("--high_value_pct", type=float, default=0.80)
    parser.add_argument("--min_rel_crit", type=float, default=0.70)
    parser.add_argument("--max_rel_crit", type=float, default=0.85)
    parser.add_argument("--min_qual_crit", type=float, default=0.40)
    parser.add_argument("--max_qual_crit", type=float, default=0.60)
    parser.add_argument("--min_weight_crit", type=float, default=1.5)
    parser.add_argument("--max_weight_crit", type=float, default=2.5)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--norm", choices=["percentiles", "log", "power"], default="percentiles")
    parser.add_argument("--p_low", type=float, default=2.0)
    parser.add_argument("--p_high", type=float, default=98.0)
    parser.add_argument("--block", type=int, default=4)
    parser.add_argument("--save_raw_logs", action="store_true")
    parser.add_argument("--no_verify", action="store_true")
    args = parser.parse_args()
    config = ExperimentConfigPhase3(
        raw_data_path=args.raw, 
        day=args.day, 
        hour_start=args.start, 
        hour_end=args.end, 
        block_size=args.block,
        cell_size_m=args.cell, 
        task_radius_m=args.radius, 
        bbox=None,
        max_users=args.max_users, 
        cost_params=(args.cost_min, args.cost_max), 
        value_mode=args.value_mode, 
        norm_mode=args.norm, 
        percentile_low=args.p_low, 
        percentile_high=args.p_high, 
        plot_dpi=args.dpi, 
        output_dir=args.out, 
        random_seed=args.seed, 
        save_raw_logs=args.save_raw_logs, 
        verify_properties=not args.no_verify, 
        rationality_distribution=args.rationality, 
        task_value_min=args.value_min, 
        task_value_max=args.value_max,
        high_value_threshold_pct=args.high_value_pct,
        min_reliability_critical=args.min_rel_crit,
        max_reliability_critical=args.max_rel_crit,
        min_quality_target_critical=args.min_qual_crit,
        max_quality_target_critical=args.max_qual_crit,
        min_feedback_weight_critical=args.min_weight_crit,
        max_feedback_weight_critical=args.max_weight_crit
    )
    try:
        run_experiment_phase3(config)
        sys.exit(0)
    except Exception as e:
        print(f"\nProblema durante l'esecuzione: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()