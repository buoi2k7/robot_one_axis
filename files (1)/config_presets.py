# ⚙️ CONFIGURATION PRESETS - BALANCING ROBOT

"""
File này chứa các cấu hình PID gains đã được test
cho các loại robot tự cân bằng khác nhau.

Sử dụng:
1. Copy phần config phù hợp với robot của bạn
2. Update vào code hoặc load dynamically
3. Fine-tune dựa trên kết quả thực tế
"""

# ============================================
# PRESET 1: LIGHT ROBOT (Nhẹ < 500g)
# ============================================
LIGHT_ROBOT = {
    "name": "Light Robot (<500g)",
    "description": "Robot nhẹ, bánh nhỏ (50-70mm), motor N20",
    "gains": {
        "K1": 70.0,   # P - Proportional
        "K2": 12.0,   # D - Derivative
        "K3": 0.06,   # Brake
        "K4": 0.4     # I - Integral
    },
    "characteristics": {
        "weight": "300-500g",
        "wheel_diameter": "50-70mm",
        "motor_type": "N20 or similar",
        "expected_rms": "< 2.5°",
        "recovery_time": "< 2.5s"
    },
    "tuning_notes": [
        "Robot nhẹ dễ bị ảnh hưởng bởi noise",
        "Cần K2 cao hơn để chống oscillation",
        "K3 thấp vì inertia nhỏ",
        "SMOOTH_WINDOW nên để 5-7"
    ]
}

# ============================================
# PRESET 2: MEDIUM ROBOT (Trung bình 500g-1kg)
# ============================================
MEDIUM_ROBOT = {
    "name": "Medium Robot (500g-1kg)",
    "description": "Robot cân đối, bánh 70-100mm, motor 12V",
    "gains": {
        "K1": 85.0,   # P - RECOMMENDED DEFAULT
        "K2": 15.0,   # D
        "K3": 0.08,   # Brake
        "K4": 0.5     # I
    },
    "characteristics": {
        "weight": "600-900g",
        "wheel_diameter": "70-100mm",
        "motor_type": "Standard DC motor 12V",
        "expected_rms": "< 2.0°",
        "recovery_time": "< 2.0s"
    },
    "tuning_notes": [
        "Đây là preset mặc định, phù hợp nhất",
        "Balance tốt giữa tốc độ và ổn định",
        "Thường chỉ cần fine-tune ±10%",
        "SMOOTH_WINDOW = 5 là optimal"
    ]
}

# ============================================
# PRESET 3: HEAVY ROBOT (Nặng > 1kg)
# ============================================
HEAVY_ROBOT = {
    "name": "Heavy Robot (>1kg)",
    "description": "Robot lớn, bánh 100-150mm, motor mạnh",
    "gains": {
        "K1": 105.0,  # P - Cần cao để đẩy mass lớn
        "K2": 20.0,   # D - Cao để chống overshoot
        "K3": 0.10,   # Brake - Cao hơn vì inertia lớn
        "K4": 0.8     # I - Cao để giữ vị trí
    },
    "characteristics": {
        "weight": "1.0-2.0kg",
        "wheel_diameter": "100-150mm",
        "motor_type": "High torque 12-24V",
        "expected_rms": "< 3.0°",
        "recovery_time": "< 3.0s"
    },
    "tuning_notes": [
        "Robot nặng cần gains cao hơn nhiều",
        "Inertia lớn → K3 quan trọng để phanh",
        "Có thể cần tăng PWM max limit",
        "SMOOTH_WINDOW = 3-5 (responsive hơn)"
    ]
}

# ============================================
# PRESET 4: TALL ROBOT (Robot cao, CoM cao)
# ============================================
TALL_ROBOT = {
    "name": "Tall Robot (High Center of Mass)",
    "description": "Robot cao (>15cm), center of mass cao",
    "gains": {
        "K1": 95.0,   # P - Cao để phản ứng nhanh
        "K2": 18.0,   # D - Rất cao để chống tip over
        "K3": 0.12,   # Brake - Cao để ổn định
        "K4": 0.3     # I - Thấp, tránh oscillation
    },
    "characteristics": {
        "height": "> 15cm",
        "com_height": "High (unstable)",
        "wheel_diameter": "Any",
        "expected_rms": "< 3.5°",
        "recovery_time": "< 1.5s"
    },
    "tuning_notes": [
        "CoM cao → Rất dễ bị ngã",
        "Cần K1, K2 cao để phản ứng cực nhanh",
        "K4 thấp vì dễ bị wind-up",
        "Có thể cần Complementary Filter"
    ]
}

