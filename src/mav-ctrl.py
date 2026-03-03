import sys
from vehicleControll import VehicleControll

#=========================== Setting up connection ==============================
# Use 'udpin' to allow bidirectional communication. 
# 14550 is the standard port Mission Planner uses to forward MAVLink.
connection_string = 'tcp:192.168.0.188:5762'
vehicle = VehicleControll(connection_string)

#==================================================================================

def ConsoleUI_SetHeading():
    try:
        new_heading = float(input("Enter new heading (0-360): "))
        x = int(input("Enter new X coordinate: "))
        y = int(input("Enter new Y coordinate: "))
        alt = int(input("Enter altitude: "))

        vehicle.set_local_target(x, y, alt*-1, new_heading)
        print("Returning to monitoring...")
    except ValueError:
        print("Invalid input. Please enter a number.")
    
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
        print("0: Exit")


        action:int = int(input("What to do: "))

        match action:
            case 0: sys.exit(0)
            case 1: ConsoleUI_SetHeading()
            case 2: ConsoleUI_SetMode()

            case _: print("Hugh? Granny cant hear!")
            
        main() # Restart the loop


if __name__ == "__main__":
    main()

