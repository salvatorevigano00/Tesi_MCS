from __future__ import annotations

import os
import sys
import re
import csv
import math
import json
import time
import gzip
import random
import warnings
import datetime as dt

from typing import Iterator, List, Tuple, Dict, Optional, Any
from collections import OrderedDict
from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from classes import Task, User, set_random_seed

class GeoConstants:
    ROME_BBOX: Tuple[float, float, float, float] = (41.78, 42.04, 12.30, 12.72)
    M_PER_DEG_LAT: float = 111_320.0
    POINT_REGEX: re.Pattern = re.compile(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)")
    TZ_SIMPLE_HH_REGEX: re.Pattern = re.compile(r"([+\-]\d{2})$")
    TZ_HHMM_REGEX: re.Pattern = re.compile(r"([+\-]\d{2})(\d{2})$")
    COMMON_TS_FORMATS: Tuple[str, ...] = ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%d/%m/%Y %H:%M:%S.%f", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S")

class TaskValueModel:
    LOG_SCALE_FACTOR: float = 10.0
    VALUE_MIN: float = 1.8
    VALUE_MAX: float = 15.0
    
    @staticmethod
    def compute_value(mode: str, count: int, low: float = None, high: float = None) -> float:
        if low is None:
            low = TaskValueModel.VALUE_MIN
        if high is None:
            high = TaskValueModel.VALUE_MAX
        if mode == "uniform":
            return random.uniform(low, high)
        elif mode == "demand_log":
            scale = TaskValueModel.LOG_SCALE_FACTOR
            normalized = min(1.0, math.log1p(count) / scale)
            return low + (high - low) * normalized
        else:
            raise ValueError(f"Modello di valore non riconosciuto: '{mode}'. Modelli disponibili: 'uniform', 'demand_log'.")

def m_per_deg_lon_at_lat(lat_deg: float) -> float:
    return GeoConstants.M_PER_DEG_LAT * math.cos(math.radians(lat_deg))

