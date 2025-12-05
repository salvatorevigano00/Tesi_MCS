import pandas as pd
import os
import traceback
import matplotlib.pyplot as plt
import numpy as np

def print_table(df, title):
    print(f"\n{title}")
    pd.options.display.float_format = '{:,.2f}'.format
    print(df.to_string(index=False))

def plot_comparison(df, scenario, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    width = 0.35
    x = np.arange(len(df['ora']))
    
    ax.bar(x - width/2, df['v_eff_f2'], width, label='v_eff F2', color='#a1c9f4')
    ax.bar(x - width/2, df['u0_eff_f2'], width, label='u0_eff F2', color='#8de5a1', alpha=0.7) # Sovrapposto o affiancato? Meglio affiancare gruppi
    
    plt.close(fig)

    plt.figure(figsize=(10, 6))
    plt.plot(df['ora'], df['v_eff_f2'], marker='o', label='Fase 2 (No GAP)', linestyle='--', color='gray')
    plt.plot(df['ora'], df['v_eff_f3'], marker='o', label='Fase 3 (GAP)', color='blue', linewidth=2)
    plt.title(f'Confronto Valore Effettivo Realizzato - Scenario {scenario.upper()}')
    plt.xlabel('Ora del Giorno')
    plt.ylabel('Valore (€)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, f'confronto_valore_{scenario}.png'), dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(df['ora'], df['u0_eff_f2'], marker='s', label='Fase 2 (No GAP)', linestyle='--', color='gray')
    plt.plot(df['ora'], df['u0_eff_f3'], marker='s', label='Fase 3 (GAP)', color='green', linewidth=2)
    plt.title(f'Confronto Utilità Piattaforma - Scenario {scenario.upper()}')
    plt.xlabel('Ora del Giorno')
    plt.ylabel('Utilità (€)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, f'confronto_utilita_{scenario}.png'), dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(df['ora'], df['completion_rate_f2']*100, marker='^', label='Fase 2 (No GAP)', linestyle='--', color='red')
    plt.plot(df['ora'], df['tasso_compl']*100, marker='^', label='Fase 3 (GAP)', color='orange', linewidth=2)
    plt.ylim(0, 105)
    plt.title(f'Confronto Tasso di Completamento - Scenario {scenario.upper()}')
    plt.xlabel('Ora del Giorno')
    plt.ylabel('Completion Rate (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, f'confronto_completion_{scenario}.png'), dpi=300)
    plt.close()

def run_comparison():
    SCENARIOS = ["low", "mixed", "high"]
    DATE_STR = "2014-02-01"
    
    BASE_PATH_F2 = os.path.join("..", "Fase_2")
    BASE_PATH_F3 = "."
    OUTPUT_IMG_DIR = "confronto_fase2_fase3"

    print(f"Analisi comparativa Fase 2 vs Fase 3 - Data: {DATE_STR}")
    print(f"Directory corrente: {os.getcwd()}")

    for scenario in SCENARIOS:
        print(f"\n{'='*60}\n SCENARIO: {scenario.upper()}\n{'='*60}")
        
        dir_f2 = os.path.join(BASE_PATH_F2, f"esperimenti_fase2_{scenario}", f"giorno_{DATE_STR}_fase2")
        file_f2 = os.path.join(dir_f2, f"{DATE_STR}_kpi_orari_fase2.csv")
        dir_f3 = os.path.join(BASE_PATH_F3, f"esperimenti_fase3_{scenario}", f"giorno_{DATE_STR}_fase3")
        file_f3 = os.path.join(dir_f3, f"{DATE_STR}_kpi_orari_fase3.csv")

        if not os.path.exists(file_f2):
            print(f"File CSV Fase 2 non trovato: {file_f2}")
            continue
        if not os.path.exists(file_f3):
            print(f"File CSV Fase 3 non trovato: {file_f3}")
            continue

        try:
            df_f2 = pd.read_csv(file_f2)
            df_f3 = pd.read_csv(file_f3)
            df_f2.columns = df_f2.columns.str.strip()
            df_f3.columns = df_f3.columns.str.strip()

            df_merged = pd.merge(df_f2, df_f3, on='ora', suffixes=('_f2', '_f3'))

            col_vincitori = 'vincitori' if 'vincitori' in df_merged.columns else 'vincitori_f2'
            df_merged['completion_rate_f2'] = df_merged.apply(
                lambda r: 1 - (r['defezioni_totali'] / r[col_vincitori]) if r[col_vincitori] > 0 else 0.0, 
                axis=1
            )

            cols_req = ['ora', 'v_eff_f2', 'v_eff_f3', 'u0_eff_f2', 'u0_eff_f3', 'completion_rate_f2', 'tasso_compl', 'mae_rho']
            df_comp = df_merged[cols_req].copy()
            
            df_comp['delta_v'] = df_comp['v_eff_f3'] - df_comp['v_eff_f2']
            df_comp['delta_u0'] = df_comp['u0_eff_f3'] - df_comp['u0_eff_f2']
            df_comp['delta_cr'] = df_comp['tasso_compl'] - df_comp['completion_rate_f2']

            print_table(df_comp, f"Dettaglio Orario - Scenario {scenario.upper()}")

            tot_v2, tot_v3 = df_comp['v_eff_f2'].sum(), df_comp['v_eff_f3'].sum()
            tot_u2, tot_u3 = df_comp['u0_eff_f2'].sum(), df_comp['u0_eff_f3'].sum()
            avg_cr2, avg_cr3 = df_comp['completion_rate_f2'].mean(), df_comp['tasso_compl'].mean()

            agg_data = [
                ["Valore Effettivo (v_eff)", f"€ {tot_v2:,.0f}", f"€ {tot_v3:,.0f}", f"{tot_v3-tot_v2:+,.0f} €", f"{(tot_v3-tot_v2)/tot_v2:+.2%}"],
                ["Utilità Piattaforma (u0)", f"€ {tot_u2:,.0f}", f"€ {tot_u3:,.0f}", f"{tot_u3-tot_u2:+,.0f} €", f"{(tot_u3-tot_u2)/tot_u2:+.2%}"],
                ["Completion Rate Medio", f"{avg_cr2:.1%}", f"{avg_cr3:.1%}", f"{avg_cr3-avg_cr2:+.1%}", "-"]
            ]
            
            print(f"\nRiepilogo Aggregato - {scenario.upper()}")
            for row in agg_data:
                print(f"{row[0]:<25} | F2: {row[1]:<10} | F3: {row[2]:<10} | Delta: {row[3]:<10} ({row[4]})")

            plot_comparison(df_comp, scenario, OUTPUT_IMG_DIR)
            print(f"\nGrafici salvati in: {os.path.abspath(OUTPUT_IMG_DIR)}")

        except Exception as e:
            print(f"Errore durante elaborazione scenario {scenario}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_comparison()