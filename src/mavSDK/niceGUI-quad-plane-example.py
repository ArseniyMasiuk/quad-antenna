import asyncio
import math
from nicegui import ui
from mavsdk import System
from mavsdk.offboard import PositionNedYaw

# Налаштування адрес
PLANE_ADDR = "udpin://10.1.1.50:14550"
DRONE_ADDR = "udpin://10.1.1.51:14551"

class DroneApp:
    def __init__(self):
        self.plane = System()
        self.drone = System()
        self.plane_pos = {"lat": 0.0, "lon": 0.0}
        self.drone_pos = {"lat": 0.0, "lon": 0.0}
        self.is_following = False
        self.azimuth = 0.0

    def calc_azimuth(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        d_lon = lon2 - lon1
        y = math.sin(d_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    async def connect_systems(self):
        await self.plane.connect(system_address=PLANE_ADDR)
        await self.drone.connect(system_address=DRONE_ADDR)
        # Запускаємо фонові задачі оновлення координат
        asyncio.create_task(self.update_plane_telemetry())
        asyncio.create_task(self.update_drone_telemetry())
        asyncio.create_task(self.control_loop())

    async def update_plane_telemetry(self):
        async for pos in self.plane.telemetry.position():
            self.plane_pos = {"lat": pos.latitude_deg, "lon": pos.longitude_deg}

    async def update_drone_telemetry(self):
        async for pos in self.drone.telemetry.position():
            self.drone_pos = {"lat": pos.latitude_deg, "lon": pos.longitude_deg}

    async def control_loop(self):
        while True:
            if self.is_following:
                self.azimuth = self.calc_azimuth(
                    self.drone_pos["lat"], self.drone_pos["lon"],
                    self.plane_pos["lat"], self.plane_pos["lon"]
                )
                # Отримуємо поточний NED для утримання висоти/позиції
                async for ned in self.drone.telemetry.position_velocity_ned():
                    p = ned.position
                    try:
                        await self.drone.offboard.set_position_ned(
                            PositionNedYaw(p.north_m, p.east_m, p.down_m, float(self.azimuth))
                        )
                    except: pass # Якщо Offboard не активний
                    break
            await asyncio.sleep(0.2)

app_logic = DroneApp()

@ui.page('/')
async def main_page():
    # Стилізація
    ui.colors(primary="#3677B8")
    
    with ui.header().classes('justify-between items-center'):
        ui.label('MAVSDK Follower').classes('text-xl font-bold')
        ui.label().bind_text_from(app_logic, 'azimuth', backward=lambda x: f'Azimuth: {x:.1f}°')

    with ui.row().classes('w-full no-wrap'):
        # Панель керування
        with ui.column().classes('w-1/4 p-4 gap-4'):
            ui.button('ARM DRONE', color='orange', on_click=lambda: app_logic.drone.action.arm()).classes('w-full')
            
            ui.separator()
            
            follow_btn = ui.button('START FOLLOWING', color='green', 
                                   on_click=lambda: setattr(app_logic, 'is_following', not app_logic.is_following))
            follow_btn.bind_text_from(app_logic, 'is_following', backward=lambda x: 'STOP FOLLOWING' if x else 'START FOLLOWING')
            follow_btn.bind_color_from(app_logic, 'is_following', backward=lambda x: 'red' if x else 'green')

            ui.button('LAND', color='blue-grey', on_click=lambda: app_logic.drone.action.land()).classes('w-full')

        # Карта
        map_view = ui.leaflet(center=(0, 0), zoom=2).classes('w-3/4 h-[600px]')
        
        # Маркери
        plane_marker = map_view.marker(latlng=(0, 0))
        drone_marker = map_view.marker(latlng=(0, 0))

        # Оновлення UI
        def update_ui():
            plane_marker.set_latlng((app_logic.plane_pos["lat"], app_logic.plane_pos["lon"]))
            drone_marker.set_latlng((app_logic.drone_pos["lat"], app_logic.drone_pos["lon"]))
            # Центруємо карту на дроні, якщо є координати
            if app_logic.drone_pos["lat"] != 0:
                map_view.set_center((app_logic.drone_pos["lat"], app_logic.drone_pos["lon"]))

        ui.timer(0.5, update_ui)

# Запуск MAVSDK та NiceGUI
asyncio.get_event_loop().create_task(app_logic.connect_systems())
ui.run(title="MavSDK Control", port=8080)