def parse_point(s: str) -> Tuple[float, float]:
    match = GeoConstants.POINT_REGEX.match(s.strip())
    if not match:
        raise ValueError(f"Formato WKT POINT non valido: {s!r}")
    lat, lon = float(match.group(1)), float(match.group(2))
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitudine fuori range [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitudine fuori range [-180, 180]: {lon}")
    return lat, lon

def _normalize_ts_iso(s: str) -> str:
    s = s.strip().replace("T", " ")
    if s.endswith("Z"):
        return s[:-1] + "+00:00"
    match = GeoConstants.TZ_SIMPLE_HH_REGEX.search(s)
    if match:
        return GeoConstants.TZ_SIMPLE_HH_REGEX.sub(f"{match.group(1)}:00", s)
    match = GeoConstants.TZ_HHMM_REGEX.search(s)
    if match:
        return GeoConstants.TZ_HHMM_REGEX.sub(f"{match.group(1)}:{match.group(2)}", s)
    return s

def parse_ts(s: str, fmt: Optional[str] = None) -> dt.datetime:
    s = s.strip()
    if fmt:
        return dt.datetime.strptime(s, fmt)
    normalized_s = _normalize_ts_iso(s)
    try:
        return dt.datetime.fromisoformat(normalized_s)
    except Exception:
        pass
    for format_str in GeoConstants.COMMON_TS_FORMATS:
        try:
            return dt.datetime.strptime(normalized_s, format_str)
        except Exception:
            continue
    raise ValueError(f"Formato timestamp non riconosciuto: {s!r}. Formati supportati: ISO 8601 o varianti comuni.")

def within_bbox(lat: float, lon: float, bbox: Tuple[float, float, float, float]) -> bool:
    lat_min, lat_max, lon_min, lon_max = bbox
    return (lat_min <= lat < lat_max) and (lon_min <= lon < lon_max)

def latlon_to_cell(lat: float, lon: float, origin_lat: float, origin_lon: float, cell_m: float) -> Tuple[int, int]:
    delta_y_m = (lat - origin_lat) * GeoConstants.M_PER_DEG_LAT
    lat_avg = (origin_lat + lat) / 2.0
    delta_x_m = (lon - origin_lon) * m_per_deg_lon_at_lat(lat_avg)
    iy = int(math.floor(delta_y_m / cell_m))
    ix = int(math.floor(delta_x_m / cell_m))
    return iy, ix

def cell_to_centroid(iy: int, ix: int, origin_lat: float, origin_lon: float, cell_m: float) -> Tuple[float, float]:
    centroid_y_m = (iy + 0.5) * cell_m
    centroid_x_m = (ix + 0.5) * cell_m
    lat = origin_lat + (centroid_y_m / GeoConstants.M_PER_DEG_LAT)
    lon = origin_lon + (centroid_x_m / m_per_deg_lon_at_lat(origin_lat))
    return lat, lon

def _smart_split_3cols(line: str) -> Optional[List[str]]:
    for separator in (";", ",", "|", "\t"):
        parts = [part.strip() for part in line.split(separator)]
        if len(parts) == 3:
            return parts
    return None

class DataManager:    
    MAX_OPEN_FILES: int = min(200, os.sysconf("SC_OPEN_MAX") // 10) if hasattr(os, "sysconf") else 200
    UPDATE_INTERVAL: int = 250_000
    
    def __init__(self, raw_txt_path: str, out_dir: str = "dataset_processato", bbox: Tuple[float, float, float, float] = None, random_seed: int = 42):
        self.raw_txt_path = raw_txt_path
        self.out_dir = out_dir
        self.part_dir = os.path.join(out_dir, "csv_partitions")
        self.meta_path = os.path.join(out_dir, "metadata.json")
        self.bbox = bbox if bbox is not None else GeoConstants.ROME_BBOX
        set_random_seed(random_seed)
        os.makedirs(self.part_dir, exist_ok=True)
        self._grid_origin_current: Tuple[float, float] = (self.bbox[0], self.bbox[2])
        self._grid_cell_m_current: int = 500
        self._last_cells_counts: Dict[Tuple[int, int], int] = {}
        self._task_cell_map: Dict[int, Tuple[int, int, float, float]] = {}
        self._partition_by: str = "day-hour"
    
    def parse_raw_to_csv(self, time_format: Optional[str] = None, compute_total_lines: bool = False, partition_by: str = "day-hour", write_master_sample: bool = True, master_sample_max: int = 1_000_000, checkpoint_interval: int = 100_000) -> Dict[str, Any]:
        print("Parsing: conversione file grezzo → CSV partizionati")
        print(f"  Partizione: {partition_by}")
        print(f"  Checkpoint ogni {checkpoint_interval:,} record")
        start_time = time.perf_counter()
        self._partition_by = partition_by
        is_gz = self.raw_txt_path.lower().endswith(".gz")
        total_lines = None
        if compute_total_lines:
            print("Pre-scansione per conteggio righe")
            open_func = gzip.open if is_gz else open
            with open_func(self.raw_txt_path, "rt", encoding="utf-8", errors="ignore") as f:
                total_lines = sum(1 for _ in f)
            print(f"Righe totali: {total_lines:,}")
        min_ts, max_ts = None, None
        min_lat, max_lat = 90.0, -90.0
        min_lon, max_lon = 180.0, -180.0
        drivers_seen: set[int] = set()
        records_rejected, records_written, master_records_written = 0, 0, 0
        master_path = os.path.join(self.out_dir, "master_sample.csv") if write_master_sample else None
        rejects_path = os.path.join(self.out_dir, "rejects.csv")
        partition_files: OrderedDict[str, Tuple[Any, Any]] = OrderedDict()
        open_func = gzip.open if is_gz else open
        try:
            with open_func(self.raw_txt_path, "rt", encoding="utf-8", errors="ignore") as f_in, open(rejects_path, "w", newline="", encoding="utf-8") as f_rej:
                reject_writer = csv.writer(f_rej)
                reject_writer.writerow(["riga_grezza", "motivo_scarto", "dettagli_errore"])
                master_file = None
                master_writer = None
                if write_master_sample and master_path:
                    master_file = open(master_path, "w", newline="", encoding="utf-8")
                    master_writer = csv.writer(master_file)
                    master_writer.writerow(["driver_id", "ts_iso", "epoch_ms", "lat", "lon", "day", "hour"])
                pbar = tqdm(total=total_lines, unit=" righe", desc="Parsing", mininterval=1.0)
                pbar.set_postfix(valid=0, reject=0)
                lines_processed = 0
                for line_num, line in enumerate(f_in, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    lines_processed += 1
                    parts = _smart_split_3cols(line)
                    if not parts:
                        records_rejected += 1
                        reject_writer.writerow([line, "formato_colonne_invalido", "expected_3_columns"])
                        if lines_processed % self.UPDATE_INTERVAL == 0:
                            pbar.update(self.UPDATE_INTERVAL)
                            pbar.set_postfix(valid=records_written, reject=records_rejected)
                        continue
                    driver_s, ts_s, point_s = parts
                    try:
                        driver_id = int(driver_s)
                        dt_obj = parse_ts(ts_s, fmt=time_format)
                        lat, lon = parse_point(point_s)
                    except ValueError as e:
                        records_rejected += 1
                        error_detail = str(e)[:100]
                        reject_writer.writerow([line, "parsing_value_error", error_detail])
                        if lines_processed % self.UPDATE_INTERVAL == 0:
                            pbar.update(self.UPDATE_INTERVAL)
                            pbar.set_postfix(valid=records_written, reject=records_rejected)
                        continue
                    except TypeError as e:
                        records_rejected += 1
                        error_detail = str(e)[:100]
                        reject_writer.writerow([line, "parsing_type_error", error_detail])
                        if lines_processed % self.UPDATE_INTERVAL == 0:
                            pbar.update(self.UPDATE_INTERVAL)
                            pbar.set_postfix(valid=records_written, reject=records_rejected)
                        continue
                    try:
                        if not within_bbox(lat, lon, self.bbox):
                            records_rejected += 1
                            reject_writer.writerow([line, "fuori_bounding_box", f"lat={lat:.6f}_lon={lon:.6f}_bbox={self.bbox}"])
                            if lines_processed % self.UPDATE_INTERVAL == 0:
                                pbar.update(self.UPDATE_INTERVAL)
                                pbar.set_postfix(valid=records_written, reject=records_rejected)
                            continue
                        epoch_ms = int(dt_obj.timestamp() * 1000)
                        min_ts = min(min_ts, dt_obj) if min_ts else dt_obj
                        max_ts = max(max_ts, dt_obj) if max_ts else dt_obj
                        min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)
                        min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
                        drivers_seen.add(driver_id)
                        day, hour = dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H")
                        partition_name = f"{day}.csv" if partition_by == "day" else f"{day}_{hour}.csv"
                        if partition_name not in partition_files:
                            if len(partition_files) >= self.MAX_OPEN_FILES:
                                oldest_name = next(iter(partition_files))
                                oldest_file, _ = partition_files.pop(oldest_name)
                                oldest_file.close()
                            partition_path = os.path.join(self.part_dir, partition_name)
                            file_exists = os.path.exists(partition_path) and os.path.getsize(partition_path) > 0
                            f_part = open(partition_path, "a", newline="", encoding="utf-8")
                            writer = csv.writer(f_part)
                            if not file_exists:
                                writer.writerow(["driver_id", "ts_iso", "epoch_ms", "lat", "lon", "day", "hour"])
                            partition_files[partition_name] = (f_part, writer)
                        else:
                            partition_files.move_to_end(partition_name)
                        _, writer = partition_files[partition_name]
                        writer.writerow([driver_id, dt_obj.isoformat(sep=" "), epoch_ms, f"{lat:.7f}", f"{lon:.7f}", day, hour])
                        records_written += 1
                        if lines_processed % self.UPDATE_INTERVAL == 0:
                            pbar.update(self.UPDATE_INTERVAL)
                            pbar.set_postfix(valid=records_written, reject=records_rejected)
                        if master_writer and master_records_written < master_sample_max:
                            master_writer.writerow([driver_id, dt_obj.isoformat(sep=" "), epoch_ms, f"{lat:.7f}", f"{lon:.7f}", day, hour])
                            master_records_written += 1
                        if records_written % checkpoint_interval == 0:
                            for f_part, _ in partition_files.values():
                                f_part.flush()
                                os.fsync(f_part.fileno())
                    except OSError as e:
                        print(f"\nErrore I/O critico riga {line_num}")
                        print(f"  Tipo: {type(e).__name__}")
                        print(f"  Messaggio: {e}")
                        print(f"  Record scritti: {records_written:,}")
                        print(f"  Salvando checkpoint")
                        for f_part, _ in partition_files.values():
                            try:
                                f_part.flush()
                                os.fsync(f_part.fileno())
                            except:
                                pass
                        pbar.close()
                        raise
                    except Exception as e:
                        print(f"\nBug rilevato riga {line_num}")
                        print(f"  Tipo: {type(e).__name__}")
                        print(f"  Messaggio: {e}")
                        print(f"  Riga: {line!r}")
                        print(f"  Dati: driver_id={driver_id}, dt={dt_obj}, lat={lat}, lon={lon}")
                        print(f"  Record scritti: {records_written:,}")
                        import traceback
                        print("\nTraceback:")
                        traceback.print_exc()
                        for f_part, _ in partition_files.values():
                            try:
                                f_part.flush()
                                os.fsync(f_part.fileno())
                            except:
                                pass
                        pbar.close()
                        raise
                remaining = lines_processed % self.UPDATE_INTERVAL
                if remaining > 0:
                    pbar.update(remaining)
                    pbar.set_postfix(valid=records_written, reject=records_rejected)
                pbar.close()
                if master_file:
                    master_file.close()
        finally:
            for f_part, _ in partition_files.values():
                try:
                    f_part.close()
                except:
                    pass
        metadata = {"raw_path": self.raw_txt_path, "out_dir": self.out_dir, "partitions_dir": self.part_dir, "partition_by": partition_by, "records_written": records_written, "records_rejected": records_rejected, "unique_drivers": len(drivers_seen), "effective_bbox": [min_lat, max_lat, min_lon, max_lon], "time_range": {"min_ts": min_ts.isoformat(sep=" ") if min_ts else None, "max_ts": max_ts.isoformat(sep=" ") if max_ts else None}, "master_sample_path": master_path, "master_records_written": master_records_written, "rejects_log_path": rejects_path}
        with open(self.meta_path, "w", encoding="utf-8") as f_meta:
            json.dump(metadata, f_meta, indent=2)
        duration_sec = time.perf_counter() - start_time
        print("\n" + "=" * 70)
        print(f"Parsing completato in {duration_sec:.1f} secondi")
        print(f"  Record validi: {records_written:,}")
        print(f"  Righe scartate: {records_rejected:,} ({records_rejected/(records_written+records_rejected)*100:.1f}%)")
        print(f"  Driver unici: {len(drivers_seen):,}")
        print(f"  Range temporale: {min_ts.strftime('%Y-%m-%d %H:%M') if min_ts else 'N/A'} → {max_ts.strftime('%Y-%m-%d %H:%M') if max_ts else 'N/A'}")
        print(f"  Bounding box: [{min_lat:.4f}, {max_lat:.4f}] lat × [{min_lon:.4f}, {max_lon:.4f}] lon")
        print(f"\nFile generati:")
        print(f"  Partizioni: {self.part_dir}")
        print(f"  Metadata: {self.meta_path}")
        print(f"  Righe scartate: {rejects_path}")
        if write_master_sample:
            print(f"  Campione master: {master_path} ({master_records_written:,} record)")
        print("=" * 70 + "\n")
        return metadata
    
    def _iter_partitions_for_window(self, day: str, hour: Optional[str], duration_hours: int) -> List[str]:
        partition_paths: List[str] = []
        start_datetime = dt.datetime.strptime(f"{day} {hour or '00'}", "%Y-%m-%d %H")
        if self._partition_by == "day":
            days_covered = set()
            for i in range(duration_hours):
                current_dt = start_datetime + dt.timedelta(hours=i)
                days_covered.add(current_dt.strftime("%Y-%m-%d"))
            for day_str in sorted(days_covered):
                partition_name = f"{day_str}.csv"
                partition_path = os.path.join(self.part_dir, partition_name)
                if os.path.exists(partition_path):
                    partition_paths.append(partition_path)
        else:
            for i in range(duration_hours):
                current_dt = start_datetime + dt.timedelta(hours=i)
                partition_name = f"{current_dt.strftime('%Y-%m-%d')}_{current_dt.strftime('%H')}.csv"
                partition_path = os.path.join(self.part_dir, partition_name)
                if os.path.exists(partition_path):
                    partition_paths.append(partition_path)
        return partition_paths
    
    def get_window_records(self, day: str, hour: str, duration_hours: int = 1, bbox: Optional[Tuple[float, float, float, float]] = None, max_rows: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        target_bbox = bbox or self.bbox
        partition_files = self._iter_partitions_for_window(day, hour, duration_hours)
        if not partition_files:
            raise FileNotFoundError(f"Nessuna partizione trovata per {day} H{hour} (durata {duration_hours}h). Verificare esecuzione parse_raw_to_csv().")
        record_count = 0
        for file_path in tqdm(partition_files, desc="Caricamento partizioni", unit="file", disable=True):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lat, lon = float(row["lat"]), float(row["lon"])
                    if within_bbox(lat, lon, target_bbox):
                        yield row
                        record_count += 1
                        if max_rows and record_count >= max_rows:
                            return
    
    def get_block_records(self, day: str, start_hour: int, end_hour: int, bbox: Optional[Tuple[float, float, float, float]] = None, max_rows: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        duration = end_hour - start_hour
        if duration <= 0:
            return iter([])
        yield from self.get_window_records(day=day, hour=f"{start_hour:02d}", duration_hours=duration, bbox=bbox, max_rows=max_rows)
    
    def create_tasks(self, day: Optional[str] = None, hour: Optional[str] = None, duration_hours: int = 1, cell_size_m: int = 500, value_mode: str = "uniform", uniform_low: float = None, uniform_high: float = None, seed: Optional[int] = None, show_progress: bool = True) -> List[Task]:
        if cell_size_m <= 0:
            raise ValueError(f"cell_size_m deve essere > 0, ricevuto {cell_size_m}")
        if cell_size_m > 50000:
            warnings.warn(f"cell_size_m={cell_size_m}m molto grande (>50km)", UserWarning)
        if value_mode not in ("uniform", "demand_log"):
            raise ValueError(f"value_mode deve essere 'uniform' o 'demand_log', ricevuto '{value_mode}'")
        if duration_hours <= 0:
            raise ValueError(f"duration_hours deve essere > 0, ricevuto {duration_hours}")
        if uniform_low is None:
            uniform_low = Task.VALUE_MIN
        if uniform_high is None:
            uniform_high = Task.VALUE_MAX
        if uniform_low > uniform_high:
            raise ValueError(f"uniform_low ({uniform_low}) > uniform_high ({uniform_high})")
        if seed is not None:
            set_random_seed(seed)
        if day is None or hour is None:
            partitions = sorted([f for f in os.listdir(self.part_dir) if f.endswith('.csv')])
            if not partitions:
                raise FileNotFoundError("Nessuna partizione trovata. Eseguire parse_raw_to_csv().")
            first_partition = partitions[0]
            day = first_partition[:10]
            hour = first_partition[11:13] if len(first_partition) > 10 else "00"
        records_iterator = self.get_window_records(day=day, hour=hour, duration_hours=duration_hours)
        lat0, _, lon0, _ = self.bbox
        self._grid_origin_current = (lat0, lon0)
        self._grid_cell_m_current = cell_size_m
        cells: Dict[Tuple[int, int], int] = {}
        for row in records_iterator:
            lat, lon = float(row["lat"]), float(row["lon"])
            iy, ix = latlon_to_cell(lat, lon, lat0, lon0, cell_size_m)
            cells[(iy, ix)] = cells.get((iy, ix), 0) + 1
        self._last_cells_counts = cells
        sorted_cells = sorted(cells.items(), key=lambda item: item[0])
        tasks: List[Task] = []
        self._task_cell_map = {}
        task_id_counter = 1
        for (iy, ix), count in sorted_cells:
            lat, lon = cell_to_centroid(iy, ix, lat0, lon0, cell_size_m)
            value = TaskValueModel.compute_value(mode=value_mode, count=count, low=uniform_low, high=uniform_high)
            task = Task(task_id=task_id_counter, x=lon, y=lat, value=value)
            tasks.append(task)
            self._task_cell_map[task.id] = (iy, ix, lat, lon)
            task_id_counter += 1
        return tasks
    
    def create_users(self, day: Optional[str] = None, hour: Optional[str] = None, duration_hours: int = 1, max_users: int = 99999, cost_mode: str = "uniform", cost_params: Tuple[float, float] = None, sampling_strategy: str = "uniform", show_progress: bool = True) -> List[User]:
        if cost_params is None:
            cost_params = (User.COST_PER_KM_MIN, User.COST_PER_KM_MAX)
        if day is None or hour is None:
            partitions = sorted([f for f in os.listdir(self.part_dir) if f.endswith('.csv')])
            if not partitions:
                raise FileNotFoundError("Nessuna partizione trovata. Eseguire parse_raw_to_csv().")
            first_partition = partitions[0]
            day = first_partition[:10]
            hour = first_partition[11:13] if len(first_partition) > 10 else "00"
        last_positions: Dict[int, Tuple[float, float, int]] = {}
        for row in self.get_window_records(day=day, hour=hour, duration_hours=duration_hours):
            driver_id = int(row["driver_id"])
            epoch_ms = int(row["epoch_ms"])
            lat, lon = float(row["lat"]), float(row["lon"])
            if driver_id not in last_positions or epoch_ms > last_positions[driver_id][2]:
                last_positions[driver_id] = (lat, lon, epoch_ms)
        driver_items = [(did, (lat, lon)) for did, (lat, lon, _) in last_positions.items()]
        if len(driver_items) > max_users:
            if sampling_strategy == "uniform":
                driver_items = random.sample(driver_items, k=max_users)
            elif sampling_strategy == "stratified":
                lat0, lat1, lon0, lon1 = self.bbox
                n_stratum = 5
                strata: Dict[Tuple[int, int], List] = {}
                for did, (lat, lon) in driver_items:
                    sy = int(min(n_stratum - 1, (lat - lat0) / (lat1 - lat0) * n_stratum))
                    sx = int(min(n_stratum - 1, (lon - lon0) / (lon1 - lon0) * n_stratum))
                    strata.setdefault((sy, sx), []).append((did, (lat, lon)))
                sampled = []
                total_drivers = len(driver_items)
                for _, drivers_in_stratum in strata.items():
                    n_sample_stratum = max(1, int(len(drivers_in_stratum) / total_drivers * max_users))
                    n_sample_stratum = min(n_sample_stratum, len(drivers_in_stratum))
                    sampled.extend(random.sample(drivers_in_stratum, k=n_sample_stratum))
                if len(sampled) < max_users:
                    sampled_ids = {item[0] for item in sampled}
                    remaining = [item for item in driver_items if item[0] not in sampled_ids]
                    additional = random.sample(remaining, k=min(max_users - len(sampled), len(remaining)))
                    sampled.extend(additional)
                driver_items = sampled[:max_users]
            else:
                raise ValueError(f"sampling_strategy non valida: '{sampling_strategy}'. Valori ammessi: 'uniform', 'stratified'")
        driver_items.sort(key=lambda item: item[0])
        users: List[User] = []
        cost_min, cost_max = cost_params
        for driver_id, (lat, lon) in driver_items:
            cost_per_km = random.uniform(cost_min, cost_max) if cost_mode == "uniform" else 0.5
            user = User(user_id=driver_id, x=lon, y=lat, cost_per_km=cost_per_km)
            users.append(user)
        return users
    
    def __repr__(self) -> str:
        try:
            n_partitions = len([f for f in os.listdir(self.part_dir) if f.endswith('.csv')])
        except Exception:
            n_partitions = 0
        return f"DataManager(file_grezzo='{os.path.basename(self.raw_txt_path)}', directory_output='{self.out_dir}', partizioni_csv={n_partitions})"
