from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import matplotlib.pyplot as plt
import os
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
    from Fase_2.plot_bounded import (
        ScientificPlotterRational, 
        PlotMetadata, 
        PlotLabelsRational
    )
except ImportError as e:
    raise ImportError(f"Impossibile importare plotter fase 2: {e}")


class PlotLabelsAdaptive(PlotLabelsRational):
    ITALIAN: Dict[str, str] = {
        **PlotLabelsRational.ITALIAN,
        "mae_rho": "Errore Medio Assoluto (MAE) su $\\hat{\\rho}$",
        "rho_convergence": "Convergenza Stima Razionalità",
        "rho_true": "Razionalità Reale $\\rho$",
        "rho_est": "Razionalità Stimata $\\hat{\\rho}$",
        "reputation_avg": "Reputazione Media $\\hat{R}$",
        "reputation_winners": "Reputazione Vincitori",
        "reputation_excluded": "Reputazione Esclusi",
        "reputation_trend": "Trend Reputazionale",
        "base_payment": "Pagamento Base (Critico)",
        "final_payment": "Pagamento Finale (Incentivato)",
        "incentive_impact": "Impatto Incentivi (Bonus/Malus)",
        "bonus": "Bonus",
        "malus": "Malus",
        "health_score": "Health Score Sistema (0-1)",
        "ir_violations_count": "Conteggio Violazioni IR",
        "exclusion_reasons": "Motivi di Esclusione Utenti",
        "hard_filter": "Filtro Reputazione (< 0.30)",
        "quality_filter": "Filtro Qualità ($\\rho < \\rho_{req}$)",
        "blacklist": "Blacklist Temporanea"
    }

    @staticmethod
    def get(key: str, lang: str = "it") -> str:
        return PlotLabelsAdaptive.ITALIAN.get(key, key) if lang == "it" else key


