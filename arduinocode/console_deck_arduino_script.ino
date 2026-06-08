const int numPulsanti = 9;
const int pinPulsanti[numPulsanti] = {2, 3, 4, 5, 6, 7, 8, 9, 10};
bool statoPrecedente[numPulsanti] = {HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numPulsanti; i++) {
    pinMode(pinPulsanti[i], INPUT_PULLUP);
  }
}

void loop() {
  for (int i = 0; i < numPulsanti; i++) {
    int statoAttuale = digitalRead(pinPulsanti[i]);

    // Rileva il fronte di discesa (quando il pulsante viene premuto)
    if (statoPrecedente[i] == HIGH && statoAttuale == LOW) {
      Serial.print("BUTTON_");
      Serial.println(i + 1);  // Stampa BUTTON_1, BUTTON_2, ...
    }

    statoPrecedente[i] = statoAttuale;
  }

  delay(20);  // debounce software semplice
}
