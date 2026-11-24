#include <Servo.h>

#define TRIG 9
#define ECHO 10
#define SERVO_PIN 6
#define LED_ROJO 4
#define LED_VERDE 5

Servo barrera;

const int DISTANCIA_ENTRADA = 5;  // cm
const int DISTANCIA_LIBRE = 7;   // cm
const int ANGULO_CERRADO = 0;
const int ANGULO_ABIERTO = 90;
const unsigned long TIEMPO_PASO = 1800;

bool ocupado = false;
bool barreraAbierta = false;
bool modoAutomatico = true;
bool esperandoPaso = false;

unsigned long tiempoLibre = 0;
unsigned long ultimoEnvio = 0;
unsigned long ultimaMedicion = 0;
float distancia = 999;

float medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  unsigned long duracion = pulseIn(ECHO, HIGH, 30000UL);
  if (duracion == 0) return 999;
  return duracion * 0.0343f / 2.0f;
}

void abrirBarrera() {
  barrera.write(ANGULO_ABIERTO);
  barreraAbierta = true;
}

void cerrarBarrera() {
  barrera.write(ANGULO_CERRADO);
  barreraAbierta = false;
  esperandoPaso = false;
  tiempoLibre = 0;
}

void actualizarLED() {
  // HW-477 bicolor de cátodo común: R y G se activan en HIGH.
  digitalWrite(LED_ROJO, ocupado ? HIGH : LOW);
  digitalWrite(LED_VERDE, ocupado ? LOW : HIGH);
}

void procesarComandos() {
  static String comando = "";

  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      comando.trim();

      if (comando == "OPEN") {
        modoAutomatico = false;
        abrirBarrera();
      } else if (comando == "CLOSE") {
        modoAutomatico = false;
        cerrarBarrera();
      } else if (comando == "AUTO") {
        modoAutomatico = true;
      } else if (comando == "EXIT") {
        // Usar solo después de confirmar que el vehículo salió.
        ocupado = false;
        modoAutomatico = true;
        cerrarBarrera();
      }

      comando = "";
    } else if (c != '\r' && comando.length() < 20) {
      comando += c;
    }
  }
}

void funcionamientoAutomatico() {
  if (!modoAutomatico || ocupado) return;

  if (!barreraAbierta && distancia <= DISTANCIA_ENTRADA) {
    abrirBarrera();
    esperandoPaso = true;
    tiempoLibre = 0;
  }

  if (esperandoPaso && barreraAbierta) {
    if (distancia > DISTANCIA_LIBRE) {
      if (tiempoLibre == 0) tiempoLibre = millis();

      if (millis() - tiempoLibre >= TIEMPO_PASO) {
        ocupado = true;
        cerrarBarrera();
      }
    } else {
      tiempoLibre = 0;
    }
  }
}

void enviarEstado() {
  if (millis() - ultimoEnvio >= 500) {
    ultimoEnvio = millis();

    Serial.print("STATUS,");
    Serial.print(distancia, 1);
    Serial.print(",");
    Serial.print(ocupado ? 1 : 0);
    Serial.print(",");
    Serial.print(barreraAbierta ? 1 : 0);
    Serial.print(",");
    Serial.println(modoAutomatico ? 1 : 0);
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);

  digitalWrite(TRIG, LOW);

  barrera.attach(SERVO_PIN);
  cerrarBarrera();
  actualizarLED();
}

void loop() {
  procesarComandos();

  if (millis() - ultimaMedicion >= 100) {
    ultimaMedicion = millis();
    distancia = medirDistancia();
  }

  funcionamientoAutomatico();
  actualizarLED();
  enviarEstado();
}
