# 🤖 HƯỚNG DẪN TỐI ƯU HÓA ROBOT TỰ CÂN BẰNG

## 📋 TÓM TẮT CÁC CẢI TIẾN

### 1. **Tối ưu UDP Communication** 🌐

#### Vấn đề ban đầu:
- Buffer mặc định quá nhỏ → dễ mất packet
- Timeout 50ms quá lớn → lag khi nhận dữ liệu
- Không kiểm soát tốc độ gửi gains

#### Giải pháp:
```python
# Tăng buffer nhận
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

# Giảm timeout để responsive hơn
sock.settimeout(0.01)  # 10ms thay vì 50ms

# Rate limiting để tránh spam ESP32
SEND_INTERVAL = 0.1  # Chỉ gửi mỗi 100ms
```

**Kết quả:** Giảm packet loss, tăng tốc độ phản hồi

---

### 2. **Data Smoothing (Làm mượt dữ liệu)** 📊

#### Vấn đề:
- Sensor có noise → đường line bị răng cưa
- Khó nhìn xu hướng thật của angle error

#### Giải pháp: Moving Average Filter
```python
def moving_average(data, window=5):
    """Lấy trung bình 5 điểm gần nhất"""
    if len(data) < window:
        return list(data)
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        result.append(np.mean(list(data)[start:i+1]))
    return result
```

**Hiển thị:** 
- Đường Raw (mờ) để thấy data gốc
- Đường Smoothed (đậm) để thấy xu hướng

**Kết quả:** Dễ quan sát, giảm stress khi tuning

---

### 3. **Tối ưu Animation Loop** 🎬

#### Cải tiến:
```python
# Tăng số packets đọc mỗi frame
for _ in range(10):  # Thay vì 5
    data, addr = sock.recvfrom(1024)
    # Xử lý...

# Tăng tốc độ refresh
interval=20  # 50 FPS thay vì 33 FPS
```

**Kết quả:** Real-time hơn, không bị lag

---

### 4. **Performance Metrics** 📈

#### Thêm các chỉ số quan trọng:

**RMS Error (Root Mean Square):**
```python
rms_error = np.sqrt(np.mean(np.square(recent_angles)))
```
- Đo độ ổn định tổng thể
- **Mục tiêu:** < 2.0° → Rất ổn định
- **Nếu > 5.0°:** Cần điều chỉnh PID

**Max Error:**
```python
max_error = np.max(np.abs(recent_angles))
```
- Góc lệch tối đa
- **Mục tiêu:** < 10°

**Packet Drop Rate:**
- Theo dõi mất gói tin
- Nếu cao → Cần tối ưu network

---

## 🎛️ HƯỚNG DẪN TUNING PID

### Bước 1️⃣: Tuning K1 (Proportional)

**Vai trò:** Lực đẩy chính để robot đứng thẳng

**Cách làm:**
1. Đặt K2=0, K3=0, K4=0
2. Bắt đầu K1 = 50
3. Tăng dần K1 (mỗi lần +5) cho đến khi:
   - Robot bắt đầu dao động liên tục
   - Hoặc phản ứng quá mạnh
4. **Giá trị tối ưu** = 80% giá trị dao động

**Dấu hiệu:**
- ✅ K1 vừa đủ: Robot đứng thẳng, hơi lung lay nhẹ
- ❌ K1 quá thấp: Robot ngã liên tục
- ❌ K1 quá cao: Robot dao động mạnh, không ổn định

**Đề xuất:** K1 = 85-95

---

### Bước 2️⃣: Tuning K2 (Derivative)

**Vai trò:** Giảm dao động, tăng độ ổn định

**Cách làm:**
1. Giữ K1 ở giá trị đã tuning
2. Bắt đầu K2 = 5
3. Tăng dần K2 cho đến khi:
   - Robot ổn định hơn
   - Dao động giảm rõ rệt
4. Nếu K2 quá cao → Robot phản ứng chậm

**Dấu hiệu:**
- ✅ K2 vừa đủ: Robot ổn định, ít dao động
- ❌ K2 quá thấp: Vẫn còn dao động nhiều (overshoot)
- ❌ K2 quá cao: Robot sluggish, phản ứng chậm

**Đề xuất:** K2 = 12-18

---

### Bước 3️⃣: Tuning K4 (Integral)

**Vai trò:** Loại bỏ sai số dài hạn (steady-state error)

**Cách làm:**
1. Quan sát: Robot có bị nghiêng 1 góc cố định không?
2. Nếu có → Thêm K4 nhỏ (0.3-1.0)
3. Tăng dần đến khi robot đứng thẳng hoàn toàn

**Cảnh báo:** 
- ⚠️ K4 quá cao → Robot không ổn định
- ⚠️ Integral windup → Cần thêm anti-windup code trên ESP32

**Đề xuất:** K4 = 0.5-1.0 (hoặc 0 nếu không cần)

---

### Bước 4️⃣: Fine-tuning K3 (Brake)

**Vai trò:** Phanh khi robot gần vị trí cân bằng

**Cách làm:**
1. Đặt K3 = 0.05
2. Nếu robot "quá nhạy" gần điểm cân bằng → Tăng K3
3. Nếu robot "ì" → Giảm K3

**Đề xuất:** K3 = 0.06-0.10

---

## 🎯 BẢNG GIÁ TRỊ ĐỀ XUẤT

