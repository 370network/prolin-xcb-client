from adb import adb_commands
from adb import sign_m2crypto
import sys

queue = list()

# Connect to the device
device = adb_commands.AdbCommands()
device.ConnectDevice(port_path=None, serial="192.168.43.168:5555")

if sys.argv[1] == 'ls':
	root = device.List(sys.argv[2])

	for i in root:
		print(i[0].decode('utf-8') + ' Perm: ' + str(oct(i[1])) + ' Size: ' + str(i[2]))

if sys.argv[1] == 'download':
	root = device.Pull(sys.argv[2], sys.argv[2].replace('/', '_'))
	print(root)

if sys.argv[1] == 'upload':
	root = device.Push(sys.argv[2], sys.argv[3])
	#root = device.Push(sys.argv[2], "/opt/testbin")

	print(root)
