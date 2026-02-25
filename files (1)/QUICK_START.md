# 🚀 QUICK START - Balancing Robot Optimized

## 📦 Installation

```bash
# 1. Cài đặt dependencies
pip install numpy matplotlib

# 2. Kiểm tra ESP32 IP
# Đảm bảo ESP32_IP = "192.168.1.200" (hoặc IP của bạn)

# 3. Run!
python balancing_robot_optimized.py
```

## ⚡ 5-MINUTE SETUP

### Bước 1: Chọn Preset (30 giây)
Mở `config_presets.py` và chọn preset phù hợp:

```python
# Trong balancing_robot_optimized.py, dòng 30:
# Thay đổi các giá trị này:

# Light robot (<500g):
K1, K2, K3, K4 = 70.0, 12.0, 0.06, 0.4

# Medium robot (500g-1kg): ⭐ RECOMMENDED
K1, K2, K3, K4 = 85.0, 15.0, 0.08, 0.5

# Heavy robot (>1kg):
K1, K2, K3, K4 = 105.0, 20.0, 0.10, 0.8
```

### Bước 2: Chạy Program (10 giây)
```bash
python balancing_robot_optimized.py
```

### Bước 3: Test Balance (1 phút)
1. Đặt robot thẳng đứng
2. Quan sát đường Angle Error
3. Mục tiêu: RMS < 2.5°

### Bước 4: Fine-tune (3 phút)
Nếu không ổn định:
- **Dao động:** Giảm K1 (-10%) hoặc tăng K2 (+20%)
- **Chậm:** Tăng K1 (+10%)
- **Lệch:** Tăng K4 (+0.2)

**DONE!** ✅

---

## 🎯 CÁC CHỈ SỐ QUAN TRỌNG

### Trong giao diện, chú ý:

**📊 Performance Panel (góc phải):**
```
RMS: 1.8°     ← Mục tiêu: < 2.5°
Max: 5.2°     ← Mục tiêu: < 10°
Stable: ✓     ← Có dấu tick = OK
```

**📊 Status Bar (dưới cùng):**
```
Angle: +1.2°  ← Góc lệch hiện tại
PWM: -85      ← Công suất motor
Packets: 1250 ← Số packets nhận được
Drop: 5       ← Mất bao nhiêu packets (càng thấp càng tốt)
FPS: 48.3     ← Frame rate (mục tiêu: >40)
```

---

## 🔧 TROUBLESHOOTING NHANH

| Vấn đề | Giải pháp 1-line |
|--------|------------------|
| **Robot dao động liên tục** | Giảm K1 slider xuống 10-15% |
| **Robot ngã ngay** | Tăng K1 slider lên 20% |
| **Robot chậm chạp** | Giảm K2 slider xuống |
| **Robot lệch 1 bên** | Tăng K4 từ 0 → 0.5 |
| **Packet loss cao** | Di chuyển gần WiFi router |
| **Đường line bị răng cưa** | Tăng SMOOTH_WINDOW trong code |
| **UI bị lag** | Giảm MAX_POINTS = 200 |

---

## 📖 FILES TRONG PACKAGE

```
📁 balancing-robot-optimized/
├── balancing_robot_optimized.py  ← MAIN CODE (chạy file này)
├── config_presets.py             ← 8 preset configs cho các loại robot
├── HUONG_DAN_TOI_UU.md          ← Hướng dẫn chi tiết (đọc nếu cần)
├── SO_SANH_CODE.md              ← So sánh với code gốc
└── QUICK_START.md               ← File này (bắt đầu ở đây!)
```

---

## 💡 TIPS

1. **Luôn bắt đầu với MEDIUM preset** (K1=85, K2=15, K3=0.08, K4=0.5)
2. **Tuning 1 slider tại 1 thời điểm** (đừng thay đổi nhiều cùng lúc)
3. **Dùng nút +/- thay vì kéo slider** (chính xác hơn)
4. **Quan sát đường Smoothed (đậm)** hơn là đường Raw (mờ)
5. **Test push recovery:** Đẩy nhẹ robot, nó phải về cân bằng <2 giây

---

## 🎓 NEXT STEPS

Sau khi robot cân bằng ổn định:

1. ✅ Lưu gains vào file (xem `config_presets.py`)
2. ✅ Test trên các bề mặt khác nhau
3. ✅ Thử AGGRESSIVE preset để tăng tốc độ
4. ✅ Đọc `HUONG_DAN_TOI_UU.md` để hiểu sâu hơn
5. ✅ Thêm tính năng mới (remote control, data logging...)

---

## 📊 BENCHMARK

Robot được coi là **"tốt"** khi:
- ✅ RMS error < 2.5°
- ✅ Max error < 10°
- ✅ Recovery time < 2s
- ✅ Packet loss < 2%
- ✅ FPS > 40

Robot được coi là **"xuất sắc"** khi:
- 🌟 RMS error < 1.5°
- 🌟 Max error < 5°
- 🌟 Recovery time < 1s
- 🌟 Packet loss < 1%
- 🌟 FPS > 45

---

## ❓ FAQ

**Q: Tôi nên dùng preset nào?**
A: Bắt đầu với MEDIUM (K1=85, K2=15). 95% trường hợp sẽ OK.

**Q: Làm sao biết gains đã tối ưu?**
A: Khi RMS < 2.0° và robot phục hồi nhanh sau khi đẩy.

**Q: K4 có nên để 0 không?**
A: Nếu robot không bị drift (lệch dần) thì để 0 OK. Nếu drift thì thêm K4=0.5.

**Q: Tại sao có 2 đường line?**
A: Đường mờ = raw data (có noise), đường đậm = smoothed (dễ nhìn xu hướng).

**Q: FPS thấp (<30) có sao không?**
A: Có thể ảnh hưởng performance. Thử giảm MAX_POINTS hoặc tắt grid.

---

## 🆘 NEED HELP?

1. Đọc `HUONG_DAN_TOI_UU.md` (hướng dẫn chi tiết)
2. Xem `SO_SANH_CODE.md` (so sánh với code cũ)
3. Thử các preset khác trong `config_presets.py`
4. Check hardware: battery, motor, sensor calibration

---

## 🎉 SUCCESS CHECKLIST

- [ ] Code chạy không lỗi
- [ ] Thấy 2 đường graph (Angle và PWM)
- [ ] Packets tăng liên tục
- [ ] FPS > 40
- [ ] Robot cân bằng được >5 giây
- [ ] RMS error < 2.5°
- [ ] Phục hồi sau push < 2s

**Nếu tất cả đều ✓ → DONE! Robot của bạn đã hoạt động tốt! 🎉**

---

**Version:** 1.0 Optimized  
**Last Updated:** February 2025  
**For:** ESP32 Self-Balancing Robot  
**Compatibility:** Python 3.7+, matplotlib 3.0+, numpy 1.19+

**Happy Balancing! 🤖🚀**
