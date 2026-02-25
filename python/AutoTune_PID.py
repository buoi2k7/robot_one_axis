"""
🤖 AUTO-TUNE PID cho Reaction Wheel Balance Robot
==================================================
Script tự động dò tìm bộ K1, K2, K3 tối ưu bằng Hill Climbing.

Cách dùng:
1. Upload code FIXED lên ESP32, đợi bíp calibrate xong
2. Chạy script này: python AutoTune_PID.py
3. Giữ robot đứng thẳng
4. Nhấn nút "▶ BẮT ĐẦU AUTO-TUNE"
5. Robot sẽ tự thử các bộ K → bạn chỉ cần ĐỠ khi ngã
6. Kết thúc: bộ K tốt nhất tự động gửi xuống ESP32
"""

import socket
import time
import threading
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, TextBox
from collections import deque

# ========== CẤU HÌNH ==========
UDP_IP_PC = "0.0.0.0"
UDP_PORT_PC = 4210
ESP32_PORT = 4210

# Bộ K ban đầu (xuất phát từ giá trị bạn đã tune tay)
START_K1 = 76.0
START_K2 = 24.0
START_K3 = 0.16

# Phạm vi cho phép
K1_MIN, K1_MAX = 20.0, 120.0
K2_MIN, K2_MAX = 2.0, 50.0
K3_MIN, K3_MAX = 0.0, 0.50

# Bước nhảy mỗi lần thử
K1_STEP = 5.0
K2_STEP = 2.0
K3_STEP = 0.02

# Thời gian đo mỗi bộ K (giây)
TRIAL_DURATION = 4.0

# Số vòng tối đa auto-tune
MAX_ROUNDS = 30

# Ngã = angle > bao nhiêu độ
FALL_THRESHOLD = 12.0

# ========== GLOBAL STATE ==========
ESP32_IP = None
angles_buffer = deque(maxlen=500)
angles_display = deque(maxlen=200)
current_K = [START_K1, START_K2, START_K3]
best_K = [START_K1, START_K2, START_K3]
best_score = -1.0
tuning_active = False
tuning_done = False
trial_number = 0
total_trials = 0
status_text = "⏸️ Chờ bấm nút để bắt đầu..."
results_log = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP_PC, UDP_PORT_PC))
sock.settimeout(0.05)

# ========== SOCKET FUNCTIONS ==========
def send_gains(k1, k2, k3):
    global ESP32_IP
    if ESP32_IP is None:
        print("⚠️ Chưa biết IP ESP32, đợi nhận data...")
        return
    msg = f"K1={k1:.2f},K2={k2:.2f},K3={k3:.2f}"
    sock.sendto(msg.encode(), (ESP32_IP, ESP32_PORT))
    print(f"📤 Gửi: {msg}")


def receive_loop():
    """Thread liên tục nhận data từ ESP32"""
    global ESP32_IP
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            decoded = data.decode().strip()

            # Auto-detect ESP32 IP
            if ESP32_IP is None and addr[0] != "127.0.0.1":
                ESP32_IP = addr[0]
                print(f"🔗 Phát hiện ESP32: {ESP32_IP}")

            if decoded.startswith("KACK"):
                continue

            values = decoded.split(',')
            if len(values) == 3:
                _, _, z = map(float, values)
            elif len(values) == 1:
                z = float(values[0])
            else:
                continue

            angles_buffer.append(z)
            angles_display.append(z)

        except socket.timeout:
            pass
        except Exception:
            pass


