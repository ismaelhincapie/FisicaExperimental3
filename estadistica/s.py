import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson

# Configuración de estilo básico para los gráficos
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 11

# Crear carpeta para guardar las gráficas si no existe
output_dir = 'graficas_geiger'
os.makedirs(output_dir, exist_ok=True)

# Numeral 1: Carga de archivo y preparación de datos
# Descripción del montaje:
# Se utilizó el detector Geiger-Müller en línea (https://luramire.github.io/GeigerCounter.io/)
# para medir la radiación ambiental en intervalos de 10 segundos. Se mantuvo la pestaña
# activa durante la prueba para asegurar la toma continua de datos.

file_name = 'Geiger_Accumulated_Data_2026-10-21.xlsx'

def find_file(target_name):
    if os.path.exists(target_name):
        return target_name
    drive_path = '/content/drive'
    if os.path.exists(drive_path):
        matches = glob.glob(os.path.join(drive_path, '**', target_name), recursive=True)
        if matches:
            return matches[0]
    return None

resolved_path = find_file(file_name)

if resolved_path:
    df = pd.read_excel(resolved_path)
else:
    try:
        from google.colab import files
        uploaded = files.upload()
        if uploaded:
            file_name = list(uploaded.keys())[0]
            df = pd.read_excel(file_name)
        else:
            raise FileNotFoundError("No se seleccionó ningún archivo.")
    except Exception as e:
        raise FileNotFoundError(f"No se pudo encontrar ni subir el archivo '{file_name}'.") from e

# Obtenemos las cuentas por intervalo restando los acumulados
df['Counts_10s'] = df['Accumulated_Counts'].diff()
df.loc[0, 'Counts_10s'] = df.loc[0, 'Accumulated_Counts']
df['Counts_10s'] = df['Counts_10s'].astype(int)

exp_counts = df['Counts_10s'].values

# Numeral 2: Promedio de cuentas en 10 segundos
lambda_exp = np.mean(exp_counts)
n_samples = len(exp_counts)

print("Numeral 1 y 2:")
print(f"Total de datos: {n_samples}")
print(f"Promedio de cuentas en 10 segundos (λ): {lambda_exp:.4f}")

# Numeral 3: Histograma experimental
max_val_exp = exp_counts.max()
bins_exp = np.arange(-0.5, max_val_exp + 1.5, 1)

plt.figure(figsize=(10, 5))
plt.hist(exp_counts, bins=bins_exp, density=True, alpha=0.75, color='#1f77b4', edgecolor='black')
plt.axvline(lambda_exp, color='red', linestyle='--', linewidth=2, label=f'Media ({lambda_exp:.2f})')
plt.title('Numeral 3: Histograma de Datos Experimentales')
plt.xlabel('Cuentas en 10s')
plt.ylabel('Frecuencia Relativa')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'numeral_3_histograma_exp.png'), dpi=300)
plt.show()

# Numeral 4: Simulación de datos con distribución de Poisson
np.random.seed(42)
sim_counts = np.random.poisson(lam=lambda_exp, size=n_samples)

# Numeral 5: Gráficas de datos reales vs simulados
max_val = max(exp_counts.max(), sim_counts.max())
bins = np.arange(-0.5, max_val + 1.5, 1)

fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharex=True, sharey=True)

axes[0].hist(exp_counts, bins=bins, density=True, alpha=0.8, color='#1f77b4', edgecolor='black', rwidth=0.85)
axes[0].axvline(lambda_exp, color='red', linestyle='--', linewidth=2, label=f'Media Exp ({lambda_exp:.2f})')
x_teorico = np.arange(0, max_val + 1)
pmf_teorica = poisson.pmf(x_teorico, lambda_exp)
axes[0].plot(x_teorico, pmf_teorica, 'ro-', label='Teoría', linewidth=1.5, markersize=5)
axes[0].set_title('Datos Reales')
axes[0].set_xlabel('Cuentas en 10s')
axes[0].set_ylabel('Frecuencia Relativa')
axes[0].legend()
axes[0].grid(True, linestyle=':', alpha=0.6)

