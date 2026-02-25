import socket
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, TextBox
from collections import deque
import numpy as np
import matplotlib
matplotlib.rcParams['font.size'] = 9

# --- Cấu hình UDP (TỐI ƯU HÓA) ---
UDP_IP_PC = "0.0.0.0"
UDP_PORT_PC = 4210
ESP32_IP = "192.168.1.200"
ESP32_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Tăng buffer
sock.bind((UDP_IP_PC, UDP_PORT_PC))
sock.settimeout(0.01)  # Giảm timeout để responsive hơn

# --- Dữ liệu biểu đồ ---
MAX_POINTS = 300
angle_data = deque(maxlen=MAX_POINTS)
pwm_data = deque(maxlen=MAX_POINTS)
time_data = deque(maxlen=MAX_POINTS)

# --- SMOOTHING DATA ---
# Thêm moving average để làm mượt đường line
angle_smooth = deque(maxlen=MAX_POINTS)
pwm_smooth = deque(maxlen=MAX_POINTS)
SMOOTH_WINDOW = 5  # Số điểm để tính trung bình

def moving_average(data, window=SMOOTH_WINDOW):
    """Tính moving average để làm mượt dữ liệu"""
    if len(data) < window:
        return list(data)
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        result.append(np.mean(list(data)[start:i+1]))
    return result

# --- HỆ SỐ PID TỐI ƯU (ĐỀ XUẤT) ---
# Bạn có thể thử các giá trị này để cân bằng tốt hơn
K1, K2, K3, K4 = 85.0, 15.0, 0.08, 0.5  # Tăng P, D, Brake và thêm I

# --- Hàm gửi hệ số ---
last_sent_time = 0
SEND_INTERVAL = 0.1  # Chỉ gửi sau 100ms để tránh spam

def send_gains(k1, k2, k3, k4, force=False):
    global last_sent_time
    import time
    current_time = time.time()
    
    if not force and (current_time - last_sent_time) < SEND_INTERVAL:
        return False  # Không gửi nếu quá gần lần gửi trước
    
    msg = f"K1={k1:.2f},K2={k2:.2f},K3={k3:.2f},K4={k4:.2f}"
    try:
        sock.sendto(msg.encode(), (ESP32_IP, ESP32_PORT))
        print(f"📤 {msg}")
        last_sent_time = current_time
        return True
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return False

send_gains(K1, K2, K3, K4, force=True)

# --- Giao diện ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7))
plt.subplots_adjust(bottom=0.38, hspace=0.35, left=0.08, right=0.95)
fig.patch.set_facecolor('#1a1a2e')
fig.canvas.manager.set_window_title('🤖 Self-Balancing Robot - PID Tuner')

# Chart 1: Góc (Angle Error)
ax1.set_facecolor('#16213e')
ax1.set_title('🎯 Angle Error (°) - Real-time & Smoothed', color='white', fontweight='bold')
ax1.set_ylim(-15, 15)
ax1.set_xlim(0, MAX_POINTS)
ax1.grid(True, alpha=0.2, color='#444', linestyle='--', linewidth=0.5)
ax1.axhline(y=0, color='#00ff88', linewidth=1.5, linestyle='--', alpha=0.7, label='Target')
ax1.axhline(y=2, color='#ff6b6b', linewidth=0.5, linestyle=':', alpha=0.4)
ax1.axhline(y=-2, color='#ff6b6b', linewidth=0.5, linestyle=':', alpha=0.4)
ax1.tick_params(colors='white')
ax1.spines['bottom'].set_color('#444')
ax1.spines['left'].set_color('#444')
ax1.spines['right'].set_color('#444')
ax1.spines['top'].set_color('#444')

# Hai đường: raw và smooth
line_angle_raw, = ax1.plot([], [], color='#4ecdc4', linewidth=0.8, alpha=0.5, label='Raw Data')
line_angle, = ax1.plot([], [], color='#00d9ff', linewidth=2, label='Smoothed')
ax1.legend(loc='upper right', facecolor='#16213e', edgecolor='#444', labelcolor='white')

# Chart 2: PWM Motor
ax2.set_facecolor('#16213e')
ax2.set_title('⚡ Motor PWM Output', color='white', fontweight='bold')
ax2.set_ylim(-280, 280)
ax2.set_xlim(0, MAX_POINTS)
ax2.grid(True, alpha=0.2, color='#444', linestyle='--', linewidth=0.5)
ax2.axhline(y=0, color='#00ff88', linewidth=1.5, linestyle='--', alpha=0.7)
ax2.axhline(y=255, color='#ff6b6b', linewidth=0.5, linestyle=':', alpha=0.3, label='Max PWM')
ax2.axhline(y=-255, color='#ff6b6b', linewidth=0.5, linestyle=':', alpha=0.3)
ax2.tick_params(colors='white')
ax2.spines['bottom'].set_color('#444')
ax2.spines['left'].set_color('#444')
ax2.spines['right'].set_color('#444')
ax2.spines['top'].set_color('#444')

