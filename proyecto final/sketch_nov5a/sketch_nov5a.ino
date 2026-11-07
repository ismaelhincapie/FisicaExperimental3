const int PIN_ROJO  = 9;
const int PIN_VERDE = 10;
const int PIN_AZUL  = 11;

// Define si tu LED es de Ánodo Común (COM a 5V)
const bool ANODO_COMUN = true;

void setup() {
  pinMode(PIN_ROJO, OUTPUT);
  pinMode(PIN_VERDE, OUTPUT);
  pinMode(PIN_AZUL, OUTPUT);

  Serial.begin(9600);
  
  // Enciende el LED con la luz solar simulada al arrancar
  actualizarLEDs(255, 230, 200);
  Serial.println("Simulación solar activa. El LED debería estar encendido.");
}

void loop() {
  // Se mantiene encendido de forma continua
}

void actualizarLEDs(int r, int g, int b) {
  if (ANODO_COMUN) {
    analogWrite(PIN_ROJO, 255 - r);
    analogWrite(PIN_VERDE, 255 - g);
    analogWrite(PIN_AZUL, 255 - b);
  } else {
    analogWrite(PIN_ROJO, r);
    analogWrite(PIN_VERDE, g);
    analogWrite(PIN_AZUL, b);
  }
}