# ============================================
# PRESET 5: AGGRESSIVE (Phản ứng nhanh)
# ============================================
AGGRESSIVE_TUNING = {
    "name": "Aggressive Tuning",
    "description": "Phản ứng rất nhanh, ít overshoot",
    "gains": {
        "K1": 100.0,  # P - Very high
        "K2": 22.0,   # D - Very high để chống overshoot
        "K3": 0.15,   # Brake - Phanh mạnh
        "K4": 0.2     # I - Thấp
    },
    "characteristics": {
        "response": "Very fast (<0.5s)",
        "overshoot": "Minimal",
        "oscillation": "Low",
        "use_case": "Competition, demo"
    },
    "tuning_notes": [
        "Cho performance cao nhất",
        "Có thể gây jerky motion",
        "Tiêu tốn nhiều pin hơn",
        "Cần motor và driver tốt"
    ]
}

# ============================================
# PRESET 6: SMOOTH (Êm ái, ít rung)
# ============================================
SMOOTH_TUNING = {
    "name": "Smooth Tuning",
    "description": "Chuyển động êm ái, ít rung",
    "gains": {
        "K1": 75.0,   # P - Thấp hơn
        "K2": 12.0,   # D - Moderate
        "K3": 0.05,   # Brake - Thấp, mềm mại
        "K4": 0.8     # I - Cao để giữ ổn định
    },
    "characteristics": {
        "response": "Slow (~2s)",
        "overshoot": "Moderate",
        "oscillation": "Very low",
        "use_case": "Display, education"
    },
    "tuning_notes": [
        "Ưu tiên smooth hơn là fast",
        "K4 cao để tránh drift",
        "SMOOTH_WINDOW = 7-10",
        "Tiết kiệm pin"
    ]
}

# ============================================
# PRESET 7: BEGINNER (Cho người mới)
# ============================================
BEGINNER_SAFE = {
    "name": "Beginner Safe",
    "description": "An toàn, dễ tuning, ít rủi ro",
    "gains": {
        "K1": 60.0,   # P - Conservative
        "K2": 10.0,   # D
        "K3": 0.04,   # Brake
        "K4": 0.0     # I - Disabled để tránh wind-up
    },
    "characteristics": {
        "response": "Slow but safe",
        "stability": "Good",
        "risk": "Low",
        "use_case": "Learning, testing"
    },
    "tuning_notes": [
        "Bắt đầu từ đây nếu mới làm lần đầu",
        "Tăng dần K1 từng bước 5",
        "Không dùng K4 ban đầu",
        "Quan sát kỹ trước khi tăng"
    ]
}

# ============================================
# PRESET 8: OUTDOOR (Sử dụng ngoài trời)
# ============================================
OUTDOOR_ROBUST = {
    "name": "Outdoor Robust",
    "description": "Chống nhiễu gió, mặt đất không bằng",
    "gains": {
        "K1": 90.0,   # P - Cao để chống disturbance
        "K2": 16.0,   # D
        "K3": 0.09,   # Brake
        "K4": 0.6     # I - Cao để reject disturbance
    },
    "characteristics": {
        "wind_resistance": "Good",
        "rough_terrain": "OK",
        "disturbance_rejection": "High",
        "use_case": "Outdoor demo"
    },
    "tuning_notes": [
        "K4 cao để chống disturbance liên tục",
        "SMOOTH_WINDOW = 3 (phản ứng nhanh với gió)",
        "Có thể cần Kalman Filter",
        "Test trên nhiều bề mặt khác nhau"
    ]
}

# ============================================
# COMPARISON TABLE
# ============================================
COMPARISON = """
┌─────────────────┬──────┬──────┬───────┬──────┬─────────────────┐
│ Preset          │  K1  │  K2  │  K3   │  K4  │ Best For        │
├─────────────────┼──────┼──────┼───────┼──────┼─────────────────┤
│ Light Robot     │  70  │  12  │ 0.06  │ 0.4  │ <500g           │
│ Medium Robot    │  85  │  15  │ 0.08  │ 0.5  │ 500g-1kg ⭐     │
│ Heavy Robot     │ 105  │  20  │ 0.10  │ 0.8  │ >1kg            │
│ Tall Robot      │  95  │  18  │ 0.12  │ 0.3  │ High CoM        │
│ Aggressive      │ 100  │  22  │ 0.15  │ 0.2  │ Competition     │
│ Smooth          │  75  │  12  │ 0.05  │ 0.8  │ Display         │
│ Beginner        │  60  │  10  │ 0.04  │ 0.0  │ First try       │
│ Outdoor         │  90  │  16  │ 0.09  │ 0.6  │ Wind/terrain    │
└─────────────────┴──────┴──────┴───────┴──────┴─────────────────┘

⭐ = Recommended default
"""

