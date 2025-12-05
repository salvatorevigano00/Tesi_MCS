from __future__ import annotations
import os
import sys
from typing import Dict, Tuple, List, Any, Optional
from dataclasses import dataclass
import argparse
import datetime as dt
import numpy as np
import warnings
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _parent_dir)

try:
    from Fase_1.fase_1 import ExperimentConfig as ExperimentConfigBase, setup_experiment_logger, save_experiment_metadata, safe_csv_write
except ImportError as e:
    raise ImportError(f"Impossibile importare i moduli della Fase 1. Verifica che Fase_1/fase_1.py esista. Dettagli tecnici: {e}")

try:
    from Fase_2.data_manager_bounded import DataManagerRational
    from Fase_2.classes_bounded import BoundedRationalUser, Task, set_random_seed
except ImportError as e:
    raise ImportError(f"Impossibile importare i moduli core della Fase 2. Verifica che data_manager_bounded.py e classes_bounded.py esistano. Dettagli tecnici: {e}")

try:
    from Fase_2.imcu_bounded import run_imcu_auction_bounded
except ImportError as e:
    raise ImportError(f"Impossibile importare imcu_bounded.py. Verifica che il modulo esista. Dettagli tecnici: {e}")

try:
    from Fase_2.plot_bounded import ScientificPlotterRational
except ImportError as e:
    raise ImportError(f"Impossibile importare plot_bounded.py. Verifica che il modulo esista. Dettagli tecnici: {e}")

def _generate_profile_names() -> List[str]:
    return ["Quasi-Rational", "Bounded Honest", "Bounded Moderate", "Bounded Opportunistic"]

PROFILE_NAMES = _generate_profile_names()

@dataclass
class ExperimentConfigPhase2(ExperimentConfigBase):
    rationality_distribution: str = "mixed"
    defection_mode: str = "profile_based"
    fft_type: str = "LENIENT"
    task_value_min: float = 1.0
    task_value_max: float = 5.0

    def validate(self) -> None:
        super().validate()
        if self.rationality_distribution not in ("high", "mixed", "low"):
            raise ValueError(f"La distribuzione di razionalità (rationality_distribution) deve essere 'high', 'mixed' o 'low', ricevuto: '{self.rationality_distribution}'")
        if self.defection_mode not in ("profile_based", "uniform", "none"):
            raise ValueError(f"La modalità di defezione (defection_mode) deve essere 'profile_based', 'uniform' o 'none', ricevuto: '{self.defection_mode}'")
        if self.defection_mode != "profile_based":
            warnings.warn(f"La modalità di defezione '{self.defection_mode}' non è supportata in questa configurazione. Verrà utilizzata 'profile_based'.", UserWarning)
        if self.fft_type not in ("LENIENT", "STRICT", "ZIGZAG"):
            raise ValueError(f"Il tipo di FFT (fft_type) deve essere 'LENIENT', 'STRICT' o 'ZIGZAG', ricevuto: '{self.fft_type}'")
        if self.task_value_min <= 0:
            raise ValueError(f"Valore minimo task (task_value_min) deve essere > 0, ricevuto: {self.task_value_min}")
        if self.task_value_max <= self.task_value_min:
            raise ValueError(f"Valore massimo task (task_value_max) deve essere maggiore del minimo, ricevuto: min={self.task_value_min}, max={self.task_value_max}")

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["razionalita_limitata"] = {
            "distribuzione_razionalita": self.rationality_distribution,
            "modalita_defezione": self.defection_mode,
            "tipo_fft": self.fft_type,
            "valore_task_min": self.task_value_min,
            "valore_task_max": self.task_value_max,
        }
        return base_dict

def compute_winners_profile_distribution(users: List[BoundedRationalUser], winners_set: set[int]) -> Dict[str, int]:
    distribuzione = {prof: 0 for prof in PROFILE_NAMES}
    for user in users:
        if user.id in winners_set:
            profilo = user.honesty_profile
            if profilo not in distribuzione:
                distribuzione[profilo] = 0
            distribuzione[profilo] += 1
    return distribuzione