class ScientificPlotterAdaptive(ScientificPlotterRational):
    def __init__(
        self, 
        output_dir: str = "figures_phase3", 
        lang: str = "it", 
        dpi: int = None, 
        style: str = "publication"
    ):
        super().__init__(output_dir, lang, dpi, style)

    def plot_learning_convergence(
        self,
        hours: List[int],
        mae_history: List[float],
        std_dev_history: Optional[List[float]] = None,
        title: str = "Convergenza Apprendimento GAP",
        filename: str = "gap_learning_mae.png"
    ) -> PlotMetadata:
        if not hours or not mae_history:
            raise ValueError("hours e mae_history non possono essere vuoti")
        if len(hours) != len(mae_history):
            raise ValueError("Lunghezza ore e mae non corrispondono")
        fig, ax = plt.subplots(figsize=(8.0, 5.0))
        ax.plot(hours, mae_history, marker='o', color='#6a3d9a', linewidth=2.0, 
               label=PlotLabelsAdaptive.get("mae_rho", self.lang))
        if std_dev_history and len(std_dev_history) == len(hours):
            upper = [m + s for m, s in zip(mae_history, std_dev_history)]
            lower = [max(0, m - s) for m, s in zip(mae_history, std_dev_history)]
            ax.fill_between(hours, lower, upper, color='#6a3d9a', alpha=0.15, 
                           label="Deviazione Std $\\sigma_{\\hat{\\rho}}$")
        ax.axhline(y=0.15, color='gray', linestyle='--', linewidth=1.0, 
                  label="Target Convergenza (0.15)")
        ax.set_xlabel(PlotLabelsAdaptive.get("hour", self.lang), fontsize=11)
        ax.set_ylabel("MAE", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xticks(hours)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.2)
        denom = mae_history[0] if mae_history[0] > 1e-9 else 1.0
        stats = {
            "mae_iniziale": mae_history[0],
            "mae_finale": mae_history[-1],
            "riduzione_pct": (mae_history[0] - mae_history[-1]) / denom * 100
        }
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "learning_convergence", {"ore": hours}, stats
        )

    def plot_reputation_dynamics(
        self,
        hours: List[int],
        avg_rep_winners: List[float],
        avg_rep_population: List[float],
        title: str = "Dinamiche Reputazione (Vincitori vs Popolazione)",
        filename: str = "gap_reputation_dynamics.png"
    ) -> PlotMetadata:
        if not hours or not avg_rep_winners or not avg_rep_population:
            raise ValueError("Input non possono essere vuoti")
        if len(hours) != len(avg_rep_winners) or len(hours) != len(avg_rep_population):
            raise ValueError("Lunghezze liste non corrispondono")
        fig, ax = plt.subplots(figsize=(8.0, 5.0))
        ax.plot(hours, avg_rep_winners, marker='s', color='#2ca02c', linewidth=2.0, 
               label=PlotLabelsAdaptive.get("reputation_winners", self.lang))
        ax.plot(hours, avg_rep_population, marker='o', color='#7f7f7f', linewidth=1.5, 
               linestyle='--', label="Media Popolazione")
        ax.axhline(y=0.30, color='red', linestyle=':', linewidth=1.5, 
                  label=f"Hard Filter (R < 0.30)")
        ax.set_xlabel(PlotLabelsAdaptive.get("hour", self.lang))
        ax.set_ylabel("Reputazione $\\hat{R}$")
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.05)
        ax.set_xticks(hours)
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        stats = {
            "delta_finale": avg_rep_winners[-1] - avg_rep_population[-1],
            "avg_winners": float(np.mean(avg_rep_winners))
        }
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "reputation_dynamics", {}, stats
        )

    def plot_incentive_impact(
        self,
        base_payments: List[float],
        final_payments: List[float],
        title: str = "Impatto Incentivi GAP",
        filename: str = "gap_incentives_scatter.png"
    ) -> PlotMetadata:
        if not base_payments or not final_payments:
            raise ValueError("Input non possono essere vuoti")
        if len(base_payments) != len(final_payments):
            raise ValueError("Lunghezze liste non corrispondono")
        fig, ax = plt.subplots(figsize=(7.0, 7.0))
        max_val = max(max(base_payments), max(final_payments)) * 1.05
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label="Neutrale (Base=Finale)")
        colors = ['#2ca02c' if f >= b else '#d62728' for b, f in zip(base_payments, final_payments)]
        ax.scatter(base_payments, final_payments, c=colors, alpha=0.6, edgecolors='none', s=30)
        ax.set_xlabel(PlotLabelsAdaptive.get("base_payment", self.lang))
        ax.set_ylabel(PlotLabelsAdaptive.get("final_payment", self.lang))
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.text(max_val*0.1, max_val*0.9, "Area BONUS\n(Trust)", color='#2ca02c', 
               fontweight='bold', ha='left')
        ax.text(max_val*0.9, max_val*0.1, "Area MALUS\n(Distrust)", color='#d62728', 
               fontweight='bold', ha='right')
        stats = {
            "total_bonus": sum(f-b for f,b in zip(final_payments, base_payments) if f>b),
            "total_malus": sum(b-f for f,b in zip(final_payments, base_payments) if f<b)
        }
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "incentive_impact", {}, stats
        )

    def plot_health_dashboard(
        self,
        hours: List[int],
        health_scores: List[float],
        ir_violations: List[float],
        completion_rates: List[float],
        title: str = "Dashboard Salute Sistema GAP",
        filename: str = "gap_health_dashboard.png"
    ) -> PlotMetadata:
        if not hours or not health_scores or not ir_violations or not completion_rates:
            raise ValueError("Input non possono essere vuoti")
        fig, ax1 = plt.subplots(figsize=(10.0, 6.0))
        ax1.plot(hours, health_scores, 'b-o', linewidth=2.5, label="Health Score")
        ax1.plot(hours, completion_rates, 'g:s', linewidth=1.5, alpha=0.7, label="Completion Rate")
        ax1.set_xlabel("Ora")
        ax1.set_ylabel("Score / Rate (0-1)", color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.set_ylim(0, 1.05)
        ax2 = ax1.twinx()
        ax2.bar(hours, [v * 100 for v in ir_violations], color='red', alpha=0.3, width=0.4, label="Violazioni IR (%)")
        ax2.set_ylabel("Violazioni IR (%)", color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        max_ir_pct = max([v * 100 for v in ir_violations]) if ir_violations else 10
        ax2.set_ylim(0, max(20, max_ir_pct * 1.1))
        ax1.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax1.set_xticks(hours)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', 
                  bbox_to_anchor=(0.5, -0.1), ncol=3)
        ax1.grid(True, alpha=0.2)
        fig.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "health_dashboard", {"ore": hours}, 
            {"avg_health": float(np.mean(health_scores))}
        )

    def plot_convergence_simulation(
        self,
        sim_data: Dict[str, Any],
        title: str = "Simulazione Convergenza Bayesiana",
        filename: str = "gap_convergence_sim.png"
    ) -> PlotMetadata:
        history_mae = sim_data['history_mae']
        rho_true = sim_data['rho_true']
        rounds = range(len(history_mae))
        fig, ax = plt.subplots(figsize=(8.0, 5.0))
        ax.plot(rounds, history_mae, color='#6a3d9a', linewidth=1.5, label="MAE")
        ax.axhline(y=0, color='green', linestyle='--', alpha=0.5, label="Target Perfetto")
        ax.set_title(f"{title} ($\\rho_{{true}}={rho_true:.2f}$)", fontsize=12, fontweight='bold')
        ax.set_xlabel("Round di Apprendimento")
        ax.set_ylabel("Errore Assoluto $|\\hat{\\rho} - \\rho|$")
        ax.legend()
        ax.grid(True, alpha=0.2)
        stats = {
            "mae_finale": history_mae[-1],
            "rho_true": rho_true
        }
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "bayesian_sim", {}, stats
        )

    def plot_reputation_histograms(
        self,
        pop_reps: List[float],
        win_reps: List[float],
        hard_filter_threshold: float = 0.30,
        title: str = "Distribuzione Reputazione: Popolazione vs Vincitori",
        filename: str = "gap_reputation_hist.png"
    ) -> PlotMetadata:
        fig, ax = plt.subplots(figsize=(8.0, 5.0))
        pop_clean = [x for x in pop_reps if not np.isnan(x)]
        win_clean = [x for x in win_reps if not np.isnan(x)]
        ax.hist(pop_clean, bins=30, alpha=0.5, label='Popolazione Totale', 
                color='#1f77b4', density=True)
        ax.hist(win_clean, bins=30, alpha=0.5, label='Vincitori Selezionati', 
                color='#ff7f0e', density=True)
        ax.axvline(x=hard_filter_threshold, color='red', linestyle='--', linewidth=1.5,
                  label=f'Hard Filter ({hard_filter_threshold})')
        ax.set_xlabel("Reputazione $\\hat{R}$")
        ax.set_ylabel("Densità di Frequenza")
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.2)
        stats = {
            "n_pop": len(pop_clean),
            "n_win": len(win_clean),
            "mean_pop": float(np.mean(pop_clean)) if pop_clean else 0,
            "mean_win": float(np.mean(win_clean)) if win_clean else 0
        }
        filepath = os.path.join(self.output_dir, filename)
        return self._save_figure_with_metadata(
            fig, filepath, "reputation_hist", {}, stats
        )