# ========== SCORING FUNCTION ==========
def evaluate_trial(trial_angles):
    """
    Tính điểm cho 1 bộ K dựa trên:
    - Góc trung bình nhỏ → tốt
    - Thời gian đứng dài → tốt
    - Không ngã → bonus
    """
    if len(trial_angles) < 10:
        return 0.0

    abs_angles = [abs(a) for a in trial_angles]
    avg_angle = sum(abs_angles) / len(abs_angles)
    max_angle = max(abs_angles)

    # Đếm bao nhiêu sample đứng được (|angle| < FALL_THRESHOLD)
    standing = sum(1 for a in abs_angles if a < FALL_THRESHOLD)
    standing_ratio = standing / len(trial_angles)

    # Nếu ngã (>50% thời gian angle lớn) → điểm rất thấp
    if standing_ratio < 0.5:
        return standing_ratio * 10

    # Score = (thời gian đứng) / (góc trung bình + 1)
    # Angle nhỏ + đứng lâu = score cao
    score = (standing_ratio * 100) / (avg_angle + 0.5)

    # Bonus nếu max_angle nhỏ (dao động ít)
    if max_angle < 5:
        score *= 1.5
    elif max_angle < 8:
        score *= 1.2

    return round(score, 2)


# ========== HILL CLIMBING AUTO-TUNE ==========
def auto_tune_thread():
    global tuning_active, tuning_done, best_K, best_score
    global current_K, trial_number, total_trials, status_text, results_log

    # Bước 1: Đo điểm của bộ K ban đầu
    status_text = f"📊 Đo bộ K ban đầu: K1={current_K[0]:.0f} K2={current_K[1]:.1f} K3={current_K[2]:.2f}"
    send_gains(*current_K)
    time.sleep(1.0)  # Đợi ổn định

    angles_buffer.clear()
    time.sleep(TRIAL_DURATION)
    trial_angles = list(angles_buffer)
    best_score = evaluate_trial(trial_angles)
    best_K = current_K.copy()
    results_log.append({
        'k': current_K.copy(),
        'score': best_score,
        'trial': 0
    })

    print(f"🏁 Bắt đầu: K=({best_K[0]:.0f}, {best_K[1]:.1f}, {best_K[2]:.2f}) → Score={best_score}")

    # Bước 2: Hill Climbing
    trial_number = 0
    no_improve_count = 0
    step_sizes = [K1_STEP, K2_STEP, K3_STEP]
    k_mins = [K1_MIN, K2_MIN, K3_MIN]
    k_maxs = [K1_MAX, K2_MAX, K3_MAX]

    while tuning_active and trial_number < MAX_ROUNDS and no_improve_count < 9:
        # Chọn 1 trong 3 K để thay đổi
        k_index = trial_number % 3  # Luân phiên K1, K2, K3
        direction = random.choice([-1, 1])  # Tăng hoặc giảm

        # Tạo bộ K thử
        test_K = best_K.copy()
        test_K[k_index] += direction * step_sizes[k_index]
        test_K[k_index] = max(k_mins[k_index], min(k_maxs[k_index], test_K[k_index]))

        # Bỏ qua nếu giống bộ best
        if test_K == best_K:
            trial_number += 1
            continue

        trial_number += 1
        total_trials = trial_number
        k_names = ['K1', 'K2', 'K3']
        status_text = (f"🔄 Thử #{trial_number}/{MAX_ROUNDS}: "
                      f"{k_names[k_index]}={test_K[k_index]:.2f} "
                      f"(best={best_score:.1f})")

        # Gửi bộ K thử
        current_K = test_K.copy()
        send_gains(*current_K)
        time.sleep(1.5)  # Đợi robot ổn định với K mới

        # Thu thập angle data
        angles_buffer.clear()
        time.sleep(TRIAL_DURATION)
        trial_angles = list(angles_buffer)

        if not tuning_active:
            break

        score = evaluate_trial(trial_angles)
        results_log.append({
            'k': test_K.copy(),
            'score': score,
            'trial': trial_number
        })

        print(f"  #{trial_number}: K=({test_K[0]:.0f}, {test_K[1]:.1f}, {test_K[2]:.2f}) "
              f"→ Score={score:.1f} {'✅ TỐT HƠN!' if score > best_score else '❌'}")

        if score > best_score:
            best_score = score
            best_K = test_K.copy()
            no_improve_count = 0
            status_text = f"✅ Tốt hơn! Score={score:.1f} | K=({best_K[0]:.0f}, {best_K[1]:.1f}, {best_K[2]:.2f})"
        else:
            no_improve_count += 1

            # Thử hướng ngược lại
            test_K2 = best_K.copy()
            test_K2[k_index] -= direction * step_sizes[k_index]
            test_K2[k_index] = max(k_mins[k_index], min(k_maxs[k_index], test_K2[k_index]))

            if test_K2 != best_K:
                trial_number += 1
                total_trials = trial_number
                status_text = (f"🔄 Thử ngược #{trial_number}: "
                              f"{k_names[k_index]}={test_K2[k_index]:.2f}")

                current_K = test_K2.copy()
                send_gains(*current_K)
                time.sleep(1.5)
                angles_buffer.clear()
                time.sleep(TRIAL_DURATION)
                trial_angles = list(angles_buffer)

                if not tuning_active:
                    break

                score2 = evaluate_trial(trial_angles)
                results_log.append({
                    'k': test_K2.copy(),
                    'score': score2,
                    'trial': trial_number
                })

                print(f"  #{trial_number}: K=({test_K2[0]:.0f}, {test_K2[1]:.1f}, {test_K2[2]:.2f}) "
                      f"→ Score={score2:.1f} {'✅' if score2 > best_score else '❌'}")

                if score2 > best_score:
                    best_score = score2
                    best_K = test_K2.copy()
                    no_improve_count = 0

    # Kết thúc: gửi bộ K tốt nhất
    current_K = best_K.copy()
    send_gains(*best_K)
    tuning_active = False
    tuning_done = True
    status_text = (f"🏆 XONG! Best: K1={best_K[0]:.1f} K2={best_K[1]:.1f} K3={best_K[2]:.2f} "
                  f"Score={best_score:.1f} ({trial_number} trials)")

    print(f"\n{'='*50}")
    print(f"🏆 KẾT QUẢ AUTO-TUNE:")
    print(f"   K1 = {best_K[0]:.1f}")
    print(f"   K2 = {best_K[1]:.1f}")
    print(f"   K3 = {best_K[2]:.2f}")
    print(f"   Score = {best_score:.1f}")
    print(f"   Trials = {trial_number}")
    print(f"{'='*50}")


