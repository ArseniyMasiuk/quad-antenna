import threading
import queue
import time
from vehicleControl import VehicleControl
from calculators import calculate_azimuth

quad_connection_string = 'tcp:localhost:5602'
quad_vehicle = VehicleControl(quad_connection_string)

plane_connection_string = 'tcp:localhost:5602'
plane_vehicle = VehicleControl(plane_connection_string)

# Об'єкти для зберігання останніх отриманих даних (Thread-safe)
# Можна використовувати прості змінні з Lock або Queue
drone_data = {"ned": None, "gps": None}
plane_data = {"gps": None}
data_lock = threading.Lock()

# 1. Процес Дрона (Читання NED/GPS + Відправка команд)
def drone_worker(command_queue):
    quad_vehicle.set_mode("GUIDED")
    
    while True:
        # ТУТ: Читання з Mavlink (NED та GPS)
        new_ned = quad_vehicle.get_NED_data()
        new_gps = quad_vehicle.get_GPS_coords()
        
        with data_lock:
            drone_data["ned"] = new_ned
            drone_data["gps"] = new_gps
        
        # ТУТ: Якщо в черзі є нова команда від основного процесу — відправляємо
        if not command_queue.empty():
            new_heading = command_queue.get()
            x, y , z, old_heading  = drone_data["ned"]
            quad_vehicle.set_local_target(x, y, z, new_heading)
        
# 2. Процес Літака (Тільки GPS)
def plane_worker():
    while True:
        # ТУТ: Читання GPS з Mavlink літака
        new_gps = quad_vehicle.get_GPS_coords()
        
        with data_lock:
            plane_data["gps"] = new_gps

# 3. Основний процес (Обчислення та керування)
def main_logic(command_queue):
    while True:
        with data_lock:
            lat1, lon1 = drone_data["gps"]
            lat2, lon2 = plane_data["gps"]
            d_ned = drone_data["ned"]

            new_heading = calculate_azimuth(lat1, lon1, lat2, lon2)
            
            print(f"[MATH] Азимут: {new_heading}. Відправка на дрон з NED {d_ned}")
            command_queue.put(new_heading)
        
        time.sleep(0.5) # Частота оновлення команд

def start_system():
    command_queue = queue.Queue()

    t1 = threading.Thread(target=drone_worker, daemon=True)
    t2 = threading.Thread(target=plane_worker, daemon=True)
    t3 = threading.Thread(target=main_logic, args=(command_queue,), daemon=True)

    t1.start()
    t2.start()
    t3.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    start_system()
