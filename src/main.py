import asyncio
import logging
from nicegui import ui
from calculators import calculate_azimuth
from connection import Connection

logging.basicConfig(level=logging.INFO , format='%(levelname)s: %(message)s', force=True)

def log(message):
     ui.notify(message)
     print(message)


class GUIApp:
    def __init__(self):
        self.drone_connection = Connection()
        self.plane_connection = Connection()

        self.map_view = None
        self.marker_drone = None
        self.marker_plane = None

        self.heading_badge = None
        self.new_heading = None
        self.button_set_heading = None

        self.start_tracking_button = None

        self.tracking_task = None

    def build_ui(self):
        ui.label('MAVLink Quad-Tracker').classes('text-h4 q-ma-md')

        # Adding connections fields
        with ui.expansion('Connections', icon='wifi').classes('w-full border rounded'):
            with ui.column().classes('p-2 gap-1 w-full'):
                self.drone_connection.add_connection_ui_row()

                self.plane_connection.add_connection_ui_row()

                self.start_tracking_button = ui.button('Start tracking', on_click=self.start_tracking).props('elevated')

        # Map
        self.map_view = ui.leaflet(center=(self.drone_connection.vehicle.lat, self.drone_connection.vehicle.lon), zoom=13, ).classes('w-full h-150')
        ui.timer(0.2, self.update_map)

        self.marker_drone = self.map_view.marker(latlng=(self.drone_connection.vehicle.lat, self.drone_connection.vehicle.lon))
        self.marker_plane = self.map_view.marker(latlng=(self.plane_connection.vehicle.lat, self.plane_connection.vehicle.lon))

        with ui.row().classes('w-full items-center gap-4'):
             self.heading_badge = ui.badge('Heading: 0')
             ui.timer(0.5, self.update_heading_badge)

             self.new_heading = ui.input(label='New heading').classes('flex-grow')
             self.button_set_heading = ui.button('Set new heading', on_click=self.button_update_heading).props('elevated')
    

    async def tracking_task_method(self):
        while True:
            new_heading = calculate_azimuth(self.drone_connection.vehicle.lat,
                                            self.drone_connection.vehicle.lon,
                                            self.plane_connection.vehicle.lat,
                                            self.plane_connection.vehicle.lon)
        
            # print(f'Calculated heading: {new_heading} with ')
            # print(f' quad lat: {self.drone_connection.vehicle.lat} lon: {self.drone_connection.vehicle.lon} ')
            # print(f'plane lat: {self.plane_connection.vehicle.lat} lon: {self.plane_connection.vehicle.lon}')

            self.drone_connection.vehicle.set_heading(new_heading)
            await asyncio.sleep(0.2)

    async def start_tracking(self):
        if self.tracking_task is None:
            self.tracking_task = asyncio.create_task(self.tracking_task_method())
            self.start_tracking_button.set_text('Stop tracking')
            self.start_tracking_button.props('color=red')
        else:
            self.start_tracking_button.set_text('Start tracking')
            self.start_tracking_button.props('color=blue')
            self.tracking_task.cancel()
            try:
                await self.tracking_task
            except asyncio.CancelledError:
                pass
            self.tracking_task = None


    def update_heading_badge(self):
            self.heading_badge.text = f'Heading: {int(self.drone_connection.vehicle.heading)}'

    async def button_update_heading(self):
        self.drone_connection.vehicle.set_heading(int(self.new_heading.value))
        log(f'New heading set to: {self.new_heading.value}')

    def update_map(self):
        self.map_view.set_center((self.drone_connection.vehicle.lat, self.drone_connection.vehicle.lon))
        if self.marker_drone:
            self.marker_drone.move(self.drone_connection.vehicle.lat, self.drone_connection.vehicle.lon)

        if self.marker_plane:
            self.marker_plane.move(self.plane_connection.vehicle.lat, self.plane_connection.vehicle.lon)

app = GUIApp()

@ui.page('/')
def main_page():
    app.build_ui()

ui.run(title="Quad Antenna", port=8080)
