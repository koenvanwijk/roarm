from lerobot_robot_roarm import RoarmConfig, Roarm

# Serial connection
config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
)

# Or WiFi
# config = RoarmConfig(
#     roarm_type="roarm_m3",
#     host="192.168.1.100",
# )

robot = Roarm(config)
robot.connect()

print("✓ Connected successfully!")
print("Current joint positions:")
obs = robot.get_observation()
for key, value in obs.items():
    if ".pos" in key:
        print(f"  {key}: {value:.3f}")

robot.disconnect()