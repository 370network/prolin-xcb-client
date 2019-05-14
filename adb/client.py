from adb import adb_commands
from adb import sign_m2crypto


# Connect to the device
device = adb_commands.AdbCommands()
device.ConnectDevice(port_path=Non, serial="192.168.43.100")
device.Stat('/tmp')