# ============================================
# USAGE EXAMPLE
# ============================================
USAGE_EXAMPLE = """
# Example 1: Load preset vào code
preset = MEDIUM_ROBOT
K1 = preset["gains"]["K1"]
K2 = preset["gains"]["K2"]
K3 = preset["gains"]["K3"]
K4 = preset["gains"]["K4"]

# Example 2: Dynamic loading
def load_preset(preset_name):
    presets = {
        "light": LIGHT_ROBOT,
        "medium": MEDIUM_ROBOT,
        "heavy": HEAVY_ROBOT,
        "tall": TALL_ROBOT,
        "aggressive": AGGRESSIVE_TUNING,
        "smooth": SMOOTH_TUNING,
        "beginner": BEGINNER_SAFE,
        "outdoor": OUTDOOR_ROBUST
    }
    return presets.get(preset_name.lower(), MEDIUM_ROBOT)

preset = load_preset("medium")
send_gains(preset["gains"]["K1"], ...)

# Example 3: Compare multiple presets
def compare_presets(preset1, preset2):
    print(f"{preset1['name']} vs {preset2['name']}")
    print(f"K1: {preset1['gains']['K1']} vs {preset2['gains']['K1']}")
    # ...
"""

# ============================================
# SAVE/LOAD FUNCTIONS
# ============================================
SAVE_LOAD_CODE = """
import json

def save_custom_config(filename, k1, k2, k3, k4, notes=""):
    '''Lưu config hiện tại ra file'''
    config = {
        "gains": {"K1": k1, "K2": k2, "K3": k3, "K4": k4},
        "notes": notes,
        "timestamp": time.time()
    }
    with open(filename, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"✅ Saved to {filename}")

def load_custom_config(filename):
    '''Load config từ file'''
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config["gains"]
    except:
        print(f"❌ Cannot load {filename}")
        return None

# Usage:
# save_custom_config("my_robot_config.json", 85, 15, 0.08, 0.5, "Best config 2025-02-23")
# gains = load_custom_config("my_robot_config.json")
"""

# ============================================
# TUNING WORKFLOW
# ============================================
TUNING_WORKFLOW = """
RECOMMENDED TUNING WORKFLOW:
════════════════════════════════════════════

Step 1: Identify robot type
   → Check weight, wheel size, CoM height
   → Select closest preset

Step 2: Load preset
   → Copy gains to code
   → Start tuning process

Step 3: Fine-tune K1 (P)
   → Adjust ±10% based on response
   → If oscillating → Decrease
   → If too slow → Increase

Step 4: Fine-tune K2 (D)
   → If overshoot → Increase
   → If sluggish → Decrease

Step 5: Add K4 (I) if needed
   → Start at preset value
   → If drift → Increase
   → If unstable → Decrease

Step 6: Adjust K3 (Brake)
   → If too jerky near balance → Increase
   → If slow to stabilize → Decrease

Step 7: Test & iterate
   → Check RMS error < 2.5°
   → Test push recovery
   → Test on slopes

Step 8: Save final config
   → Document settings
   → Note any special conditions
"""

# ============================================
# TROUBLESHOOTING MATRIX
# ============================================
TROUBLESHOOTING = """
PROBLEM-SOLUTION MATRIX:
════════════════════════════════════════════

Symptom                    | Likely Cause      | Solution
──────────────────────────┼──────────────────┼─────────────────
Oscillates continuously    | K1 too high       | Decrease K1 -10%
                          | K2 too low        | Increase K2 +20%
──────────────────────────┼──────────────────┼─────────────────
Falls immediately         | K1 too low        | Increase K1 +20%
                          | Sensor reversed   | Check MPU6050
──────────────────────────┼──────────────────┼─────────────────
Slow response             | K1 too low        | Increase K1 +10%
                          | K2 too high       | Decrease K2 -20%
──────────────────────────┼──────────────────┼─────────────────
Drifts to one side        | K4 = 0            | Enable K4 = 0.5
                          | Sensor bias       | Recalibrate MPU
──────────────────────────┼──────────────────┼─────────────────
Jerky near balance        | K3 too low        | Increase K3 +50%
──────────────────────────┼──────────────────┼─────────────────
Overshoots too much       | K2 too low        | Increase K2 +30%
                          | K4 too high       | Decrease K4 -50%
──────────────────────────┼──────────────────┼─────────────────
RMS > 5°                  | Wrong preset      | Try different one
                          | Bad tuning        | Start over
──────────────────────────┼──────────────────┼─────────────────
Works indoor, fails outdoor| Disturbance      | Use OUTDOOR preset
                          | Wind sensitive    | Increase K4
"""

# Print comparison when run
if __name__ == "__main__":
    print(COMPARISON)
    print("\n" + TUNING_WORKFLOW)
    print("\n" + TROUBLESHOOTING)
