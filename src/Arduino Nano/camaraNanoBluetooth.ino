// Nano 33 BLE / BLE Sense — BLE -> UART (UNO)
// Recibe 'A'/'C' por característica BLE y los reenvía por Serial1 (D1->UNO D10).

#include <ArduinoBLE.h>

BLEService cmdService("12345678-1234-5678-1234-56789abcdef0");
BLEByteCharacteristic cmdChar(
  "12345678-1234-5678-1234-56789abcdef1",
  BLEWriteWithoutResponse | BLEWrite
);

static void failBlink() {
  pinMode(LED_BUILTIN, OUTPUT);
  for (;;) { digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); delay(150); }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}  // opcional: capturar primeros logs

  Serial1.begin(9600);  // UART hacia el UNO (debe coincidir con el UNO)

  if (!BLE.begin()) failBlink();

  BLE.setLocalName("NanoDoorBLE");
  BLE.setDeviceName("NanoDoorBLE");
  BLE.setAdvertisedService(cmdService);
  cmdService.addCharacteristic(cmdChar);
  BLE.addService(cmdService);
  cmdChar.writeValue((byte)0);
  BLE.advertise();

  Serial.println("OK: Advertising NanoDoorBLE");
}

void loop() {
  BLE.poll();  // no bloqueante

  // Heartbeat 1 Hz
  static unsigned long last = 0;
  if (millis() - last > 500) {
    last = millis();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

  // Log de cambio de estado de conexión
  static bool wasConnected = false;
  bool connected = BLE.connected();
  if (connected != wasConnected) {
    wasConnected = connected;
    Serial.println(connected ? "BLE connected" : "BLE disconnected");
  }

  // Procesar comandos escritos en la característica
  if (cmdChar.written()) {
    uint8_t v = cmdChar.value();   // 1 byte
    // Acepta 'A'/'C' (mayúsc/minúsc)
    if (v=='A' || v=='a' || v=='C' || v=='c') {
      char c = (v=='a') ? 'A' : (v=='c') ? 'C' : (char)v;
      Serial1.write(c);            // reenvía al UNO
      Serial.print("FWD->UNO: "); Serial.write(c); Serial.println();
    } else {
      Serial.print("Ignorado: 0x"); Serial.println(v, HEX);
    }
  }
}
