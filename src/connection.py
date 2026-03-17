from nicegui import ui
import logging
from vehicle import Vehicle

class Connection:
    def __init__(self):
        self.proto = 'tcp'
        self.ip = '127.0.0.1'
        self.port = '5762'

        self.is_connected = False
        self.status_badge = None

        self.vehicle = Vehicle()

    @ui.refreshable
    def add_connection_ui_row(self):
        with ui.row().classes('w-full items-center gap-4'):
            # Badge
            color = 'green' if self.is_connected else 'red'
            label = 'Connected' if self.is_connected else 'Waiting...'
            ui.badge(label, color=color)

            # Inputs
            ui.select(['tcp', 'udp', 'tcpin', 'udpin']).bind_value(self, 'proto').classes('w-32')
            ui.input(label='IP').bind_value(self, 'ip').classes('flex-grow')
            ui.input(label='Port').bind_value(self, 'port').classes('w-24')

            # Button
            btn_label = 'Disconnect' if self.is_connected else 'Connect'
            btn_color = 'red' if self.is_connected else 'green'
            
            ui.button(btn_label, color=btn_color, 
                      on_click=self.toggle_connection)
            
    async def toggle_connection(self):
        if self.is_connected:
            logging.info('Connection:toggle_connect: disconnecting')
            await self.vehicle.disconnect()
            self.is_connected = False
        else:
            logging.info('Connection:Toggle_connect: connecting')
            conn_str = f"{self.proto}:{self.ip}:{self.port}"
            self.is_connected = self.vehicle.connect(conn_str)
        
        self.add_connection_ui_row.refresh()