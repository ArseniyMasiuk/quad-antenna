import math
import asyncio
import logging
from pymavlink import mavutil

class VehicleControll:
    def __init__(self):
        self.subscribers = {}
        self.heart_beat_timeout = 30 # in seconds

    async def __del__(self):
        self.disconnect()
    
    def connect(self, connection_string):
        logging.info(f'VehicleControll:connect: Connecting to {connection_string}')
        self.vehicle = mavutil.mavlink_connection(connection_string)

        # IMPORTANT: Some flight stacks won't send heartbeats until they receive one
        self.vehicle.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS,
                                        mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)

        logging.info("VehicleControll:connect: Waiting for vehicle heartbeat...")

        heartbeat_message = self.vehicle.wait_heartbeat(blocking=True, timeout=self.heart_beat_timeout)
        if heartbeat_message:
            logging.info(f"VehicleControll:connect: Connected to System {self.vehicle.target_system}, Component {self.vehicle.target_component}")
            self.watch_connection_task = asyncio.create_task(self.listen_to_the_messages())
            return True
        
        logging.error(f'VehicleControll:connect: No heartbeat detected from {connection_string} after {self.heart_beat_timeout} seconds')
        return False

    async def disconnect(self):
        logging.info('VehicleControll:disconnect: Called disconnect')
        if self.watch_connection_task is not None:
            self.watch_connection_task.cancel()
            try:
                await self.watch_connection_task
            except asyncio.CancelledError:
                pass
            self.watch_connection_task = None

        self.vehicle.close()

    def subscribe(self, msg_type, callback):
        """Register subscriber"""
        if msg_type not in self.subscribers:
            self.subscribers[msg_type] = []

        self.subscribers[msg_type].append(callback)

    async def listen_to_the_messages(self):
        """Main cycle of buffer handler"""
        while True:
            msg = self.vehicle.recv_msg()
            if msg:
                # print(f'received message with type: {msg.get_type()}')
                msg_type = msg.get_type()
                if msg_type in self.subscribers:
                    for callback in self.subscribers[msg_type]:
                        self.process_message(msg, callback)
            
            # give some time for the rest of the app
            await asyncio.sleep(0.01)

    def process_message(self, msg, callback):
        """Route message to dedicated handler."""
        message_type = msg.get_type()
        logging.debug(f'VehicleControl:process_message: got message with type {message_type}')

        match message_type:
            case 'VFR_HUD':
                heading = self.handle_heading_message(msg)
                callback(heading)
                return

            case 'LOCAL_POSITION_NED':
                x, y, z = self.handle_possition_NED_message(msg)
                callback(x, y, z)
                return 
            
            case 'ATTITUDE':
                heading = self.handle_attitude_message(msg)
                callback(heading)
                return

            case 'GLOBAL_POSITION_INT' | 'GPS_RAW_INT':
                lat, lon = self.handle_GPS_message(msg)
                callback(lat, lon)
                return

            case _: logging.error(f"VehicleControll Error: No handler for such message {message_type}")

    def handle_GPS_message(self, msg):
         '''This method accepts 'GLOBAL_POSITION_INT' | 'GPS_RAW_INT' messages, the second one is a raw data from GPS'''
        # There should be additional logic here to only fall back to raw data if global possiton is not calculated in UAV
         if msg is None:
            return None
         
         # Both messages use degrees * 1E7
         return msg.lat / 1e7, msg.lon / 1e7

    def handle_heading_message(self, msg):
        """Retrieves current heading from VFR_HUD message."""
        if msg:
            return msg.heading
        
    def handle_possition_NED_message(self, pos_msg):
        if pos_msg:
           return pos_msg.x, pos_msg.y, pos_msg.z
        
        logging.error(f'VehicleControll:handle_possition_NED_message Error: message is invalid')
        return 0, 0, 0

    def handle_attitude_message(self, att_msg):
        if att_msg:
           # Convert Yav from radians to degrees
           yaw_deg = math.degrees(att_msg.yaw)
           # If heading is negative (eg. -1.57 rad), make it 0-360
           if yaw_deg < 0:
              yaw_deg += 360
              
           return yaw_deg
        
        logging.error(f'VehicleControll:handle_attitude_message Error: message is invalid')
        return 0

# ============================================================================================================

    def set_NED_location(self, x, y, z, yaw_deg):
        """
        Відправляє команду на утримання локальної позиції та курсу
        Sends command to hold local possition and heading
        x, y, z - in meters (NED: North, Eash, Down, z must be negative for the height)
        yaw_deg — angle in degrees (0-360)
        """
        self.set_mode("GUIDED")

        # Бітова маска: ігноруємо швидкості (vx, vy, vz) та прискорення
        # 0b0000 10 111 111 000 (позиція + yaw)
        # Binary: 0b0000101111111000 => Decimal: 3064
        type_mask = (
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
        )

        self.vehicle.mav.set_position_target_local_ned_send(
            0,                              # time_boot_ms (не використовується)
            self.vehicle.target_system,       # target_system
            self.vehicle.target_component,    # target_component
            mavutil.mavlink.MAV_FRAME_LOCAL_NED, # Система координат (від вашого опт. модуля)
            type_mask,
            x, y, z,                        # Позиція в метрах
            0, 0, 0,                        # Швидкість (ігнорується маскою)
            0, 0, 0,                        # Прискорення (ігнорується маскою)
            math.radians(yaw_deg),          # Yaw в радіанах
            0                               # Yaw Rate (ігнорується маскою)
        )

    def get_vehicle_modes(self):
        return self.vehicle.mode_mapping().keys()
    
    def set_mode(self, mode):
        if mode not in self.vehicle.mode_mapping() :
            logging.error(f'VehicleControll:set_mode: Mode \'{mode}\' does not exist.')
            return
    
        self.vehicle.mav.set_mode_send(self.vehicle.target_system,
                                  mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                                  self.vehicle.mode_mapping()[mode])
        
        logging.debug(f'VehicleControll:set_mode: Set mode ({mode}) message sent')
