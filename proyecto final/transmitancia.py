import serial
import time

# Sustituye por tu puerto (ej: 'COM3' en Windows o '/dev/ttyUSB0' / '/dev/ttyACM0' en Linux)
puerto = '/dev/ttyACM0' 
baudios = 9600

try:
    # Conectar con el Arduino
    arduino = serial.Serial(puerto, baudios, timeout=1)
    time.sleep(2) # Espera breve mientras el Arduino reinicia la conexión
    print("Conexión serial establecida.")

    def set_espectro_led(r, g, b):
        """Envía los tres valores de intensidad al Arduino"""
        comando = f"{r},{g},{b}\n"
        arduino.write(comando.encode('utf-8'))
        print(f"Espectro enviado a Arduino -> R:{r} G:{g} B:{b}")

    # Ejemplo 1: Simular luz blanca directa (Sol)
    set_espectro_led(255, 230, 200)
    time.sleep(5)

    # Ejemplo 2: Simular luz transmitida por hoja (Predominio verde, bajo rojo/azul)
    #set_espectro_led(40, 220, 30)
    #time.sleep(5)

    # Cerrar conexión al terminar
    arduino.close()

except Exception as e:
    print(f"Error de conexión: {e}")