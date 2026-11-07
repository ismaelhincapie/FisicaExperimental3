import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def calcular_autocorrelacion(ruta_imagen):
    # 1. Cargar la imagen en escala de grises
    img = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: No se pudo cargar la imagen desde {ruta_imagen}")
        return

    # 2. Normalizar la intensidad (0 a 1)
    I = img.astype(float) / 255.0

    # 3. Calcular la iFFT2
    F_inv = np.fft.ifft2(I)
    F_inv_shift = np.fft.fftshift(F_inv)
    
    # Magnitud
    magnitud = np.abs(F_inv_shift)
    
    # Escala logarítmica para amplificar valores pequeños
    magnitud_log = np.log1p(magnitud)

    # 4. Graficar ajustando el contraste (vmax) para resaltar los puntos débiles
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    axes[0].imshow(img, cmap='gray')
    axes[0].set_title('Patrón de Difracción $I(x,y)$')
    axes[0].axis('off')

    # Ajustamos vmax al percentil 99.5 para que el pico central no "apague" el resto de la imagen
    vmax_val = np.percentile(magnitud_log, 99.8)
    
    im = axes[1].imshow(magnitud_log, cmap='inferno', vmin=0, vmax=vmax_val)
    axes[1].set_title(r'Autocorrelación 2D ($\mathcal{F}^{-1}\{I(x,y)\}$)')
    axes[1].axis('off')

    plt.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
    plt.tight_layout()

    nombre_archivo = os.path.basename(ruta_imagen)
    nombre_salida = f"resultado_{nombre_archivo}"
    
    plt.savefig(nombre_salida, dpi=300)
    print(f"¡Imagen guardada como: {nombre_salida}!")
    plt.show()

if __name__ == '__main__':
    ruta = '/home/ismael/Downloads/20261002_132849.jpg'
    calcular_autocorrelacion(ruta)