| Robot Type | K1 (P) | K2 (D) | K3 (Brake) | K4 (I) | Ghi chú |
|------------|--------|--------|------------|--------|---------|
| **Nhẹ (<500g)** | 70-80 | 10-14 | 0.05-0.08 | 0.3-0.8 | Robot nhẹ cần gain thấp hơn |
| **Trung bình (500g-1kg)** | 85-95 | 14-18 | 0.07-0.10 | 0.5-1.2 | Cân bằng giữa tốc độ và ổn định |
| **Nặng (>1kg)** | 100-120 | 18-25 | 0.08-0.12 | 0.8-1.5 | Cần gain cao hơn cho inertia lớn |
| **Bánh lớn** | +10% | +20% | +15% | +10% | Tăng theo tỷ lệ |
| **Bánh nhỏ** | -10% | -15% | -10% | -5% | Giảm theo tỷ lệ |

---

## 📊 ĐÁNH GIÁ HIỆU SUẤT

### Kiểm tra RMS Error:

```
RMS < 1.5°  → 🌟🌟🌟 Xuất sắc!
RMS < 2.5°  → 🌟🌟 Tốt
RMS < 4.0°  → 🌟 Chấp nhận được
RMS > 5.0°  → ❌ Cần điều chỉnh
```

### Test Scenarios:

1. **Static Balance Test:**
   - Đặt robot ở giữa
   - Để yên 30 giây
   - **Mục tiêu:** RMS < 2.0°

2. **Push Test:**
   - Đẩy nhẹ robot
   - Đo thời gian về cân bằng
   - **Mục tiêu:** < 2 giây

3. **Ramp Test:**
   - Đặt robot trên dốc nhẹ (5-10°)
   - **Mục tiêu:** Vẫn cân bằng được

---

## 🔧 TROUBLESHOOTING

### Vấn đề 1: Robot dao động liên tục
**Nguyên nhân:** K1 quá cao hoặc K2 quá thấp
**Giải pháp:**
- Giảm K1 xuống 10-15%
- Tăng K2 lên 20-30%

### Vấn đề 2: Robot phản ứng chậm
**Nguyên nhân:** K2 quá cao hoặc K1 quá thấp
**Giải pháp:**
- Tăng K1 lên 10%
- Giảm K2 xuống 20%

### Vấn đề 3: Robot nghiêng 1 bên
**Nguyên nhân:** 
- Cảm biến không cân chỉnh đúng
- Thiếu I term (K4)
**Giải pháp:**
- Cân chỉnh MPU6050 offset
- Thêm K4 = 0.5

### Vấn đề 4: Packet loss cao
**Nguyên nhân:** 
- WiFi yếu
- ESP32 bận xử lý
**Giải pháp:**
- Di chuyển gần router
- Giảm tốc độ gửi data trên ESP32
- Tăng buffer size

### Vấn đề 5: Đường line vẫn bị răng cưa
**Giải pháp:**
- Tăng SMOOTH_WINDOW = 7 hoặc 10
- Thêm Kalman filter cho sensor (code ESP32)

---

## 💡 TIPS & TRICKS

### 1. Tuning nhanh với Auto-tune:
```python
# TODO: Implement Ziegler-Nichols method
# Tự động tìm K1, K2, K4 tối ưu
```

### 2. Lưu cấu hình tốt nhất:
```python
# Thêm nút "Save Config" để lưu gains hiện tại
# Tự động load lại khi khởi động
```

### 3. So sánh configs:
```python
# A/B testing: So sánh 2 bộ gains
# Xem bộ nào cho RMS thấp hơn
```

### 4. Slow-motion mode:
```python
# Giảm tốc độ animation để xem chi tiết
# Useful khi debug
```

---

## 🚀 NÂNG CAO

### Kalman Filter (cho ESP32):
Thay vì moving average đơn giản, dùng Kalman filter:
- Ước lượng góc chính xác hơn
- Loại bỏ noise tốt hơn
- Giảm delay

### Complementary Filter:
```cpp
// Trên ESP32
angle = 0.98 * (angle + gyro * dt) + 0.02 * accel_angle;
```

### Adaptive PID:
- Tự động điều chỉnh gains theo điều kiện
- Tăng K1 khi góc lệch lớn
- Giảm K1 khi gần cân bằng

---

## 📞 HỖ TRỢ

Nếu vẫn gặp vấn đề:
1. Check hardware: Motor, driver, battery voltage
2. Check sensor: MPU6050 calibration
3. Check timing: ESP32 control loop frequency
4. Check mechanical: Bánh xe, center of mass

**Tốc độ control loop lý tưởng:** 100-200 Hz (5-10ms)

---

## ✅ CHECKLIST TRƯỚC KHI CHẠY

- [ ] MPU6050 đã calibrate
- [ ] Battery đầy (>7V)
- [ ] Bánh xe không bị trượt
- [ ] WiFi kết nối ổn định
- [ ] ESP32 IP đúng: 192.168.1.200
- [ ] Motor driver hoạt động bình thường
- [ ] Center of mass đúng vị trí
- [ ] Code ESP32 đã upload
- [ ] Gains ban đầu: K1=85, K2=15, K3=0.08, K4=0.5

---

## 🎉 KẾT QUẢ MONG ĐỢI

Với các tối ưu hóa này, bạn sẽ có:

✅ **Smoothness:** Đường line mượt mà, dễ quan sát
✅ **Responsiveness:** Không lag, real-time
✅ **Stability:** RMS error < 2.0°
✅ **Reliability:** Ít mất packet
✅ **Tunability:** Dễ điều chỉnh PID

**Good luck! 🚀**