axes[1].hist(sim_counts, bins=bins, density=True, alpha=0.8, color='#ff7f0e', edgecolor='black', rwidth=0.85)
axes[1].axvline(lambda_exp, color='red', linestyle='--', linewidth=2, label=f'Media Sim ({np.mean(sim_counts):.2f})')
axes[1].plot(x_teorico, pmf_teorica, 'ro-', label='Teoría', linewidth=1.5, markersize=5)
axes[1].set_title('Datos Simulados')
axes[1].set_xlabel('Cuentas en 10s')
axes[1].legend()
axes[1].grid(True, linestyle=':', alpha=0.6)

plt.suptitle('Numeral 5: Comparación Lado a Lado')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'numeral_5_comparacion_lado_a_lado.png'), dpi=300)
plt.show()

# Barras agrupadas por cada valor de cuenta
valores_posibles = np.arange(0, max_val + 1)
frec_exp = np.array([np.sum(exp_counts == v) for v in valores_posibles]) / n_samples
frec_sim = np.array([np.sum(sim_counts == v) for v in valores_posibles]) / n_samples

width = 0.35

plt.figure(figsize=(14, 6))
plt.bar(valores_posibles - width/2, frec_exp, width, label='Experimental', color='#1f77b4', edgecolor='black', alpha=0.85)
plt.bar(valores_posibles + width/2, frec_sim, width, label='Simulado', color='#ff7f0e', edgecolor='black', alpha=0.85)
plt.plot(valores_posibles, pmf_teorica, 'ro-', label='Teórica Poisson', linewidth=2, markersize=6)
plt.title('Numeral 5: Comparación por Barras Agrupadas')
plt.xlabel('Cuentas en 10s')
plt.ylabel('Frecuencia Relativa')
plt.xticks(valores_posibles)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'numeral_5_barras_agrupadas.png'), dpi=300)
plt.show()

# Corrección en el Numeral 8 y formateo de probabilidad
lambda_1min = lambda_exp * 6
prob_1min = (poisson.cdf(20, lambda_1min) - poisson.cdf(9, lambda_1min)) * 100
esperadas_10min = lambda_exp * 60

# Numeral 6: Gráfico de residuos
residuos = sim_counts - exp_counts

plt.figure(figsize=(14, 4.5))
plt.plot(residuos, marker='o', linestyle='-', color='purple', alpha=0.6, markersize=4, linewidth=0.8)
plt.axhline(0, color='red', linestyle='--', linewidth=1.5, label='Línea Cero')
plt.title('Numeral 6: Gráfico de Residuos (Simulados - Reales)')
plt.xlabel('Índice de Medición')
plt.ylabel('Diferencia de Cuentas')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'numeral_6_residuos.png'), dpi=300)
plt.show()

# Numeral 7: Distribución acumulativa (CDF)
x_exp, counts_exp = np.unique(exp_counts, return_counts=True)
cdf_exp = np.cumsum(counts_exp) / n_samples

x_sim, counts_sim = np.unique(sim_counts, return_counts=True)
cdf_sim = np.cumsum(counts_sim) / n_samples

plt.figure(figsize=(12, 5.5))
plt.step(x_exp, cdf_exp, where='post', label='CDF Experimental', color='#1f77b4', linewidth=2.5)
plt.step(x_sim, cdf_sim, where='post', label='CDF Simulada', color='#ff7f0e', linestyle='--', linewidth=2.5)
plt.title('Numeral 7: Función de Distribución Acumulativa (CDF)')
plt.xlabel('Cuentas en 10s')
plt.ylabel('Probabilidad Acumulada')
plt.xticks(np.arange(0, max_val + 1))
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'numeral_7_cdf.png'), dpi=300)
plt.show()