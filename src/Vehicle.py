import logging
from vehicleControll import VehicleControll

class Vehicle:
    def __init__(self):
        self.lat = 49.84814986011828
        self.lon = 24.03920928224038
        self.heading = 0
        self.is_connected = False
        self.local_NED_x = 0
        self.local_NED_y = 0
        self.local_NED_z = 0

    def connect(self, connection_string):
        if self.is_connected:
            logging.warning('Vehicle:connect: There is already vehicle connected')
            return True
        
        logging.info(f"Connecting to MAVLink with route : {connection_string}...")
        self.drone = VehicleControll()
        connection_result = self.drone.connect(connection_string)
        if connection_result:
            self.is_connected = True
            self.drone.subscribe('VFR_HUD', self.watch_heading_callback)
            self.drone.subscribe('GLOBAL_POSITION_INT', self.watch_gps_callback)
            self.drone.subscribe('LOCAL_POSITION_NED', self.watch_NED_callback)

            logging.info('Vehicle:connect: Successfully connected to the vehicle')
            return True
        
        logging.error(f"Vehicle:connect: Connection failed")
        return False

    async def disconnect(self):
        await self.drone.disconnect()
        self.drone = None
        self.is_connected = False

        self.lat = 49.84814986011828
        self.lon = 24.03920928224038

    def watch_heading_callback(self, heading):
            self.heading = heading

    def watch_gps_callback(self, lat, lon):
                self.lat = lat
                self.lon = lon

    def watch_NED_callback(self, x, y, z):
          self.local_NED_x = x
          self.local_NED_y = y
          self.local_NED_z = z

          logging.debug(f'Vehicle:watch_NED_callback: Local NED possiotion: x: {self.local_NED_x}, y: {self.local_NED_y}, z: {self.local_NED_z}')

    def set_heading(self, new_heading):
          self.drone.set_NED_location(self.local_NED_x, self.local_NED_y, self.local_NED_z, new_heading)