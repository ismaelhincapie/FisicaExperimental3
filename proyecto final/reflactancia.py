import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import csv
import warnings

# CONFIGURACIÓN
directorio = '/home/ismael/Projects/UDEA/experimental3/FisicaExperimental3/proyecto final/TyR Follaje'
ESPECIES = ['Mango', 'Guayabo', 'Nacedero', 'Guamo']
COLORES = {'Mango': '#2ca02c', 'Guayabo': '#ff7f0e',
           'Nacedero': '#9467bd', 'Guamo': '#1f77b4'}
WL_MIN, WL_MAX = 400, 875          # rango útil del espectrómetro (según la referencia)
R_SPECTRALON = 0.99                # reflectancia real aprox. del Spectralon (~99%)


def cargar_archivo_scope(ruta):
    """Lee un .Master.Scope omitiendo el encabezado de metadatos."""
    wl, inten = [], []
    leyendo = False
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            s = line.strip()
            if '>>>>>Begin Spectral Data<<<<<' in s:
                leyendo = True
                continue
            if '>>>>>End Spectral Data<<<<<' in s:
                break
            if leyendo and s:
                p = s.split('\t')
                if len(p) >= 2:
                    try:
                        wl.append(float(p[0]))
                        inten.append(float(p[1]))
                    except ValueError:
                        continue
    return np.array(wl), np.array(inten)


# 1. CARGAR REFERENCIA
ref_path = os.path.join(directorio, 'referencia_spectralon.Master.Scope')
if not os.path.exists(ref_path):
    cand = glob.glob(os.path.join(directorio, '*referencia*.Scope'))
    if not cand:
        raise FileNotFoundError("No se encontró el archivo de referencia de Spectralon.")
    ref_path = cand[0]

wl_ref, I_ref = cargar_archivo_scope(ref_path)
mask = (wl_ref >= WL_MIN) & (wl_ref <= WL_MAX)
wl = wl_ref[mask]
I_ref_r = I_ref[mask]

# 2. CARGAR MUESTRAS POR ESPECIE
archivos = [f for f in glob.glob(os.path.join(directorio, '*.Master.Scope'))
            if 'referencia' not in os.path.basename(f).lower()]

datos = {e: [] for e in ESPECIES}
for ruta in sorted(archivos):
    nombre = os.path.basename(ruta).replace('.Master.Scope', '')
    especie = nombre.split('_')[0]
    if especie not in datos:
        continue
    w, I = cargar_archivo_scope(ruta)
    # Por seguridad: llevar a la misma malla de longitudes de onda de la referencia
    I = np.interp(wl, w, I)
    datos[especie].append((nombre, I))

ESPECIES = [e for e in ESPECIES if datos[e]]

# 3. GRÁFICA 1: INTENSIDAD CRUDA
fig1, axs = plt.subplots(2, 2, figsize=(13, 8), sharex=True, sharey=True,
                         layout='constrained')
ymax = I_ref_r.max()

for ax, esp in zip(axs.ravel(), ESPECIES):
    ax.plot(wl, I_ref_r, 'k--', lw=2, label='Referencia')
    for nombre, I in datos[esp]:
        ax.plot(wl, I, lw=1.3, alpha=0.85, label=nombre)
    ax.set_title(f'{esp} (n = {len(datos[esp])})', fontsize=12, fontweight='bold')
    ax.set_ylim(0, ymax * 1.35)                 # espacio libre arriba para la leyenda
    ax.grid(True, ls='--', alpha=0.4)
    ax.legend(loc='upper center', ncol=3, fontsize=8, frameon=False)
    ax.tick_params(labelleft=True, labelbottom=True)   # mostrar números en todos los paneles

for ax in axs[1]:
    ax.set_xlabel('Longitud de onda [nm]')
for ax in axs[:, 0]:
    ax.set_ylabel('Intensidad [cuentas]')

fig1.suptitle('Espectros crudos: muestras foliares vs. referencia', fontsize=14)

# 4. REFLECTANCIA  R(λ) = I_hoja / I_ref * R_spectralon
#    (si tienes archivo de oscuro, resta I_dark a ambos antes)
UMBRAL = 0.05 * I_ref_r.max()          # evita dividir donde la referencia es casi cero
valido = I_ref_r > UMBRAL

def reflectancia(I):
    R = np.full_like(I, np.nan, dtype=float)
    R[valido] = I[valido] / I_ref_r[valido] * R_SPECTRALON * 100.0   # en %
    return R

R_esp = {}   # R_esp[especie] = matriz (n_muestras, n_wl)
for esp in ESPECIES:
    R_esp[esp] = np.array([reflectancia(I) for _, I in datos[esp]])

# Gráfica 2: promedio ± desviación estándar, las 4 especies juntas
fig2, ax = plt.subplots(figsize=(11, 6))
for esp in ESPECIES:
    m = np.nanmean(R_esp[esp], axis=0)
    s = np.nanstd(R_esp[esp], axis=0)
    ax.plot(wl, m, color=COLORES[esp], lw=2.4, label=f'{esp} (n={len(datos[esp])})')
    ax.fill_between(wl, m - s, m + s, color=COLORES[esp], alpha=0.2)