line_pwm_raw, = ax2.plot([], [], color='#ffd93d', linewidth=0.8, alpha=0.5, label='Raw PWM')
line_pwm, = ax2.plot([], [], color='#ffaa00', linewidth=2, label='Smoothed PWM')
ax2.legend(loc='upper right', facecolor='#16213e', edgecolor='#444', labelcolor='white')
ax2.set_xlabel('Samples', color='white', fontweight='bold')

# --- Sliders với ranges được tối ưu ---
slider_color = '#0f3460'
axK1 = plt.axes([0.15, 0.25, 0.50, 0.025], facecolor=slider_color)
axK2 = plt.axes([0.15, 0.20, 0.50, 0.025], facecolor=slider_color)
axK3 = plt.axes([0.15, 0.15, 0.50, 0.025], facecolor=slider_color)
axK4 = plt.axes([0.15, 0.10, 0.50, 0.025], facecolor=slider_color)

sliderK1 = Slider(axK1, 'K1 (P)',     0, 200, valinit=K1, valstep=0.5, color='#4ecdc4')
sliderK2 = Slider(axK2, 'K2 (D)',     0, 50,  valinit=K2, valstep=0.25, color='#ffd93d')
sliderK3 = Slider(axK3, 'K3 (Brake)', 0, 1,   valinit=K3, valstep=0.01, color='#ff6b6b')
sliderK4 = Slider(axK4, 'K4 (I)',     0, 10,  valinit=K4, valstep=0.1, color='#a8e6cf')

# --- Text boxes ---
for ax_s in [axK1, axK2, axK3, axK4]:
    ax_s.tick_params(colors='white')

vbK1 = plt.axes([0.72, 0.25, 0.06, 0.025]); tK1 = TextBox(vbK1, '', initial=f'{K1:.1f}')
vbK2 = plt.axes([0.72, 0.20, 0.06, 0.025]); tK2 = TextBox(vbK2, '', initial=f'{K2:.1f}')
vbK3 = plt.axes([0.72, 0.15, 0.06, 0.025]); tK3 = TextBox(vbK3, '', initial=f'{K3:.2f}')
vbK4 = plt.axes([0.72, 0.10, 0.06, 0.025]); tK4 = TextBox(vbK4, '', initial=f'{K4:.1f}')

# --- Buttons ---
def make_btn(pos): return plt.axes(pos)
bm1 = Button(make_btn([0.05, 0.25, 0.04, 0.025]), '–'); bp1 = Button(make_btn([0.82, 0.25, 0.04, 0.025]), '+')
bm2 = Button(make_btn([0.05, 0.20, 0.04, 0.025]), '–'); bp2 = Button(make_btn([0.82, 0.20, 0.04, 0.025]), '+')
bm3 = Button(make_btn([0.05, 0.15, 0.04, 0.025]), '–'); bp3 = Button(make_btn([0.82, 0.15, 0.04, 0.025]), '+')
bm4 = Button(make_btn([0.05, 0.10, 0.04, 0.025]), '–'); bp4 = Button(make_btn([0.82, 0.10, 0.04, 0.025]), '+')

# --- Status text với nhiều thông tin hơn ---
status_ax = plt.axes([0.15, 0.03, 0.70, 0.04])
status_ax.set_facecolor('#0f3460')
status_ax.set_xticks([]); status_ax.set_yticks([])
status_text = status_ax.text(0.5, 0.5, 'Waiting for data...', transform=status_ax.transAxes,
                              ha='center', va='center', color='#4ecdc4', fontsize=10, fontweight='bold')

# --- Performance metrics ---
perf_ax = plt.axes([0.87, 0.25, 0.12, 0.15])
perf_ax.set_facecolor('#0f3460')
perf_ax.set_xticks([]); perf_ax.set_yticks([])
perf_ax.spines['bottom'].set_color('#444')
perf_ax.spines['left'].set_color('#444')
perf_ax.spines['right'].set_color('#444')
perf_ax.spines['top'].set_color('#444')
perf_text = perf_ax.text(0.5, 0.5, '📊 Stats\n---\nRMS: --\nMax: --', 
                         transform=perf_ax.transAxes,
                         ha='center', va='center', color='#ffd93d', 
                         fontsize=8, fontweight='bold')

# --- Callbacks ---
update_pending = False

def update_display():
    global update_pending
    tK1.set_val(f'{sliderK1.val:.1f}')
    tK2.set_val(f'{sliderK2.val:.1f}')
    tK3.set_val(f'{sliderK3.val:.2f}')
    tK4.set_val(f'{sliderK4.val:.1f}')
    update_pending = True  # Đánh dấu cần gửi

def on_slider(val): 
    update_display()

sliderK1.on_changed(on_slider)
sliderK2.on_changed(on_slider)
sliderK3.on_changed(on_slider)
sliderK4.on_changed(on_slider)

def make_adj(slider, delta):
    def adj(event):
        v = min(max(slider.val + delta, slider.valmin), slider.valmax)
        slider.set_val(v)
        update_display()
    return adj

