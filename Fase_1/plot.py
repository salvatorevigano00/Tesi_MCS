from __future__ import annotations
import os
import sys
from typing import Any, Dict, Tuple, List, Optional, Iterable
from dataclasses import dataclass
import json
import datetime as dt
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, PowerNorm, Normalize

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
  
from data_manager import GeoConstants

@dataclass
class PlotMetadata:
    figure_path: str
    generated_at: str
    plot_type: str
    parameters: Dict[str, Any]
    data_stats: Dict[str, Any]
    software_versions: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"figure_path": self.figure_path, "generated_at": self.generated_at, "plot_type": self.plot_type, "parameters": self.parameters, "data_stats": self.data_stats, "software_versions": self.software_versions}
    
    def save_json(self, json_path: Optional[str] = None) -> None:
        if json_path is None:
            json_path = os.path.splitext(self.figure_path)[0] + "_metadata.json"
        os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

class PlotLabels:
    ITALIAN: Dict[str, str] = {"longitude": "Longitudine (gradi)", "latitude": "Latitudine (gradi)", "hour": "Ora del giorno", "time_window": "Finestra temporale", "value": "Valore (€)", "payment": "Pagamento (€)", "platform_value": "Valore piattaforma v(S) (€)", "total_payments": "Pagamenti totali Σp_i (€)", "platform_utility": "Utilità piattaforma u_0 (€)", "efficiency": "Efficienza u_0 / v(S)", "winners": "Vincitori selezionati", "rank": "Posizione (rank)", "cumulative_fraction": "Frazione cumulativa", "cdf": "Funzione di distribuzione cumulativa", "lorenz_curve": "Curva di Lorenz", "equality_line": "Linea di uguaglianza", "winner_fraction": "Frazione vincitori", "payment_fraction": "Frazione pagamenti cumulativi", "density": "Densità osservazioni", "coverage": "Copertura task", "gap": "Gap (densità − copertura)", "cell_count": "Conteggio per cella", "no_data": "Nessun dato disponibile", "no_payments": "Nessun pagamento registrato"}
    
    @staticmethod
    def get(key: str, lang: str = "it") -> str:
        if lang == "it":
            return PlotLabels.ITALIAN.get(key, key)
        return key

class ColorPalettes:
    SEQUENTIAL: Dict[str, str] = {"default": "viridis", "density": "magma", "coverage": "plasma", "energy": "inferno"}
    DIVERGING: Dict[str, str] = {"default": "RdBu_r", "gap": "RdBu_r", "correlation": "PuOr_r", "balance": "BrBG_r"}
    QUALITATIVE: Dict[str, List[str]] = {"default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"], "pastel": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"]}
    
    @staticmethod
    def get_sequential(variant: str = "default") -> str:
        return ColorPalettes.SEQUENTIAL.get(variant, "viridis")
    
    @staticmethod
    def get_diverging(variant: str = "default") -> str:
        return ColorPalettes.DIVERGING.get(variant, "RdBu_r")

