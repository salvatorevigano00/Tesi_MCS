import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 1, 100)
y_perfect = x
y_lorenz = x**3

plt.figure(figsize=(8, 6))

plt.plot(x, y_perfect, linestyle='--', color='black', label='Perfetta equità')
plt.plot(x, y_lorenz, color='#d32f2f', linewidth=2, label='Curva di Lorenz')

plt.fill_between(x, y_perfect, y_lorenz, color='#e0e0e0', alpha=0.5, label='Area A (disuguaglianza)')
plt.fill_between(x, y_lorenz, 0, color='#ffcdd2', alpha=0.3, label='Area B')

plt.text(0.45, 0.35, 'Area A', fontsize=12, fontweight='bold')
plt.text(0.7, 0.15, 'Area B', fontsize=12, fontweight='bold')
plt.title('Curva di Lorenz e indice di Gini', fontsize=14)
plt.xlabel('Percentuale cumulativa utenti', fontsize=12)
plt.ylabel('Percentuale cumulativa budget', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim([0, 1])
plt.ylim([0, 1])

plt.savefig('../docs/Stesura/Immagini/figura_2_4_curva_lorenz_indice_gini.png', dpi=300)
#plt.show()