bm1.on_clicked(make_adj(sliderK1, -0.5));  bp1.on_clicked(make_adj(sliderK1, 0.5))
bm2.on_clicked(make_adj(sliderK2, -0.25)); bp2.on_clicked(make_adj(sliderK2, 0.25))
bm3.on_clicked(make_adj(sliderK3, -0.01)); bp3.on_clicked(make_adj(sliderK3, 0.01))
bm4.on_clicked(make_adj(sliderK4, -0.1));  bp4.on_clicked(make_adj(sliderK4, 0.1))

# --- Animation với xử lý tốt hơn ---
packet_count = 0
dropped_packets = 0
last_update_time = 0

def update(frame):
    global packet_count, dropped_packets, update_pending, last_update_time
    import time
    
    current_time = time.time()
    
    # Gửi gains nếu có thay đổi pending
    if update_pending:
        if send_gains(sliderK1.val, sliderK2.val, sliderK3.val, sliderK4.val):
            update_pending = False
    
    # Đọc nhiều packets để tránh bị tụt hậu
    packets_read = 0
    try:
        for _ in range(10):  # Tăng lên 10 để đọc nhanh hơn
            data, addr = sock.recvfrom(1024)
            decoded = data.decode().strip()
            
            if decoded.startswith("KACK"):
                status_text.set_text('✅ ESP32 confirmed gains')
                continue
                
            values = decoded.split(',')
            if len(values) >= 2:
                angle_err = float(values[0])
                pwm = float(values[1])
                angle_data.append(angle_err)
                pwm_data.append(pwm)
                time_data.append(current_time)
                packet_count += 1
                packets_read += 1
                
    except socket.timeout:
        if packets_read == 0:
            dropped_packets += 1
    except Exception as e:
        status_text.set_text(f'⚠️ {e}')

    # Cập nhật đồ thị với smoothing
    if len(angle_data) > 0:
        x = range(len(angle_data))
        
        # Raw data
        line_angle_raw.set_data(x, list(angle_data))
        line_pwm_raw.set_data(x, list(pwm_data))
        
        # Smoothed data
        angle_smoothed = moving_average(angle_data, SMOOTH_WINDOW)
        pwm_smoothed = moving_average(pwm_data, SMOOTH_WINDOW)
        line_angle.set_data(x, angle_smoothed)
        line_pwm.set_data(x, pwm_smoothed)

        # Status với FPS
        last_angle = angle_data[-1]
        last_pwm = pwm_data[-1] if pwm_data else 0
        
        # Tính FPS
        if last_update_time > 0:
            fps = 1.0 / (current_time - last_update_time) if current_time > last_update_time else 0
        else:
            fps = 0
        last_update_time = current_time
        
        status_text.set_text(
            f'📊 Angle: {last_angle:+.2f}°  |  PWM: {last_pwm:+.0f}  |  '
            f'Packets: {packet_count}  |  Drop: {dropped_packets}  |  FPS: {fps:.1f}'
        )
        
        # Tính performance metrics
        if len(angle_data) >= 10:
            recent_angles = list(angle_data)[-100:]  # 100 điểm gần nhất
            rms_error = np.sqrt(np.mean(np.square(recent_angles)))
            max_error = np.max(np.abs(recent_angles))
            perf_text.set_text(
                f'📊 Performance\n'
                f'───────\n'
                f'RMS: {rms_error:.2f}°\n'
                f'Max: {max_error:.2f}°\n'
                f'Stable: {"✓" if rms_error < 2.0 else "✗"}'
            )

    return line_angle, line_pwm, line_angle_raw, line_pwm_raw

# Tăng tốc độ update lên 20ms (50 FPS)
ani = animation.FuncAnimation(fig, update, interval=20, blit=False, cache_frame_data=False)

print("=" * 60)
print("🚀 SELF-BALANCING ROBOT - PID TUNER (OPTIMIZED)")
print("=" * 60)
print("📌 ĐỀ XUẤT CÁCH TUNING:")
print("   1. Bắt đầu với K1 (P) = 85, tăng dần đến khi robot dao động")
print("   2. Sau đó giảm K1 xuống 80-90% giá trị dao động")
print("   3. Tăng K2 (D) = 15 để giảm overshoot và làm ổn định")
print("   4. Thêm K4 (I) = 0.5 để loại bỏ steady-state error")
print("   5. Điều chỉnh K3 (Brake) = 0.08 để tránh quá mạnh khi dừng")
print("=" * 60)
print("✨ CẢI TIẾN:")
print("   ✓ Smoothing filter (moving average) cho đường line mượt hơn")
print("   ✓ Tăng UDP buffer và tối ưu timeout")
print("   ✓ Đọc nhiều packets mỗi frame để tránh lag")
print("   ✓ Hiển thị metrics: RMS error, Max error, Stability")
print("   ✓ Rate limiting cho gain updates")
print("   ✓ FPS counter và packet drop tracking")
print("=" * 60)

plt.show()