def _get_adaptive_plotter(filepath: str) -> Tuple[ScientificPlotterAdaptive, str]:
    output_dir = os.path.dirname(filepath) or "."
    filename = os.path.basename(filepath)
    return ScientificPlotterAdaptive(output_dir=output_dir), filename

def plot_learning_curve(hours, mae, std, title, out_path):
    plotter, filename = _get_adaptive_plotter(out_path)
    return plotter.plot_learning_convergence(hours, mae, std, title, filename)

def plot_reputation(hours, win_rep, pop_rep, title, out_path):
    plotter, filename = _get_adaptive_plotter(out_path)
    return plotter.plot_reputation_dynamics(hours, win_rep, pop_rep, title, filename)

def plot_incentives(base, final, title, out_path):
    plotter, filename = _get_adaptive_plotter(out_path)
    return plotter.plot_incentive_impact(base, final, title, filename)

def plot_health(hours, health, ir, compl, title, out_path):
    plotter, filename = _get_adaptive_plotter(out_path)
    return plotter.plot_health_dashboard(hours, health, ir, compl, title, filename)

def plot_mech_vs_eff(hours, v_mech, v_eff, title, out_path):
    plotter, filename = _get_adaptive_plotter(out_path)
    return plotter.plot_mech_vs_eff_timeseries(hours, v_mech, v_eff, title, filename)
