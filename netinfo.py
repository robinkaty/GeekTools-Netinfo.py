#!/usr/bin/env python3


import re
import subprocess
import socket
import psutil
from ipaddress import IPv4Network
import time
import sys


# Function to convert hexadecimal netmask to CIDR notation
def hex_to_cidr(hex_netmask):
    binary_netmask = bin(int(hex_netmask, 16))[2:].zfill(32)
    netmask_length = sum(1 for bit in binary_netmask if bit == "1")
    return netmask_length


# Function to get interface throughput
def get_interface_throughput(interface):
    io_counters = psutil.net_io_counters(pernic=True)
    # Remove the asterisk from the interface name if it exists
    interface_name = interface.rstrip("*")
    return (
        io_counters[interface_name].bytes_recv,
        io_counters[interface_name].bytes_sent,
    )


# Run ifconfig command and capture output
output = subprocess.check_output(["ifconfig"]).decode("utf-8")

# Run gethost command
myHostName = socket.gethostname()

print("Hostname : {}".format(myHostName.upper()))

# Get the default interface using route command
route_output = subprocess.run(
    ["route", "get", "0.0.0.0"], capture_output=True, text=True
)
default_interface_match = re.search(r"interface: (\S+)", route_output.stdout)
default_interface = (
    default_interface_match.group(1) if default_interface_match else None
)

# Define regex patterns to extract interface names, IP addresses, and netmasks
interface_pattern = r"^([^\s:]+):"
ip_pattern = r"inet (\d+\.\d+\.\d+\.\d+)"
netmask_pattern = r"netmask (\S+)"

# Find all interface sections
interface_sections = re.split(r"(?=^\w)", output, flags=re.MULTILINE)

# Collect initial interface throughput readings
initial_io_counters = {}
for interface in psutil.net_io_counters(pernic=True).keys():
    initial_io_counters[interface] = psutil.net_io_counters(pernic=True)[interface]

# Store interface information
interface_info = {}

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
        # Print the IP address and netmask combined, and interface name
        for ip, netmask in zip(ip_addresses, netmasks):
            netmask_length = hex_to_cidr(netmask)
            ip_netmask = ip + "/" + str(netmask_length)
            interface_info[interface_name] = {"ip_netmask": ip_netmask}

# Wait for a moment
time.sleep(1)

# Collect final interface throughput readings
final_io_counters = {}
for interface in psutil.net_io_counters(pernic=True).keys():
    final_io_counters[interface] = psutil.net_io_counters(pernic=True)[interface]

# Calculate current throughput rates for each interface
rates = {}
for interface in initial_io_counters:
    recv_bytes = int(
        final_io_counters[interface].bytes_recv
        - initial_io_counters[interface].bytes_recv
    )
    sent_bytes = int(
        final_io_counters[interface].bytes_sent
        - initial_io_counters[interface].bytes_sent
    )
    # rates[interface] = ( (recv_bytes * 8 ) / 1024**2, (sent_bytes * 8) / 1024**2 ) #Mbps
    rates[interface] = ((recv_bytes * 8) / 1024**1, (sent_bytes * 8) / 1024**1)  # Kbps


# Print final interface information with throughput rates
for interface_name in interface_info:
    rx_rate = (
        rates[interface_name.rstrip("*")][0]
        if interface_name.rstrip("*") in rates
        else 0
    )
    tx_rate = (
        rates[interface_name.rstrip("*")][1]
        if interface_name.rstrip("*") in rates
        else 0
    )
    rx_rate = int(rx_rate)
    tx_rate = int(tx_rate)
    print(
        f"Interface: {interface_name:<10} IP: {interface_info[interface_name]['ip_netmask']:<15}  RX/TX Rate Kbps: {rx_rate:8,} | {tx_rate:<8,} "
    )
sys.exit(0)  # Return 0 to the operating system upon exit
