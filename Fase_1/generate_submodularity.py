import numpy as np
import matplotlib.pyplot as plt

def generate_diminishing_returns_submodularity_plot():
    curve_color = '#08306b'       
    marginal_gain_color = '#2171b5' 
    projection_color = '#bdbdbd'  
    asymptote_color = '#7f7f7f'
    text_color = '#444444'
    axis_color = '#525252'
    
    saturation_rate = 0.45 
    unit_delta_x = 1.5 
    x_initial_phase = 0.8
    x_intermediate_phase = 3.5
    x_asymptotic_phase = 6.5
    y_phase_labels_position = -0.14
    x_final = x_asymptotic_phase + unit_delta_x
    
    x_domain = np.linspace(0, x_final, 2000)
    utility_curve_y = 1 - np.exp(-saturation_rate * x_domain)
    _, ax = plt.subplots(figsize=(13, 9.5), dpi=100)

    ax.plot(x_domain, utility_curve_y, color=curve_color, linewidth=2.5, zorder=5)
    ax.axhline(y=1.0, color=asymptote_color, linestyle='--', linewidth=1, alpha=0.7, zorder=1)
    ax.text(x_final, 1.01, r'Limite $v(S)=1$', ha='right', va='bottom', fontsize=9, color=asymptote_color)
    ax.text(5.2, 0.45, r"$v(S) = 1 - e^{-k \cdot |S|}$", fontsize=15, color='#333333', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', boxstyle='round,pad=0.5'))

    def visualize_marginal_gain(x_start, delta_label, phase_description, y_description_pos=-0.12):
        x_end = x_start + unit_delta_x
        y_start_val = 1 - np.exp(-saturation_rate * x_start)
        y_end_val = 1 - np.exp(-saturation_rate * x_end)
        x_fill = np.linspace(x_start, x_end, 200)
        y_fill_curve = 1 - np.exp(-saturation_rate * x_fill)
        baseline = np.full_like(x_fill, y_start_val)
        ax.fill_between(x_fill, baseline, y_fill_curve, color=marginal_gain_color, alpha=0.8, zorder=10, edgecolor=None)
        projection_style = dict(color=projection_color, linestyle=':', linewidth=0.8, zorder=1)
        ax.plot([0, x_start], [y_start_val, y_start_val], **projection_style) 
        ax.plot([0, x_end], [y_end_val, y_end_val], **projection_style)     
        ax.plot([x_start, x_start], [0, y_start_val], **projection_style)
        ax.plot([x_end, x_end], [0, y_end_val], **projection_style)
        mid_x = (x_start + x_end) / 2
        vertical_text_offset = 0.03 
        ax.text(mid_x, y_start_val - vertical_text_offset, delta_label, color=marginal_gain_color, fontsize=16, va='top', ha='center', zorder=15)
        ax.text(mid_x, y_description_pos, phase_description, color=text_color, fontsize=10, ha='center', va='top', style='italic')
        return y_start_val, y_end_val

    y1_start, y1_end = visualize_marginal_gain(x_initial_phase, r'$\Delta_1$', "Fase iniziale\n(guadagno rapido)", y_description_pos=y_phase_labels_position)
    y2_start, y2_end = visualize_marginal_gain(x_intermediate_phase, r'$\Delta_2$', "Fase di saturazione\n(rendimenti decrescenti)", y_description_pos=y_phase_labels_position)
    y3_start, y3_end = visualize_marginal_gain(x_asymptotic_phase, r'$\Delta_3$', "Fase asintotica\n(guadagno quasi nullo)", y_description_pos=y_phase_labels_position)

    x_tick_positions = [0, x_initial_phase, x_initial_phase + unit_delta_x, x_intermediate_phase, x_intermediate_phase + unit_delta_x, x_asymptotic_phase, x_asymptotic_phase + unit_delta_x]
    x_tick_labels = ['0', r'$S_1$', r'$S_1+1$', r'$S_2$', r'$S_2+1$', r'$S_3$', r'$S_3+1$']
    ax.set_xticks(x_tick_positions)
    ax.set_xticklabels(x_tick_labels, fontsize=10, color=text_color)
    ax.set_xlabel(r"Dimensione insieme $S$ (numero di utenti)", fontsize=12, labelpad=80, color='#252525')

    y_ticks_standard = [0, y1_start, y1_end]
    y_tick_labels_standard = ['0', r'$v(S_1)$', r'$v(S_1+1)$']
    ax.set_yticks(y_ticks_standard)
    ax.set_yticklabels(y_tick_labels_standard, fontsize=10, color=text_color)

    def add_manual_y_tick(y_value, label, vertical_nudge=0):
        trans = ax.get_yaxis_transform()
        ax.plot([-0.015, 0], [y_value, y_value], color=axis_color, linewidth=0.8, transform=trans, clip_on=False)
        ax.text(-0.02, y_value + vertical_nudge, label, transform=trans, ha='right', va='center', fontsize=9, color=text_color)

    add_manual_y_tick(y2_start, r'$v(S_2)$', vertical_nudge=-0.012)
    add_manual_y_tick(y2_end, r'$v(S_2+1)$', vertical_nudge=0.008) 
    add_manual_y_tick(y3_start, r'$v(S_3)$', vertical_nudge=-0.008)
    add_manual_y_tick(y3_end, r'$v(S_3+1)$', vertical_nudge=0.012)

    ax.set_title("Rendimenti decrescenti nelle funzioni submodulari", fontsize=15, pad=30, color='#252525')
    ax.set_ylabel(r"Utilità totale accumulata $v(S)$", fontsize=12, labelpad=20, color='#252525')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(axis_color)
    ax.spines['bottom'].set_color(axis_color)
    ax.set_ylim(0, 1.1) 
    ax.set_xlim(0, x_final)
    plt.subplots_adjust(bottom=0.25, left=0.15)
    
    output_filename = "../docs/Stesura/Immagini/figura_2_6_rendimenti_decrescenti_submodularita.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    #plt.show()
    print(f"Grafico salvato in questa cartella: {output_filename}")

if __name__ == "__main__":
    generate_diminishing_returns_submodularity_plot()
