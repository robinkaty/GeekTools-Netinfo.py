#!/usr/bin/env python3
import re
import subprocess
import socket

# Function to convert hexadecimal netmask to dotted notation
def hex_to_dotted_netmask(hex_netmask):
    binary_netmask = bin(int(hex_netmask, 16))[2:].zfill(32)
    dotted_netmask = ".".join([str(int(binary_netmask[i:i+8], 2)) for i in range(0, 32, 8)])
    return dotted_netmask

# Run ifconfig command and capture output
output = subprocess.check_output(["ifconfig"]).decode("utf-8")

# Run gethost command
myHostName = socket.gethostname()

print("Hostname : {}".format(myHostName.upper()))

# Get the default interface using route command
route_output = subprocess.run(["route", "get", "0.0.0.0"], capture_output=True, text=True)
default_interface_match = re.search(r'interface: (\S+)', route_output.stdout)
default_interface = default_interface_match.group(1) if default_interface_match else None

# Define regex patterns to extract interface names, IP addresses, and netmasks
interface_pattern = r'^([^\s:]+):'
ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
netmask_pattern = r'netmask (\S+)'

# Find all interface sections
interface_sections = re.split(r'(?=^\w)', output, flags=re.MULTILINE)

# Iterate through each interface section
for interface_section in interface_sections:
    # Extract interface name
    interface_match = re.search(interface_pattern, interface_section)
    if interface_match:
        interface_name = interface_match.group(1)
        # Append asterisk to interface name if it's the default interface
        if interface_name == default_interface:
            interface_name += "*"
        # Find all IP addresses and netmasks in the interface section
        ip_addresses = re.findall(ip_pattern, interface_section)
        netmasks = re.findall(netmask_pattern, interface_section)
        # Print the IP address, netmask (in dotted notation), and interface name
        for ip, netmask in zip(ip_addresses, netmasks):
            dotted_netmask = hex_to_dotted_netmask(netmask)
            print("Interface: {:<10} IP: {:<15} Netmask: {:<15}".format(interface_name, ip, dotted_netmask))
