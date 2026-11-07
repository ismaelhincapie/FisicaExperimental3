import numpy as np
import matplotlib.pyplot as plt
import time

# Parámetros de la simulación gaussiana
angulos_sim = np.linspace(0, 30, 60)
theta0 = 15.0  # Centro del cono
sigma = 2.5    # Ancho del cono
I_max = 750    # Pico de intensidad
I_fondo = 80   # Luz ambiental

# Generación del perfil con un poco de ruido
intensidades_sim = I_fondo + I_max * np.exp(-((angulos_sim - theta0)**2) / (2 * sigma**2))
intensidades_sim += np.random.normal(0, 5, len(angulos_sim)) # Ruido experimental

# Graficado dinámico
plt.ion()
fig, ax = plt.subplots()
linea, = ax.plot([], [], 'r-o', label='Perfil del Cono de Luz')
ax.set_xlabel('Ángulo (grados)')
ax.set_ylabel('Intensidad (u.a.)')
ax.set_title('Perfil de Intensidad del Láser (Simulación Gaussiana)')
ax.grid(True)
ax.legend()

angulos_x = []
intensidades_y = []

print("Simulando envío de datos...")
for ang, intens in zip(angulos_sim, intensidades_sim):
    angulos_x.append(ang)
    intensidades_y.append(intens)

    linea.set_xdata(angulos_x)
    linea.set_ydata(intensidades_y)

    ax.relim()
    ax.autoscale_view()
    plt.draw()
    plt.pause(0.05)

plt.ioff()
plt.show()