def run_hourly_simulation_phase2(dm: DataManagerRational, config: ExperimentConfigPhase2, day: str, hour: int, persistent_users: List[BoundedRationalUser], logger: Any) -> Optional[Dict[str, Any]]:
    try:
        logger.info(f"[{day} H{hour:02d}] Avvio simulazione oraria Fase 2 (coorte persistente)")
        tasks = dm.create_tasks(
            day=day,
            hour=f"{hour:02d}",
            duration_hours=1,
            cell_size_m=config.cell_size_m,
            value_mode=config.value_mode,
            uniform_low=config.task_value_min,
            uniform_high=config.task_value_max,
            seed=None,
        )
        logger.info("\n" + "=" * 70)
        logger.info(f"[STEP 1] Generazione task per l'ora H{hour:02d}")
        logger.info(f"  Task generati: {len(tasks)}")
        if tasks:
            valori = [t.value for t in tasks]
            logger.info(f"  Valore task: min={min(valori):.2f}, max={max(valori):.2f}, media={np.mean(valori):.2f}")
            logger.info(f"  Valore totale task disponibili: {sum(valori):.2f} euro")
        logger.info("=" * 70 + "\n")
        if not tasks:
            logger.warning(f"[{day} H{hour:02d}] Nessun task generato. L'ora viene saltata.")
            return None
        users_with_tasks: List[BoundedRationalUser] = []
        for user in persistent_users:
            candidate_tasks: List[Task] = []
            for task in tasks:
                dist_m = user.calculate_distance_to(task)
                if dist_m <= config.task_radius_m:
                    candidate_tasks.append(task)
            if candidate_tasks:
                desired_tasks = user.select_task_set_bounded(candidate_tasks)
                user.set_tasks(desired_tasks)
                if desired_tasks:
                    user.generate_bid()
                    users_with_tasks.append(user)
        logger.info(f"  Utenti con almeno un task selezionato (post-FFT): {len(users_with_tasks)} su {len(persistent_users)}")
        if not users_with_tasks:
            logger.warning(f"[{day} H{hour:02d}] Nessun utente ha selezionato task. L'ora viene saltata.")
            return None
        winners_set, _, diagnostics = run_imcu_auction_bounded(
            users_with_tasks,
            verify_properties=config.verify_properties,
            debug=False,
        )
        winners = [u for u in users_with_tasks if u.id in winners_set]
        logger.info(f"[STEP 3] Risultati asta (ex-ante) H{hour:02d}")
        logger.info(f"  Vincitori: {len(winners_set)}")
        logger.info(f"  Valore meccanismo v_mech: {diagnostics.get('platform_value_vS', 0.0):.2f} euro")
        logger.info(f"  Pagamenti totali sumP: {diagnostics.get('payments_sum', 0.0):.2f} euro")
        logger.info(f"  Utilità piattaforma u0_mech: {diagnostics.get('platform_utility_u0', 0.0):.2f} euro")
        logger.info(f"[STEP 4] Analisi azzardo morale H{hour:02d}")
        n_defections_total = 0
        n_defections_detected = 0
        for winner in winners:
            if hasattr(winner, "actually_completed"):
                if not winner.actually_completed:
                    n_defections_total += 1
                    if winner.completed is False:
                        n_defections_detected += 1
        if n_defections_total > 0:
            logger.info(f"  Defezioni totali (reali): {n_defections_total} su {len(winners)} vincitori")
            logger.info(f"  Defezioni rilevate (sanzionate): {n_defections_detected} su {len(winners)} vincitori")
        v_mech = diagnostics.get("platform_value_vS", 0.0)
        sumP = diagnostics.get("payments_sum", 0.0)
        u0_mech = diagnostics.get("platform_utility_u0", 0.0)
        v_eff = diagnostics.get("property_checks", {}).get("BoundedRationalityMetrics", {}).get("v_eff_expost", 0.0)
        completed_count = sum(1 for w in winners if hasattr(w, "actually_completed") and w.actually_completed)
        logger.info(f"[{day} H{hour:02d}] Valore effettivo v_eff = {v_eff:.2f} euro, completamenti reali = {completed_count}/{len(winners)}")
        u0_eff = v_eff - sumP
        eff_ratio = v_eff / v_mech if v_mech > 1e-9 else 0.0
        winner_profiles = compute_winners_profile_distribution(persistent_users, winners_set)
        return {
            "day": day,
            "hour": hour,
            "n_tasks": len(tasks),
            "n_users": len(persistent_users),
            "n_users_with_tasks": len(users_with_tasks),
            "n_winners": len(winners_set),
            "v_mech": v_mech,
            "sumP": sumP,
            "u0_mech": u0_mech,
            "v_eff": v_eff,
            "u0_eff": u0_eff,
            "eff_ratio": eff_ratio,
            "winner_profiles": winner_profiles,
            "diagnostics": diagnostics,
            "n_defections_detected": n_defections_detected,
            "n_defections_total": n_defections_total,
            "n_users_blacklisted": 0,
        }
    except Exception as e:
        logger.error(f"[{day} H{hour:02d}] Errore critico nella simulazione oraria: {e}", exc_info=True)
        return None

