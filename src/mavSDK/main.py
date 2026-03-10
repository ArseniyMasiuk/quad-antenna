import asyncio
from nicegui import ui
from Vehicle import Vehicle

is_connected = False

vehicle = Vehicle()

def log(message):
     ui.notify(message)
     print(message)

class GUIApp:
    def __init__(self):
        self.map_view = None
        self.connection = {'proto': None, 'ip': None, 'port': None}
        self.button_connect = None
        self.marker_drone = None

    def buidl_ui(self):
        ui.label('MAVLink Quad-Tracker').classes('text-h4 q-ma-md')

        # connetion 
        with ui.row().classes('w-full items-center gap-4'):
            # Label передається як іменований аргумент
            self.connection['proto'] = ui.select(['tcp', 'udp'], label='Protocol', value='tcp').classes('w-32')
            self.connection['ip'] = ui.input(label='IP Address', placeholder='10.1.1.50').classes('flex-grow')
            self.connection['port'] = ui.input(label='Port', placeholder='14550').props('mask="#####"').classes('w-24')

            self.button_connect = ui.button('Connect', on_click=self.toggle_connection).props('elevated')

        # Map
        self.map_view = ui.leaflet(center=(vehicle.lat, vehicle.lon), zoom=13, ).classes('w-full h-150')
        self.marker_drone = self.map_view.marker(latlng=(vehicle.lat, vehicle.lon))
        ui.timer(0.2, self.update_map)

    def update_map(self):
        self.map_view.set_center((vehicle.lat, vehicle.lon))
        if self.marker_drone:
            self.marker_drone.move(vehicle.lat, vehicle.lon)

    async def toggle_connection(self):
        global is_connected
        if not is_connected:
            asyncio.get_event_loop().create_task(vehicle.connect(f"{self.connection['proto'].value}://{self.connection['ip'].value}:{self.connection['port'].value}"))
            log(f'Connecting via {self.connection['proto'].value} to {self.connection['ip'].value}:{self.connection['port'].value}')
            is_connected = True
            self.button_connect.set_text('Disconnect')
            self.button_connect.props('color=red')
        else:
            await vehicle.disconnect()
            is_connected = False
            self.button_connect.set_text('Connect')
            self.button_connect.props('color=green')


@ui.page('/')
def main_page():
    ui = GUIApp()
    ui.buidl_ui()

ui.run(title="Quad Antenna", port=8080)
