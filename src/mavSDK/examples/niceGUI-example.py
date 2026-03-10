import asyncio
from nicegui import app, ui
from mavsdk import System

class TelemetryApp:
    def __init__(self):
        self.drone = System()
        self.lat = 50.45  # Початкові координати (Київ для прикладу)
        self.lon = 30.52
        self.is_connected = False

    async def start_mavsdk(self):
        """Ця функція тепер запускається автоматично при старті додатка"""
        print("Підключення до MAVLink...")
        # Спробуйте змінити адресу на "udp://:14540" для SITL або вашу конкретну
        await self.drone.connect(system_address="tcp://127.0.0.1:5762")
        
        # Запускаємо моніторинг статусу
        asyncio.create_task(self.watch_connection())
        
        # Стрімінг GPS
        try:
            async for pos in self.drone.telemetry.position():
                self.lat = pos.latitude_deg
                self.lon = pos.longitude_deg
        except Exception as e:
            print(f"Помилка телеметрії: {e}")

    async def watch_connection(self):
        async for state in self.drone.core.connection_state():
            self.is_connected = state.is_connected
            print(f"Статус зв'язку: {self.is_connected}")

# Екземпляр логіки
telemetry = TelemetryApp()

# --- РЕЄСТРАЦІЯ ФОНОВОЇ ЗАДАЧІ ---
app.on_startup(telemetry.start_mavsdk)

@ui.page('/')
def main_page():
    ui.label('MAVLink Tracker').classes('text-h4 q-ma-md')
    
    with ui.row().classes('items-center q-ma-md'):
        status_badge = ui.badge('Waiting...')
        
        def update_status():
            status_badge.text = 'Connected' if telemetry.is_connected else 'Waiting...'
            color = 'green' if telemetry.is_connected else 'red'
            status_badge.props(f'color={color}')
        
        ui.timer(0.5, update_status)

    # Карта
    map_view = ui.leaflet(center=(telemetry.lat, telemetry.lon), zoom=13).classes('w-full h-150')
    marker = map_view.marker(latlng=(telemetry.lat, telemetry.lon))

    def update_map():
        if telemetry.is_connected:
           marker.move(telemetry.lat, telemetry.lon)
           map_view.set_center((telemetry.lat, telemetry.lon)) # за бажанням

    ui.timer(0.2, update_map)

    # Вивід текстових координат для перевірки
    with ui.row().classes('q-ma-md'):
        ui.label().bind_text_from(telemetry, 'lat', backward=lambda x: f'Lat: {x:.6f}')
        ui.label().bind_text_from(telemetry, 'lon', backward=lambda x: f'Lon: {x:.6f}')

ui.run(title="Drone Map", port=8080)