# ========== GUI ==========
plt.style.use('seaborn-v0_8-darkgrid')
fig, (ax_angle, ax_score) = plt.subplots(2, 1, figsize=(10, 7),
                                          gridspec_kw={'height_ratios': [2, 1]})
plt.subplots_adjust(bottom=0.18, hspace=0.35)

# --- Angle plot ---
line_angle, = ax_angle.plot([], [], color='dodgerblue', linewidth=1.5, label='Robot Angle')
ax_angle.axhline(y=0, color='green', linestyle='--', alpha=0.5, linewidth=0.8)
ax_angle.axhline(y=FALL_THRESHOLD, color='red', linestyle=':', alpha=0.4, label=f'Ngã ({FALL_THRESHOLD}°)')
ax_angle.axhline(y=-FALL_THRESHOLD, color='red', linestyle=':', alpha=0.4)
ax_angle.set_ylim(-20, 20)
ax_angle.set_xlim(0, 200)
ax_angle.set_xlabel("Samples")
ax_angle.set_ylabel("Angle (°)")
ax_angle.set_title("🤖 AUTO-TUNE PID — Reaction Wheel Balance")
ax_angle.legend(loc='upper right', fontsize=8)

# --- Score plot ---
ax_score.set_ylabel("Score")
ax_score.set_xlabel("Trial #")
ax_score.set_title("📊 Điểm mỗi lần thử (cao = tốt)")

# --- Status text ---
status_display = fig.text(0.5, 0.10, status_text, ha='center', fontsize=11,
                          fontweight='bold', color='navy',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow'))

# --- Current K display ---
k_display = fig.text(0.5, 0.05, f"K1={current_K[0]:.1f}  K2={current_K[1]:.1f}  K3={current_K[2]:.2f}",
                     ha='center', fontsize=10, color='darkgreen',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='honeydew'))