ax.set_xlabel('Longitud de onda [nm]')
ax.set_ylabel('Reflectancia [%]')
ax.set_title('Reflectancia foliar promedio ± 1σ por especie')
ax.set_xlim(450, 850)
ax.grid(True, ls='--', alpha=0.5)
ax.legend()
fig2.tight_layout()

# 5. TRANSMITANCIA nos faltan datos de transmitancia, por lo que no podemos calcularla directamente.
# Lo que sí se puede es A + T = 1 - R  (absorbancia + transmitancia).
# Aquí solo mostramos 1 - R =( A + T) como cota:
fig3, ax = plt.subplots(figsize=(11, 6))
for esp in ESPECIES:
    m = np.nanmean(R_esp[esp], axis=0)
    ax.plot(wl, 100 - m, color=COLORES[esp], lw=2.4, label=esp)
ax.set_xlabel('Longitud de onda [nm]')
ax.set_ylabel('A + T = 100 − R  [%]')
ax.set_title('Absorbancia + Transmitancia (no separadas)')
ax.set_xlim(450, 850)
ax.grid(True, ls='--', alpha=0.5)
ax.legend()
fig3.tight_layout()

# GRÁFICA 4: COMPARACIÓN DE LAS 4 ESPECIES (solo promedios)

fig4, (axA, axB) = plt.subplots(1, 2, figsize=(14, 6), layout='constrained')

# Izquierda: intensidad cruda promedio + referencia
axA.plot(wl, I_ref_r, 'k--', lw=2, label='Referencia')
for esp in ESPECIES:
    I_prom = np.mean([I for _, I in datos[esp]], axis=0)
    axA.plot(wl, I_prom, color=COLORES[esp], lw=2.4, label=esp)
axA.set_title('Intensidad promedio por especie', fontweight='bold')
axA.set_xlabel('Longitud de onda [nm]')
axA.set_ylabel('Intensidad [cuentas]')
axA.set_ylim(0, I_ref_r.max() * 1.15)
axA.grid(True, ls='--', alpha=0.4)
axA.legend(loc='upper right')

# Derecha: reflectancia promedio
for esp in ESPECIES:
    R_prom = np.nanmean(R_esp[esp], axis=0)
    axB.plot(wl, R_prom, color=COLORES[esp], lw=2.4, label=esp)
axB.set_title('Reflectancia promedio por especie', fontweight='bold')
axB.set_xlabel('Longitud de onda [nm]')
axB.set_ylabel('Reflectancia [%]')
axB.set_xlim(450, 850)
axB.grid(True, ls='--', alpha=0.4)
axB.legend(loc='upper left')

fig4.suptitle('Comparación entre especies', fontsize=14)

warnings.filterwarnings('ignore', category=RuntimeWarning)
botones = []
for fig in (fig1, fig2, fig3, fig4):
    ax_btn = fig.add_axes([0.87, 0.93, 0.12, 0.05])
    btn = Button(ax_btn, 'Cerrar', color='#ff9999', hovercolor='#ff3333')
    btn.on_clicked(lambda event, f=fig: plt.close(f))
    botones.append(btn)

plt.show()

# 6. VALOR DE R POR HOJA 

BANDAS = {                      # nombre: (nm_min, nm_max)
    'R_prom_450-850': (450, 850),
    'R_verde_530-570': (530, 570),
    'R_rojo_640-680': (640, 680),
    'R_NIR_750-850': (750, 850),
}

def r_banda(R, a, b):
    m = (wl >= a) & (wl <= b)
    return np.nanmean(R[m])

filas = []
for esp in ESPECIES:
    for (nombre, _), R in zip(datos[esp], R_esp[esp]):
        fila = {'especie': esp, 'hoja': nombre}
        for k, (a, b) in BANDAS.items():
            fila[k] = round(r_banda(R, a, b), 2)
        filas.append(fila)

# Imprimir tabla
cols = ['especie', 'hoja'] + list(BANDAS)
print('\n' + ' | '.join(f'{c:>16}' for c in cols))
print('-' * (19 * len(cols)))
for f in filas:
    print(' | '.join(f'{str(f[c]):>16}' for c in cols))

# Promedio por especie
print('\nPromedio por especie (%R):')
for esp in ESPECIES:
    sub = [f for f in filas if f['especie'] == esp]
    vals = {k: np.mean([f[k] for f in sub]) for k in BANDAS}
    print(f'{esp:>10}: ' + ', '.join(f'{k}={v:.2f}' for k, v in vals.items()))

# Guardar CSV
ruta_csv = os.path.join(directorio, 'reflectancia_por_hoja.csv')
with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(filas)
print(f'\nGuardado en: {ruta_csv}')