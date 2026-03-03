from pymavlink import mavutil
import time

# 1. Підключення до дрона (змініть порт на ваш, наприклад '/dev/ttyUSB0' або '127.0.0.1:14550')
connection = mavutil.mavlink_connection('udpin:localhost:14550')
connection.wait_heartbeat()
print("Дрон підключений!")

def set_guided_mode():
    """Перемикає дрон у режим GUIDED"""
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        4) # 4 — це номер режиму GUIDED для Copter

def send_local_target(x, y, z, yaw_deg):
    """
    Відправляє команду на утримання локальної позиції та курсу
    x, y, z — в метрах (NED: North, East, Down. z має бути від'ємним для висоти)
    yaw_deg — кут у градусах (0-360)
    """
    import math
    
    # Бітова маска: ігноруємо швидкості (vx, vy, vz) та прискорення
    # 0b0000 10 111 111 000 (позиція + yaw)
    # Binary: 0b0000101111111000 => Decimal: 3064
    type_mask = (
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
        mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
    )

    connection.mav.set_position_target_local_ned_send(
        0,                              # time_boot_ms (не використовується)
        connection.target_system,       # target_system
        connection.target_component,    # target_component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # Система координат (від вашого опт. модуля)
        type_mask,
        x, y, z,                        # Позиція в метрах
        0, 0, 0,                        # Швидкість (ігнорується маскою)
        0, 0, 0,                        # Прискорення (ігнорується маскою)
        math.radians(yaw_deg),          # Yaw в радіанах
        0                               # Yaw Rate (ігнорується маскою)
    )

# --- ПРИКЛАД ВИКОРИСТАННЯ ---

# Переходимо в GUIDED
set_guided_mode()
time.sleep(1)

# 1. Зависаємо в точці 0,0 на висоті 2 метри, ніс на Північ (0°)
print("Зависаємо в точці 0,0, висота 2м, курс 0°")
for _ in range(50): # Надсилаємо команду циклічно для стабільності
    send_local_target(0, 0, -2, 0)
    time.sleep(0.1)

# 2. Змінюємо курс на 90 градусів, залишаючись в тій же точці
print("Змінюємо курс на 90°")
for _ in range(50):
    send_local_target(0, 0, -2, 90)
    time.sleep(0.1)

print("Команду виконано.")
