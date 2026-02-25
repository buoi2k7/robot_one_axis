#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>

// ===== WIFI =====
const char *ssid = "link";
const char *password = "buoinha132/";

// 🖥️ IP máy tính chạy py
const char *udpAddress = "192.168.1.13"; // Thay bằng IP của máy bạn
const int udpPort = 4210;

// 🌐 IP tĩnh cho ESP32
IPAddress local_IP(192, 168, 1, 7);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);
IPAddress secondaryDNS(8, 8, 4, 4);

WiFiUDP udp;

// --- CẤU HÌNH CHÂN (PINOUT) CHO ESP32 ---
// LPT nhớ sửa lại các chân này cho đúng với board của ông nha
#define BRAKE_PIN 26  // Chân phanh
#define PWM_PIN 25    // Chân băm xung động cơ
#define DIR_PIN 27    // Chân chiều động cơ
#define BUZZER_PIN 14 // Chân còi

// Địa chỉ I2C MPU6050
#define MPU6050 0x68
#define ACCEL_CONFIG 0x1C
#define GYRO_CONFIG 0x1B
#define PWR_MGMT_1 0x6B

// Cấu hình PWM cho ESP32
const int PWM_FREQ = 20000; // 20kHz
// const int PWM_CHANNEL = 0;     // Kênh PWM 0
const int PWM_RES = 8; // Độ phân giải 8-bit (0-255)

// Các biến PID (đã fix cứng, bỏ phần Tuning)
float X1 = 167;      // P  (bắt đầu thấp, tăng dần qua Python app)
float X2 = 16.8;     // D  (tắt trước, thêm sau)
float X3 = 0.10;     // Motor brake (tắt trước)
float X4 = 1.0;      // I  (tắt trước)
float loop_time = 5; // 200Hz — nhanh gấp đôi!
float loop_time_py = 50;

// ===== MOTOR CONTROL CONFIG =====
const int PWM_CMD_MAX = 255;
const int PWM_CMD_STEP = 10; // Slew-rate limiter
int pwm_applied = 0;         // PWM thực tế đang áp dụng

float pitch = 0;
float roll = 0;
float yaw = 0;

int pwm_s = 0;
int32_t motor_speed;
long currentT, previousT_1 = 0;
long currentT_py, previousT_1_py = 0;

// Biến cảm biến
int16_t AcX, AcY, AcZ, GyZ;
float gyroZ, gyroZfilt;
#define accSens 0
#define gyroSens 1
#define Gyro_amount 0.996

// Offset từ calic.ino (lần 1: góc -0.23°, ổn định 0.131° - tốt nhất)
int16_t AcX_offset = -803;
int16_t AcY_offset = 62;
int16_t AcZ_offset = 0;
int16_t GyZ_offset = -6;
int32_t GyZ_offset_sum = 0;

float alpha = 1.0; // Tăng = phản ứng NHANH hơn (cũ: 0.70)
float robot_angle;
float Acc_angle;
bool vertical = false;
float error_sum = 0;      // Tích lũy lỗi cho Integral
float angle_offset = 2.5; // Serial đo khi thẳng đứng = -2.22°

// --- SETUP & LOOP ---

void setup() {
  Serial.begin(115200); // ESP32 nên dùng tốc độ cao

  // ===== Cấu hình wifi =====
  Wire.begin();

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("⚠️ Cấu hình IP tĩnh thất bại!");
  }

  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Kết nối WiFi thành công!");
  udp.begin(udpPort);
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // Cấu hình PWM cho ESP32 (thay cho TCCR1A/B cũ)
  // ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttach(PWM_PIN, PWM_FREQ, PWM_RES);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(BRAKE_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  digitalWrite(BRAKE_PIN, LOW); // Mới vào phanh lại

  delay(1000);
  angle_setup();

  // Tự đo angle_offset khi khởi động (đặt robot thẳng đứng trước khi bật!)
  float sum = 0;
  for (int i = 0; i < 50; i++) {
    angle_calc();
    sum += robot_angle;
    delay(10);
  }
  angle_offset = sum / 50.0;
  Serial.printf("Auto angle_offset = %.2f\n", angle_offset);
}

void loop() {
  currentT = millis();
  if (currentT - previousT_1 >= loop_time) {

    angle_calc();

    if (vertical) {
      digitalWrite(BRAKE_PIN, HIGH); // HIGH = thả phanh (enable motor)

      gyroZ = GyZ / 65.5; // gyroSens=1 (500°/s) → 65.5 LSB/(°/s)
      gyroZfilt = alpha * gyroZ + (1 - alpha) * gyroZfilt;

      // Tính PID + INTEGRAL
      float angle_error = robot_angle - angle_offset;
      error_sum += angle_error * loop_time / 1000.0;   // Tích lũy góc lệch
      error_sum = constrain(error_sum, -30.0f, 30.0f); // Anti-windup

      pwm_s = constrain(X1 * angle_error + X2 * gyroZfilt + X3 * -motor_speed +
                            X4 * error_sum,
                        -255, 255);

      Motor_control(pwm_s);
      motor_speed = motor_speed * 0.995 +
                    pwm_s; // 0.995 cho 5ms loop (tương đương 0.99 ở 10ms)
      motor_speed = constrain(motor_speed, -2000, 2000);
    } else {
      Motor_control(0);
      digitalWrite(BRAKE_PIN, LOW); // LOW = phanh giữ khi ngã
      motor_speed = 0;
      error_sum = 0; // Reset integral khi ngã
    }

    previousT_1 = currentT;
  }

  currentT_py = millis();
  if (currentT_py - previousT_1_py >= loop_time_py) {

    updateToUDP();
    receiveUDP();

    previousT_1_py = currentT;
  }
}