class ScientificPlotter:
    DEFAULT_DPI_PRINT: int = 300
    DEFAULT_DPI_SCREEN: int = 150
    IEEE_COLUMN_WIDTH_INCH: float = 3.5
    IEEE_TEXT_WIDTH_INCH: float = 7.0
    
    def __init__(self, output_dir: str = "figures", lang: str = "it", dpi: int = None, style: str = "publication"):
        self.output_dir = output_dir
        self.lang = lang
        self.dpi = dpi if dpi is not None else self.DEFAULT_DPI_PRINT
        self.style = style
        self.metadata_enabled = True
        os.makedirs(self.output_dir, exist_ok=True)
        self._configure_matplotlib_style()
    
    def _configure_matplotlib_style(self) -> None:
        base_config = {'font.family': 'serif', 'font.size': 10, 'axes.labelsize': 11, 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 9, 'legend.framealpha': 0.9, 'legend.edgecolor': 'gray', 'figure.dpi': self.dpi, 'savefig.dpi': self.dpi, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05, 'lines.linewidth': 1.5, 'lines.markersize': 4, 'grid.alpha': 0.2, 'grid.linewidth': 0.5, 'axes.grid': True, 'axes.axisbelow': True}
        try:
            plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman']
        except:
            warnings.warn("Font Times New Roman non disponibile, uso default serif")
        if self.style == "publication":
            base_config.update({'figure.figsize': (7.0, 5.0), 'axes.linewidth': 1.0})
        elif self.style == "presentation":
            base_config.update({'font.size': 14, 'axes.labelsize': 16, 'axes.titlesize': 18, 'figure.figsize': (10.0, 7.0), 'lines.linewidth': 2.5})
        elif self.style == "draft":
            base_config.update({'figure.dpi': self.DEFAULT_DPI_SCREEN, 'savefig.dpi': self.DEFAULT_DPI_SCREEN})
        plt.rcParams.update(base_config)
    
    def _get_software_versions(self) -> Dict[str, str]:
        return {"python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "matplotlib": plt.matplotlib.__version__, "numpy": np.__version__}
    
    def _save_figure_with_metadata(self, fig: Figure, filepath: str, plot_type: str, parameters: Dict[str, Any], data_stats: Dict[str, Any]) -> PlotMetadata:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close(fig)
        metadata = PlotMetadata(figure_path=filepath, generated_at=dt.datetime.now().isoformat(), plot_type=plot_type, parameters=parameters, data_stats=data_stats, software_versions=self._get_software_versions())
        if self.metadata_enabled:
            metadata.save_json()
        return metadata
    
    def _cells_to_array(self, cells: Dict[Tuple[int, int], float]) -> Tuple[np.ndarray, int, int, int, int]:
        if not cells:
            return np.zeros((1, 1), dtype=float), 0, 0, 1, 1
        iys = [iy for (iy, ix) in cells.keys()]
        ixs = [ix for (iy, ix) in cells.keys()]
        min_iy, max_iy = min(iys), max(iys)
        min_ix, max_ix = min(ixs), max(ixs)
        H = max_iy - min_iy + 1
        W = max_ix - min_ix + 1
        arr = np.zeros((H, W), dtype=float)
        for (iy, ix), v in cells.items():
            arr[iy - min_iy, ix - min_ix] = float(v)
        return arr, min_iy, min_ix, H, W
    
    def _grid_edges_latlon(self, lat0: float, lon0: float, min_iy: int, min_ix: int, H: int, W: int, cell_m: float) -> Tuple[np.ndarray, np.ndarray]:
        M_LAT = GeoConstants.M_PER_DEG_LAT
        y_edges_m = (np.arange(H + 1) + min_iy) * cell_m
        x_edges_m = (np.arange(W + 1) + min_ix) * cell_m
        lat_edges = lat0 + (y_edges_m / M_LAT)
        lat_mean = (lat_edges[0] + lat_edges[-1]) / 2.0
        M_LON = M_LAT * np.cos(np.radians(lat_mean))
        lon_edges = lon0 + (x_edges_m / M_LON)
        return lat_edges, lon_edges
    
    def _compute_robust_limits(self, data: np.ndarray, mode: str = "percentiles", p_low: float = 2.0, p_high: float = 98.0) -> Tuple[Optional[Normalize], float, float]:
        data_valid = data[np.isfinite(data) & (data > 0)]
        if data_valid.size == 0:
            return None, 0.0, 1.0
        if mode == "log":
            p_low_value = float(np.percentile(data_valid, p_low))
            adaptive_floor = p_low_value * 1e-3
            vmin = max(adaptive_floor, p_low_value, 1e-12)
            vmax = float(np.percentile(data_valid, p_high))
            vmax = max(vmax, vmin * 10.0)
            norm = LogNorm(vmin=vmin, vmax=vmax)
        elif mode == "power":
            vmin = float(np.percentile(data_valid, p_low))
            vmax = float(np.percentile(data_valid, p_high))
            vmax = max(vmax, vmin + 1e-9)
            norm = PowerNorm(gamma=0.5, vmin=vmin, vmax=vmax)
        else:
            vmin = float(np.percentile(data_valid, p_low))
            vmax = float(np.percentile(data_valid, p_high))
            vmax = max(vmax, vmin + 1e-9)
            norm = None
        return norm, vmin, vmax
    
    def heatmap(self, cells: Dict[Tuple[int, int], float], origin: Tuple[float, float], cell_m: float, title: str, filename: str, colormap: str = None, norm_mode: str = "percentiles", p_low: float = 2.0, p_high: float = 98.0, colorbar_label: str = None, vmin: Optional[float] = None, vmax: Optional[float] = None) -> PlotMetadata:
        if not cells or len(cells) == 0:
            raise ValueError("Parametro 'cells' vuoto. Impossibile generare heatmap")
        if cell_m <= 0:
            raise ValueError(f"cell_m deve essere > 0, ricevuto: {cell_m}")
        if cell_m > 100_000:
            warnings.warn(f"cell_m={cell_m}m molto grande (>100km)", UserWarning)
        lat0, lon0 = origin
        if not (-90.0 <= lat0 <= 90.0):
            raise ValueError(f"Latitudine origine fuori range [-90, 90]: {lat0}")
        if not (-180.0 <= lon0 <= 180.0):
            raise ValueError(f"Longitudine origine fuori range [-180, 180]: {lon0}")
        if not (0.0 <= p_low < p_high <= 100.0):
            raise ValueError(f"Percentili invalidi: p_low={p_low}, p_high={p_high}. Richiesto: 0 ≤ p_low < p_high ≤ 100")
        if vmin is not None and vmax is not None:
            if vmin >= vmax:
                raise ValueError(f"vmin ({vmin}) deve essere < vmax ({vmax})")
        if norm_mode not in ("percentiles", "log", "power"):
            raise ValueError(f"norm_mode non valido: '{norm_mode}'. Valori ammessi: 'percentiles', 'log', 'power'")
        arr, min_iy, min_ix, H, W = self._cells_to_array(cells)
        lat_edges, lon_edges = self._grid_edges_latlon(lat0, lon0, min_iy, min_ix, H, W, cell_m)
        norm = None
        if vmin is None or vmax is None:
            norm, vmin_auto, vmax_auto = self._compute_robust_limits(arr, norm_mode, p_low, p_high)
            if vmin is None:
                vmin = vmin_auto
            if vmax is None:
                vmax = vmax_auto
        if colormap is None:
            colormap = ColorPalettes.get_sequential("density")
        if colorbar_label is None:
            colorbar_label = PlotLabels.get("cell_count", self.lang)
        fig, ax = plt.subplots(figsize=(7.5, 6.5))
        mesh = ax.pcolormesh(lon_edges, lat_edges, arr, shading="auto", cmap=colormap, norm=norm if norm else None, vmin=None if norm else vmin, vmax=None if norm else vmax)
        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label(colorbar_label, fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("longitude", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("latitude", self.lang), fontsize=11)
        ax.set_aspect("equal")
        data_stats = {"n_cells": int(np.sum(arr > 0)), "total_cells": int(H * W), "min_value": float(np.min(arr[arr > 0])) if np.any(arr > 0) else 0.0, "max_value": float(np.max(arr)), "mean_value": float(np.mean(arr[arr > 0])) if np.any(arr > 0) else 0.0, "std_value": float(np.std(arr[arr > 0])) if np.any(arr > 0) else 0.0}
        parameters = {"origin_lat": float(lat0), "origin_lon": float(lon0), "cell_size_m": float(cell_m), "colormap": colormap, "norm_mode": norm_mode, "p_low": float(p_low), "p_high": float(p_high), "vmin": float(vmin), "vmax": float(vmax)}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "heatmap", parameters, data_stats)
    
    def timeseries_kpi(self, hours: List[int], platform_values: List[float], total_payments: List[float], platform_utilities: List[float], title: str, filename: str) -> PlotMetadata:
        fig, ax = plt.subplots(figsize=(8.0, 4.5))
        ax.plot(hours, platform_values, marker="o", markersize=4, linewidth=1.8, label=PlotLabels.get("platform_value", self.lang), color="#1f77b4")
        ax.plot(hours, total_payments, marker="s", markersize=4, linewidth=1.8, label=PlotLabels.get("total_payments", self.lang), color="#ff7f0e")
        ax.plot(hours, platform_utilities, marker="^", markersize=4, linewidth=1.8, label=PlotLabels.get("platform_utility", self.lang), color="#2ca02c")
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("value", self.lang), fontsize=11)
        ax.set_xticks(hours)
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        data_stats = {"n_hours": len(hours), "mean_platform_value": float(np.mean(platform_values)), "mean_total_payments": float(np.mean(total_payments)), "mean_platform_utility": float(np.mean(platform_utilities)), "total_platform_value": float(np.sum(platform_values)), "total_payments": float(np.sum(total_payments))}
        parameters = {"hours": hours, "n_datapoints": len(hours)}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "timeseries_kpi", parameters, data_stats)
    
    def boxplot_payments(self, hours: List[int], payments_per_hour: Dict[int, List[float]], title: str, filename: str) -> PlotMetadata:
        data = [payments_per_hour.get(h, [0.0]) for h in hours]
        data = [list(map(float, d)) if d else [0.0] for d in data]
        fig, ax = plt.subplots(figsize=(8.0, 4.5))
        bp = ax.boxplot(data, showmeans=True, meanline=True, showfliers=True, patch_artist=True, widths=0.6)
        for patch in bp['boxes']:
            patch.set_facecolor('#8dd3c7')
            patch.set_alpha(0.7)
        ax.set_xticklabels([f"{h:02d}" for h in hours])
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("payment", self.lang), fontsize=11)
        ax.grid(True, alpha=0.2, axis='y', linewidth=0.5)
        all_payments = [p for hour_payments in data for p in hour_payments]
        data_stats = {"n_hours": len(hours), "total_payments": len(all_payments), "mean_payment": float(np.mean(all_payments)), "median_payment": float(np.median(all_payments)), "std_payment": float(np.std(all_payments))}
        parameters = {"hours": hours}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "boxplot_payments", parameters, data_stats)
    
    def barplot_topN_payments(self, payments: Iterable[float], N: int, title: str, filename: str) -> PlotMetadata:
        vals = sorted([float(x) for x in payments if np.isfinite(x)], reverse=True)[:N]
        if not vals:
            fig, ax = plt.subplots(figsize=(6.0, 3.5))
            ax.text(0.5, 0.5, PlotLabels.get("no_payments", self.lang), ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "barplot_topN", {"N": N}, {"n_payments": 0})
        ranks = list(range(1, len(vals) + 1))
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(ranks, vals, color='#ff7f0e', alpha=0.8, edgecolor='black', linewidth=0.8)
        for rank, val in zip(ranks, vals):
            ax.text(rank, val, f"{val:.1f}", ha='center', va='bottom', fontsize=8)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("rank", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("payment", self.lang), fontsize=11)
        ax.set_xticks(ranks)
        ax.grid(True, alpha=0.2, axis='y', linewidth=0.5)
        data_stats = {"N": len(vals), "max_payment": float(vals[0]) if vals else 0.0, "min_payment": float(vals[-1]) if vals else 0.0, "mean_topN": float(np.mean(vals))}
        parameters = {"N": N, "actual_N": len(vals)}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "barplot_topN", parameters, data_stats)
    
    def plot_cdf(self, payments: Iterable[float], title: str, filename: str) -> PlotMetadata:
        vals = np.array([float(x) for x in payments if np.isfinite(x)], dtype=float)
        vals.sort()
        if vals.size == 0:
            fig, ax = plt.subplots(figsize=(6.5, 4.0))
            ax.text(0.5, 0.5, PlotLabels.get("no_data", self.lang), ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "cdf", {}, {"n_datapoints": 0})
        y = np.linspace(0, 1, len(vals), endpoint=True)
        fig, ax = plt.subplots(figsize=(7.0, 4.5))
        ax.plot(vals, y, linewidth=2.0, color='#1f77b4')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("payment", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("cdf", self.lang), fontsize=11)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        p25, p50, p75, p90 = np.percentile(vals, [25, 50, 75, 90])
        data_stats = {"n_datapoints": int(len(vals)), "min": float(vals[0]), "max": float(vals[-1]), "p25": float(p25), "p50": float(p50), "p75": float(p75), "p90": float(p90), "mean": float(np.mean(vals))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "cdf", {}, data_stats)
    
    def plot_lorenz_gini(self, payments: Iterable[float], title: str, filename: str) -> Tuple[PlotMetadata, float]:
        vals = np.asarray([float(x) for x in payments if np.isfinite(x)], dtype=float)
        if vals.size == 0:
            fig, ax = plt.subplots(figsize=(6.5, 4.5))
            ax.text(0.5, 0.5, PlotLabels.get("no_data", self.lang), ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            metadata = self._save_figure_with_metadata(fig, filepath, "lorenz_gini", {}, {"n_datapoints": 0, "gini": 0.0})
            return metadata, 0.0
        vals.sort()
        cumvals = np.cumsum(vals)
        total = float(cumvals[-1])
        if total <= 0.0:
            x = np.linspace(0.0, 1.0, len(vals), dtype=float)
            lorenz = x.copy()
            gini = 0.0
        else:
            cumvals = (cumvals / total).astype(float)
            x = np.linspace(0.0, 1.0, len(vals), dtype=float)
            lorenz = np.insert(cumvals, 0, 0.0).astype(float)
            x = np.insert(x, 0, 0.0).astype(float)
            if hasattr(np, "trapezoid"):
                B = float(np.trapezoid(lorenz, x))
            else:
                B = float(np.trapz(lorenz, x))
            gini = float(1.0 - 2.0 * B)
            gini = max(0.0, min(1.0, gini))
        fig, ax = plt.subplots(figsize=(7.0, 6.0))
        ax.plot(x, lorenz, linewidth=2.5, color='#d62728', label=PlotLabels.get("lorenz_curve", self.lang))
        ax.plot([0, 1], [0, 1], '--', linewidth=1.5, color='gray', label=PlotLabels.get("equality_line", self.lang))
        ax.text(0.6, 0.2, f"Gini = {gini:.3f}", fontsize=14, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabels.get("winner_fraction", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabels.get("payment_fraction", self.lang), fontsize=11)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        ax.set_aspect('equal')
        data_stats = {"n_datapoints": int(len(vals)), "gini": float(gini), "min_payment": float(vals[0]), "max_payment": float(vals[-1]), "mean_payment": float(np.mean(vals)), "total_payment": float(total)}
        parameters = {"gini_coefficient": float(gini)}
        filepath = os.path.join(self.output_dir, filename)
        metadata = self._save_figure_with_metadata(fig, filepath, "lorenz_gini", parameters, data_stats)
        return metadata, gini
    
    def compare_heatmaps_sidebyside(self, left_cells: Dict[Tuple[int, int], float], right_cells: Dict[Tuple[int, int], float], origin: Tuple[float, float], cell_m: float, left_title: str, right_title: str, overall_title: str, filename: str, colormap: str = None, colorbar_label: str = None, validate_alignment: bool = True) -> PlotMetadata:
        if not left_cells:
            raise ValueError("left_cells vuoto")
        if not right_cells:
            raise ValueError("right_cells vuoto")
        arr_left, min_iy_l, min_ix_l, H_l, W_l = self._cells_to_array(left_cells)
        arr_right, min_iy_r, min_ix_r, H_r, W_r = self._cells_to_array(right_cells)
        lat0, lon0 = origin
        if validate_alignment:
            max_iy_l = min_iy_l + H_l - 1
            max_ix_l = min_ix_l + W_l - 1
            max_iy_r = min_iy_r + H_r - 1
            max_ix_r = min_ix_r + W_r - 1
            overlap_y = not (max_iy_l < min_iy_r or max_iy_r < min_iy_l)
            overlap_x = not (max_ix_l < min_ix_r or max_ix_r < min_ix_l)
            if not (overlap_y and overlap_x):
                warnings.warn("Verificare compatibilità dati (stessa origine/cell_m)", UserWarning)
            size_ratio_y = max(H_l, H_r) / min(H_l, H_r) if min(H_l, H_r) > 0 else 1.0
            size_ratio_x = max(W_l, W_r) / min(W_l, W_r) if min(W_l, W_r) > 0 else 1.0
            if size_ratio_y > 3.0 or size_ratio_x > 3.0:
                warnings.warn("Dimensioni griglie molto diverse", UserWarning)
        all_vals = np.concatenate([arr_left[arr_left > 0].flatten(), arr_right[arr_right > 0].flatten()])
        if all_vals.size > 0:
            vmin = float(np.percentile(all_vals, 2))
            vmax = float(np.percentile(all_vals, 98))
        else:
            vmin, vmax = 0.0, 1.0
        if colormap is None:
            colormap = ColorPalettes.get_sequential("density")
        if colorbar_label is None:
            colorbar_label = PlotLabels.get("cell_count", self.lang)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        lat_edges_l, lon_edges_l = self._grid_edges_latlon(lat0, lon0, min_iy_l, min_ix_l, H_l, W_l, cell_m)
        ax1.pcolormesh(lon_edges_l, lat_edges_l, arr_left, shading="auto", cmap=colormap, vmin=vmin, vmax=vmax)
        ax1.set_title(left_title, fontsize=12, fontweight='bold')
        ax1.set_xlabel(PlotLabels.get("longitude", self.lang), fontsize=10)
        ax1.set_ylabel(PlotLabels.get("latitude", self.lang), fontsize=10)
        ax1.set_aspect("equal")
        lat_edges_r, lon_edges_r = self._grid_edges_latlon(lat0, lon0, min_iy_r, min_ix_r, H_r, W_r, cell_m)
        mesh2 = ax2.pcolormesh(lon_edges_r, lat_edges_r, arr_right, shading="auto", cmap=colormap, vmin=vmin, vmax=vmax)
        ax2.set_title(right_title, fontsize=12, fontweight='bold')
        ax2.set_xlabel(PlotLabels.get("longitude", self.lang), fontsize=10)
        ax2.set_ylabel(PlotLabels.get("latitude", self.lang), fontsize=10)
        ax2.set_aspect("equal")
        fig.colorbar(mesh2, ax=[ax1, ax2], label=colorbar_label, fraction=0.046, pad=0.04)
        fig.suptitle(overall_title, fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout(rect=([0, 0, 1, 0.96]))
        data_stats = {"left_n_cells": int(np.sum(arr_left > 0)), "right_n_cells": int(np.sum(arr_right > 0)), "left_mean": float(np.mean(arr_left[arr_left > 0])) if np.any(arr_left > 0) else 0.0, "right_mean": float(np.mean(arr_right[arr_right > 0])) if np.any(arr_right > 0) else 0.0}
        parameters = {"cell_size_m": float(cell_m), "colormap": colormap, "vmin": float(vmin), "vmax": float(vmax), "validate_alignment": validate_alignment}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "compare_heatmaps", parameters, data_stats)

def diagnostics_to_series(diag_list: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    vS = [float(d.get("platform_value_vS", 0.0)) for d in diag_list]
    sumP = [float(d.get("payments_sum", 0.0)) for d in diag_list]
    u0 = [float(d.get("platform_utility_u0", 0.0)) for d in diag_list]
    winners = [float(d.get("winners_count", 0.0)) for d in diag_list]
    return {"vS": vS, "sumP": sumP, "u0": u0, "winners": winners}

def cells_from_points(points: Iterable[Tuple[int, int]]) -> Dict[Tuple[int, int], float]:
    cells: Dict[Tuple[int, int], float] = {}
    for ij in points:
        cells[ij] = cells.get(ij, 0.0) + 1.0
    return cells
