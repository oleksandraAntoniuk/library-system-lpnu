#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const int trigPin = 2;
const int echoPin = 3;

const int buttonPin = 4;
const int greenLED = 5;
const int redLED = 6;
const int buzzer = 7;

long duration;
int distance;

bool alertActive = false;

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(buttonPin, INPUT_PULLUP);

  pinMode(greenLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(buzzer, OUTPUT);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("System ready");

  Serial.begin(9600);
}

// короткий сигнал
void beep(int delayTime) {
  digitalWrite(buzzer, HIGH);
  delay(100);
  digitalWrite(buzzer, LOW);
  delay(delayTime);
}

void loop() {

  // вимірювання відстані
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;

  // якщо людина поруч
  if (distance > 0 && distance < 30) {
    digitalWrite(greenLED, HIGH);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("User detected");

    beep(1000);

  } else {
    digitalWrite(greenLED, LOW);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Waiting...");
  }

  // натискання кнопки
  if (digitalRead(buttonPin) == LOW) {
    alertActive = !alertActive;
    delay(300);
  }

  // виклик
  if (alertActive) {
    digitalWrite(redLED, HIGH);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Call librarian");

    lcd.setCursor(0, 1);
    lcd.print("Please wait...");

    beep(200);
    beep(200);
    beep(500);

  } else {
    digitalWrite(redLED, LOW);
  }

  delay(300);
}