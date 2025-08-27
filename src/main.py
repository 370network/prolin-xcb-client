#!/usr/bin/env python3
from xcb_adb import adb_commands
from xcb_adb import sign_m2crypto
import stat
import os
import time
import json
import argparse

def init_device(args):
	device = adb_commands.AdbCommands()
	device.ConnectDevice(
		serial_port=args.serial,
		ip=args.ip,
		default_timeout_ms=args.timeout
	)
	return device

def scandir(path, device):
	files = []
	directories = []
	unknowns = []
	result = device.List(path)
	for i in result[2:]:
		if stat.S_ISDIR(i[1]):
			directories.append(i[0])
		if stat.S_ISREG(i[1]) and ((i[1] & stat.S_IRUSR) or (i[1] & stat.S_IRGRP) or (i[1] & stat.S_IROTH)):
			files.append(i[0])
		else:
			unknowns.append(i[0])
	return files, directories, unknowns

def tree(path, device):
	exclude = ["proc", "sys", "dev"]
	all_files = []
	all_directories = []
	all_unknowns = []
	queue = []
	current = path
	while True:
		files, directories, unknowns = scandir(current, device)
		for file in files:
			all_files.append(current + file.decode('utf-8'))
		for directory in directories:
			all_directories.append(current + directory.decode('utf-8') + '/')
			if directory.decode('utf-8') not in exclude:
				queue.append(current + directory.decode('utf-8') + '/')
		if not queue:
			break
		current = queue.pop()
		#print(current)

	return all_files, all_directories, all_unknowns

def cmd_dump(device, args, extra_args):
	if len(extra_args) < 1:
		print("dump <dump name> [optional:  device path to dump]")
		exit(1)
	name = extra_args[0]
	target = "dumps/" + name + '/'
	device_path = "/"
	if len(extra_args) > 1:
		device_path = extra_args[1]
		if not device_path.endswith("/"):
			device_path += "/"
	print("[+] Listing everything from: {}".format(device_path))
	all_files, all_directories, all_unknowns = tree(device_path, device)
	print("[+] Writing to local path: {}".format(target))
	if not os.path.exists(target):
		os.makedirs(target, exist_ok=True)
	if not os.path.isdir(target):
		print("Target is not a directory")
		exit(1)
	for dir in all_directories:
		if not os.path.exists(target + dir):
			os.makedirs(target + dir, exist_ok=True)
	print("[+] Pulling all files")
	for file in all_files:
		if not os.path.isfile(target + file):
			time.sleep(1)
			try:
				device.Pull(file, target + file)
				print("[+] Downloading " + file)
			except:
				print("[-] Failed downloading " + file)
				os.remove(target + file)
				# This sucks but...
				device = None
				time.sleep(5)
				device = init_device(args)
	print("[+] Saving lists")
	with open(target + 'files.txt', 'w') as f:
		f.write(json.dumps(all_files))
	with open(target + 'directories.txt', 'w') as f:
		f.write(json.dumps(all_directories))
	with open(target + 'unknowns.txt', 'w') as f:
		f.write(json.dumps(all_unknowns))

def handle_command(args, extra_args):
	device = init_device(args)
	command = args.command
	if command == 'ls':
		if len(extra_args) < 1:
			print("Missing args: ls <device path>")
			exit(1)
		root = device.List(extra_args[0])
		for i in root:
			print(i[0].decode('utf-8') + ' Perm: ' + str(oct(i[1])) + ' Size: ' + str(i[2]))

	elif command == 'pull':
		if len(extra_args) < 1:
			print("Missing args: pull <device source> [optional: local destination]")
			exit(1)
		if len(extra_args) < 2:
			target = extra_args[0].replace('/', '_')
		else:
			target = extra_args[1]
		root = device.Pull(extra_args[0], target)
		print(root)

	elif command == 'push':
		if len(extra_args) < 2:
			print("Missing args: push <local source> <device destination>")
			exit(1)
		root = device.Push(extra_args[0], extra_args[1])
		print(root)

	elif command == 'logcat':
		logcat = device.Logcat(options=extra_args)
		for line in logcat:
			print(line)

	elif command == 'get-state':
		state = device.GetState()
		if state == None:
			print("No state value returned")
		else:
			print("State: '{}'".format(str(state, 'utf-8')))

	elif command == 'forward':
		print("Error: For port forwarding (ie: for gdbserver) use the original XCB client. xcb.exe connect com:COM12; xcb.exe forward tcp:2020 tcp:2020")
		print("The protocol for port forwarding should be ADB compatible. However python-adb doesn't support it as of now")

	elif command == 'dump':
		cmd_dump(device, extra_args)

	else:
		print("Error: Unknown command! {}".format(command))
		exit(1)

	device.Close()
	device = None

def main():
	parser = argparse.ArgumentParser(description='Prolin XCB client')
	parser.add_argument('-s', "--serial", dest="serial", help="Device serial line to use, like /dev/ttyACM0")
	parser.add_argument('-c', "--ip", dest="ip", help="Device network address to connect, like 192.168.43.168:5555")
	parser.add_argument('-t', "--timeout", type=int, default=None, dest="timeout", help="Connection timeout in ms")
	parser.add_argument('-r', "--retry", type=int, default=5, dest="retry", help="How many connections retries to attempt")
	parser.add_argument("command", choices=[
		"ls", "pull", "push", "logcat", "forward",
		"get-state", "dump"
	], help="What command to run")
	args, extra_args = parser.parse_known_args()

	# Load from ENV if any
	if args.ip is None and "PAX_CLIENT_IP" in os.environ:
		args.ip = os.environ["PAX_CLIENT_IP"]
	if args.serial is None and "PAX_CLIENT_SERIAL" in os.environ:
		args.serial = os.environ["PAX_CLIENT_SERIAL"]

	# Handle ip arg
	if args.ip is not None:
		if ":" not in args.ip:
			args.ip += ":5555"

	# Check if any or both are set
	if args.serial is None and args.ip is None:
		print("Error: Please provide serial or network address of device to connect")
		exit(1)
	if args.serial is not None and args.ip is not None:
		print("Error: Please only provide serial or network address to connect, not both")
		exit(1)

	attempts = args.retry
	while True:
		try:
			handle_command(args, extra_args)
			break
		except ConnectionError as e:
			if 0 < attempts:
				print("Got connection error, attempts left: {}".format(attempts))
				attempts -= 1
				device = None
				time.sleep(5)
			else:
				raise e

if __name__ == '__main__':
	main()
