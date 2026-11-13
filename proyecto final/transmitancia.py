import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# ==============================================================================
# 1. CONFIGURACIÓN DE ARCHIVOS (DETECCIÓN AUTOMÁTICA)
# ==============================================================================
carpeta_datos = "/home/ismael/Projects/UDEA/experimental3/FisicaExperimental3/proyecto final/Transmitancia_follaje"
carpeta_salida = os.path.dirname(os.path.abspath(__file__))

archivos_en_carpeta = sorted(os.listdir(carpeta_datos))

# Buscar automáticamente el archivo de referencia (el que no tenga nombre de árbol)
especies = ("guamo", "guayabo", "nacedero", "mango")
candidatos_ref = [
    f for f in archivos_en_carpeta
    if os.path.isfile(os.path.join(carpeta_datos, f))
    and not any(esp in f.lower() for esp in especies)
]

if not candidatos_ref:
    raise FileNotFoundError("No se detectó ningún archivo de referencia en la carpeta.")

archivo_referencia = os.path.join(carpeta_datos, candidatos_ref[0])

# Buscar automáticamente los 3 archivos de cada especie ordenados
archivos_arboles = {}
for arbol in ["Guamo", "Guayabo", "Nacedero", "Mango"]:
    coincidencias = sorted([
        os.path.join(carpeta_datos, f)
        for f in archivos_en_carpeta
        if arbol.lower() in f.lower()
    ])
    if not coincidencias:
        raise FileNotFoundError(f"No se encontraron archivos para {arbol}.")
    archivos_arboles[arbol] = coincidencias

# Rango de longitud de onda de interés (Visible + NIR: 400 nm a 850 nm)
WL_MIN = 400.0
WL_MAX = 850.0

# ==============================================================================
# 2. FUNCIÓN PARA LEER ARCHIVOS OOIBase32
# ==============================================================================
def leer_ooibase32(ruta_archivo):
    tiempo_integracion = 1.0
    longitudes_onda = []
    intensidades = []
    leyendo_datos = False

    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("Integration Time (msec):"):
                tiempo_integracion = float(linea.split(":")[1].strip())

            if ">>>>>Begin Spectral Data<<<<<" in linea:
                leyendo_datos = True
                continue
            if ">>>>>End Spectral Data<<<<<" in linea:
                break

            if leyendo_datos:
                partes = linea.split()
                if len(partes) >= 2:
                    wl = float(partes[0])
                    val = float(partes[1])
                    longitudes_onda.append(wl)
                    intensidades.append(val / tiempo_integracion)

    return np.array(longitudes_onda), np.array(intensidades), tiempo_integracion

# ==============================================================================
# 3. PROCESAMIENTO DE DATOS Y CÁLCULO DE TRANSMITANCIA
# ==============================================================================
wl_ref, int_ref, t_ref = leer_ooibase32(archivo_referencia)

# Evitar zonas donde la lámpara casi no tiene señal para no amplificar ruido
umbral_luz = np.max(int_ref) * 0.02
mascara = (wl_ref >= WL_MIN) & (wl_ref <= WL_MAX) & (int_ref > umbral_luz)
wl = wl_ref[mascara]
I0 = int_ref[mascara]

T_referencia = np.ones_like(I0) * 100.0

resultados_arboles = {}
tabla_exportar = {"Longitud_Onda_nm": wl, "Referencia_%": T_referencia}
resumen_estadistico = []
maximo_global_hojas = 0.0

for arbol, lista_rutas in archivos_arboles.items():
    transmitancias_muestras = []

    for i, ruta in enumerate(lista_rutas, start=1):
        wl_m, int_m, t_m = leer_ooibase32(ruta)
        I_muestra = int_m[mascara]

        T_porcentaje = (I_muestra / I0) * 100.0
        transmitancias_muestras.append(T_porcentaje)

        max_actual = np.max(T_porcentaje)
        if max_actual > maximo_global_hojas:
            maximo_global_hojas = max_actual

        col_nombre = f"{arbol}_Muestra_{i}_%"
        tabla_exportar[col_nombre] = T_porcentaje

        resumen_estadistico.append({
            "Especie": arbol,
            "Muestra": f"Muestra {i}",
            "T_Promedio_%": np.mean(T_porcentaje),
            "T_Max_%": max_actual,
            "WL_Max_nm": wl[np.argmax(T_porcentaje)],
            "T_550nm_(Verde)_%": np.interp(550.0, wl, T_porcentaje),
            "T_680nm_(Clorofila)_%": np.interp(680.0, wl, T_porcentaje),
            "T_750nm_(NIR)_%": np.interp(750.0, wl, T_porcentaje)
        })

    matriz_T = np.array(transmitancias_muestras)
    T_prom = np.mean(matriz_T, axis=0)
    T_std = np.std(matriz_T, axis=0)

    resultados_arboles[arbol] = {
        "individuales": transmitancias_muestras,
        "promedio": T_prom,
        "std": T_std
    }

    tabla_exportar[f"{arbol}_PROMEDIO_%"] = T_prom

    resumen_estadistico.append({
        "Especie": arbol,
        "Muestra": "PROMEDIO",
        "T_Promedio_%": np.mean(T_prom),
        "T_Max_%": np.max(T_prom),
        "WL_Max_nm": wl[np.argmax(T_prom)],
        "T_550nm_(Verde)_%": np.interp(550.0, wl, T_prom),
        "T_680nm_(Clorofila)_%": np.interp(680.0, wl, T_prom),
        "T_750nm_(NIR)_%": np.interp(750.0, wl, T_prom)
    })

