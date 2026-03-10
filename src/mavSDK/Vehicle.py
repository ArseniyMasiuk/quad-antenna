from mavsdk import System
import asyncio

class Vehicle:
    def __init__(self):
        self.drone = System()
        self.lat = 49.84814986011828
        self.lon = 24.03920928224038
        self.is_connected = False

        self.watch_connection_task = None
        self.watch_gps_task = None

    async def connect(self, connection_string = 'tcp://127.0.0.1:5762'):
        print("Connecting to MAVLink...")
        if(self.drone is None):
            self.drone = System()

        await self.drone.connect(system_address=connection_string)

        self.watch_connection_task = asyncio.create_task(self.watch_connection())
        self.watch_gps_task = asyncio.create_task(self.watch_gps())

    async def disconnect(self):
        await self.close_task(self.watch_connection_task)
        await self.close_task(self.watch_gps_task)

        self.drone = None
        self.is_connected = False

        self.lat = 49.84814986011828
        self.lon = 24.03920928224038
        self.is_connected = False

    async def close_task(self, task):
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            task = None

    async def watch_gps(self):
        try:
            async for pos in self.drone.telemetry.position():
                self.lat = pos.latitude_deg
                self.lon = pos.longitude_deg
        except Exception as e:
            print(f"Telemetry error: {e}")

    async def watch_connection(self):
        async for state in self.drone.core.connection_state():
            self.is_connected = state.is_connected
