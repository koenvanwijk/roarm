from roarm_sdk.roarm import roarm
#roarm1 = roarm(roarm_type="roarm_m3", host="192.168.86.43")
#roarm2 = roarm(roarm_type="roarm_m3", host="192.168.86.55")
roarm1 = roarm(roarm_type="roarm_m3", port="/dev/ttyUSB0", baudrate=115200)
roarm2 = roarm(roarm_type="roarm_m3", port="/dev/ttyUSB1", baudrate=115200)
roarm = roarm1  # Change to roarm2 to use serial connection
import threading
import time

def teleop(roarm1, roarm2):
    input_thread = threading.Thread(target=roarm1.listen_for_input)
    input_thread.daemon = True 
    input_thread.start()
    roarm1.torque_set(cmd=0)
    while not roarm1.stop_flag: 
        roarm2.joints_angle_ctrl(angles=roarm1.joints_angle_get(), speed=1000, acc=50)
        time.sleep(0.1)
    roarm1.stop_flag = False  # Reset stop flag for future use

def main():
    cmd = 0
    joint = 1
    radian = 1.5708
    angle = 90
    gripper_radian = 1.5708
    gripper_angle = 0    
    speed = 1000
    acc = 50
    
    radians= [0, 0, 3.1415926, -1.5708, 0, 0]
    angles= [0, 0, 180, -90, 0, 0]
    filename = "drag_teach.json"
    pose = [235, 0, 234, 0, 0, 0]
    ssid = "Garage"
    password = "Don12345!"
  
    commands = {
        "0": lambda: roarm.move_init(),
        "1": lambda: roarm.torque_set(cmd=cmd),
        "2": lambda: roarm.joint_radian_ctrl(joint=joint, radian=radian, speed=speed, acc=acc),
        "3": lambda: roarm.joints_radian_ctrl(radians=radians, speed=speed, acc=acc),
        "4": lambda: print(roarm.joints_radian_get()),
        "5": lambda: roarm.joint_angle_ctrl(joint=joint, angle=angle, speed=speed, acc=acc),
        "6": lambda: roarm.joints_angle_ctrl(angles=angles, speed=speed, acc=acc),
        "7": lambda: print(roarm.joints_angle_get()),
        "8": lambda: roarm.drag_teach_start(filename=filename),
        "9": lambda: roarm.drag_teach_replay(filename=filename),
        "w": lambda: roarm.gripper_radian_ctrl(radian=gripper_radian, speed=speed, acc=acc),
        "a": lambda: print(roarm.gripper_radian_get()),
        "s": lambda: roarm.gripper_angle_ctrl(angle=gripper_angle, speed=speed, acc=acc),
        "d": lambda: print(roarm.gripper_angle_get()),
        "i": lambda: roarm.pose_ctrl(pose=pose),
        "j": lambda: print(roarm.pose_get()),
        "k": lambda: roarm.ap_set(ssid=ssid, password=password),
        "t": lambda: teleop(roarm1, roarm2),
        "q": lambda: exit()
    }

    while True:
        print("\nChoose an option:")
        print("0. Move to init position")
        print("1. Set torque release")
        print("2. Joint radian control")
        print("3. Joints radian control")
        print("4. Joints radian get")
        print("5. Joint angle control")
        print("6. Joints angle control")
        print("7. Joints angle get")
        print("8. Drag teach start")
        print("9. Drag teach replay")
        print("w. Gripper radian control")
        print("a. Gripper radian get")
        print("s. Gripper angle control")
        print("d. Gripper angle get")
        print("i. Pose control")
        print("j. Pose get")
        print("k. AP set")
        print("t. Teleoperation")
        print("q. Quit")
        choice = input("Enter your choice: ").strip()
        
        if choice in commands:
            roarm = roarm1
            commands[choice]()
            roarm = roarm2
            commands[choice]()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