# --- Buttons ---
ax_start = plt.axes([0.15, 0.01, 0.25, 0.04])
ax_stop = plt.axes([0.45, 0.01, 0.15, 0.04])
ax_apply = plt.axes([0.65, 0.01, 0.20, 0.04])

btn_start = Button(ax_start, '▶ BẮT ĐẦU AUTO-TUNE', color='lightgreen', hovercolor='lime')
btn_stop = Button(ax_stop, '⏹ DỪNG', color='lightyellow', hovercolor='orange')
btn_apply = Button(ax_apply, '💾 ÁP DỤNG BEST', color='lightcyan', hovercolor='cyan')


def on_start(event):
    global tuning_active, tuning_done, trial_number, results_log
    if tuning_active:
        return
    if ESP32_IP is None:
        print("⚠️ Chưa kết nối ESP32! Đợi nhận data trước...")
        return
    tuning_active = True
    tuning_done = False
    trial_number = 0
    results_log = []
    t = threading.Thread(target=auto_tune_thread, daemon=True)
    t.start()
    print("🚀 Bắt đầu Auto-Tune!")


def on_stop(event):
    global tuning_active, status_text
    tuning_active = False
    status_text = "⏹ Đã dừng. Bộ K tốt nhất đã được gửi."
    send_gains(*best_K)

def on_apply(event):
    send_gains(*best_K)
    print(f"💾 Áp dụng: K1={best_K[0]:.1f} K2={best_K[1]:.1f} K3={best_K[2]:.2f}")


btn_start.on_clicked(on_start)
btn_stop.on_clicked(on_stop)
btn_apply.on_clicked(on_apply)


# ========== ANIMATION UPDATE ==========
def update(frame):
    # Update angle chart
    if len(angles_display) > 0:
        line_angle.set_data(range(len(angles_display)), list(angles_display))

    # Update score chart
    if len(results_log) > 0:
        ax_score.clear()
        trials = [r['trial'] for r in results_log]
        scores = [r['score'] for r in results_log]
        colors = ['green' if s == best_score else 'steelblue' for s in scores]
        ax_score.bar(trials, scores, color=colors, alpha=0.7)
        ax_score.set_ylabel("Score")
        ax_score.set_xlabel("Trial #")
        ax_score.set_title(f"📊 Scores — Best: {best_score:.1f}")
        if best_score > 0:
            ax_score.axhline(y=best_score, color='green', linestyle='--', alpha=0.5, linewidth=1)

    # Update status
    status_display.set_text(status_text)
    k_display.set_text(f"K1={current_K[0]:.1f}  K2={current_K[1]:.1f}  K3={current_K[2]:.2f}  |  "
                       f"Best: K1={best_K[0]:.1f}  K2={best_K[1]:.1f}  K3={best_K[2]:.2f}")

    return line_angle,


# ========== START ==========
# Khởi động thread nhận data
recv_thread = threading.Thread(target=receive_loop, daemon=True)
recv_thread.start()

print("=" * 50)
print("🤖 AUTO-TUNE PID — Reaction Wheel Balance")
print("=" * 50)
print(f"📍 Bắt đầu từ: K1={START_K1}, K2={START_K2}, K3={START_K3}")
print(f"📍 Phạm vi: K1=[{K1_MIN}-{K1_MAX}] K2=[{K2_MIN}-{K2_MAX}] K3=[{K3_MIN}-{K3_MAX}]")
print(f"📍 Thời gian đo: {TRIAL_DURATION}s/trial | Tối đa: {MAX_ROUNDS} trials")
print("📍 Đợi kết nối ESP32...")
print()

# Gửi K ban đầu khi có IP
def wait_and_send():
    while ESP32_IP is None:
        time.sleep(0.5)
    time.sleep(1)
    send_gains(START_K1, START_K2, START_K3)

threading.Thread(target=wait_and_send, daemon=True).start()

ani = animation.FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)
plt.show()
