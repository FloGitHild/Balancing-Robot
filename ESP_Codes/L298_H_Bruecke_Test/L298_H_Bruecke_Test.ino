// Gleichstrommotor 1
int GSM1 = 12;
int in1 = 14;
int in2 = 27;
// Gleichstrommotor 2
int GSM2 = 13;
int in3 = 25;
int in4 = 26;
void setup() {
  pinMode(GSM1, OUTPUT);
  pinMode(GSM2, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}


void loop() {
  tone(GSM1, 10);
  tone(GSM2, 10);
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
}