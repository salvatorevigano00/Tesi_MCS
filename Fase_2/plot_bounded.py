from __future__ import annotations
from typing import Dict, List, Tuple, Iterable, Optional
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import warnings
import os
import sys
import json
import datetime
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
    from Fase_1.plot import ScientificPlotter, PlotMetadata, PlotLabels, ColorPalettes
except ImportError as e:
    raise ImportError(f"Impossibile importare il modulo di plotting della Fase 1:\n  File richiesto: {_fase1_dir}/plot.py\n  Dettaglio: {e}")

try:
    from Fase_2.imcu_bounded import IMCURationalConfig
except ImportError:
    IMCURationalConfig = None
    warnings.warn("IMCURationalConfig non disponibile, metadati ridotti.", category=ImportWarning)

def _get_git_commit_hash() -> Optional[str]:
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=2, check=True)
        return result.stdout.strip()
    except Exception:
        return None

def _get_plotter_from_path(filepath: str) -> Tuple['ScientificPlotterRational', str]:
    output_dir = os.path.dirname(filepath) or "."
    filename = os.path.basename(filepath)
    return ScientificPlotterRational(output_dir=output_dir), filename

class PlotLabelsRational(PlotLabels):
    ITALIAN: Dict[str, str] = {**PlotLabels.ITALIAN, "v_mech": "Valore meccanismo $v(S_{mech})$ (euro)", "v_eff": "Valore effettivo $v(S_{eff})$ (euro)", "u0_mech": "Utilità piattaforma (ex-ante) $u_{0, mech}$ (euro)", "u0_eff": "Utilità piattaforma (ex-post) $u_{0, eff}$ (euro)", "efficiency": "Rapporto di realizzazione ($v_{eff} / v_{mech}$)", "gap_value": "Perdita di valore (gap): $v_{mech} - v_{eff}$ (euro)", "breakdown_pct": "Tasso di rottura (%)", "feasible_region": "Regione fattibile (valore teorico)", "profile": "Profilo di onestà", "perfect_rational": "Razionale perfetto", "quasi_rational": "Quasi-razionale", "bounded_honest": "Onesto limitato", "bounded_moderate": "Moderato limitato", "bounded_opportunistic": "Opportunistico limitato", "winners_by_profile": "Distribuzione vincitori per profilo", "rationality_level": "Livello di razionalità $\\rho$", "bid_deviation": "Deviazione offerta $(b-c)/c$ (%)", "gap_quality": "Qualità attesa GAP (euro)", "gap_spend": "Spesa totale GAP (euro)", "quality_vs_spend": "Qualità vs spesa", "gap_density_coverage": "GAP copertura (domanda - copertura effettiva)", "density": "Densità osservazioni (domanda)", "coverage_mech": "Copertura meccanismo (ex-ante)", "coverage_eff": "Copertura effettiva (ex-post)", "r_min": "Ricompensa minima $r_{min}$ (euro)", "r_min_distribution": "Distribuzione ricompensa minima", "cdf_r_min": "Funzione cumulativa (CDF) $r_{min}$", "histogram_r_min": "Istogramma $r_{min}$", "phase1_baseline": "Fase 1 (baseline razionale)", "phase2_bounded": "Fase 2 (razionalità limitata)", "comparison": "Confronto Fase 1 vs Fase 2", "efficiency_loss": "Perdita di efficienza (%)"}
    
    @staticmethod
    def get(key: str, lang: str = "it") -> str:
        return PlotLabelsRational.ITALIAN.get(key, key) if lang == "it" else key