def generate_summary_report_phase2(output_dir: str, day: str, hourly_results: List[Dict[str, Any]], config: ExperimentConfigPhase2, logger: Any) -> None:
    report_path = os.path.join(output_dir, f"{day}_REPORT_RIEPILOGATIVO_FASE2.txt")
    try:
        hours = [r["hour"] for r in hourly_results]
        v_mech_arr = [r["v_mech"] for r in hourly_results]
        v_eff_arr = [r["v_eff"] for r in hourly_results]
        u0_mech_arr = [r["u0_mech"] for r in hourly_results]
        u0_eff_arr = [r["u0_eff"] for r in hourly_results]
        eff_ratio_arr = [r["eff_ratio"] for r in hourly_results]
        winners_arr = [r["n_winners"] for r in hourly_results]
        defections_detected_arr = [r.get("n_defections_detected", 0) for r in hourly_results]
        defections_total_arr = [r.get("n_defections_total", 0) for r in hourly_results]
        total_profiles = {prof: 0 for prof in PROFILE_NAMES}
        for r in hourly_results:
            for prof, count in r["winner_profiles"].items():
                if prof in total_profiles:
                    total_profiles[prof] += count
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Report simulazione IMCU Fase 2 - giornata {day}\n")
            f.write("Analisi vulnerabilità del meccanismo con popolazione persistente (senza apprendimento)\n")
            f.write("=" * 80 + "\n\n")
            f.write("Configurazione esperimento\n")
            f.write("-" * 80 + "\n")
            f.write(f"Giorno simulato: {config.day}\n")
            f.write(f"Finestra oraria: {config.hour_start:02d}:00 - {config.hour_end:02d}:00\n")
            f.write(f"Seed casuale: {config.random_seed}\n\n")
            f.write("Parametri task:\n")
            f.write(f"  Dimensione cella: {config.cell_size_m} m\n")
            f.write(f"  Raggio assegnazione task: {config.task_radius_m} m\n")
            f.write(f"  Modalità valore: {config.value_mode}\n")
            f.write(f"  Intervallo valore task: [{config.task_value_min}, {config.task_value_max}] euro\n\n")
            f.write("Parametri utenti (razionalità limitata):\n")
            f.write(f"  Numero massimo utenti/ora: {config.max_users}\n")
            f.write(f"  Distribuzione razionalità: {config.rationality_distribution}\n")
            f.write(f"  Modalità defezione: {config.defection_mode}\n\n")
            f.write("Statistiche aggregate giornaliere\n")
            f.write("-" * 80 + "\n")
            v_mech_total = sum(v_mech_arr)
            v_eff_total = sum(v_eff_arr)
            u0_mech_total = sum(u0_mech_arr)
            u0_eff_total = sum(u0_eff_arr)
            sumP_total = v_mech_total - u0_mech_total
            f.write("Metriche ex-ante (teoria del meccanismo IMCU):\n")
            f.write(f"Valore meccanismo v(S_mech): {v_mech_total:,.2f} euro\n")
            f.write(f"Pagamenti totali (sumP): {sumP_total:,.2f} euro\n")
            f.write(f"Utilità piattaforma u0_mech: {u0_mech_total:,.2f} euro\n")
            if v_mech_total > 0:
                f.write(f"Efficienza economica (u0_mech/v_mech): {u0_mech_total/v_mech_total:.4f}\n\n")
            f.write("Metriche ex-post (realtà comportamentale, dopo le defezioni):\n")
            f.write(f"Valore effettivo v(S_eff): {v_eff_total:,.2f} euro\n")
            f.write(f"Utilità piattaforma u0_eff: {u0_eff_total:,.2f} euro\n")
            f.write(f"Rapporto di realizzazione eff_ratio (media): {np.mean(eff_ratio_arr):.4f}\n")
            f.write(f"Rapporto di realizzazione eff_ratio (mediana): {np.median(eff_ratio_arr):.4f}\n")
            f.write(f"Rapporto di realizzazione eff_ratio (min): {min(eff_ratio_arr):.4f}\n")
            f.write(f"Rapporto di realizzazione eff_ratio (max): {max(eff_ratio_arr):.4f}\n\n")
            breakdown_total = v_mech_total - v_eff_total
            breakdown_pct = 100 * breakdown_total / v_mech_total if v_mech_total > 0 else 0.0
            f.write("Rottura del meccanismo (gap ex-ante vs ex-post):\n")
            f.write(f"Perdita di valore (v_mech - v_eff): {breakdown_total:,.2f} euro\n")
            f.write(f"Tasso di rottura (percentuale di valore perso): {breakdown_pct:.2f}%\n\n")
            f.write("Analisi azzardo morale (coorte persistente, senza apprendimento):\n")
            f.write(f"Defezioni totali (reali): {sum(defections_total_arr)}\n")
            f.write(f"Defezioni rilevate (sanzionate): {sum(defections_detected_arr)}\n")
            f.write(f"Tasso medio defezioni rilevate: {np.mean(defections_detected_arr):.2f} defezioni/ora\n")
            f.write(f"Tasso medio defezioni totali: {np.mean(defections_total_arr):.2f} defezioni/ora\n\n")
            f.write(f"Vincitori totali nell'intera giornata: {sum(winners_arr)}\n")
            f.write(f"Ore simulate con successo: {len(hours)}\n\n")
            f.write("Distribuzione dei profili vincitori (sull'intera giornata)\n")
            f.write("-" * 80 + "\n")
            total_winners_sum = max(1, sum(total_profiles.values()))
            for prof, count in total_profiles.items():
                pct = 100 * count / total_winners_sum
                f.write(f"{prof:<30} {count:>5} ({pct:>5.1f}%)\n")
            f.write("\n")
            f.write("Dettaglio orario Fase 2 (coorte persistente, senza apprendimento)\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Ora':<6} {'v_mech':<12} {'v_eff':<12} {'u0_eff':<12} {'Rapp.':<8} {'Vincitori':<10} {'Def. ril.':<10} {'Def. tot.':<10}\n")
            f.write("-" * 80 + "\n")
            for i, h in enumerate(hours):
                f.write(f"{h:02d}h    {v_mech_arr[i]:10,.2f}  {v_eff_arr[i]:10,.2f}  {u0_eff_arr[i]:10,.2f}  {eff_ratio_arr[i]:6.4f}  {winners_arr[i]:8d}  {defections_detected_arr[i]:9d}  {defections_total_arr[i]:9d}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("Fine report Fase 2\n")
            f.write("=" * 80 + "\n")
        logger.info(f"Report riepilogativo Fase 2 salvato in: {report_path}")
    except Exception as e:
        logger.error(f"Errore durante la generazione del report riepilogativo: {e}", exc_info=True)

def run_experiment_phase2(config: ExperimentConfigPhase2) -> None:
    experiment_id = f"imcu_fase2_{config.day}_{config.hour_start:02d}-{config.hour_end:02d}"
    day_output_dir = os.path.join(config.output_dir, f"giorno_{config.day}_fase2")
    os.makedirs(day_output_dir, exist_ok=True)
    logger = setup_experiment_logger(day_output_dir, experiment_id)
    logger.info("=" * 80)
    logger.info(f"Avvio esperimento IMCU Fase 2 (coorte persistente): {experiment_id}")
    logger.info("=" * 80)
    start_time = dt.datetime.now()
    logger.info(f"Avvio simulazione: {start_time.isoformat()}")
    try:
        config.validate()
        logger.info("Configurazione verificata con successo.")
    except Exception as e:
        logger.error(f"Configurazione non valida: {e}")
        raise
    set_random_seed(config.random_seed)
    logger.info(f"Seed casuale globale impostato: {config.random_seed}")
    logger.info(f"Caricamento DataManagerRational da: {config.raw_data_path}")
    dm = DataManagerRational(
        raw_txt_path=config.raw_data_path,
        out_dir=os.path.join(config.output_dir, "dataset_processato"),
        bbox=config.bbox,
        random_seed=config.random_seed,
    )
    partitions_exist = os.path.exists(dm.part_dir) and len([f for f in os.listdir(dm.part_dir) if f.endswith(".csv")]) > 0
    if not partitions_exist:
        logger.info("Partizioni dati non trovate, avvio del processo ETL (parsing dei dati grezzi).")
        metadata_etl = dm.parse_raw_to_csv(compute_total_lines=True, partition_by="day-hour", write_master_sample=True)
        logger.info(f"ETL completato: {metadata_etl['records_written']:,} record processati.")
    else:
        logger.info("Partizioni dati già presenti, fase di parsing saltata.")
    hours_range = list(range(config.hour_start, config.hour_end))
    logger.info("=" * 80)
    logger.info("Creazione coorte persistente di utenti")
    logger.info(f"Finestra temporale: H{config.hour_start:02d} - H{config.hour_end:02d}")
    logger.info(f"Dimensione coorte desiderata: {config.max_users} utenti")
    logger.info("=" * 80)
    persistent_users = dm.create_users_bounded(
        day=config.day,
        hour=f"{config.hour_start:02d}",
        duration_hours=(config.hour_end - config.hour_start),
        max_users=config.max_users,
        rationality_distribution=config.rationality_distribution,
        tasks=None,
        task_radius_m=config.task_radius_m,
        cost_params=config.cost_params,
    )
    if not persistent_users:
        logger.error("Errore critico: nessun utente nella coorte persistente. Esperimento interrotto.")
        return
    logger.info(f"Coorte persistente creata: {len(persistent_users)} utenti attivi.")
    profile_counts: Dict[str, int] = {}
    for u in persistent_users:
        prof = u.honesty_profile
        profile_counts[prof] = profile_counts.get(prof, 0) + 1
    logger.info("Distribuzione dei profili nella coorte:")
    for prof in PROFILE_NAMES:
        count = profile_counts.get(prof, 0)
        pct = 100 * count / len(persistent_users) if persistent_users else 0.0
        logger.info(f"  {prof:<30} {count:>5} ({pct:>5.1f}%)")
    logger.info("=" * 80)
    logger.info(f"Inizio loop orario su {len(hours_range)} ore con coorte persistente...")
    logger.info("=" * 80)
    all_hourly_results: List[Dict[str, Any]] = []
    with logging_redirect_tqdm():
        for hour in tqdm(hours_range, desc=f"Simulazione giorno {config.day}", unit="ora"):
            result = run_hourly_simulation_phase2(
                dm=dm,
                config=config,
                day=config.day,
                hour=hour,
                persistent_users=persistent_users,
                logger=logger,
            )
            if result:
                all_hourly_results.append(result)
    if not all_hourly_results:
        logger.error("Nessun risultato orario valido disponibile. Impossibile generare KPI e report.")
        return
    logger.info(f"Simulazioni orarie completate: {len(all_hourly_results)}/{len(hours_range)} ore valide.")
    logger.info("Aggregazione risultati e generazione degli output CSV...")
    csv_header_hourly = "ora,v_mech,sumP,u0_mech,v_eff,u0_eff,eff_ratio,vincitori,utenti_attivi,defezioni_rilevate,defezioni_totali\n"
    csv_rows_hourly = []
    for r in all_hourly_results:
        csv_rows_hourly.append(
            f"{r['hour']},{r['v_mech']},{r['sumP']},{r['u0_mech']},{r['v_eff']},{r['u0_eff']},{r['eff_ratio']},{r['n_winners']},{r.get('n_users_with_tasks', 0)},{r.get('n_defections_detected', 0)},{r.get('n_defections_total', 0)}\n"
        )
    safe_csv_write(csv_header_hourly + "".join(csv_rows_hourly), os.path.join(day_output_dir, f"{config.day}_kpi_orari_fase2.csv"), logger)
    v_mech_sum = sum(r["v_mech"] for r in all_hourly_results)
    sumP_sum = sum(r["sumP"] for r in all_hourly_results)
    v_eff_sum = sum(r["v_eff"] for r in all_hourly_results)
    eff_ratio_mean = float(np.mean([r["eff_ratio"] for r in all_hourly_results]))
    csv_daily = "v_mech_tot,sumP_tot,u0_mech_tot,v_eff_tot,u0_eff_tot,eff_ratio_media\n"
    csv_daily += f"{v_mech_sum},{sumP_sum},{v_mech_sum - sumP_sum},{v_eff_sum},{v_eff_sum - sumP_sum},{eff_ratio_mean}\n"
    safe_csv_write(csv_daily, os.path.join(day_output_dir, f"{config.day}_kpi_giornalieri_fase2.csv"), logger)
    try:
        logger.info("Generazione delle visualizzazioni per la Fase 2...")
        figures_dir = os.path.join(day_output_dir, "grafici")
        os.makedirs(figures_dir, exist_ok=True)
        plotter = ScientificPlotterRational(output_dir=figures_dir, lang="it", dpi=config.plot_dpi, style="publication")
        hours = [r["hour"] for r in all_hourly_results]
        v_mech_arr = [r["v_mech"] for r in all_hourly_results]
        v_eff_arr = [r["v_eff"] for r in all_hourly_results]
        u0_mech_arr = [r["u0_mech"] for r in all_hourly_results]
        u0_eff_arr = [r["u0_eff"] for r in all_hourly_results]
        total_profiles = {prof: 0 for prof in PROFILE_NAMES}
        for r in all_hourly_results:
            for prof, count in r["winner_profiles"].items():
                if prof in total_profiles:
                    total_profiles[prof] += count
        plotter.plot_mech_vs_eff_timeseries(
            hours,
            v_mech_arr,
            v_eff_arr,
            title=f"Valore meccanismo vs valore effettivo (ex-post) — {config.day}",
            filename=f"{config.day}_valore_mech_vs_eff.png",
            annotate_gap=True,
        )
        plotter.plot_utility_compare(
            hours,
            u0_mech_arr,
            u0_eff_arr,
            title=f"Utilità piattaforma (ex-ante vs ex-post) — {config.day}",
            filename=f"{config.day}_utilita_piattaforma.png",
        )
        plotter.plot_efficiency_series(
            hours,
            v_mech_arr,
            v_eff_arr,
            title=f"Rapporto di realizzazione v_eff / v_mech — {config.day}",
            filename=f"{config.day}_rapporto_realizzazione.png",
        )
        plotter.plot_winners_profile_bar(
            total_profiles,
            title=f"Distribuzione profili vincitori (totale giornata) — {config.day}",
            filename=f"{config.day}_distribuzione_profili.png",
        )
        logger.info(f"Grafici Fase 2 generati in: {figures_dir}")
    except Exception as e:
        logger.error(f"Errore durante la generazione delle visualizzazioni: {e}", exc_info=True)
    end_time = dt.datetime.now()
    generate_summary_report_phase2(output_dir=day_output_dir, day=config.day, hourly_results=all_hourly_results, config=config, logger=logger)
    save_experiment_metadata(output_dir=day_output_dir, experiment_id=experiment_id, config=config, start_time=start_time, end_time=end_time)
    duration = (end_time - start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"Esperimento completato in {duration:.1f} secondi complessivi")
    logger.info(f"Output salvati nella directory: {day_output_dir}")
    logger.info("=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description="Orchestratore simulazione IMCU Fase 2 (razionalità limitata)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--raw", required=True, help="Percorso del file dati grezzo")
    parser.add_argument("--day", required=True, help="Giorno da simulare (formato AAAA-MM-GG)")
    parser.add_argument("--start", type=int, default=8, help="Ora di inizio (inclusa, 0-23)")
    parser.add_argument("--end", type=int, default=20, help="Ora di fine (esclusa, 1-24)")
    parser.add_argument("--out", default="esperimenti_fase2", help="Directory radice per gli output")
    parser.add_argument("--seed", type=int, default=42, help="Seed casuale per la riproducibilità")
    parser.add_argument("--cell", type=int, default=500, help="Dimensione cella della griglia (metri)")
    parser.add_argument("--radius", type=float, default=2500.0, help="Raggio massimo assegnazione task (metri)")
    parser.add_argument("--max_users", type=int, default=316, help="Dimensione coorte persistente (numero utenti)")
    parser.add_argument("--cost_min", type=float, default=0.45, help="Costo/km minimo per utente (€/km)")
    parser.add_argument("--cost_max", type=float, default=0.70, help="Costo/km massimo per utente (€/km)")
    parser.add_argument("--value_min", type=float, default=1.8, help="Valore task minimo (€)")
    parser.add_argument("--value_max", type=float, default=15.0, help="Valore task massimo (€)")
    parser.add_argument("--value_mode", choices=["uniform", "demand_log"], default="demand_log", help="Modalità di generazione del valore dei task")
    parser.add_argument("--rationality", choices=["high", "mixed", "low"], default="mixed", help="Distribuzione di razionalità degli utenti")
    parser.add_argument("--defection", choices=["profile_based", "uniform", "none"], default="profile_based", help="Modalità di defezione")
    parser.add_argument("--fft", choices=["LENIENT", "STRICT", "ZIGZAG"], default="LENIENT", help="Tipo FFT")
    parser.add_argument("--dpi", type=int, default=300, help="Risoluzione DPI per i grafici")
    parser.add_argument("--norm", choices=["percentiles", "log", "power"], default="percentiles", help="Modalità di normalizzazione per le heatmap")
    parser.add_argument("--p_low", type=float, default=2.0, help="Percentile basso per normalizzazione colormap")
    parser.add_argument("--p_high", type=float, default=98.0, help="Percentile alto per normalizzazione colormap")
    parser.add_argument("--block", type=int, default=4, help="Ampiezza blocchi ore (non usato)")
    parser.add_argument("--save_raw_logs", action="store_true", help="Salva eventuali log grezzi JSON/CSV (non usato)")
    parser.add_argument("--no_verify", action="store_true", help="Disabilita la verifica delle proprietà IMCU")
    args = parser.parse_args()
    config = ExperimentConfigPhase2(
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
        defection_mode=args.defection,
        fft_type=args.fft,
        task_value_min=args.value_min,
        task_value_max=args.value_max,
    )
    try:
        run_experiment_phase2(config)
        sys.exit(0)
    except Exception as e:
        print(f"Errore critico durante l'esecuzione dell'esperimento: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()