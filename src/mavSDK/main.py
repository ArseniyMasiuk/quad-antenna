import asyncio
from nicegui import ui
from Vehicle import Vehicle



def log(message):
     ui.notify(message)
     print(message)

class GUIApp:
    def __init__(self):
        self.vehicle = Vehicle()
        self.connection = {'proto': None, 'ip': None, 'port': None}
        self.button_connect = None
        self.button_is_connected = False
        self.status_badge = None

        self.map_view = None
        self.marker_drone = None

        self.current_headin = None
        self.heading_badge = None
        self.new_heading = None
        self.button_set_heading = None

    def buidl_ui(self):
        ui.label('MAVLink Quad-Tracker').classes('text-h4 q-ma-md')

        # connetion 
        with ui.row().classes('w-full items-center gap-4'):
            self.status_badge = ui.badge('Waiting...')
            ui.timer(0.5, self.update_status)

            self.connection['proto'] = ui.select(['tcp', 'udp'], label='Protocol', value='tcp').classes('w-32')
            self.connection['ip'] = ui.input(label='IP Address', placeholder='10.1.1.50').classes('flex-grow')
            self.connection['port'] = ui.input(label='Port', placeholder='14550').props('mask="#####"').classes('w-24')

            self.button_connect = ui.button('Connect', on_click=self.toggle_connection).props('elevated')

        # Map
        self.map_view = ui.leaflet(center=(self.vehicle.lat, self.vehicle.lon), zoom=13, ).classes('w-full h-150')
        self.marker_drone = self.map_view.marker(latlng=(self.vehicle.lat, self.vehicle.lon))
        ui.timer(0.2, self.update_map)

        with ui.row().classes('w-full items-center gap-4'):
             self.heading_badge = ui.badge('Heading: 0')
             ui.timer(0.5, self.update_heading_badge)

             self.new_heading = ui.input(label='New heading').classes('flex-grow')
             self.button_set_heading = ui.button('Set new heading', on_click=self.button_update_heading).props('elevated')

    def update_heading_badge(self):
            self.heading_badge.text = f'Heading: {int(self.vehicle.heading)}'

    async def button_update_heading(self):
        self.vehicle.set_heading_ned(self.new_heading.value)
        log(f'New heading set to: {self.new_heading.value}')

    def update_map(self):
        self.map_view.set_center((self.vehicle.lat, self.vehicle.lon))
        if self.marker_drone:
            self.marker_drone.move(self.vehicle.lat, self.vehicle.lon)

    async def toggle_connection(self):
        if not self.button_is_connected:
            asyncio.get_event_loop().create_task(self.vehicle.connect(f"{self.connection['proto'].value}://{self.connection['ip'].value}:{self.connection['port'].value}"))
            log(f'Connecting via {self.connection['proto'].value} to {self.connection['ip'].value}:{self.connection['port'].value}')
            self.button_is_connected = True
            self.button_connect.set_text('Disconnect')
            self.button_connect.props('color=red')
        else:
            await self.vehicle.disconnect()
            self.button_is_connected = False
            self.button_connect.set_text('Connect')
            self.button_connect.props('color=green')

    def update_status(self):
            self.status_badge.text = 'Connected' if self.vehicle.is_connected else 'Waiting...'
            color = 'green' if self.vehicle.is_connected else 'red'
            self.status_badge.props(f'color={color}')

@ui.page('/')
def main_page():
    ui = GUIApp()
    ui.buidl_ui()

ui.run(title="Quad Antenna", port=8080)