class ScientificPlotterRational(ScientificPlotter):
    def __init__(self, output_dir: str = "figures", lang: str = "it", dpi: int = None, style: str = "publication"):
        super().__init__(output_dir, lang, dpi, style)
    
    def _save_figure_with_metadata_extended(self, fig, filepath: str, plot_type: str, parameters: dict, data_stats: dict) -> PlotMetadata:
        metadata = super()._save_figure_with_metadata(fig, filepath, plot_type, parameters, data_stats)
        extended_data_stats = dict(data_stats)
        if IMCURationalConfig is not None:
            extended_data_stats["config_razionalita_limitata"] = {"soglia_avviso_offerta_pct": IMCURationalConfig.BID_DEVIATION_WARNING_PCT, "simula_azzardo_morale": IMCURationalConfig.SIMULATE_MORAL_HAZARD}
        git_commit = _get_git_commit_hash()
        if git_commit:
            extended_data_stats["git_commit_hash"] = git_commit
        json_path = filepath.replace(".png", ".json").replace(".pdf", ".json")
        timestamp = datetime.datetime.now().isoformat()
        json_export = {"percorso_file": filepath, "tipo_grafico": plot_type, "parametri": parameters, "statistiche_dati": extended_data_stats, "timestamp_generazione": timestamp}
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_export, f, indent=2, ensure_ascii=False)
        except Exception as e:
            warnings.warn(f"Impossibile salvare i metadati JSON: {e}")
        return metadata
    
    def _save_figure_with_metadata(self, fig, filepath: str, plot_type: str, parameters: dict, data_stats: dict) -> PlotMetadata:
        return self._save_figure_with_metadata_extended(fig, filepath, plot_type, parameters, data_stats)
    
    def plot_gap_heatmap(self, density_cells: Dict[Tuple[int, int], float], coverage_cells: Dict[Tuple[int, int], float], origin: Tuple[float, float], cell_m: float, title: str, filename: str, norm_mode: str = "percentiles", p_low: float = 2.0, p_high: float = 98.0) -> PlotMetadata:
        if not density_cells:
            raise ValueError("Il dizionario `density_cells` è vuoto.")
        if not coverage_cells:
            raise ValueError("Il dizionario `coverage_cells` è vuoto.")
        all_keys = set(density_cells.keys()) | set(coverage_cells.keys())
        gap_cells = {k: float(density_cells.get(k, 0.0) - coverage_cells.get(k, 0.0)) for k in all_keys}
        colormap = ColorPalettes.get_diverging("gap")
        colorbar_label = PlotLabelsRational.get("gap_density_coverage", self.lang)
        return self.heatmap(cells=gap_cells, origin=origin, cell_m=cell_m, title=title, filename=filename, colormap=colormap, norm_mode=norm_mode, p_low=p_low, p_high=p_high, colorbar_label=colorbar_label)
    
    def plot_mech_vs_eff_timeseries(self, hours: List[int], v_mech: List[float], v_eff: List[float], title: str, filename: str, annotate_gap: bool = True) -> PlotMetadata:
        if len(hours) != len(v_mech) or len(hours) != len(v_eff):
            raise ValueError(f"Lunghezze delle liste non consistenti: ore={len(hours)}, v_mech={len(v_mech)}, v_eff={len(v_eff)}")
        if not hours:
            raise ValueError("La lista 'hours' è vuota. Impossibile generare il grafico.")
        fig, ax = plt.subplots(figsize=(10.0, 6.0))
        ax.plot(hours, v_mech, 'b-', marker='o', label=PlotLabelsRational.get("v_mech", self.lang), linewidth=2.0, markersize=5)
        ax.plot(hours, v_eff, 'r--', marker='s', label=PlotLabelsRational.get("v_eff", self.lang), linewidth=2.0, markersize=5)
        ax.fill_between(hours, 0, v_mech, alpha=0.15, color='blue', label=PlotLabelsRational.get("feasible_region", self.lang))
        gaps = [vm - ve for vm, ve in zip(v_mech, v_eff)]
        breakdown_pct = 0.0
        if annotate_gap and v_mech:
            avg_gap = float(np.mean(gaps))
            avg_v_mech = float(np.mean(v_mech))
            breakdown_pct = 100 * avg_gap / avg_v_mech if avg_v_mech > 1e-9 else 0.0
            textstr = f"Perdita di valore (gap) media: {avg_gap:.2f} euro\nTasso di rottura (breakdown): {breakdown_pct:.1f}%"
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.6)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11, verticalalignment='top', bbox=props)
        ax.set_xlabel(PlotLabelsRational.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("value", self.lang), fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xticks(hours)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        _, ymax = ax.get_ylim()
        ax.set_ylim(0, ymax * 1.05)
        data_stats = {"n_ore": len(hours), "media_v_mech": float(np.mean(v_mech)), "media_v_eff": float(np.mean(v_eff)), "media_gap": float(np.mean(gaps)), "tasso_rottura_pct": float(breakdown_pct), "totale_v_mech": float(np.sum(v_mech)), "totale_v_eff": float(np.sum(v_eff))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "timeseries_valore_mech_vs_eff", {"ore": hours, "annotazione_gap": annotate_gap}, data_stats)
    
    def plot_utility_compare(self, hours: List[int], u0_mech: List[float], u0_eff: List[float], title: str, filename: str) -> PlotMetadata:
        if len(hours) != len(u0_mech) or len(hours) != len(u0_eff):
            raise ValueError(f"Lunghezze delle liste non consistenti: ore={len(hours)}, u0_mech={len(u0_mech)}, u0_eff={len(u0_eff)}")
        if not hours:
            raise ValueError("La lista 'hours' è vuota. Impossibile generare il grafico.")
        fig, ax = plt.subplots(figsize=(8.0, 4.5))
        ax.plot(hours, u0_mech, marker="o", markersize=4, linewidth=1.8, label=PlotLabelsRational.get("u0_mech", self.lang), color="#1f77b4")
        ax.plot(hours, u0_eff, marker="s", markersize=4, linewidth=1.8, label=PlotLabelsRational.get("u0_eff", self.lang), color="#d62728")
        ax.axhline(y=0.0, color='black', linestyle=':', linewidth=1.0, alpha=0.7)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("utility", self.lang), fontsize=11)
        ax.set_xticks(hours)
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        data_stats = {"n_ore": len(hours), "media_u0_mech": float(np.mean(u0_mech)), "media_u0_eff": float(np.mean(u0_eff)), "media_gap_utilita": float(np.mean([um - ue for um, ue in zip(u0_mech, u0_eff)]))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "confronto_utilita", {"ore": hours}, data_stats)
    
    def plot_efficiency_series(self, hours: List[int], v_mech: List[float], v_eff: List[float], title: str, filename: str) -> PlotMetadata:
        if len(hours) != len(v_mech) or len(hours) != len(v_eff):
            raise ValueError(f"Lunghezze delle liste non consistenti: ore={len(hours)}, v_mech={len(v_mech)}, v_eff={len(v_eff)}")
        eps = 1e-9
        valid_data = [(h, ve / vm) for h, vm, ve in zip(hours, v_mech, v_eff) if vm > eps]
        if not valid_data:
            fig, ax = plt.subplots(figsize=(7.5, 4.0))
            ax.text(0.5, 0.5, "Nessuna allocazione di valore valida", ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "serie_efficienza", {}, {"n_punti_dati": 0})
        hours_plot, efficiency = zip(*valid_data)
        fig, ax = plt.subplots(figsize=(7.5, 4.0))
        ax.plot(hours_plot, efficiency, marker="o", color="#2ca02c", linewidth=2.0, markersize=5)
        ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.0, alpha=0.6, label="Efficienza perfetta (100%)")
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("efficiency", self.lang), fontsize=11)
        ax.set_xticks(hours_plot)
        ax.set_ylim(0, 1.05)
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        data_stats = {"n_ore_valide": len(hours_plot), "n_ore_saltate": len(hours) - len(hours_plot), "efficienza_media": float(np.mean(efficiency)), "efficienza_min": float(np.min(efficiency)), "efficienza_max": float(np.max(efficiency))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "serie_efficienza", {"ore": list(hours), "ore_valide": list(hours_plot)}, data_stats)
    
    def plot_winners_profile_bar(self, profile_counts: Dict[str, int], title: str, filename: str) -> PlotMetadata:
        if not profile_counts or sum(profile_counts.values()) == 0:
            fig, ax = plt.subplots(figsize=(6.0, 3.5))
            ax.text(0.5, 0.5, "Nessun vincitore da analizzare", ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "barre_profili_vincitori", {}, {"n_profili": 0, "totale_vincitori": 0})
        profiles = list(profile_counts.keys())
        counts = [profile_counts[p] for p in profiles]
        color_map = {"Quasi-Rational": "#2ca02c","Bounded Honest": "#8dd3c7","Bounded Moderate": "#ff7f0e","Bounded Opportunistic": "#d62728"}
        colors = [color_map.get(p, "#1f77b4") for p in profiles]
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(profiles, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=0.8)
        for i, (p, c) in enumerate(zip(profiles, counts)):
            ax.text(i, c, f"{c}", ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("profile", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("winners", self.lang), fontsize=11)
        ax.grid(True, alpha=0.2, axis='y', linewidth=0.5)
        plt.xticks(rotation=15, ha='right')
        data_stats = {"n_profili": len(profiles), "totale_vincitori": sum(counts), "distribuzione_profili": profile_counts}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "barre_profili_vincitori", {"profili": profiles}, data_stats)
    
    def plot_gap_quality_vs_spend(self, hours: List[int], quality: List[float], spend: List[float], title: str, filename: str) -> PlotMetadata:
        if len(hours) != len(quality) or len(hours) != len(spend):
            raise ValueError(f"Lunghezze delle liste non consistenti: ore={len(hours)}, qualità={len(quality)}, spesa={len(spend)}")
        if not hours:
            raise ValueError("La lista 'hours' è vuota. Impossibile generare il grafico.")
        fig, ax = plt.subplots(figsize=(8.0, 4.0))
        ax.plot(hours, quality, marker="o", label=PlotLabelsRational.get("gap_quality", self.lang), color="#2ca02c", linewidth=2.0, markersize=5)
        ax.plot(hours, spend, marker="s", label=PlotLabelsRational.get("gap_spend", self.lang), color="#d62728", linewidth=2.0, markersize=5)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("hour", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("value", self.lang), fontsize=11)
        ax.set_xticks(hours)
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        data_stats = {"n_ore": len(hours), "media_qualita": float(np.mean(quality)), "media_spesa": float(np.mean(spend)), "totale_qualita": float(np.sum(quality)), "totale_spesa": float(np.sum(spend))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "gap_qualita_vs_spesa", {"ore": hours}, data_stats)
    
    def plot_rmin_histogram(self, rmins: Iterable[float], title: str, filename: str, bins: int = 30) -> PlotMetadata:
        vals = np.array([float(x) for x in rmins if np.isfinite(x)], dtype=float)
        if vals.size == 0:
            fig, ax = plt.subplots(figsize=(6.0, 3.5))
            ax.text(0.5, 0.5, "Nessun dato valido per r_min", ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "istogramma_rmin", {"bins": bins}, {"n_punti_dati": 0})
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        ax.hist(vals, bins=bins, color="#4477aa", alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("r_min", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("frequency", self.lang), fontsize=11)
        ax.grid(True, alpha=0.2, axis='y', linewidth=0.5)
        data_stats = {"n_punti_dati": int(len(vals)), "media": float(np.mean(vals)), "mediana": float(np.median(vals)), "dev_std": float(np.std(vals)), "min": float(np.min(vals)), "max": float(np.max(vals))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "istogramma_rmin", {"bins": bins}, data_stats)
    
    def plot_rmin_cdf(self, rmins: Iterable[float], title: str, filename: str) -> PlotMetadata:
        vals = np.array([float(x) for x in rmins if np.isfinite(x)], dtype=float)
        if vals.size == 0:
            fig, ax = plt.subplots(figsize=(6.0, 3.5))
            ax.text(0.5, 0.5, "Nessun dato valido per r_min", ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.axis('off')
            filepath = os.path.join(self.output_dir, filename)
            return self._save_figure_with_metadata(fig, filepath, "cdf_rmin", {}, {"n_punti_dati": 0})
        vals.sort()
        y = np.linspace(0, 1, len(vals), endpoint=True)
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        ax.plot(vals, y, linewidth=2.0, color='#1f77b4')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel(PlotLabelsRational.get("r_min", self.lang), fontsize=11)
        ax.set_ylabel(PlotLabelsRational.get("cdf", self.lang), fontsize=11)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        data_stats = {"n_punti_dati": int(len(vals)), "p25": float(np.percentile(vals, 25)), "p50": float(np.percentile(vals, 50)), "p75": float(np.percentile(vals, 75)), "p90": float(np.percentile(vals, 90))}
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(fig, filepath, "cdf_rmin", {}, data_stats)
    
    def plot_rmin_lorenz_gini(self, rmins: Iterable[float], title: str, filename: str) -> Tuple[PlotMetadata, float]:
        return self.plot_lorenz_gini(rmins, title, filename)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def heatmap(cells, origin, cell_m, title, out_png, **kwargs):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.heatmap(cells=cells, origin=origin, cell_m=cell_m, title=title, filename=filename, **kwargs)

def gap_heatmap(density_cells, coverage_cells, origin, cell_m, title, out_png, **kwargs):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_gap_heatmap(density_cells=density_cells, coverage_cells=coverage_cells, origin=origin, cell_m=cell_m, title=title, filename=filename, **kwargs)

def mech_eff_timeseries(hours, v_mech, v_eff, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_mech_vs_eff_timeseries(hours=hours, v_mech=v_mech, v_eff=v_eff, title=title, filename=filename)

def utility_compare_series(hours, u0_mech, u0_eff, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_utility_compare(hours=hours, u0_mech=u0_mech, u0_eff=u0_eff, title=title, filename=filename)

def efficiency_series(hours, v_mech, v_eff, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_efficiency_series(hours=hours, v_mech=v_mech, v_eff=v_eff, title=title, filename=filename)

def winners_profile_bar(profile_counts, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_winners_profile_bar(profile_counts=profile_counts, title=title, filename=filename)

def rmin_hist_cdf(rmins, title_prefix, out_hist, out_cdf):
    plotter_hist, filename_hist = _get_plotter_from_path(out_hist)
    plotter_cdf, filename_cdf = _get_plotter_from_path(out_cdf)
    plotter_hist.plot_rmin_histogram(rmins=rmins, title=f"{title_prefix} - {PlotLabelsRational.get('histogram_r_min')}", filename=filename_hist)
    plotter_cdf.plot_rmin_cdf(rmins=rmins, title=f"{title_prefix} - {PlotLabelsRational.get('cdf_r_min')}", filename=filename_cdf)

def lorenz_gini(values, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    _, gini = plotter.plot_lorenz_gini(values, title, filename)
    return gini

def gap_quality_vs_spend(hours, quality, spend, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.plot_gap_quality_vs_spend(hours=hours, quality=quality, spend=spend, title=title, filename=filename)

def payments_box(hours, per_hour_values, title, out_png):
    plotter, filename = _get_plotter_from_path(out_png)
    plotter.boxplot_payments(hours=hours, payments_per_hour=per_hour_values, title=title, filename=filename)
