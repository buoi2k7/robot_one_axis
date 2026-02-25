// --- CÁC HÀM HỖ TRỢ (Functions) ---

void receiveUDP() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    char incoming[128];
    int len = udp.read(incoming, 127);
    if (len > 0)
      incoming[len] = '\0';
    String msg = String(incoming);

    if (msg.startsWith("K1")) {
      int k1Start = msg.indexOf('=') + 1;
      int k2Start = msg.indexOf("K2=") + 3;
      int k3Start = msg.indexOf("K3=") + 3;

      X1 = msg.substring(k1Start, msg.indexOf(',', k1Start)).toFloat();
      X2 = msg.substring(k2Start, msg.indexOf(',', k2Start)).toFloat();

      // K4 tùy chọn (nếu có)
      int k4Idx = msg.indexOf("K4=");
      if (k4Idx >= 0) {
        X3 = msg.substring(k3Start, msg.indexOf(',', k3Start)).toFloat();
        X4 = msg.substring(k4Idx + 3).toFloat();
      } else {
        X3 = msg.substring(k3Start).toFloat();
      }

      Serial.printf("📩 K1=%.2f K2=%.2f K3=%.2f K4=%.2f\n", X1, X2, X3, X4);

      udp.beginPacket(udp.remoteIP(), udp.remotePort());
      udp.print("KACK");
      udp.endPacket();
    }
  }
}

// ===== HÀM CẬP NHẬT GIÁ TRỊ ĐẾN PYTHON =====
void updateToUDP() {
  char buffer[64];
  float ae = robot_angle - angle_offset;
  sprintf(buffer, "%.2f,%.2f,%.2f", ae, (float)pwm_s, robot_angle);

  udp.beginPacket(udpAddress, udpPort);
  udp.print(buffer);
  udp.endPacket();
}

void writeTo(byte device, byte address, byte value) {
  Wire.beginTransmission(device);
  Wire.write(address);
  Wire.write(value);
  Wire.endTransmission(true);
}

void angle_setup() {
  Wire.begin();
  Wire.setClock(400000); // Fast mode 400kHz
  delay(100);

  writeTo(MPU6050, PWR_MGMT_1, 0);
  writeTo(MPU6050, ACCEL_CONFIG, accSens << 3);
  writeTo(MPU6050, GYRO_CONFIG, gyroSens << 3);
  writeTo(MPU6050, 0x1A, 3); // DLPF = 44Hz (giảm nhiễu phần cứng)
  delay(100);

  // ===== AUTO-CALIBRATE Gyro (chỉ Gyro, KHÔNG đụng Accel offset) =====
  // Accel offset đã được set từ calic.ino - không cần tự tính lại

  GyZ_offset_sum = 0;
  for (int i = 0; i < 1024; i++) {
    Wire.beginTransmission(MPU6050);
    Wire.write(0x47);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050, 2, true);
    GyZ = Wire.read() << 8 | Wire.read();
    GyZ_offset_sum += GyZ;
    delay(3);
  }
  GyZ_offset = GyZ_offset_sum >> 10;

  // Bíp còi báo xong
  digitalWrite(BUZZER_PIN, HIGH);
  delay(70);
  digitalWrite(BUZZER_PIN, LOW);
  delay(80);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(70);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.printf("GyZ offset = %d\n", GyZ_offset);
  Serial.printf("AcX offset (calic) = %d\n", AcX_offset);
  Serial.printf("AcY offset (calic) = %d\n", AcY_offset);
}

void angle_calc() {
  // Đọc Accelerometer
  Wire.beginTransmission(MPU6050);
  Wire.write(0x3B);
  byte err1 = Wire.endTransmission(false);
  Wire.requestFrom(MPU6050, 4, true);
  if (err1 == 0 && Wire.available() >= 4) {
    AcX = Wire.read() << 8 | Wire.read();
    AcY = Wire.read() << 8 | Wire.read();
  } else {
    while (Wire.available())
      Wire.read();
    return;
  }

  // Đọc Gyroscope
  Wire.beginTransmission(MPU6050);
  Wire.write(0x47);
  byte err2 = Wire.endTransmission(false);
  Wire.requestFrom(MPU6050, 2, true);
  if (err2 == 0 && Wire.available() >= 2) {
    GyZ = Wire.read() << 8 | Wire.read();
  } else {
    while (Wire.available())
      Wire.read();
    return;
  }

  // Trừ Offset
  AcX += AcX_offset;
  AcY += AcY_offset;
  GyZ -= GyZ_offset;

  // Serial.print(AcX);
  // Serial.print("__");
  // Serial.println(AcY);

  // Tính góc
  robot_angle += GyZ * loop_time / 1000.0 / 65.536;
  Acc_angle = atan2(AcY, -AcX) * 57.2958;
  robot_angle = robot_angle * Gyro_amount + Acc_angle * (1.0 - Gyro_amount);

  // Kiểm tra trạng thái đứng (tính theo góc đã bù offset)
  float angle_err = robot_angle - angle_offset;
  if (abs(angle_err) > 10)
    vertical = false;
  if (abs(angle_err) < 2.0)
    vertical = true;

  Serial.print(Acc_angle);
  Serial.print("__");
  Serial.println(robot_angle);
}

void setPWM(int dutyCycle) {
  // Ghi giá trị PWM vào kênh đã cấu hình
  ledcWrite(PWM_PIN, dutyCycle);
}

void Motor_control(int pwm) {
  if (pwm == 0) {
    setPWM(255); // Motor dừng (Active Low)
    return;
  }

  if (pwm <= 0) {
    digitalWrite(DIR_PIN, LOW);
    pwm = -pwm;
  } else {
    digitalWrite(DIR_PIN, HIGH);
  }

  pwm = constrain(pwm, 0, 255);

  // Active Low: map ngược (0=full, 255=stop)
  int pwm_output = map(pwm, 0, 255, 255, 0);
  setPWM(pwm_output);
}