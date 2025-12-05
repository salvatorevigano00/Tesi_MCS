from __future__ import annotations
import os
from pathlib import Path
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from typing import Dict, Tuple, List, Any, Optional
from dataclasses import dataclass
from classes import set_random_seed
from data_manager import DataManager, GeoConstants, latlon_to_cell
from imcu import run_imcu_auction
from plot import ScientificPlotter

import json
import argparse
import logging
import hashlib
import platform
import datetime as dt
import warnings
import traceback
import numpy as np

@dataclass
class ExperimentConfig:
    raw_data_path: str
    day: str
    hour_start: int
    hour_end: int
    block_size: int
    cell_size_m: int
    task_radius_m: Optional[float]
    bbox: Optional[Tuple[float, float, float, float]]
    max_users: int
    cost_params: Tuple[float, float]
    value_mode: str
    norm_mode: str
    percentile_low: float
    percentile_high: float
    plot_dpi: int
    output_dir: str
    random_seed: int
    save_raw_logs: bool
    verify_properties: bool
    dataset_out: Optional[str] = None
    
    def validate(self) -> None:
        if not os.path.exists(self.raw_data_path):
            raise FileNotFoundError(f"File dati non trovato: {self.raw_data_path}")
        if self.hour_start >= self.hour_end:
            raise ValueError(f"Range ore invalido: hour_start={self.hour_start} >= hour_end={self.hour_end}")
        if not (0 <= self.hour_start < 24 and 0 < self.hour_end <= 24):
            raise ValueError(f"Ore fuori range [0,24): hour_start={self.hour_start}, hour_end={self.hour_end}")
        if self.block_size <= 0:
            raise ValueError(f"block_size deve essere > 0, ricevuto: {self.block_size}")
        if self.cell_size_m <= 0:
            raise ValueError(f"cell_size_m deve essere > 0, ricevuto: {self.cell_size_m}")
        if self.cell_size_m > 50000:
            warnings.warn(f"cell_size_m={self.cell_size_m}m molto grande (>50km)", UserWarning)
        if self.task_radius_m is not None and self.task_radius_m <= 0:
            raise ValueError(f"task_radius_m deve essere > 0 o None, ricevuto: {self.task_radius_m}")
        if self.max_users <= 0:
            raise ValueError(f"max_users deve essere > 0, ricevuto: {self.max_users}")
        cost_min, cost_max = self.cost_params
        if cost_min <= 0 or cost_max <= 0:
            raise ValueError(f"cost_params deve essere > 0, ricevuto: {self.cost_params}")
        if cost_min > cost_max:
            raise ValueError(f"cost_params: min > max, ricevuto: {self.cost_params}")
        if self.value_mode not in ("uniform", "demand_log"):
            raise ValueError(f"value_mode deve essere 'uniform' o 'demand_log', ricevuto: '{self.value_mode}'")
        if self.norm_mode not in ("percentiles", "log", "power"):
            raise ValueError(f"norm_mode deve essere 'percentiles', 'log' o 'power', ricevuto: '{self.norm_mode}'")
        if not (0 <= self.percentile_low < self.percentile_high <= 100):
            raise ValueError(f"Percentili invalidi: low={self.percentile_low}, high={self.percentile_high}")
        try:
            dt.datetime.strptime(self.day, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Formato data invalido '{self.day}': atteso YYYY-MM-DD. {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Tuple):
                data[key] = list(value)
            elif isinstance(value, Path):
                data[key] = str(value)
            elif isinstance(value, (str, int, float, bool, type(None), list, dict)):
                data[key] = value
            else:
                data[key] = str(value)
        return data

def setup_experiment_logger(output_dir: str, experiment_id: str) -> logging.Logger:
    os.makedirs(output_dir, exist_ok=True)
    logger = logging.getLogger(experiment_id)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log_path = os.path.join(output_dir, f"{experiment_id}_experiment.log")
    file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    error_path = os.path.join(output_dir, f"{experiment_id}_errors.log")
    error_handler = logging.FileHandler(error_path, mode='w', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    return logger

def compute_data_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def save_experiment_metadata(output_dir: str, experiment_id: str, config: ExperimentConfig, start_time: dt.datetime, end_time: dt.datetime) -> None:
    data_hash = compute_data_hash(config.raw_data_path)
    metadata = {"experiment_id": experiment_id, "execution": {"timestamp_start": start_time.isoformat(), "timestamp_end": end_time.isoformat(), "duration_seconds": (end_time - start_time).total_seconds()}, "configuration": config.to_dict(), "data_source": {"path": config.raw_data_path, "sha256": data_hash, "size_bytes": os.path.getsize(config.raw_data_path)}, "environment": {"python_version": platform.python_version(), "platform": platform.platform(), "processor": platform.processor(), "hostname": platform.node()}, "software_versions": {"numpy": np.__version__, "matplotlib": __import__("matplotlib").__version__}}
    metadata_path = os.path.join(output_dir, f"{experiment_id}_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def safe_json_dump(data: Dict, filepath: str, logger: logging.Logger) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        logger.error(f"Errore I/O salvataggio JSON {filepath}: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.error(f"Errore serializzazione JSON {filepath}: {e}")
        return False
    except Exception as e:
        logger.error(f"Errore imprevisto salvataggio JSON {filepath}: {e}")
        return False

def safe_csv_write(content: str, filepath: str, logger: logging.Logger) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        logger.error(f"Errore I/O scrittura CSV {filepath}: {e}")
        return False
    except Exception as e:
        logger.error(f"Errore imprevisto scrittura CSV {filepath}: {e}")
        return False

def compute_density_cells(dm: DataManager, day: str, hour: int, origin: Tuple[float, float], cell_m: float) -> Dict[Tuple[int, int], float]:
    density = {}    
    for row in dm.get_window_records(day=day, hour=f"{hour:02d}", duration_hours=1):
        lat = float(row["lat"])
        lon = float(row["lon"])
        iy, ix = latlon_to_cell(lat, lon, origin[0], origin[1], cell_m)
        density[(iy, ix)] = density.get((iy, ix), 0.0) + 1.0
    return density

def generate_summary_report(output_dir: str, day: str, hours: List[int], vS_values: List[float], sumP_values: List[float], u0_values: List[float], winners_per_hour: Dict[int, int], all_payments: List[float], gini: float, logger: logging.Logger) -> None:
    report_path = os.path.join(output_dir, f"{day}_SUMMARY_REPORT.txt")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Report simulazione IMCU Fase 1 - giornata {day}\n")
            f.write("=" * 80 + "\n\n")
            f.write("Statistiche aggregate giornaliere\n")
            f.write("-" * 80 + "\n")
            f.write(f"Valore totale piattaforma v(S): {sum(vS_values):,.2f} €\n")
            f.write(f"Pagamenti totali Σp_i: {sum(sumP_values):,.2f} €\n")
            f.write(f"Utilità piattaforma u_0: {sum(u0_values):,.2f} €\n")
            if vS_values:
                efficiencies = []
                for u, v in zip(u0_values, vS_values):
                    if np.isfinite(u) and np.isfinite(v) and v > 0:
                        efficiencies.append(u / v)
                    elif np.isfinite(u) and v == 0:
                        efficiencies.append(0.0)
                if efficiencies:
                    f.write(f"Efficienza media u_0/v(S): {np.mean(efficiencies):.4f}\n")
                    f.write(f"Efficienza mediana: {np.median(efficiencies):.4f}\n")
                    f.write(f"Efficienza min: {min(efficiencies):.4f}\n")
                    f.write(f"Efficienza max: {max(efficiencies):.4f}\n")
                else:
                    f.write("Efficienza u_0/v(S): N/A\n")
            f.write(f"Vincitori totali: {sum(winners_per_hour.values())}\n")
            f.write(f"Ore simulate: {len(hours)}\n\n")
            if all_payments:
                f.write("Distribuzione pagamenti\n")
                f.write("-" * 80 + "\n")
                f.write(f"Numero pagamenti: {len(all_payments)}\n")
                f.write(f"Minimo: {min(all_payments):,.2f} €\n")
                f.write(f"Massimo: {max(all_payments):,.2f} €\n")
                f.write(f"Media: {np.mean(all_payments):,.2f} €\n")
                f.write(f"Mediana: {np.median(all_payments):,.2f} €\n")
                f.write(f"Deviazione standard: {np.std(all_payments):,.2f} €\n")
                f.write(f"Percentile 10°: {np.percentile(all_payments, 10):,.2f} €\n")
                f.write(f"Percentile 25°: {np.percentile(all_payments, 25):,.2f} €\n")
                f.write(f"Percentile 75°: {np.percentile(all_payments, 75):,.2f} €\n")
                f.write(f"Percentile 90°: {np.percentile(all_payments, 90):,.2f} €\n")
                f.write(f"Indice di Gini: {gini:.4f}\n\n")
            f.write("Breakdown orario\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Ora':<6} {'v(S) €':<14} {'Σp_i €':<14} {'u_0 €':<14} {'Eff.':<8} {'Vincitori':<10}\n")
            f.write("-" * 80 + "\n")
            for i, h in enumerate(hours):
                eff = u0_values[i] / max(1e-9, vS_values[i])
                f.write(f"{h:02d}h    {vS_values[i]:11,.2f}  {sumP_values[i]:11,.2f}  {u0_values[i]:11,.2f}  {eff:6.4f}  {winners_per_hour.get(h, 0):8d}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("Fine report\n")
            f.write("=" * 80 + "\n")
        logger.info(f"Summary report salvato: {report_path}")
    except Exception as e:
        logger.error(f"Errore generazione summary report: {e}")

def run_hourly_simulation(dm: DataManager, config: ExperimentConfig, day: str, hour: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    try:
        logger.info(f"[{day} H{hour:02d}] Inizio simulazione oraria")
        tasks = dm.create_tasks(day=day, hour=f"{hour:02d}", duration_hours=1, cell_size_m=config.cell_size_m, value_mode=config.value_mode, show_progress=False)
        logger.debug(f"[{day} H{hour:02d}] Task generati: {len(tasks)}")
        if not tasks:
            logger.warning(f"[{day} H{hour:02d}] Nessun task generato, skip ora")
            return None
        task_values = [t.value for t in tasks]
        logger.debug(f"[{day} H{hour:02d}] Distribuzione task: min={min(task_values):.2f}, max={max(task_values):.2f}, mean={np.mean(task_values):.2f}, median={np.median(task_values):.2f}")
        users = dm.create_users(day=day, hour=f"{hour:02d}", duration_hours=1, max_users=config.max_users, cost_mode="uniform", cost_params=config.cost_params, show_progress=False)
        logger.debug(f"[{day} H{hour:02d}] Utenti selezionati: {len(users)}")
        if not users:
            logger.warning(f"[{day} H{hour:02d}] Nessun utente trovato, skip ora")
            return None
        for user in users:
            if config.task_radius_m is None:
                user.set_tasks(tasks)
            else:
                tasks_in_radius = [t for t in tasks if user.calculate_distance_to(t) <= config.task_radius_m]
                user.set_tasks(tasks_in_radius)
            user.calculate_cost_and_bid()
        users_with_tasks = [u for u in users if len(u.tasks) > 0]
        if users_with_tasks:
            tasks_per_user = [len(u.tasks) for u in users_with_tasks]
            logger.debug(f"[{day} H{hour:02d}] Task assignment: utenti con task {len(users_with_tasks)}/{len(users)}, task/user: min={min(tasks_per_user)}, max={max(tasks_per_user)}, mean={np.mean(tasks_per_user):.1f}")
            bids = [u.bid for u in users_with_tasks]
            logger.debug(f"[{day} H{hour:02d}] Distribuzione bid: min={min(bids):.2f}, max={max(bids):.2f}, mean={np.mean(bids):.2f}")
        if not users_with_tasks:
            logger.warning(f"[{day} H{hour:02d}] Nessun utente con task assegnati (raggio {config.task_radius_m}m troppo restrittivo?), skip ora")
            return None
        winners_set, payments, diagnostics = run_imcu_auction(users_with_tasks, debug=True, verify_properties=config.verify_properties)
        logger.debug(f"[{day} H{hour:02d}] IMCU completato: {len(winners_set)} vincitori su {len(users_with_tasks)} partecipanti")
        if config.verify_properties:
            props = diagnostics.get("property_checks", {})
            ir_ok = props.get("IndividualRationality", {}).get("passed", False)
            prof_ok = props.get("Profitability", {}).get("passed", False)
            mono_ok = len(props.get("Monotonicity", {})) > 0
            crit_ok = len(props.get("CriticalValue", {})) > 0
            truth_ok = len(props.get("Truthfulness", {})) > 0
            subm = props.get("Submodularity", {})
            logger.info(f"[{day} H{hour:02d}] Proprietà: IR={ir_ok}, Profit={prof_ok}, Monot={mono_ok}, Crit={crit_ok}, Truth={truth_ok}, SubmViol={subm.get('violations', 'N/A')}")
        return {"day": day, "hour": hour, "n_tasks": len(tasks), "n_users": len(users_with_tasks), "n_winners": len(winners_set), "platform_value": diagnostics.get("platform_value_vS", 0.0), "total_payments": diagnostics.get("payments_sum", 0.0), "platform_utility": diagnostics.get("platform_utility_u0", 0.0), "mv_calls_selection": diagnostics.get("mv_calls_selection", 0), "mv_calls_payment": diagnostics.get("mv_calls_payment", 0), "payments_list": list(payments.values()), "properties": diagnostics.get("property_checks", {}), "users": users_with_tasks, "tasks": tasks, "winners_set": winners_set}
    except Exception as e:
        logger.error(f"[{day} H{hour:02d}] Errore simulazione oraria: {e}", exc_info=True)
        return None

def run_experiment(config: ExperimentConfig) -> None:
    experiment_id = f"imcu_fase1_{config.day}_{config.hour_start:02d}-{config.hour_end:02d}"
    day_output_dir = os.path.join(config.output_dir, f"day_{config.day}")
    os.makedirs(day_output_dir, exist_ok=True)
    logger = setup_experiment_logger(day_output_dir, experiment_id)
    logger.info("=" * 80)
    logger.info(f"Esperimento IMCU Fase 1: {experiment_id}")
    logger.info("=" * 80)
    start_time = dt.datetime.now()
    logger.info(f"Avvio: {start_time.isoformat()}")
    try:
        config.validate()
        logger.info("Parametri allineamento paper IMCU:")
        logger.info(f"  Task values: uniforme [1.8, 15.0]")
        logger.info(f"  User costs: uniforme [{config.cost_params[0]}, {config.cost_params[1]}] €/km")
        logger.info(f"  URBAN_CORRECTION_FACTOR: 1.30")
        logger.info(f"  Cost model: star routing")
        logger.info("Configurazione validata")
    except Exception as e:
        logger.error(f"Configurazione invalida: {e}")
        raise
    set_random_seed(config.random_seed)
    logger.info(f"Seed RNG: {config.random_seed}")
    logger.info(f"Caricamento DataManager da: {config.raw_data_path}")
    etl_out_dir = config.dataset_out if config.dataset_out else os.path.join(config.output_dir, "dataset_processato")
    logger.info(f"Path output ETL: {etl_out_dir}")
    dm = DataManager(raw_txt_path=config.raw_data_path, out_dir=etl_out_dir, bbox=config.bbox if config.bbox else GeoConstants.ROME_BBOX, random_seed=config.random_seed)
    partitions_exist = os.path.exists(dm.part_dir) and len([f for f in os.listdir(dm.part_dir) if f.endswith('.csv')]) > 0
    if not partitions_exist:
        logger.info("Partizioni CSV non trovate, avvio ETL parsing")
        try:
            metadata_etl = dm.parse_raw_to_csv(compute_total_lines=True, partition_by="day-hour", write_master_sample=True, checkpoint_interval=100_000)
            logger.info(f"ETL completato: {metadata_etl['records_written']:,} record scritti")
            logger.info(f"Driver unici: {metadata_etl['unique_drivers']:,}")
            logger.info(f"Range temporale: {metadata_etl['time_range']['min_ts']} → {metadata_etl['time_range']['max_ts']}")
        except Exception as e:
            logger.error(f"Errore critico ETL: {e}", exc_info=True)
            raise
    else:
        logger.info(f"Partizioni CSV esistenti in: {dm.part_dir}")
        n_partitions = len([f for f in os.listdir(dm.part_dir) if f.endswith('.csv')])
        logger.info(f"Trovate {n_partitions} partizioni, skip parsing")
    plotter = ScientificPlotter(output_dir=os.path.join(day_output_dir, "figures"), lang="it", dpi=config.plot_dpi, style="publication")
    logger.info(f"ScientificPlotter configurato: DPI={config.plot_dpi}")
    hours_range = list(range(config.hour_start, config.hour_end))
    logger.info(f"Ore da simulare: {len(hours_range)} ({hours_range[0]}-{hours_range[-1]})")
    all_hourly_results = []
    for block_start in range(config.hour_start, config.hour_end, config.block_size):
        block_end = min(block_start + config.block_size, config.hour_end)
        block_hours = list(range(block_start, block_end))
        for hour in block_hours:
            result = run_hourly_simulation(dm=dm, config=config, day=config.day, hour=hour, logger=logger)
            if result:
                all_hourly_results.append(result)
    if not all_hourly_results:
        logger.error("Nessun risultato orario disponibile")
        return
    logger.info("Generazione aggregati giornalieri")
    hours_all = [r["hour"] for r in all_hourly_results]
    vS_all = [r["platform_value"] for r in all_hourly_results]
    sumP_all = [r["total_payments"] for r in all_hourly_results]
    u0_all = [r["platform_utility"] for r in all_hourly_results]
    winners_all = {r["hour"]: r["n_winners"] for r in all_hourly_results}
    all_payments = [p for r in all_hourly_results for p in r["payments_list"]]
    csv_hourly = "hour,vS,sumP,u0,winners\n"
    for i, h in enumerate(hours_all):
        csv_hourly += f"{h},{vS_all[i]},{sumP_all[i]},{u0_all[i]},{winners_all.get(h, 0)}\n"
    safe_csv_write(csv_hourly, os.path.join(day_output_dir, f"{config.day}_hourly_kpi.csv"), logger)
    csv_daily = "vS_total,sumP_total,u0_total,winners_total\n"
    csv_daily += f"{sum(vS_all)},{sum(sumP_all)},{sum(u0_all)},{sum(winners_all.values())}\n"
    safe_csv_write(csv_daily, os.path.join(day_output_dir, f"{config.day}_daily_kpi.csv"), logger)
    try:
        plotter.timeseries_kpi(hours=hours_all, platform_values=vS_all, total_payments=sumP_all, platform_utilities=u0_all, title=f"KPI giornalieri — {config.day}", filename=f"{config.day}_kpi_timeseries.png")
        _, gini_day = plotter.plot_lorenz_gini(payments=all_payments, title=f"Curva di Lorenz giornaliera — {config.day}", filename=f"{config.day}_payments_lorenz.png")
        plotter.plot_cdf(payments=all_payments, title=f"CDF pagamenti giornalieri — {config.day}", filename=f"{config.day}_payments_cdf.png")
        logger.debug("Visualizzazioni giornaliere generate")
    except Exception as e:
        logger.error(f"Errore generazione visualizzazioni giornaliere: {e}")
        gini_day = 0.0
    generate_summary_report(output_dir=day_output_dir, day=config.day, hours=hours_all, vS_values=vS_all, sumP_values=sumP_all, u0_values=u0_all, winners_per_hour=winners_all, all_payments=all_payments, gini=gini_day, logger=logger)
    end_time = dt.datetime.now()
    save_experiment_metadata(output_dir=day_output_dir, experiment_id=experiment_id, config=config, start_time=start_time, end_time=end_time)
    logger.info("=" * 80)
    logger.info(f"Esperimento completato: durata {(end_time - start_time).total_seconds():.1f}s")
    logger.info(f"Output: {day_output_dir}")
    logger.info("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Orchestratore esperimenti IMCU Fase 1", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--raw", required=True, help="Path file dati grezzo")
    parser.add_argument("--day", required=True, help="Giorno simulazione (YYYY-MM-DD)")
    parser.add_argument("--start", type=int, default=8, help="Ora inizio (0-23)")
    parser.add_argument("--end", type=int, default=20, help="Ora fine esclusa (1-24)")
    parser.add_argument("--block", type=int, default=4, help="Ampiezza blocchi ore")
    parser.add_argument("--dataset_out", default=None, help="Path output ETL dataset condiviso")
    parser.add_argument("--cell", type=int, default=500, help="Dimensione cella griglia (m)")
    parser.add_argument("--radius", type=float, default=2500.0, help="Raggio assegnazione task (m)")
    parser.add_argument("--max_users", type=int, default=316, help="Max utenti per ora")
    parser.add_argument("--cost_min", type=float, default=0.45, help="Costo/km minimo (€/km)")
    parser.add_argument("--cost_max", type=float, default=0.70, help="Costo/km massimo (€/km)")
    parser.add_argument("--value_mode", default="uniform", help="Modalità generazione valore task")
    parser.add_argument("--norm", default="percentiles", help="Normalizzazione colormap")
    parser.add_argument("--p_low", type=float, default=2.0, help="Percentile inferiore")
    parser.add_argument("--p_high", type=float, default=98.0, help="Percentile superiore")
    parser.add_argument("--dpi", type=int, default=300, help="DPI figure")
    parser.add_argument("--out", default="experiments_fase1", help="Directory output")
    parser.add_argument("--seed", type=int, default=42, help="Seed RNG")
    parser.add_argument("--save_raw_logs", action="store_true", help="Salva log grezzi JSON/CSV")
    parser.add_argument("--no_verify", action="store_true", help="Disabilita verifica proprietà IMCU")
    args = parser.parse_args()
    config = ExperimentConfig(raw_data_path=args.raw, day=args.day, hour_start=args.start, hour_end=args.end, block_size=args.block, cell_size_m=args.cell, task_radius_m=args.radius, bbox=None, max_users=args.max_users, cost_params=(args.cost_min, args.cost_max), value_mode=args.value_mode, norm_mode=args.norm, percentile_low=args.p_low, percentile_high=args.p_high, plot_dpi=args.dpi, output_dir=args.out, random_seed=args.seed, save_raw_logs=args.save_raw_logs, verify_properties=not args.no_verify, dataset_out=args.dataset_out)
    try:
        run_experiment(config)
        sys.exit(0)
    except Exception as e:
        print(f"Errore critico: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()