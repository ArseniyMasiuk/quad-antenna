import sys
import threading
from vehicleControll import VehicleControll

#=========================== Setting up connection ==============================
# Use 'udpin' to allow bidirectional communication. 
# 14550 is the standard port Mission Planner uses to forward MAVLink.
connection_string = 'udp:172.17.218.13:14777'
vehicle = VehicleControll(connection_string)

#==================================================================================

def ConsoleUI_SetHeading():
    try:
        val = input("Enter new heading (0-360): ")
        new_heading = float(val)
        vehicle.set_local_target(0, 0, -100, new_heading)
        print("Returning to monitoring...")
    except ValueError:
        print("Invalid input. Please enter a number.")
        main()
    
def ConsoleUI_SetMode():
    print("Awailable modes: ")
    for mode_name in vehicle.get_vehicle_modes():
        print(f"• {mode_name}")

    val = input("Enter new mode: ")
    vehicle.set_mode(val)

#=================================================================================

def main():
    try:
        while True:
            vehicle.get_NED_data()
                       
    except KeyboardInterrupt:
        print("\n" + "-"*30)
        print("1: Set heading")
        print("2: Set mode")

        action:int = int(input("What to do: "))

        match action:
            case 1: ConsoleUI_SetHeading()
            case 2: ConsoleUI_SetMode()
            case _: print("Hugh? Granny cant hear!")
            
        main() # Restart the loop


if __name__ == "__main__":
    main()

