import asyncio
from nicegui import app, ui
from Vehicle import Vehicle

is_connected = False

vehicle = Vehicle()

def log(message):
     ui.notify(message)
     print(message)


@ui.page('/')
def main_page():
    ui.label('MAVLink Quad-Tracker').classes('text-h4 q-ma-md')

    async def toggle_connection():
        global is_connected
        if not is_connected:
            asyncio.get_event_loop().create_task(vehicle.connect(f"{proto.value}://{ip.value}:{port.value}"))
            log(f'Connecting via {proto.value} to {ip.value}:{port.value}')
            is_connected = True
            btn.set_text('Disconnect')
            btn.props('color=red')
        else:
            await vehicle.disconnect()
            is_connected = False
            btn.set_text('Connect')
            btn.props('color=green')

    with ui.row().classes('w-full items-center gap-4'):
        # Label передається як іменований аргумент
        proto = ui.select(['tcp', 'udp'], label='Protocol', value='tcp').classes('w-32')
        ip = ui.input(label='IP Address', placeholder='10.1.1.50').classes('flex-grow')
        port = ui.input(label='Port', placeholder='14550').props('mask="#####"').classes('w-24')

        btn = ui.button('Connect', on_click=toggle_connection).props('elevated')

    # Карта
    map_view = ui.leaflet(center=(vehicle.lat, vehicle.lon), zoom=13, ).classes('w-full h-150')
    marker = map_view.marker(latlng=(vehicle.lat, vehicle.lon))

    def update_map():
           marker.move(vehicle.lat, vehicle.lon)
           map_view.set_center((vehicle.lat, vehicle.lon))

    ui.timer(0.2, update_map)

ui.run(title="Quad Antenna", port=8080)