# Límite superior dinámico con margen del 20% para que las curvas llenen la gráfica
limite_y_zoom = maximo_global_hojas * 1.20

# ==============================================================================
# 4. EXPORTACIÓN DE VALORES DE TRANSMITANCIA
# ==============================================================================
df_espectros = pd.DataFrame(tabla_exportar)
df_resumen = pd.DataFrame(resumen_estadistico)

df_espectros.to_csv(os.path.join(carpeta_salida, "transmitancia_espectros_completos.csv"), index=False)
df_resumen.to_csv(os.path.join(carpeta_salida, "resumen_valores_transmitancia.csv"), index=False)

print("=== RESUMEN DE VALORES DE TRANSMITANCIA (%) ===")
print(df_resumen.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

# ==============================================================================
# 5. GRÁFICAS AMPLIADAS
# ==============================================================================
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# --- FIGURA 1: 4 Subgráficas ampliadas por especie ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
axes = axes.flatten()
colores_arboles = {"Guamo": "#1f77b4", "Guayabo": "#2ca02c", "Nacedero": "#ff7f0e", "Mango": "#d62728"}

for idx, (arbol, datos) in enumerate(resultados_arboles.items()):
    ax = axes[idx]
    color = colores_arboles[arbol]

    for i, T_ind in enumerate(datos["individuales"], start=1):
        ax.plot(wl, T_ind, linestyle="--", alpha=0.65, linewidth=1.3, label=f"Hoja {i}")

    ax.plot(wl, datos["promedio"], color=color, linewidth=2.8, label=f"Promedio {arbol}")

    ax.set_title(f"Transmitancia Espectral: {arbol} (Normalizada a Referencia)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Transmitancia (%)")
    ax.set_ylim(0, limite_y_zoom)
    ax.legend(loc="upper left", fontsize=9)

axes[2].set_xlabel("Longitud de onda (nm)")
axes[3].set_xlabel("Longitud de onda (nm)")
plt.tight_layout()
plt.savefig(os.path.join(carpeta_salida, "1_transmitancia_por_arbol_ampliada.png"), dpi=300)
plt.show()

# --- FIGURA 2: Comparación Ampliada de los 4 Promedios + Referencia (Doble Eje Y) ---
fig, ax1 = plt.subplots(figsize=(12, 6))

lineas = []
for arbol, datos in resultados_arboles.items():
    color = colores_arboles[arbol]
    prom = datos["promedio"]
    std = datos["std"]

    l, = ax1.plot(wl, prom, color=color, linewidth=2.8, label=f"Promedio {arbol}")
    ax1.fill_between(wl, np.maximum(0, prom - std), prom + std, color=color, alpha=0.15)
    lineas.append(l)

ax1.set_title("Comparación de Transmitancia Promedio entre Especies vs Referencia", fontsize=14, fontweight="bold")
ax1.set_xlabel("Longitud de onda (nm)", fontsize=12)
ax1.set_ylabel("Transmitancia Follaje (%)", fontsize=12)
ax1.set_xlim(WL_MIN, WL_MAX)
ax1.set_ylim(0, limite_y_zoom)

# Segundo eje Y a la derecha para mostrar la Referencia al 100% sin aplastar las hojas
ax2 = ax1.twinx()
l_ref, = ax2.plot(wl, T_referencia, color="black", linestyle="--", linewidth=2, label="Referencia (100%)")
ax2.set_ylabel("Transmitancia Referencia (%)", fontsize=12, color="black")
ax2.set_ylim(0, 110)
ax2.grid(False)

# Leyenda unificada con los 4 árboles y la referencia
lineas.append(l_ref)
etiquetas = [l.get_label() for l in lineas]
ax1.legend(lineas, etiquetas, loc="upper left", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(carpeta_salida, "2_comparacion_4_promedios_vs_referencia.png"), dpi=300)
plt.show()