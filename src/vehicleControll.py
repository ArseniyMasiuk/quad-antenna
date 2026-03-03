import math
from pymavlink import mavutil

class VehicleControll:
    def __init__(self, connection_string):
        print(f'Connecting to {connection_string}')
        self.vehicle = mavutil.mavlink_connection(connection_string)

        print("Waiting for vehicle heartbeat...")
        self.vehicle.wait_heartbeat()
        print(f"Connected to System {self.vehicle.target_system}, Component {self.vehicle.target_component}")
    
    def __del__(self):
        self.vehicle.close()
    def get_heading(self):
        """Retrieves current heading from VFR_HUD message."""
        msg = self.vehicle.recv_match(type='VFR_HUD', blocking=True, timeout=1.0)
        if msg:
            # Use \r to update the same line in the terminal
            print(f"Current Heading: {msg.heading}°  (Press Ctrl+C to enter new heading)", end='\r')

    def get_NED_data(self):
        # Get possition data
        pos_msg = self.vehicle.recv_match(type='LOCAL_POSITION_NED', blocking=True)
        # Get heading data
        att_msg = self.vehicle.recv_match(type='ATTITUDE', blocking=True)

        if pos_msg and att_msg:
           # Convert Yav from radians to degrees
           yaw_deg = math.degrees(att_msg.yaw)
           # If heading is negative (eg. -1.57 rad), make it 0-360
           if yaw_deg < 0:
              yaw_deg += 360
              
           print(f"NED Pos: X={pos_msg.x:.2f}m (N), Y={pos_msg.y:.2f}m (E), Z={pos_msg.z:.2f}m (D), Heading: {yaw_deg:.1f}°", end='\r')

    def get_vehicle_modes(self):
        return self.vehicle.mode_mapping().keys()
    
    def set_heading(self, heading):
        """
        Sends a yaw command. 
        Note: Requires GUIDED mode for Copters to execute.
        """
        # Parameters: angle (deg), speed (deg/s), direction (1=CW, -1=CCW), type (0=abs, 1=rel)
        self.vehicle.mav.command_long_send(
            self.vehicle.target_system, self.vehicle.target_component,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,          # confirmation
            heading,    # param 1: target angle
            0,          # param 2: speed (0 = default)
            1,          # param 3: direction (1 for clockwise)
            0,          # param 4: 0 = absolute angle
            0, 0, 0     # param 5-7: unused
        )
        print(f"\n--- Heading command ({heading}°) sent ---")

    def set_local_target(self, x, y, z, yaw_deg):
        """
        Відправляє команду на утримання локальної позиції та курсу
        x, y, z — в метрах (NED: North, East, Down. z має бути від'ємним для висоти)
        yaw_deg — кут у градусах (0-360)
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



    def set_mode(self, mode):
        if mode not in self.vehicle.mode_mapping() :
            print(f'Mode \'{mode}\' does not exist.')
            return
    
        self.vehicle.mav.set_mode_send(self.vehicle.target_system,
                                  mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                                  self.vehicle.mode_mapping()[mode])
        
        print(f"\n--- Set mode ({mode}) message sent ---")
