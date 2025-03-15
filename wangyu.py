#Author: https://github.com/Azumi67
import os
import subprocess
import platform
import urllib.request
import yaml
import shutil
import colorama
import io
from colorama import Fore, Style
from time import sleep
import sys
import re
import readline

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")

if os.geteuid() != 0:
    print("\033[91mThis script must be run as root. Please use sudo -i.\033[0m")
    sys.exit(1)

def logo():
    logo_path = "/etc/logo2.sh"
    try:
        subprocess.run(["bash", "-c", logo_path], check=True)
    except subprocess.CalledProcessError as e:
        return e

    return None

BASE_URL = "https://github.com/Azumi67/Wangyu_azumi_UDP/releases/download/cores/"

FILE_NAMES = {
    "amd64": {
        "tinyvpn": "tinyvpn_amd64",
        "udp2raw": "udp2raw_amd64",
        "speederv2": "speederv2_amd64"
    },
    "arm64": {
        "tinyvpn": "tinyvpn_arm64",
        "udp2raw": "udp2raw_arm64",
        "speederv2": "speederv2_arm64"
    }
}

def download_file(file_key, destination):
    arch = platform.architecture()[0]  

    if "64bit" in arch:
        arch = "amd64"
    elif "32bit" in arch:
        arch = "arm"  

    file_name = FILE_NAMES.get(arch, {}).get(file_key)

    if file_name:
        url = f"{BASE_URL}{file_name}"
        temp_destination = destination + "_" + arch  

        if not os.path.exists(destination):  
            print(f"Downloading {file_key} ({file_name})...")
            subprocess.run(["wget", "-q", "--show-progress", url, "-O", temp_destination])
            
            os.rename(temp_destination, destination)

            subprocess.run(["chmod", "+x", destination])

            print(f"Downloaded and renamed to {destination}")
        else:
            print(f"{destination} already exists. Skipping download.")
    else:
        print(f"Error: No file found for {file_key} with architecture {arch}.")

def make_executable(file_path):
    subprocess.run(["chmod", "+x", file_path])

def get_binary_path(component):
    base_component = component.split('_')[0] 

    component_map = {
        "tinyvpn": "tinyvpn",  
        "udp2raw": "udp2raw",
        "speederv2": "speederv2",
    }
    
    binary_key = component_map.get(base_component, base_component) 
    return f"/usr/local/bin/{binary_key}"  


def create_service(name, command):
    binary_path = get_binary_path(name)
    
    if not binary_path or not os.path.exists(binary_path):
        print(f"Error: Binary for {name} does not exist. Skipping service creation.")
        return
    
    service_path = f"/etc/systemd/system/{name}.service"
    
    service_content = f"""[Unit]
Description={name} service

[Service]
ExecStart={binary_path} {command}
Restart=always
User=root
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""
    
    with open(service_path, "w") as f:
        f.write(service_content)
    
    display_notification(f"\n\033[93mCreated {name} service at {service_path}\033[0m")
    
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", name])
    subprocess.run(["systemctl", "restart", name])
    
    display_checkmark(f"\033[92mService {name} started and enabled\033[0m")

def display_checkmark(message):
    print("\u2714 " + message)


def display_error(message):
    print("\u2718 Error: " + message)


def display_notification(message):
    print("\u2728 " + message)

def uninstall_proxy_forwarders():
    os.system("clear")
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRemoving \033[92mForwarder...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "proxyforwarder"
    service_path = f"/etc/systemd/system/{service_name}.service"
    binary_path = "/usr/local/bin/proxyforwarder"
    daemon_service_path = "/etc/systemd/system/proxyforwarder_daemon.service"
    daemon_script_path = "/usr/local/bin/proxyforwarder_daemon.sh"

    try:
        subprocess.run(["systemctl", "stop", service_name], check=True)
        subprocess.run(["systemctl", "disable", service_name], check=True)
    except subprocess.CalledProcessError:
        print(f"\033[91mWarning: Failed to stop or disable {service_name} (might not exist).\033[0m")

    try:
        if os.path.exists(service_path):
            os.remove(service_path)
            display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Service file for {service_name} not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing service file: {e}\033[0m")

    try:
        if os.path.exists(binary_path):
            if os.path.isdir(binary_path):
                shutil.rmtree(binary_path)  
                display_checkmark(f"\033[92mRemoved directory: {binary_path}\033[0m")
            else:
                os.remove(binary_path)  
                display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
        else:
            print("\033[91mWarning: ProxyForwarder directory or binary not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing ProxyForwarder: {e}\033[0m")

    try:
        if os.path.exists(daemon_service_path):
            os.remove(daemon_service_path)
            display_checkmark(f"\033[92mRemoved daemon service file: {daemon_service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon service file '{daemon_service_path}' not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing daemon service file: {e}\033[0m")

    try:
        if os.path.exists(daemon_script_path):
            os.remove(daemon_script_path)
            display_checkmark(f"\033[92mRemoved daemon script: {daemon_script_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon script '{daemon_script_path}' not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing daemon script: {e}\033[0m")

    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
    except subprocess.CalledProcessError:
        print("\033[91mWarning: Failed to reload systemd daemon.\033[0m")

    display_checkmark("\033[92mUninstall completed!\033[0m")


def status_proxy_forwarders():
    os.system("clear")
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking TCP Forwarders Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "proxyforwarder"

    result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{service_name} is running.\n")
    else:
        print(f"{service_name} is not running.\n")

    print("\n\033[93mRecent logs for ProxyForwarder:\033[0m\n", flush=True)
    try:
        subprocess.run(["journalctl", "-u", service_name, "--since", "1 hour ago", "--no-pager"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching logs: {e}")
    print("\033[93m───────────────────────────────────────\033[0m")


def status_tinyvpn():
    os.system("clear")
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking TinyVPN Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    service_name = "tinyvpn"

    result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"{service_name} is running.\n")
    else:
        print(f"{service_name} is not running.\n")

    print("\n\033[93mRecent logs for TinyVPN:\033[0m\n", flush=True)
    
    subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
    
    print("\033[93m───────────────────────────────────────\033[0m")



def status_udp2raw_server():
    os.system("clear")
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDP2RAW Server Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    try:
        num_ports = int(input("\033[93mHow many \033[92mports do you have? \033[0m").strip())
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    for port_num in range(1, num_ports + 1):
        service_name = f"udp2raw_{port_num}"

        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{service_name} is running.\n")
        else:
            print(f"{service_name} is not running.\n")

        print(f"\n\033[93mRecent logs for {service_name}:\033[0m\n", flush=True)
        subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
        print("\033[93m───────────────────────────────────────\033[0m")


def status_udp2raw_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDP2RAW client Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    service_name = "udp2raw"

    result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{service_name} is running.\n")
    else:
        print(f"{service_name} is not running.\n")

    print(f"\n\033[93mRecent logs for {service_name}:\033[0m\n", flush=True)
    subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
    print("\033[93m───────────────────────────────────────\033[0m")


def status_speederv2_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDPSpeeder Server Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    try:
        num_clients = int(input("\033[93mHow many \033[92mclients do you have? \033[0m").strip())
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    for client_num in range(1, num_clients + 1):
        service_name = f"speederv2_{client_num}"

        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{service_name} is running.\n")
        else:
            print(f"{service_name} is not running.\n")

        print(f"\n\033[93mRecent logs for {service_name}:\033[0m\n", flush=True)
        subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
        print("\033[93m───────────────────────────────────────\033[0m")


def status_speederv2_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDPSpeeder Client Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2"

    result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"{service_name} is running.\n")
    else:
        print(f"{service_name} is not running.\n")

    print(f"\n\033[93mRecent logs for {service_name}:\033[0m\n", flush=True)
    subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
    print("\033[93m───────────────────────────────────────\033[0m")

def status_udp2raw_speederv2_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDP2RAW + UDPSpeeder Server Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    try:
        num_clients = int(input("\033[93mHow many \033[92mclients do you have?\033[0m ").strip())
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    for client_num in range(1, num_clients + 1):
        udp2raw_service = f"udp2raw_{client_num}"
        speederv2_service = f"speederv2_{client_num}"

        udp2raw_status = subprocess.run(["systemctl", "is-active", udp2raw_service], capture_output=True, text=True)
        print(f"{udp2raw_service} is {'running' if udp2raw_status.returncode == 0 else 'not running'}.\n")

        print(f"\n\033[93mRecent logs for {udp2raw_service}:\033[0m\n", flush=True)
        subprocess.run(["journalctl", "-u", udp2raw_service, "--since", "1h ago", "--no-pager"])
        print("\033[93m───────────────────────────────────────\033[0m")

        speederv2_status = subprocess.run(["systemctl", "is-active", speederv2_service], capture_output=True, text=True)
        print(f"{speederv2_service} is {'running' if speederv2_status.returncode == 0 else 'not running'}.\n")

        print(f"\n\033[93mRecent logs for {speederv2_service}:\033[0m\n", flush=True)
        subprocess.run(["journalctl", "-u", speederv2_service, "--since", "1h ago", "--no-pager"])
        print("\033[93m───────────────────────────────────────\033[0m")


def status_udp2raw_speederv2_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking UDP2RAW + UDPSpeeder Client Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    udp2raw_service = "udp2raw"
    udp2raw_status = subprocess.run(["systemctl", "is-active", udp2raw_service], capture_output=True, text=True)
    print(f"{udp2raw_service} is {'running' if udp2raw_status.returncode == 0 else 'not running'}.\n")

    print(f"\n\033[93mRecent logs for {udp2raw_service}:\033[0m\n", flush=True)
    subprocess.run(["journalctl", "-u", udp2raw_service, "--since", "1h ago", "--no-pager"])
    print("\033[93m───────────────────────────────────────\033[0m")

    speederv2_service = "speederv2"
    speederv2_status = subprocess.run(["systemctl", "is-active", speederv2_service], capture_output=True, text=True)
    print(f"{speederv2_service} is {'running' if speederv2_status.returncode == 0 else 'not running'}.\n")

    print(f"\n\033[93mRecent logs for {speederv2_service}:\033[0m\n", flush=True)
    subprocess.run(["journalctl", "-u", speederv2_service, "--since", "1h ago", "--no-pager"])
    print("\033[93m───────────────────────────────────────\033[0m")


def show_status_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mStatus \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    while True:
        print("1. \033[93mTinyvpn\033[0m")
        print("2. \033[96mUDPSpeeder\033[0m")
        print("3. \033[92mUDP2RAW\033[0m")
        print("4. \033[93mUDP2RAW + UDPSpeeder\033[0m")
        print("5. \033[96mProxyforwarder\033[0m")
        print("6. \033[92mTinymapper\033[0m")
        print("0. \033[97mBack to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        choice = input("Choose an option (0-6): ").strip()
        
        if choice == "1":
            status_tinyvpn()
        elif choice == "2":
            status_speederv2()
        elif choice == "3":
            status_udp2raw()
        elif choice == "4":
            status_udp2raw_speederv2()
        elif choice == "5":
            status_proxy_forwarders()
        elif choice == "6":
            status_tinymapper()
        elif choice == "0":
            show_menu()
        else:
            print("Wrong option. choose a valid number (0-6).")

def status_tinymapper():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mChecking Tinymapper Status...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    try:
        num_ports = int(input("\033[93mHow many \033[92mports do you have?\033[0m ").strip())
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    for i in range(1, num_ports + 1):
        service_name = f"tinymapper_{i}"

        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{service_name} is running.\n")
        else:
            print(f"{service_name} is not running.\n")

        print(f"\n\033[93mRecent logs for {service_name}:\033[0m\n", flush=True)
        subprocess.run(["journalctl", "-u", service_name, "--since", "1h ago", "--no-pager"])
        print("\033[93m───────────────────────────────────────\033[0m")

def status_udp2raw_speederv2():
    print("\033[93m──────────────────────────────\033[0m")
    while True:
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0) \033[94mback to status menu\033[0m")
        print("\033[93m──────────────────────────────\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            status_udp2raw_speederv2_server()  
        elif choice == "2":
            status_udp2raw_speederv2_client()
        elif choice == "0":
            show_status_menu()  
        else:
            print("Invalid option. Please choose a valid number from 0 to 2.")

def status_udp2raw():
    print("\033[93m──────────────────────────────\033[0m")
    while True:
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0)\033[93m back to status menu\033[0m")
        print("\033[93m──────────────────────────────\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            status_udp2raw_server()  
        elif choice == "2":
            status_udp2raw_client()
        elif choice == "0":
            show_status_menu()
        else:
            print("Invalid option. Please choose a valid number from 0 to 2.")

def status_speederv2():
    print("\033[93m──────────────────────────────\033[0m")
    while True:
        print("1)\033[93m Server\033[0m")
        print("2)\033[93m Client\033[0m")
        print("0)\033[93m back to status menu\033[0m")
        print("\033[93m──────────────────────────────\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            status_speederv2_server() 
        elif choice == "2":
            status_speederv2_client()
        elif choice == "0":
            show_status_menu()  
        else:
            print("Invalid option. Please choose a valid number from 0 to 2.")


#custom daemon 
def restart_tinyvpn_daemon():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for TinyVPN...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60 
            break
        else:
            print("\033[91mInvalid choice. select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}  # Interval in seconds
    systemctl restart tinyvpn
done
    """

    bash_script_path = "/usr/local/bin/tinyvpn_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=TinyVPN Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/tinyvpn_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "tinyvpn_daemon.service"])
    subprocess.run(["systemctl", "start", "tinyvpn_daemon.service"])

    display_checkmark(f"\033[92mTinyVPN restart daemon set up successfully.\033[0m")

def display_subnet_in_box(subnet):

    box_width = len(subnet) + 15  
    print("\033[93m" + "─" * box_width + "\033[0m")  
    print("\033[93m│ \033[92mSubnet: \033[97m" + subnet + " \033[93m│\033[0m") 
    print("\033[93m" + "─" * box_width + "\033[0m")  

def edit_keepalive_timer():
    script_path = "/usr/local/bin/keepalive.sh"

    if not os.path.exists(script_path):
        print("\033[91mKeep-Alive script not found!\033[0m")
        return

    with open(script_path, "r") as script_file:
        script_content = script_file.read()

    match = re.search(r"sleep (\d+)", script_content)
    current_timer = match.group(1) if match else "10"  

    print("\033[93m───────────────────────────────────────\033[0m")
    print(f"\033[93mCurrent Keep-Alive Timer:\033[92m {current_timer} seconds\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    new_timer = input("\033[93mEnter \033[92mnew Keep-Alive timer\033[97m (seconds, default 10)\033[93m:\033[0m ").strip() or "10"

    updated_script = re.sub(r"sleep \d+", f"sleep {new_timer}", script_content)

    with open(script_path, "w") as script_file:
        script_file.write(updated_script)

    os.chmod(script_path, 0o755)  

    print("\033[92mKeep-Alive timer updated successfully!\033[0m")

    subprocess.run(["systemctl", "restart", "keepalive.service"], check=True)
    print("\033[92mKeep-Alive service restarted.\033[0m")

def setup_tinyvpn_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling TinyVPN Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    binary_path = get_binary_path("tinyvpn")
    if not binary_path or not os.path.exists(binary_path):
        download_file("tinyvpn", binary_path)
        make_executable(binary_path)
    
    tinyvpnport = input("\033[93mEnter TinyVPN \033[92mport\033[93m:\033[0m ")
    subnet = input("\033[93mEnter \033[92msubnet \033[97m(example, 10.22.22.1)\033[93m:\033[0m ")
    tun_name = input("\033[93mEnter \033[92mTUN name \033[97m(example, azumi)\033[93m:\033[0m ")
    
    display_subnet_in_box(subnet)

    fec_enabled = input("\033[93mDo you want to \033[92menable FEC\033[93m? (\033[92myes\033[93m/\033[91mn\033[97m, default yes)\033[93m:\033[0m ").strip().lower() or "yes"
    fec_option = "-f20:10" if fec_enabled in ["yes", "y"] else "--disable-fec"

    mode = input("\033[93mEnter \033[92mmode \033[97m(0 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    timeout = input("\033[93mEnter \033[92mtimeout \033[97m(8 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    tun_mtu = input("\033[93mEnter \033[92mTUN MTU \033[97m(default 1250)\033[93m:\033[0m ") or "1250"
    password = input("\033[93mEnter\033[92m password\033[93m:\033[0m ")

    tinyvpn_command = f"./tinyvpn -s -l0.0.0.0:{tinyvpnport} {fec_option} -k \"{password}\" --sub-net {subnet} --tun {tun_name} --mode {mode} --timeout {timeout} --tun-mtu {tun_mtu}"

    create_service("tinyvpn", tinyvpn_command)
    setup_keepalive(subnet, is_server=True)
    restart_tinyvpn_daemon()


def setup_udp2raw_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    binary_path = get_binary_path("udp2raw")
    if not binary_path or not os.path.exists(binary_path):
        download_file("udp2raw", binary_path)
        make_executable(binary_path)

    num_ports = int(input("\033[93mHow many \033[92mports\033[93m do you have?\033[0m "))
    
    for port_num in range(1, num_ports + 1):
        print("\033[93m───────────────────────────────────────\033[0m")
        print(f"\033[93mConfiguring Port\033[96m {port_num}\033[0m")
        print("\033[93m───────────────────────────────────────\033[0m")
        
        tunnel_port = input("\033[93mEnter \033[92mtunnel port\033[93m:\033[0m ")
        wireguard_port = input("\033[93mEnter \033[92mUDP port\033[93m:\033[0m ")
        password = input("\033[93mEnter \033[92mpassword\033[93m:\033[0m ")

        print("\033[93mRaw mode options:\033[97m (1)\033[96m UDP\033[97m (2)\033[92m ICMP \033[97m(3)\033[93m FakeTCP,\033[97m default is UDP\033[0m")
        raw_mode = input().strip() or "1"
        raw_mode = {"1": "udp", "2": "icmp", "3": "faketcp"}.get(raw_mode, "udp")

        udp2raw_command = f"{binary_path} -s -l0.0.0.0:{tunnel_port} -r 127.0.0.1:{wireguard_port} -k \"{password}\" --raw-mode {raw_mode} -a"

        service_name = f"udp2raw_{port_num}"
        create_service(service_name, udp2raw_command)
        restart_udp2raw_daemon_server()


def setup_tinyvpn_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling TinyVPN Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    binary_path = get_binary_path("tinyvpn")
    if not binary_path or not os.path.exists(binary_path):
        download_file("tinyvpn", binary_path)
        make_executable(binary_path)
    
    server_public_ip = input("\033[93mEnter the \033[92mserver's public IP address\033[93m:\033[0m ")
    subnet = input("\033[93mEnter subnet \033[97m(default 10.22.22.2)\033[93m:\033[0m ") or "10.22.22.2" 
    fec_enabled = input("\033[93mDo you want to \033[92menable FEC\033[93m? \033[93m?(\033[92myes\033[93m/\033[91mn\033[97m default yes)\033[93m:\033[0m ").strip().lower() or "yes"
    fec_option = "-f20:10" if fec_enabled in ["yes", "y"] else "--disable-fec"
    
    tinyvpnport = input("\033[93mEnter \033[92mTinyVPN port\033[93m:\033[0m ")
    tun_name = input("\033[93mEnter \033[92mTUN name\033[97m (example, azumi)\033[93m:\033[0m ")
    mode = input("\033[93mEnter \033[92mmode \033[97m(0 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    timeout = input("\033[93mEnter \033[92mtimeout \033[97m(8 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    tun_mtu = input("\033[93mEnter \033[92mTUN MTU \033[97m(default 1250)\033[93m:\033[0m ") or "1250"
    password = input("\033[93mEnter \033[92mpassword\033[93m:\033[0m ")
    display_subnet_in_box(subnet)

    tinyvpn_command = f"{binary_path} -c -r {server_public_ip}:{tinyvpnport} {fec_option} -k \"{password}\" --tun {tun_name} --sub-net {subnet} --keep-reconnect --mode {mode} --timeout {timeout} --tun-mtu {tun_mtu}"

    create_service("tinyvpn", tinyvpn_command)
    setup_keepalive(subnet, is_server=False)
    restart_tinyvpn_daemon()
    

def stop_delete_keepalive():
    keepalive_script_path = "/usr/local/bin/keepalive.sh"
    keepalive_service_path = "/etc/systemd/system/keepalive.service"
    
    subprocess.run(["sudo", "systemctl", "stop", "keepalive.service"], check=True)
    subprocess.run(["sudo", "systemctl", "disable", "keepalive.service"], check=True)
    
    if os.path.exists(keepalive_script_path):
        os.remove(keepalive_script_path)
    else:
        print(f"\033[91mNo keepalive script found at {keepalive_script_path}...\033[0m")
    
    if os.path.exists(keepalive_service_path):
        print(f"\033[93mDeleting keepalive service file at {keepalive_service_path}...\033[0m")
        os.remove(keepalive_service_path)
    else:
        print(f"\033[91mNo keepalive service file found at {keepalive_service_path}...\033[0m")
    
    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "systemctl", "reset-failed"], check=True)

    display_checkmark("\033[92mKeepalive script deleted.\033[0m")

#subnet + keepalive
def getopposite_subnet(subnet, is_server=True):
    parts = subnet.split(".")
    
    if parts[-1] == "1":
        opposite_ip = "2" if is_server else "1"
    elif parts[-1] == "2":
        opposite_ip = "1" if is_server else "2"
    else:
        raise ValueError("The subnet should end with either .1 or .2 for this setup.")
    
    opposite_subnet = parts[:-1] + [opposite_ip]
    return ".".join(opposite_subnet)

def keepalive_script(subnet, is_server=True, keepalive_interval=10):
    opposite_subnet = getopposite_subnet(subnet, is_server)

    script_content = f"""#!/bin/bash
while true; do
    ping -c 2 {opposite_subnet} > /dev/null
    sleep {keepalive_interval}
done
"""

    script_path = "/usr/local/bin/keepalive.sh"
    with open(script_path, "w") as script_file:
        script_file.write(script_content)

    os.chmod(script_path, 0o755)
    print(f"Keepalive script created at {script_path} with {keepalive_interval}s interval")

def keepalive_service():
    service_content = """
[Unit]
Description=Keep-Alive Service for TinyVPN

[Service]
ExecStart=/usr/local/bin/keepalive.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/keepalive.service"
    with open(service_path, "w") as service_file:
        service_file.write(service_content)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    print(f"Keep-Alive service created at {service_path}")

    subprocess.run(["systemctl", "enable", "keepalive.service"], check=True)
    subprocess.run(["systemctl", "start", "keepalive.service"], check=True)
    print("✅ Keep-Alive service is now running")

def setup_keepalive(subnet, is_server=True):
    try:
        keepalive_interval = int(input("\033[93mEnter \033[92mkeep-alive\033[93m interval in\033[97m seconds\033[93m: \033[0m"))
        if keepalive_interval <= 0:
            raise ValueError("Input must be greater than 0")
    except ValueError as e:
        print(f"Invalid input: {e}")
        return
    
    keepalive_script(subnet, is_server, keepalive_interval)
    keepalive_service()


#custom daemon for udp2raw 
def restart_udp2raw_daemon():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for udp2raw...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60  
            break
        else:
            print("\033[91mInvalid choice. select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}  
    systemctl restart udp2raw
done
    """

    bash_script_path = "/usr/local/bin/udp2raw_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=udp2raw Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/udp2raw_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])

    subprocess.run(["systemctl", "enable", "udp2raw_daemon.service"])
    subprocess.run(["systemctl", "start", "udp2raw_daemon.service"])

    display_checkmark(f"\033[92mTinyVPN restart daemon set up successfully.\033[0m")

def restart_udp2raw_daemon_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for udp2raw...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return
    
    num_ports = int(input("\033[93mHow many \033[92mports\033[93m do you have? \033[0m").strip())
    

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60  
            break
        else:
            print("\033[91mInvalid choice. Select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    restart_commands = []
    for port_num in range(1, num_ports + 1):
        restart_commands.append(f"systemctl restart udp2raw_{port_num}")

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}
    {"; ".join(restart_commands)}
done
    """

    bash_script_path = "/usr/local/bin/udp2raw_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=udp2raw Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/udp2raw_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])

    subprocess.run(["systemctl", "enable", "udp2raw_daemon.service"])
    subprocess.run(["systemctl", "start", "udp2raw_daemon.service"])

    print("\033[92mUDP2RAW restart daemon set up successfully.\033[0m")

def setup_udp2raw_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDP2RAW Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    binary_path = get_binary_path("udp2raw")
    if not binary_path or not os.path.exists(binary_path):
        download_file("udp2raw", binary_path)
        make_executable(binary_path)

    wireguard_ovpn_port = input("\033[93mEnter\033[92m UDP port\033[93m:\033[0m ")
    tunnel_port = input("\033[93mEnter\033[92m tunnel port\033[93m:\033[0m ")
    server_private_ip = input("\033[93mEnter the \033[96mserver's private IP address\033[93m:\033[0m ")
    password = input("\033[93mEnter \033[92mpassword\033[93m:\033[0m ")

    print("\033[93mRaw mode options:\033[97m (1)\033[96m UDP\033[97m (2)\033[92m ICMP \033[97m(3)\033[93m FakeTCP,\033[97m default is UDP\033[0m")
    raw_mode = input().strip() or "1"
    raw_mode = {"1": "udp", "2": "icmp", "3": "faketcp"}.get(raw_mode, "udp")

    udp2raw_command = f"{binary_path} -c -l0.0.0.0:{wireguard_ovpn_port} -r {server_private_ip}:{tunnel_port} -k \"{password}\" --raw-mode {raw_mode} -a"

    create_service("udp2raw", udp2raw_command)
    restart_udp2raw_daemon()

#custom daemon for speederv
def restart_speederv_daemon_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for speederv2...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return
    
    num_ports = int(input("\033[93mHow many \033[92mClients\033[93m do you have? \033[0m").strip())
    

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60  
            break
        else:
            print("\033[91mInvalid choice. Select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    restart_commands = []
    for port_num in range(1, num_ports + 1):
        restart_commands.append(f"systemctl restart speederv2_{port_num}")

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}
    {"; ".join(restart_commands)}
done
    """

    bash_script_path = "/usr/local/bin/speederv_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=speederv Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/speederv_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "speederv_daemon.service"])
    subprocess.run(["systemctl", "start", "speederv_daemon.service"])

    print("\033[92mspeederv restart daemon set up successfully.\033[0m")

def setup_speederv2_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDPSpeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    binary_path = get_binary_path("speederv2")
    if not binary_path or not os.path.exists(binary_path):
        download_file("speederv2", binary_path)
        make_executable(binary_path)
    
    num_clients = int(input("\033[93mHow many \033[92mclients do you have?\033[0m "))
    
    for i in range(num_clients):
        print("\033[93m───────────────────────────────────────\033[0m")
        print(f"\033[93mConfiguring \033[92mClient {i+1}\033[0m")
        print("\033[93m───────────────────────────────────────\033[0m")
        
        tunnel_port = input("\033[93mEnter \033[92mtunnel port\033[93m:\033[0m ")
        wireguard_port = input("\033[93mEnter \033[92mUDP \033[93mport:\033[0m ")
        password = input("\033[93mEnter \033[92mpassword\033[93m:\033[0m ")

        timeout = input("\033[93mEnter \033[92mtimeout \033[97m(8 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
        tun_mtu = input("\033[93mEnter \033[92mTUN MTU \033[97m(default 1250)\033[93m:\033[0m ") or "1250"

        fec_enabled = input("\033[93mDo you want to \033[92menable FEC\033[93m? \033[93m?(\033[92myes\033[93m/\033[91mn\033[97m default yes)\033[93m:\033[0m ").strip().lower() or "yes"
        if fec_enabled in ["yes", "y"]:
            fec_option = "-f20:10"
        else:
            fec_option = "--disable-fec"

        mode = input("\033[93mEnter\033[92m mode\033[97m (0 or 1, default 1)\033[93m: \033[0m").strip() or "1"
        
        speederv2_command = f"{binary_path} -s -l0.0.0.0:{tunnel_port} --mode {mode} --timeout {timeout} --mtu {tun_mtu} -r127.0.0.1:{wireguard_port} {fec_option} -k \"{password}\""

        create_service(f"speederv2_{i+1}", speederv2_command)
        restart_speederv_daemon_server()

# custom daemon for speederv client
def restart_speederv_daemon():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for speederv...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60 
            break
        else:
            print("\033[91mInvalid choice. select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}  
    systemctl restart speederv2
done
    """

    bash_script_path = "/usr/local/bin/speederv_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=speederv Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/speederv_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "speederv_daemon.service"])
    subprocess.run(["systemctl", "start", "speederv_daemon.service"])

    display_checkmark(f"\033[92mspeederv restart daemon set up successfully.\033[0m")

def setup_speederv2_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDPSpeeder Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    binary_path = get_binary_path("speederv2")
    if not binary_path or not os.path.exists(binary_path):
        download_file("speederv2", binary_path)
        make_executable(binary_path)
    
    wireguard_port = input("\033[93mEnter \033[92mUDP \033[93mport:\033[0m ")
    tunnel_port = input("\033[93mEnter \033[92mtunnel port\033[93m:\033[0m ")
    password = input("\033[93mEnter \033[92mpassword\033[93m:\033[0m ")
    server_ip = input(f"\033[93mEnter \033[92mserver IP address\033[93m: \033[0m")

    timeout = input("\033[93mEnter \033[92mtimeout \033[97m(8 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    tun_mtu = input("\033[93mEnter \033[92mTUN MTU \033[97m(default 1250)\033[93m:\033[0m ") or "1250"

    fec_enabled = input("\033[93mDo you want to \033[92menable FEC\033[93m? \033[93m?(\033[92myes\033[93m/\033[91mn\033[97m default yes)\033[93m:\033[0m ").strip().lower() or "yes"
    if fec_enabled in ["yes", "y"]:
        fec_option = "-f20:10"
    else:
        fec_option = "--disable-fec"
    
    mode = input("\033[93mEnter mode \033[97m(0 or 1, default 1)\033[93m:\033[0m ").strip() or "1"
    
    speederv2_command = f"{binary_path} -c -l0.0.0.0:{wireguard_port} -r{server_ip}:{tunnel_port} --mode {mode} --timeout {timeout} --mtu {tun_mtu} {fec_option} -k \"{password}\""

    create_service(f"speederv2", speederv2_command)
    restart_speederv_daemon()


def setup_server_udp2raw_updspeeder():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDP2RAW and UDPSpeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    udp2raw_binary_path = get_binary_path("udp2raw")
    if not udp2raw_binary_path or not os.path.exists(udp2raw_binary_path):
        download_file("udp2raw", udp2raw_binary_path)
        make_executable(udp2raw_binary_path)

    speederv2_binary_path = get_binary_path("speederv2")
    if not speederv2_binary_path or not os.path.exists(speederv2_binary_path):
        download_file("speederv2", speederv2_binary_path)
        make_executable(speederv2_binary_path)

    num_clients = int(input("\033[93mHow many \033[92mclients do you have? \033[0m"))

    for client_num in range(1, num_clients + 1):
        print("\033[93m───────────────────────────────────────\033[0m")
        print(f"\033[93mConfiguring\033[92m Config {client_num}...\033[0m")
        print("\033[93m───────────────────────────────────────\033[0m")

        tunnel_port = input(f"\033[93mEnter \033[92mtunnel port \033[93mfor \033[96mClient {client_num}:\033[0m ")
        wireguard_ovpn_port = input(f"\033[93mEnter \033[92mUDP port \033[93mfor \033[96mClient {client_num}:\033[0m ")
        fec_port = input(f"\033[93mEnter \033[92mFEC port \033[93mfor \033[96mClient {client_num}:\033[0m ")

        print("\033[93mRaw mode options:\033[97m (1)\033[96m UDP\033[97m (2)\033[92m ICMP \033[97m(3)\033[93m FakeTCP,\033[97m default is UDP\033[0m")
        raw_mode_input = input().strip() or "1"
        raw_mode = {"1": "udp", "2": "icmp", "3": "faketcp"}.get(raw_mode_input, "udp")
        enable_fec = input(f"\033[93mEnable \033[92mFEC \033[93mfor \033[96mClient {client_num}\033[93m? \033[93m?(\033[92myes\033[93m/\033[91mn\033[97m default yes): \033[0m").strip().lower() or "yes"
        fec_option = "-f20:10" if enable_fec == "yes" else "--disable-fec"
        password = input(f"\033[93mEnter password for \033[96mClient {client_num}:\033[0m ")
        timeout = input(f"\033[93mEnter \033[92mtimeout \033[97m(1 or 8, default 1) for Client {client_num}:\033[0m ").strip() or "1"
        mode = input("\033[93mEnter \033[92mmode \033[97m(0 or 1, default 1): \033[0m").strip() or "1"

        udp2raw_server_command = f"{udp2raw_binary_path} -s -l0.0.0.0:{tunnel_port} -r 127.0.0.1:{fec_port} -k \"{password}\" --raw-mode {raw_mode} -a"

        speederv2_server_command = f"{speederv2_binary_path} -s -l0.0.0.0:{fec_port} --mode {mode} --timeout {timeout} -r 127.0.0.1:{wireguard_ovpn_port} {fec_option} -k \"{password}\""

        create_service(f"udp2raw_{client_num}", udp2raw_server_command)
        create_service(f"speederv2_{client_num}", speederv2_server_command)


def setup_client_udp2raw_updspeeder():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDP2RAW and UDPSpeeder Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    udp2raw_binary_path = get_binary_path("udp2raw")
    if not udp2raw_binary_path or not os.path.exists(udp2raw_binary_path):
        download_file("udp2raw", udp2raw_binary_path)
        make_executable(udp2raw_binary_path)

    speederv2_binary_path = get_binary_path("speederv2")
    if not speederv2_binary_path or not os.path.exists(speederv2_binary_path):
        download_file("speederv2", speederv2_binary_path)
        make_executable(speederv2_binary_path)

    tunnel_port = input(f"\033[93mEnter \033[92mtunnel port\033[93m for the \033[96mclient:\033[0m ")
    wireguard_ovpn_port = input(f"\033[93mEnter \033[92mUDP\033[93m port for the \033[96mclient:\033[0m ")
    fec_port = input(f"\033[93mEnter \033[92mFEC port \033[93mfor the \033[96mclient:\033[0m ")

    server_ip = input(f"\033[93mEnter \033[92mserver IP address\033[93m: \033[0m")

    print("\033[93mRaw mode options:\033[97m (1)\033[96m UDP\033[97m (2)\033[92m ICMP \033[97m(3)\033[93m FakeTCP,\033[97m default is UDP\033[0m")
    raw_mode_input = input().strip() or "1"
    raw_mode = {"1": "udp", "2": "icmp", "3": "faketcp"}.get(raw_mode_input, "udp")

    enable_fec = input(f"\033[93mEnable \033[92mFEC for the \033[96mclient? \033[93m?(\033[92myes\033[93m/\033[91mn\033[97m default yes):\033[0m ").strip().lower() or "yes"
    fec_option = "-f20:10" if enable_fec == "yes" else "--disable-fec"
    password = input(f"\033[93mEnter \033[92mpassword\033[93m for the client:\033[0m ")
    timeout = input(f"\033[93mEnter timeout \033[92mtimeout\033[92m (1 or 8,\033[97m default 1)\033[93m: \033[0m").strip() or "1"
    mode = input(f"\033[93mEnter mode \033[92m(0 or 1,\033[97m default 1)\033[93m: \033[0m").strip() or "1"

    udp2raw_client_command = f"{udp2raw_binary_path} -c -l0.0.0.0:{wireguard_ovpn_port} -r {server_ip}:{tunnel_port} -k \"{password}\" --raw-mode {raw_mode} -a"

    speederv2_client_command = f"{speederv2_binary_path} -c -l0.0.0.0:{fec_port} --mode {mode} --timeout {timeout} -r {server_ip}:{wireguard_ovpn_port} {fec_option} -k \"{password}\""

    create_service(f"udp2raw", udp2raw_client_command)
    create_service(f"speederv2", speederv2_client_command)


def show_menu():
    os.system("clear")
    logo()
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mMain Menu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("0.\033[97m Status\033[0m")
        print("1.\033[93m TinyVPN\033[0m")
        print("2.\033[92m TinyVPN + UDP2RAW\033[0m")
        print("3.\033[96m UDPSpeeder setup\033[0m")
        print("4.\033[93m UDPSpeeder + UDP2RAW setup\033[0m")
        print("5.\033[92m TinyVPN + ProxyForwarder\033[0m")
        print("6.\033[97m Geneve + ProxyForwarder\033[0m")
        print("7.\033[93m ProxyForwarder\033[0m")
        print("8.\033[92m Tinyvpn + Tinymapper\033[0m")
        print("9.\033[93m Tinymapper\033[0m")
        print("10.\033[96mEdit\033[0m")
        print("11.\033[97mEdit Keepalive Timer\033[0m")
        print("12.\033[93mReset Timer\033[0m")
        print("13.\033[92mRestart\033[0m")
        print("14.\033[91mUninstall\033[0m")
        print("\033[93m───────────────────────────────────────\033[0m")
        choice = input("Choose an option (0-12): ").strip()

        if choice == "0":
            show_status_menu()
        elif choice == "1":
            tinyvpn_menu()  
        elif choice == "2":
            tinyvpn_udp2raw_menu()  
        elif choice == "3":
            speederv2_menu()  
        elif choice == "4":
            udpspeeder_udp2raw_menu()
        elif choice == "5":
            proxyforwarder_tinyvpn_menu()
        elif choice == "6":
            proxyforwarder_geneve_menu()
        elif choice == "7":
            setup_proxyforwarder()
        elif choice == "8":
            tinymapper_tinyvpn_menu()
        elif choice == "9":
            download_and_setup_tinymapper()
        elif choice == "10":
            edit_menu()
        elif choice == "11":
            edit_keepalive_timer()
        elif choice == "12":
            reset_menu()
        elif choice == "13":
            restart_menu()
        elif choice == "14":
            uninstall_menu()
        else:
            print("Wrong option. choose a valid number from 0 to 10.")

def read_tinyvpn_service():
    service_path = "/etc/systemd/system/tinyvpn.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def parse_execstart(service_content):
    for line in service_content.splitlines():
        if line.startswith("ExecStart"):
            return line.split("ExecStart=")[1].strip()
    return None

def extract_parameters_tinyvpn(command):
    parameters = {}

    port_match = re.search(r"-l0.0.0.0:(\d+)", command)
    if port_match:
        parameters["port"] = port_match.group(1)

    fec_match = re.search(r"(-f[\d\:]+|--disable-fec)", command)
    if fec_match:
        parameters["fec_option"] = fec_match.group(1)

    password_match = re.search(r'-k "([^"]+)"', command)
    if password_match:
        parameters["password"] = password_match.group(1)

    subnet_match = re.search(r"--sub-net ([\d\.]+)", command)
    if subnet_match:
        parameters["subnet"] = subnet_match.group(1)

    tun_name_match = re.search(r"--tun (\S+)", command)
    if tun_name_match:
        parameters["tun_name"] = tun_name_match.group(1)

    mode_match = re.search(r"--mode (\d)", command)
    if mode_match:
        parameters["mode"] = mode_match.group(1)

    timeout_match = re.search(r"--timeout (\d+)", command)
    if timeout_match:
        parameters["timeout"] = timeout_match.group(1)

    mtu_match = re.search(r"--tun-mtu (\d+)", command)
    if mtu_match:
        parameters["tun_mtu"] = mtu_match.group(1)

    server_ip_match = re.search(r"-r (\S+):(\d+)", command)
    if server_ip_match:
        parameters["server_ip"] = server_ip_match.group(1)
        parameters["server_port"] = server_ip_match.group(2)

    return parameters

def extract_parameters_tinyvpn_client(command):
    parameters = {}

    server_ip_match = re.search(r"-r (\S+):(\d+)", command)
    if server_ip_match:
        parameters["server_ip"] = server_ip_match.group(1)
        parameters["port"] = server_ip_match.group(2)  

    fec_match = re.search(r"(-f[\d\:]+|--disable-fec)", command)
    if fec_match:
        parameters["fec_option"] = fec_match.group(1)

    password_match = re.search(r'-k "([^"]+)"', command)
    if password_match:
        parameters["password"] = password_match.group(1)

    subnet_match = re.search(r"--sub-net ([\d\.]+)", command)
    if subnet_match:
        parameters["subnet"] = subnet_match.group(1)

    tun_name_match = re.search(r"--tun (\S+)", command)
    if tun_name_match:
        parameters["tun_name"] = tun_name_match.group(1)

    mode_match = re.search(r"--mode (\d)", command)
    if mode_match:
        parameters["mode"] = mode_match.group(1)

    timeout_match = re.search(r"--timeout (\d+)", command)
    if timeout_match:
        parameters["timeout"] = timeout_match.group(1)

    mtu_match = re.search(r"tun-mtu (\d+)", command)
    if mtu_match:
        parameters["tun_mtu"] = mtu_match.group(1)

    return parameters

def prompt_for_edit(parameter_name, current_value, valid_options=None):
    new_value = input(f"Edit {parameter_name} (current value: {current_value}): ")
    
    if valid_options and new_value not in valid_options:
        print(f"Invalid input. Please choose from {valid_options}")
        return current_value
    
    return new_value.strip() or current_value

def update_execstart_tinyvpn(command, new_parameters):
    command = re.sub(r"-l0.0.0.0:\d+", f"-l0.0.0.0:{new_parameters['port']}", command) 
    command = re.sub(r"(-f[\d\:]+|--disable-fec)", new_parameters["fec_option"], command) 
    command = re.sub(r'-k "[^"]+"', f'-k "{new_parameters["password"]}"', command) 
    command = re.sub(r"--sub-net [\d\.]+", f"--sub-net {new_parameters['subnet']}", command) 
    command = re.sub(r"--tun \S+", f"--tun {new_parameters['tun_name']}", command) 
    command = re.sub(r"--mode \d", f"--mode {new_parameters['mode']}", command) 
    command = re.sub(r"--timeout \d+", f"--timeout {new_parameters['timeout']}", command)  
    command = re.sub(r"--tun-mtu \d+", f"--tun-mtu {new_parameters['tun_mtu']}", command) 

    return command

def update_execstart_client_tinyvpn(current_command, current_parameters):
    updated_command = current_command
    updated_command = re.sub(r'-r (\S+):(\d+)', f'-r {current_parameters["server_ip"]}:{current_parameters["port"]}', updated_command)
    updated_command = re.sub(r'(\S+) -k "(.*?)"', f'{current_parameters["fec_option"]} -k "{current_parameters["password"]}"', updated_command)
    updated_command = re.sub(r'--tun (\S+)', f'--tun {current_parameters["tun_name"]}', updated_command)
    updated_command = re.sub(r'--sub-net (\S+)', f'--sub-net {current_parameters["subnet"]}', updated_command)
    updated_command = re.sub(r'--mode (\d+)', f'--mode {current_parameters["mode"]}', updated_command)
    updated_command = re.sub(r'--timeout (\d+)', f'--timeout {current_parameters["timeout"]}', updated_command)
    updated_command = re.sub(r'--tun-mtu (\d+)', f'--tun-mtu {current_parameters["tun_mtu"]}', updated_command)
    return updated_command

def save_service_file_tinyvpn(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/tinyvpn.service", "w") as file:
        file.write(updated_content)


def reload_and_restart_service_tinyvpn():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "tinyvpn"])
    subprocess.run(["systemctl", "enable", "tinyvpn"])

    display_checkmark("\033[92mTinyVPN service updated and restarted successfully\033[0m")

def edit_tinyvpn_service():
    service_content = read_tinyvpn_service()
    if not service_content:
        return

    current_command = parse_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_parameters_tinyvpn(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mEdit Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    while True:
        print("1) \033[93mEdit \033[92mPort\033[97m (current: {0})\033[0m".format(current_parameters["port"]))
        print("2) \033[93mToggle \033[92mFEC\033[97m (current: {0})\033[0m".format(current_parameters["fec_option"]))
        print("3) \033[93mEdit \033[92mPassword\033[97m (current: {0})\033[0m".format(current_parameters["password"]))
        print("4) \033[93mEdit \033[92mSubnet\033[97m (current: {0})\033[0m".format(current_parameters["subnet"]))
        print("5) \033[93mEdit \033[92mTUN Name\033[97m (current: {0})\033[0m".format(current_parameters["tun_name"]))
        print("6) \033[93mEdit \033[92mMode\033[97m (current: {0})\033[0m".format(current_parameters["mode"]))
        print("7) \033[93mEdit \033[92mTimeout\033[97m (current: {0})\033[0m".format(current_parameters["timeout"]))
        print("8) \033[93mEdit \033[92mTUN MTU\033[97m (current: {0})\033[0m".format(current_parameters["tun_mtu"]))
        print("9) \033[92mSave and Apply Changes\033[0m")
        print("0) Exit")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit("Port", current_parameters["port"])
        elif choice == '2':
            valid_fec_options = ["-f20:10", "--disable-fec"]
            current_parameters["fec_option"] = prompt_for_edit("FEC Option", current_parameters["fec_option"], valid_fec_options)
        elif choice == '3':
            current_parameters["password"] = prompt_for_edit("Password", current_parameters["password"])
        elif choice == '4':
            current_parameters["subnet"] = prompt_for_edit("Subnet", current_parameters["subnet"])
        elif choice == '5':
            current_parameters["tun_name"] = prompt_for_edit("TUN Name", current_parameters["tun_name"])
        elif choice == '6':
            current_parameters["mode"] = prompt_for_edit("Mode (0 or 1)", current_parameters["mode"], valid_options=["0", "1"])
        elif choice == '7':
            current_parameters["timeout"] = prompt_for_edit("Timeout (0 or 8)", current_parameters["timeout"], valid_options=["0", "8"])
        elif choice == '8':
            current_parameters["tun_mtu"] = prompt_for_edit("TUN MTU", current_parameters["tun_mtu"])
        elif choice == '9':
            updated_command = update_execstart_tinyvpn(current_command, current_parameters)
            save_service_file_tinyvpn(service_content, updated_command)
            reload_and_restart_service_tinyvpn()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_tinyvpn_client_service():
    service_content = read_tinyvpn_service()
    if not service_content:
        return

    current_command = parse_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_parameters_tinyvpn_client(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mEdit Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    while True:
        print("1)\033[93m Edit \033[92mServer IP\033[97m (current: {0})\033[0m".format(current_parameters["server_ip"]))
        print("2)\033[93m Edit \033[92mPort\033[97m (current: {0})\033[0m".format(current_parameters["port"]))
        print("3)\033[93m Toggle \033[92mFEC\033[97m (current: {0})\033[0m".format(current_parameters["fec_option"]))
        print("4)\033[93m Edit \033[92mPassword\033[97m (current: {0})\033[0m".format(current_parameters["password"]))
        print("5)\033[93m Edit \033[92mSubnet\033[97m (current: {0})\033[0m".format(current_parameters["subnet"]))
        print("6)\033[93m Edit \033[92mTUN Name\033[97m (current: {0})\033[0m".format(current_parameters["tun_name"]))
        print("7)\033[93m Edit \033[92mMode\033[97m (current: {0})\033[0m".format(current_parameters["mode"]))
        print("8)\033[93m Edit \033[92mTimeout\033[97m (current: {0})\033[0m".format(current_parameters["timeout"]))
        print("9)\033[93m Edit \033[92mTUN MTU\033[97m (current: {0})\033[0m".format(current_parameters["tun_mtu"]))
        print("10)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["server_ip"] = prompt_for_edit("Server IP", current_parameters["server_ip"])
        elif choice == '2':
            current_parameters["port"] = prompt_for_edit("Port", current_parameters["port"])
        elif choice == '3':
            valid_fec_options = ["-f20:10", "--disable-fec"]
            current_parameters["fec_option"] = prompt_for_edit("FEC Option", current_parameters["fec_option"], valid_fec_options)
        elif choice == '4':
            current_parameters["password"] = prompt_for_edit("Password", current_parameters["password"])
        elif choice == '5':
            current_parameters["subnet"] = prompt_for_edit("Subnet", current_parameters["subnet"])
        elif choice == '6':
            current_parameters["tun_name"] = prompt_for_edit("TUN Name", current_parameters["tun_name"])
        elif choice == '7':
            valid_modes = ["0", "1"]
            current_parameters["mode"] = prompt_for_edit("Mode (0 or 1)", current_parameters["mode"], valid_modes)
        elif choice == '8':
            valid_timeouts = ["0", "8"]
            current_parameters["timeout"] = prompt_for_edit("Timeout (0 or 8)", current_parameters["timeout"], valid_timeouts)
        elif choice == '9':
            current_parameters["tun_mtu"] = prompt_for_edit("TUN MTU", current_parameters["tun_mtu"])
        elif choice == '10':
            updated_command = update_execstart_client_tinyvpn(current_command, current_parameters)
            save_service_file_tinyvpn(service_content, updated_command)
            reload_and_restart_service_tinyvpn()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")


def edit_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mEdit \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TinyVPN\033[0m")
    print("2)\033[92m UDP2RAW\033[0m")
    print("3)\033[94m UDPSpeeder\033[0m")
    print("4)\033[93m ProxyForwarder\033[0m")
    print("5)\033[92m Tinymapper\033[0m")
    print("0)\033[94m back to main menu\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        edit_tinyvpn_menu()
    elif choice == "2":
        edit_udp2raw_menu()
    elif choice == "3":
        edit_udpspeed_menu()
    elif choice == "4":
        edit_proxyforwarder_menu()
    elif choice == "5":
        edit_tinymapper_service_menu()
    elif choice == "0":
        return  
    else:
        print("Invalid choice. Please select a valid option.")


def reset_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mReset \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TinyVPN\033[0m")
    print("2)\033[92m UDP2RAW\033[0m")
    print("3)\033[94m UDPSpeeder\033[0m")
    print("4)\033[93m ProxyForwarder\033[0m")
    print("5)\033[92m Tinymapper\033[0m")
    print("0)\033[94m back to main menu\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        restart_tinyvpn_daemon()
    elif choice == "2":
        reset_udp2raw_menu()
    elif choice == "3":
        reset_udpspeed_menu()
    elif choice == "4":
        restart_proxyforwarder_daemon()
    elif choice == "5":
        restart_tinymapper_daemon_server()
    elif choice == "0":
        return  
    
    else:
        print("Invalid choice. Please select a valid option.")

def reset_udp2raw_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mReset udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-2): ").strip()

    if choice == "1":
        restart_udp2raw_daemon_server()
    elif choice == "2":
        restart_udp2raw_daemon()
    elif choice == "0":
        reset_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def reset_udpspeed_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mReset udpspeed \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-2): ").strip()

    if choice == "1":
        restart_speederv_daemon_server()
    elif choice == "2":
        restart_speederv_daemon()
    elif choice == "0":
        reset_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def edit_proxyforwarder_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mProxyforwarder edit \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TCP Proxyforwarder\033[0m")
    print("2)\033[92m UDP Proxyforwarder\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        edit_proxyforwarder_config()
    elif choice == "2":
        edit_udp_config()
    elif choice == "0":
        edit_menu()  
    else:
        print("Invalid choice. Please select a valid option.")

def edit_tinymapper_service_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mTinymapper edit \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Tinymapper Config [1]\033[0m")
    print("2)\033[93m Tinymapper Config [2]\033[0m")
    print("3)\033[92m Tinymapper Config [3]\033[0m")
    print("4)\033[93m Tinymapper Config [4]\033[0m")
    print("5)\033[93m Tinymapper Config [5]\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        edit_tinymapper_service1()
    elif choice == "2":
        edit_tinymapper_service2()
    elif choice == "3":
        edit_tinymapper_service3()
    elif choice == "4":
        edit_tinymapper_service4()
    elif choice == "5":
        edit_tinymapper_service5()
    elif choice == "0":
        edit_menu() 
    else:
        print("Invalid choice. Please select a valid option.")

def edit_tinymapper_service1():
    service_file_path = "/etc/systemd/system/tinymapper_1.service"
    
    if not os.path.exists(service_file_path):
        print(f"\033[91mError: {service_file_path} not found.\033[0m")
        return

    with open(service_file_path, 'r') as file:
        lines = file.readlines()
    
    exec_start_line = None
    for line in lines:
        if line.strip().startswith("ExecStart"):  
            exec_start_line = line
            break

    if not exec_start_line:
        print("\033[91mError: ExecStart line not found in the service file.\033[0m")
        return
    
    pattern = r"-l\s([0-9\.]+):(\d+)\s-r\s([0-9\.]+):(\d+)\s(-u|-t)?"
    match = re.search(pattern, exec_start_line)
    
    if not match:
        print("\033[91mError: Could not parse the ExecStart line.\033[0m")
        return
    
    current_listen_address = match.group(1)
    current_listen_port = match.group(2)
    current_target_address = match.group(3)
    current_target_port = match.group(4)
    current_flags = match.group(5) or ''

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinymapper \033[93mService \033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m')

    print(f"\n\033[92mCurrent Tinymapper Service File:\033[0m")
    for line in lines:
        print(f"\033[97m{line.strip()}\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    print("\n\033[93mEditing line...\033[0m")
    
    listen_address = input(f"\033[93mEnter \033[92mListen Address\033[97m (current: {current_listen_address}):\033[0m") or current_listen_address
    listen_port = input(f"\033[93mEnter \033[92mListen Port\033[97m (current: {current_listen_port}): \033[0m") or current_listen_port
    target_address = input(f"\033[93mEnter \033[92mTarget Address\033[97m (current: {current_target_address}): \033[0m") or current_target_address
    target_port = input(f"\033[93mEnter \033[92mTarget Port\033[97m (current: {current_target_port}): \033[0m") or current_target_port

    print(f"\n\033[93mCurrent Flags: \033[92m{current_flags}\033[0m")
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("\033[93mChoose protocol for tinymapper service:\033[0m")
    print("\033[92m1.\033[97m UDP only (-u)\033[0m")
    print("\033[92m2.\033[97m TCP only (-t)\033[0m")
    print("\033[92m3.\033[97m Both UDP and TCP (-u and -t)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input("\033[93mEnter your choice (1/2/3): \033[0m").strip()

    if choice == '1':
        new_flags = ' -u' 
    elif choice == '2':
        new_flags = ' -t' 
    elif choice == '3':
        new_flags = ' -u -t'  
    else:
        print("\033[91mno choice. No flags will be applied.\033[0m")
        new_flags = ''

    new_exec_start = f"ExecStart=/usr/local/bin/tinymapper -l {listen_address}:{listen_port} -r {target_address}:{target_port}{new_flags}\n"
    
    for idx, line in enumerate(lines):
        if line.strip().startswith("ExecStart"):
            lines[idx] = new_exec_start
            break
    
    with open(service_file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"\n\033[92mTinymapper service updated with the following:\033[0m")
    print(f"\033[97m{new_exec_start}\033[0m")
    
    os.system("systemctl daemon-reload")
    display_checkmark("\033[92mSystemd configuration reloaded.\033[0m")

    restart = input("\n\033[93mDo you want to restart \033[92mthe tinymapper\033[93m service now? (\033[92my\033[93m/\033[91mn\033[93m): \033[0m").strip().lower()
    if restart == 'y':
        os.system("systemctl restart tinymapper_1.service")
        display_checkmark("\033[92mTinymapper service restarted.\033[0m")
    else:
        print("\033[93mTinymapper service restart skipped.\033[0m")

def edit_tinymapper_service2():
    service_file_path = "/etc/systemd/system/tinymapper_2.service"
    
    if not os.path.exists(service_file_path):
        print(f"\033[91mError: {service_file_path} not found.\033[0m")
        return

    with open(service_file_path, 'r') as file:
        lines = file.readlines()
    
    exec_start_line = None
    for line in lines:
        if line.strip().startswith("ExecStart"): 
            exec_start_line = line
            break

    if not exec_start_line:
        print("\033[91mError: ExecStart line not found in the service file.\033[0m")
        return
    
    pattern = r"-l\s([0-9\.]+):(\d+)\s-r\s([0-9\.]+):(\d+)\s(-u|-t)?"
    match = re.search(pattern, exec_start_line)
    
    if not match:
        print("\033[91mError: Could not parse the ExecStart line.\033[0m")
        return
    
    current_listen_address = match.group(1)
    current_listen_port = match.group(2)
    current_target_address = match.group(3)
    current_target_port = match.group(4)
    current_flags = match.group(5) or ''

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinymapper \033[93mService \033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m')

    print(f"\n\033[92mCurrent Tinymapper Service File:\033[0m")
    for line in lines:
        print(f"\033[97m{line.strip()}\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    print("\n\033[93mEditing line...\033[0m")
    
    listen_address = input(f"\033[93mEnter \033[92mListen Address\033[97m (current: {current_listen_address}):\033[0m") or current_listen_address
    listen_port = input(f"\033[93mEnter \033[92mListen Port\033[97m (current: {current_listen_port}): \033[0m") or current_listen_port
    target_address = input(f"\033[93mEnter \033[92mTarget Address\033[97m (current: {current_target_address}): \033[0m") or current_target_address
    target_port = input(f"\033[93mEnter \033[92mTarget Port\033[97m (current: {current_target_port}): \033[0m") or current_target_port

    print(f"\n\033[93mCurrent Flags: \033[92m{current_flags}\033[0m")
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("\033[93mChoose protocol for tinymapper service:\033[0m")
    print("\033[92m1.\033[97m UDP only (-u)\033[0m")
    print("\033[92m2.\033[97m TCP only (-t)\033[0m")
    print("\033[92m3.\033[97m Both UDP and TCP (-u and -t)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input("\033[93mEnter your choice (1/2/3): \033[0m").strip()

    if choice == '1':
        new_flags = ' -u' 
    elif choice == '2':
        new_flags = ' -t'  
    elif choice == '3':
        new_flags = ' -u -t'  
    else:
        print("\033[91mno choice. No flags will be applied.\033[0m")
        new_flags = ''

    new_exec_start = f"ExecStart=/usr/local/bin/tinymapper -l {listen_address}:{listen_port} -r {target_address}:{target_port}{new_flags}\n"
    
    for idx, line in enumerate(lines):
        if line.strip().startswith("ExecStart"):
            lines[idx] = new_exec_start
            break
    
    with open(service_file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"\n\033[92mTinymapper service updated with the following:\033[0m")
    print(f"\033[97m{new_exec_start}\033[0m")
    
    os.system("systemctl daemon-reload")
    display_checkmark("\033[92mSystemd configuration reloaded.\033[0m")

    restart = input("\n\033[93mDo you want to restart \033[92mthe tinymapper\033[93m service now? (\033[92my\033[93m/\033[91mn\033[93m): \033[0m").strip().lower()
    if restart == 'y':
        os.system("systemctl restart tinymapper_2.service")
        display_checkmark("\033[92mTinymapper service restarted.\033[0m")
    else:
        print("\033[93mTinymapper service restart skipped.\033[0m")

def edit_tinymapper_service3():
    service_file_path = "/etc/systemd/system/tinymapper_3.service"
    
    if not os.path.exists(service_file_path):
        print(f"\033[91mError: {service_file_path} not found.\033[0m")
        return

    with open(service_file_path, 'r') as file:
        lines = file.readlines()
    
    exec_start_line = None
    for line in lines:
        if line.strip().startswith("ExecStart"):  
            exec_start_line = line
            break

    if not exec_start_line:
        print("\033[91mError: ExecStart line not found in the service file.\033[0m")
        return
    
    pattern = r"-l\s([0-9\.]+):(\d+)\s-r\s([0-9\.]+):(\d+)\s(-u|-t)?"
    match = re.search(pattern, exec_start_line)
    
    if not match:
        print("\033[91mError: Could not parse the ExecStart line.\033[0m")
        return
    
    current_listen_address = match.group(1)
    current_listen_port = match.group(2)
    current_target_address = match.group(3)
    current_target_port = match.group(4)
    current_flags = match.group(5) or ''

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinymapper \033[93mService \033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m')

    print(f"\n\033[92mCurrent Tinymapper Service File:\033[0m")
    for line in lines:
        print(f"\033[97m{line.strip()}\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    print("\n\033[93mEditing line...\033[0m")
    
    listen_address = input(f"\033[93mEnter \033[92mListen Address\033[97m (current: {current_listen_address}):\033[0m") or current_listen_address
    listen_port = input(f"\033[93mEnter \033[92mListen Port\033[97m (current: {current_listen_port}): \033[0m") or current_listen_port
    target_address = input(f"\033[93mEnter \033[92mTarget Address\033[97m (current: {current_target_address}): \033[0m") or current_target_address
    target_port = input(f"\033[93mEnter \033[92mTarget Port\033[97m (current: {current_target_port}): \033[0m") or current_target_port

    print(f"\n\033[93mCurrent Flags: \033[92m{current_flags}\033[0m")
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("\033[93mChoose protocol for tinymapper service:\033[0m")
    print("\033[92m1.\033[97m UDP only (-u)\033[0m")
    print("\033[92m2.\033[97m TCP only (-t)\033[0m")
    print("\033[92m3.\033[97m Both UDP and TCP (-u and -t)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input("\033[93mEnter your choice (1/2/3): \033[0m").strip()

    if choice == '1':
        new_flags = ' -u'  
    elif choice == '2':
        new_flags = ' -t' 
    elif choice == '3':
        new_flags = ' -u -t'  
    else:
        print("\033[91mno choice. No flags will be applied.\033[0m")
        new_flags = ''

    new_exec_start = f"ExecStart=/usr/local/bin/tinymapper -l {listen_address}:{listen_port} -r {target_address}:{target_port}{new_flags}\n"
    
    for idx, line in enumerate(lines):
        if line.strip().startswith("ExecStart"):
            lines[idx] = new_exec_start
            break
    
    with open(service_file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"\n\033[92mTinymapper service updated with the following:\033[0m")
    print(f"\033[97m{new_exec_start}\033[0m")
    
    os.system("systemctl daemon-reload")
    display_checkmark("\033[92mSystemd configuration reloaded.\033[0m")

    restart = input("\n\033[93mDo you want to restart \033[92mthe tinymapper\033[93m service now? (\033[92my\033[93m/\033[91mn\033[93m): \033[0m").strip().lower()
    if restart == 'y':
        os.system("systemctl restart tinymapper_3.service")
        display_checkmark("\033[92mTinymapper service restarted.\033[0m")
    else:
        print("\033[93mTinymapper service restart skipped.\033[0m")

def edit_tinymapper_service4():
    service_file_path = "/etc/systemd/system/tinymapper_4.service"
    
    if not os.path.exists(service_file_path):
        print(f"\033[91mError: {service_file_path} not found.\033[0m")
        return

    with open(service_file_path, 'r') as file:
        lines = file.readlines()
    
    exec_start_line = None
    for line in lines:
        if line.strip().startswith("ExecStart"): 
            exec_start_line = line
            break

    if not exec_start_line:
        print("\033[91mError: ExecStart line not found in the service file.\033[0m")
        return
    
    pattern = r"-l\s([0-9\.]+):(\d+)\s-r\s([0-9\.]+):(\d+)\s(-u|-t)?"
    match = re.search(pattern, exec_start_line)
    
    if not match:
        print("\033[91mError: Could not parse the ExecStart line.\033[0m")
        return
    
    current_listen_address = match.group(1)
    current_listen_port = match.group(2)
    current_target_address = match.group(3)
    current_target_port = match.group(4)
    current_flags = match.group(5) or ''

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinymapper \033[93mService \033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m')

    print(f"\n\033[92mCurrent Tinymapper Service File:\033[0m")
    for line in lines:
        print(f"\033[97m{line.strip()}\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    print("\n\033[93mEditing line...\033[0m")
    
    listen_address = input(f"\033[93mEnter \033[92mListen Address\033[97m (current: {current_listen_address}):\033[0m") or current_listen_address
    listen_port = input(f"\033[93mEnter \033[92mListen Port\033[97m (current: {current_listen_port}): \033[0m") or current_listen_port
    target_address = input(f"\033[93mEnter \033[92mTarget Address\033[97m (current: {current_target_address}): \033[0m") or current_target_address
    target_port = input(f"\033[93mEnter \033[92mTarget Port\033[97m (current: {current_target_port}): \033[0m") or current_target_port

    print(f"\n\033[93mCurrent Flags: \033[92m{current_flags}\033[0m")
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("\033[93mChoose protocol for tinymapper service:\033[0m")
    print("\033[92m1.\033[97m UDP only (-u)\033[0m")
    print("\033[92m2.\033[97m TCP only (-t)\033[0m")
    print("\033[92m3.\033[97m Both UDP and TCP (-u and -t)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input("\033[93mEnter your choice (1/2/3): \033[0m").strip()

    if choice == '1':
        new_flags = ' -u' 
    elif choice == '2':
        new_flags = ' -t' 
    elif choice == '3':
        new_flags = ' -u -t'  
    else:
        print("\033[91mno choice. No flags will be applied.\033[0m")
        new_flags = ''

    new_exec_start = f"ExecStart=/usr/local/bin/tinymapper -l {listen_address}:{listen_port} -r {target_address}:{target_port}{new_flags}\n"
    
    for idx, line in enumerate(lines):
        if line.strip().startswith("ExecStart"):
            lines[idx] = new_exec_start
            break
    
    with open(service_file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"\n\033[92mTinymapper service updated with the following:\033[0m")
    print(f"\033[97m{new_exec_start}\033[0m")
    
    os.system("systemctl daemon-reload")
    display_checkmark("\033[92mSystemd configuration reloaded.\033[0m")

    restart = input("\n\033[93mDo you want to restart \033[92mthe tinymapper\033[93m service now? (\033[92my\033[93m/\033[91mn\033[93m): \033[0m").strip().lower()
    if restart == 'y':
        os.system("systemctl restart tinymapper_4.service")
        display_checkmark("\033[92mTinymapper service restarted.\033[0m")
    else:
        print("\033[93mTinymapper service restart skipped.\033[0m")

def edit_tinymapper_service5():
    service_file_path = "/etc/systemd/system/tinymapper_5.service"
    
    if not os.path.exists(service_file_path):
        print(f"\033[91mError: {service_file_path} not found.\033[0m")
        return

    with open(service_file_path, 'r') as file:
        lines = file.readlines()
    
    exec_start_line = None
    for line in lines:
        if line.strip().startswith("ExecStart"):  
            exec_start_line = line
            break

    if not exec_start_line:
        print("\033[91mError: ExecStart line not found in the service file.\033[0m")
        return
    
    pattern = r"-l\s([0-9\.]+):(\d+)\s-r\s([0-9\.]+):(\d+)\s(-u|-t)?"
    match = re.search(pattern, exec_start_line)
    
    if not match:
        print("\033[91mError: Could not parse the ExecStart line.\033[0m")
        return
    
    current_listen_address = match.group(1)
    current_listen_port = match.group(2)
    current_target_address = match.group(3)
    current_target_port = match.group(4)
    current_flags = match.group(5) or ''

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinymapper \033[93mService \033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m')

    print(f"\n\033[92mCurrent Tinymapper Service File:\033[0m")
    for line in lines:
        print(f"\033[97m{line.strip()}\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    print("\n\033[93mEditing line...\033[0m")
    
    listen_address = input(f"\033[93mEnter \033[92mListen Address\033[97m (current: {current_listen_address}):\033[0m") or current_listen_address
    listen_port = input(f"\033[93mEnter \033[92mListen Port\033[97m (current: {current_listen_port}): \033[0m") or current_listen_port
    target_address = input(f"\033[93mEnter \033[92mTarget Address\033[97m (current: {current_target_address}): \033[0m") or current_target_address
    target_port = input(f"\033[93mEnter \033[92mTarget Port\033[97m (current: {current_target_port}): \033[0m") or current_target_port

    print(f"\n\033[93mCurrent Flags: \033[92m{current_flags}\033[0m")
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("\033[93mChoose protocol for tinymapper service:\033[0m")
    print("\033[92m1.\033[97m UDP only (-u)\033[0m")
    print("\033[92m2.\033[97m TCP only (-t)\033[0m")
    print("\033[92m3.\033[97m Both UDP and TCP (-u and -t)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input("\033[93mEnter your choice (1/2/3): \033[0m").strip()

    if choice == '1':
        new_flags = ' -u'  
    elif choice == '2':
        new_flags = ' -t' 
    elif choice == '3':
        new_flags = ' -u -t'  
    else:
        print("\033[91mno choice. No flags will be applied.\033[0m")
        new_flags = ''

    new_exec_start = f"ExecStart=/usr/local/bin/tinymapper -l {listen_address}:{listen_port} -r {target_address}:{target_port}{new_flags}\n"
    
    for idx, line in enumerate(lines):
        if line.strip().startswith("ExecStart"):
            lines[idx] = new_exec_start
            break
    
    with open(service_file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"\n\033[92mTinymapper service updated with the following:\033[0m")
    print(f"\033[97m{new_exec_start}\033[0m")
    
    os.system("systemctl daemon-reload")
    display_checkmark("\033[92mSystemd configuration reloaded.\033[0m")

    restart = input("\n\033[93mDo you want to restart \033[92mthe tinymapper\033[93m service now? (\033[92my\033[93m/\033[91mn\033[93m): \033[0m").strip().lower()
    if restart == 'y':
        os.system("systemctl restart tinymapper_5.service")
        display_checkmark("\033[92mTinymapper service restarted.\033[0m")
    else:
        print("\033[93mTinymapper service restart skipped.\033[0m")

def read_proxyforwarder_config():
    config_path = "/usr/local/bin/proxyforwarder/src/config.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found!")
        return None

    with open(config_path, "r") as file:
        config_content = yaml.safe_load(file)

    return config_content

def prompt_for_editp(field_name, current_value=None, is_new=False):

    if is_new:
        example_values = {
            "Listen Address": "0.0.0.0",
            "Listen Port": "20820",
            "Target Address": "10.22.22.1",
            "Target Port": "20820"
        }
        example_value = example_values.get(field_name, f"Example: {field_name}") 
        print(f"\033[93mAdd {field_name} (Example: \033[94m{example_value}\033[93m):\033[0m", end=" ")
        value = input("\033[92mEnter new value \033[93m: \033[0m").strip() 
    else:
        print(f"\033[93mEdit {field_name} (current value: \033[94m{current_value}\033[93m):\033[0m", end=" ")
        value = input("\033[92mEnter new value\033[97m (press enter to keep current)\033[93m: \033[0m").strip()

    if is_new and not value:
        return example_value.split(": ")[1]  
    return value if value else current_value


def edit_forwarders(forwarders):
    while True:
        os.system("clear")
        print("\033[93m───────────────────────────────────────\033[0m")
        print("\033[93mCurrent Forwarders:\033[0m")
        for idx, forwarder in enumerate(forwarders):
            print("\033[93m───────────────────────────────────────\033[0m")
            print(f"\n\033[93mForwarder033[96m {idx + 1}:\033[0m")
            print(f"  Listen Address: {forwarder['listen_address']}")
            print(f"  Listen Port: {forwarder['listen_port']}")
            print(f"  Target Address: {forwarder['target_address']}")
            print(f"  Target Port: {forwarder['target_port']}")
            print("\033[93m───────────────────────────────────────\033[0m")
        
        print("\n\033[93mChoose a forwarder to \033[92medit:\033[0m")
        print("0)\033[93m Add a \033[92mnew forwarder\033[0m")
        for idx in range(len(forwarders)):
            print(f"\033[97m{idx + 1})\033[93m Edit Forwarder\033[97m {idx + 1}\033[0m")
        print(f"{len(forwarders) + 1})\033[91m Delete a forwarder\033[0m")  
        print(f"{len(forwarders) + 2})\033[94m Back to Previous Menu\033[0m")  
        
        choice = input("\n\033[93mEnter your choice \033[92m(0 to add new, \033[97mnumber to edit, \033[91mnumber to delete, or \033[93mback to exit): \033[0m")

        if choice == '0': 
            forwarder = {}
            forwarder['listen_address'] = prompt_for_editp("Listen Address", "0.0.0.0", is_new=True)
            forwarder['listen_port'] = int(prompt_for_editp("Listen Port", 2020, is_new=True))
            forwarder['target_address'] = prompt_for_editp("Target Address", "66.200.1.1", is_new=True)
            forwarder['target_port'] = int(prompt_for_editp("Target Port", 2020, is_new=True))
            forwarders.append(forwarder)
            display_checkmark("\n\033[92mNew forwarder added!\033[0m")
            print("\033[93m───────────────────────────────────────\033[0m")
        elif choice.isdigit() and 1 <= int(choice) <= len(forwarders): 
            idx = int(choice) - 1
            print(f"\nEditing Forwarder {idx + 1}:")
            forwarders[idx]['listen_address'] = prompt_for_editp("Listen Address", forwarders[idx]['listen_address'])
            forwarders[idx]['listen_port'] = int(prompt_for_editp("Listen Port", forwarders[idx]['listen_port']))
            forwarders[idx]['target_address'] = prompt_for_editp("Target Address", forwarders[idx]['target_address'])
            forwarders[idx]['target_port'] = int(prompt_for_editp("Target Port", forwarders[idx]['target_port']))
            display_checkmark(f"\n\033[92mForwarder {idx + 1} updated!\033[0m")
            print("\033[93m───────────────────────────────────────\033[0m")
        
        elif choice == str(len(forwarders) + 1): 
            print("\n\033[91mChoose a forwarder to delete:\033[0m")
            for idx, forwarder in enumerate(forwarders, 1):
                print(f"{idx}) Forwarder {idx}")
            delete_choice = input("\033[93mEnter the number of the forwarder you want to delete: \033[0m")
            
            if delete_choice.isdigit() and 1 <= int(delete_choice) <= len(forwarders):
                forwarders.pop(int(delete_choice) - 1)
                display_checkmark("\n\033[91mForwarder deleted!\033[0m")
                print("\033[93m───────────────────────────────────────\033[0m")
            else:
                print("\033[91mInvalid selection.\033[0m")
        
        elif choice == str(len(forwarders) + 2):  
            break
        
        else:
            print("Wrong choice. Please try again.")
            continue

        continue_editing = input("\n\033[93mDo you want to edit \033[92manother forwarder\033[93m? (\033[92my\033[93m/\033[91mn\033[93m):\033[0m ").strip().lower()
        if continue_editing != 'y':
            break

    return forwarders


def reload_and_restart_proxy_service():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "proxyforwarder"])

    display_checkmark("\033[92mproxyforwarder service updated and restarted successfully\033[0m")

def edit_thread_pool(thread_pool):
    thread_pool['threads'] = int(prompt_for_edit("Thread Pool Size", thread_pool['threads']))
    return thread_pool

def edit_max_connections(max_connections):
    return int(prompt_for_edit("Max Connections", max_connections))

def edit_retry_attempts(retry_attempts):
    return int(prompt_for_edit("Retry Attempts", retry_attempts))

def edit_retry_delay(retry_delay):
    return int(prompt_for_edit("Retry Delay", retry_delay))

def edit_tcp_no_delay(tcp_no_delay):
    new_value = input(f"\033[93mEdit TCP No Delay\033[97m (current value: {tcp_no_delay}): \033[0m")
    return new_value.strip().lower() == "true" if new_value else tcp_no_delay

def edit_buffer_size(buffer_size):
    return int(prompt_for_edit("Buffer Size", buffer_size))

def edit_monitoring_port(monitoring_port):
    return int(prompt_for_edit("Monitoring Port", monitoring_port))

def edit_timeout(timeout):
    timeout['connection'] = int(prompt_for_edit("Connection Timeout", timeout['connection']))
    return timeout

def edit_health_check(health_check):
    health_check['enabled'] = input(f"\033[93mEnable Health Check\033[97m (current value: {health_check['enabled']}): \033[0m").strip().lower() == "true"
    if health_check['enabled']:
        health_check['interval'] = int(prompt_for_edit("Health Check Interval", health_check['interval']))
    return health_check

def edit_tcp_keep_alive(tcp_keep_alive):
    tcp_keep_alive['enabled'] = input(f"\033[93mEnable TCP Keep Alive\033[97m (current value: {tcp_keep_alive['enabled']}): \033[0m").strip().lower() == "true"
    if tcp_keep_alive['enabled']:
        tcp_keep_alive['idle'] = int(prompt_for_edit("Idle Time (seconds)", tcp_keep_alive['idle']))
        tcp_keep_alive['interval'] = int(prompt_for_edit("Interval (seconds)", tcp_keep_alive['interval']))
        tcp_keep_alive['count'] = int(prompt_for_edit("Count", tcp_keep_alive['count']))
    return tcp_keep_alive

def edit_logging(logging):
    logging['enabled'] = input(f"\033[93mEnable Logging\033[97m (current value: {logging['enabled']}): \033[0m").strip().lower() == "true"
    if logging['enabled']:
        logging['file'] = prompt_for_edit("Log File", logging['file'])
        logging['level'] = prompt_for_edit("Log Level", logging['level'])
    return logging

def update_proxyforwarder_config(config_content):
    with open("/usr/local/bin/proxyforwarder/src/config.yaml", "w") as file:
        yaml.dump(config_content, file, default_flow_style=False)

def edit_proxyforwarder_config():
    config_content = read_proxyforwarder_config()
    if not config_content:
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mProxyforwarder \033[93mConfig \033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    
    while True:
        print("\n1)\033[93m Edit \033[92mForwarders\033[0m")
        print(f"2)\033[93m Edit \033[92mThread Pool Size\033[97m (current: {config_content['thread_pool']['threads']})\033[0m")
        print(f"3)\033[93m Edit \033[92mMax Connections\033[97m (current: {config_content['max_connections']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRetry Attempts\033[97m (current: {config_content['retry_attempts']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRetry Delay\033[97m (current: {config_content['retry_delay']})\033[0m")
        print(f"6)\033[93m Edit \033[92mTCP No Delay\033[97m (current: {config_content['tcp_no_delay']})\033[0m")
        print(f"7)\033[93m Edit \033[92mBuffer Size\033[97m (current: {config_content['buffer_size']})\033[0m")
        print(f"8)\033[93m Edit \033[92mMonitoring Port\033[97m (current: {config_content['monitoring_port']})\033[0m")
        print(f"9)\033[93m Edit \033[92mTimeout\033[97m (current: {config_content['timeout']['connection']})\033[0m")
        print(f"10)\033[93m Edit \033[92mHealth Check\033[97m (current: {config_content['health_check']['enabled']})\033[0m")
        print(f"11)\033[93m Edit \033[92mTCP Keep Alive\033[97m (current: {config_content['tcp_keep_alive']['enabled']})\033[0m")
        print(f"12)\033[93m Edit \033[92mLogging\033[97m (current: {config_content['logging']['enabled']})\033[0m")
        print("13)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")

        choice = input("\nChoose an option: ")

        if choice == '1':
            config_content['forwarders'] = edit_forwarders(config_content['forwarders'])
        elif choice == '2':
            config_content['thread_pool'] = edit_thread_pool(config_content['thread_pool'])
        elif choice == '3':
            config_content['max_connections'] = edit_max_connections(config_content['max_connections'])
        elif choice == '4':
            config_content['retry_attempts'] = edit_retry_attempts(config_content['retry_attempts'])
        elif choice == '5':
            config_content['retry_delay'] = edit_retry_delay(config_content['retry_delay'])
        elif choice == '6':
            config_content['tcp_no_delay'] = edit_tcp_no_delay(config_content['tcp_no_delay'])
        elif choice == '7':
            config_content['buffer_size'] = edit_buffer_size(config_content['buffer_size'])
        elif choice == '8':
            config_content['monitoring_port'] = edit_monitoring_port(config_content['monitoring_port'])
        elif choice == '9':
            config_content['timeout'] = edit_timeout(config_content['timeout'])
        elif choice == '10':
            config_content['health_check'] = edit_health_check(config_content['health_check'])
        elif choice == '11':
            config_content['tcp_keep_alive'] = edit_tcp_keep_alive(config_content['tcp_keep_alive'])
        elif choice == '12':
            config_content['logging'] = edit_logging(config_content['logging'])
        elif choice == '13':
            update_proxyforwarder_config(config_content)
            reload_and_restart_proxy_service()
            display_checkmark("\033[92mConfiguration saved successfully\033[0m")
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_udp_config():
    config_content = read_udp_config()
    if not config_content:
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUDP \033[93mConfig \033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )

    while True:
        print("\n1)\033[93m Edit \033[92mSource Address Ports\033[0m")
        print(f"2)\033[93m Edit \033[92mDestination Address Ports\033[97m (current: {', '.join(config_content['dstAddrPorts'])})\033[0m")
        print(f"3)\033[93m Edit \033[92mTimeout\033[97m (current: {config_content['timeout']})\033[0m")
        print(f"4)\033[93m Edit \033[92mBuffer Size\033[97m (current: {config_content['buffer_size']})\033[0m")
        print(f"5)\033[93m Edit \033[92mThread Pool Size\033[97m (current: {config_content['thread_pool']['threads']})\033[0m")
        print(f"6)\033[93m Edit \033[92mLogging\033[97m (current: {config_content['logging']['enabled']})\033[0m")
        print(f"7)\033[93m Edit \033[92mMonitoring Port\033[97m (current: {config_content['monitoring_port']})\033[0m")
        print("8)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")

        choice = input("\nChoose an option: ")

        if choice == '1':
            config_content['srcAddrPorts'] = edit_srcAddrPorts(config_content['srcAddrPorts'])
        elif choice == '2':
            config_content['dstAddrPorts'] = edit_dstAddrPorts(config_content['dstAddrPorts'])
        elif choice == '3':
            config_content['timeout'] = edit_timeout(config_content['timeout'])
        elif choice == '4':
            config_content['buffer_size'] = edit_buffer_size(config_content['buffer_size'])
        elif choice == '5':
            config_content['thread_pool'] = edit_thread_pool(config_content['thread_pool'])
        elif choice == '6':
            config_content['logging'] = edit_logging(config_content['logging'])
        elif choice == '7':
            config_content['monitoring_port'] = edit_monitoring_port(config_content['monitoring_port'])
        elif choice == '8':
            update_udp_config(config_content)
            reload_and_restart_udp_service()
            display_checkmark("\033[92mConfiguration saved successfully\033[0m")
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

CONFIG_PATH = "/usr/local/bin/proxyforwarder/src/config.yaml"  

def read_udp_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading UDP config: {e}")
        return None

def update_udp_config(config_content):
    try:
        with open(CONFIG_PATH, "w") as file:
            yaml.dump(config_content, file)
    except Exception as e:
        print(f"Error saving UDP config: {e}")

def edit_srcAddrPorts(srcAddrPorts):
    print(f"\033[93mCurrent source address ports:\033[97m {', '.join(srcAddrPorts)}\033[0m")
    choice = input("\033[93mDo you want to \033[92medit an existing port\033[96m (1), \033[97mor add a new one \033[93m(2), \033[91mor delete a port \033[91m(3)? \033[0m").strip().lower()
    
    if choice == '1':
        print("\033[93mChoose a \033[92mport \033[93mto edit:\033[0m")
        for i, port in enumerate(srcAddrPorts, 1):
            print(f"{i}) {port}")
        
        try:
            edit_choice = int(input(f"\033[93mEnter the \033[92mnumber of the port\033[93m you want to edit (1-{len(srcAddrPorts)}):\033[0m "))
            if 1 <= edit_choice <= len(srcAddrPorts):
                new_port = input(f"\033[93mEnter the \033[92mnew source address port\033[93m for {srcAddrPorts[edit_choice - 1]}: \033[0m")
                srcAddrPorts[edit_choice - 1] = new_port.strip()  
                display_checkmark(f"\033[92mPort {srcAddrPorts[edit_choice - 1]} has been updated\033[0m")
                print("\033[93m───────────────────────────────────────\033[0m")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    elif choice == '2':
        new_port = input("\033[93mEnter the \033[92mnew source address port\033[97m (format 0.0.0.0:port)\033[93m:\033[0m ").strip()
        if ':' in new_port:
            srcAddrPorts.append(new_port)
            display_checkmark(f"\033[92mNew port {new_port} has been added\033[0m")
            print("\033[93m───────────────────────────────────────\033[0m")
        else:
            print("Invalid port format. Please use the format 0.0.0.0:port.")
    
    elif choice == '3':
        print("\033[93mChoose a \033[91mport \033[93mto delete:\033[0m")
        for i, port in enumerate(srcAddrPorts, 1):
            print(f"{i}) {port}")
        
        try:
            delete_choice = int(input(f"\033[93mEnter the \033[92mnumber of the port\033[93m you want to delete (1-{len(srcAddrPorts)}):\033[0m "))
            if 1 <= delete_choice <= len(srcAddrPorts):
                deleted_port = srcAddrPorts.pop(delete_choice - 1)
                display_checkmark(f"\033[91mPort {deleted_port} has been deleted\033[0m")
                print("\033[93m───────────────────────────────────────\033[0m")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    else:
        print("\033[91mInvalid choice\033[93m. Please enter \033[92m'1' \033[93mto edit, \033[92m'2' \033[93mto add, or \033[91m'3'\033[93m to delete.\033[0m")

    return srcAddrPorts


def edit_dstAddrPorts(dstAddrPorts):
    print(f"\033[93mCurrent destination address ports: \033[97m{', '.join(dstAddrPorts)}\033[0m")
    choice = input("\033[93mDo you want to \033[92medit an existing port\033[96m (1), \033[97mor add a new one \033[93m(2), \033[91mor delete a port \033[91m(3)? \033[0m").strip().lower()
    
    if choice == '1':
        print("\033[93mChoose a\033[92m port to edit\033[93m:\033[0m")
        for i, port in enumerate(dstAddrPorts, 1):
            print(f"{i}) {port}")
        
        try:
            edit_choice = int(input(f"\033[93mEnter the \033[92mnumber of the port\033[93m you want to edit (1-{len(dstAddrPorts)}): \033[0m"))
            if 1 <= edit_choice <= len(dstAddrPorts):
                new_port = input(f"\033[93mEnter the\033[92m new destination address port\033[93m for {dstAddrPorts[edit_choice - 1]}:\033[0m")
                dstAddrPorts[edit_choice - 1] = new_port.strip()  
                display_checkmark(f"\033[92mPort {dstAddrPorts[edit_choice - 1]} has been updated.\033[0m")
                print("\033[93m───────────────────────────────────────\033[0m")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    elif choice == '2':
        new_port = input("\033[93mEnter the \033[92mnew destination address port\033[97m (format 10.22.22.1:port):\033[0m ").strip()
        if ':' in new_port:
            dstAddrPorts.append(new_port)
            display_checkmark(f"\033[92mNew port {new_port} has been added\033[0m")
            print("\033[93m───────────────────────────────────────\033[0m")
        else:
            print("Invalid port format. Please use the format ip:port.")
    
    elif choice == '3':
        print("\033[93mChoose a \033[91mport \033[93mto delete:\033[0m")
        for i, port in enumerate(dstAddrPorts, 1):
            print(f"{i}) {port}")
        
        try:
            delete_choice = int(input(f"\033[93mEnter the \033[92mnumber of the port\033[93m you want to delete (1-{len(dstAddrPorts)}):\033[0m "))
            if 1 <= delete_choice <= len(dstAddrPorts):
                deleted_port = dstAddrPorts.pop(delete_choice - 1)
                display_checkmark(f"\033[91mPort {deleted_port} has been deleted\033[0m")
                print("\033[93m───────────────────────────────────────\033[0m")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    else:
        print("\033[91mInvalid choice\033[93m. Please enter \033[92m'1' \033[93mto edit, \033[92m'2' \033[93mto add, or \033[91m'3'\033[93m to delete.\033[0m")

    return dstAddrPorts



def edit_timeout(timeout):
    print(f"\033[93mCurrent timeout: \033[97m{timeout}\033[0m")
    new_timeout = input("\033[93mEnter \033[92mnew timeout value\033[93m:\033[0m ")
    return int(new_timeout)

def edit_buffer_size(buffer_size):
    print(f"\033[93mCurrent buffer size:\033[97m {buffer_size}\033[0m")
    new_size = input("\033[93mEnter \033[92mnew buffer size\033[93m:\033[0m ")
    return int(new_size)

def edit_thread_pool(thread_pool):
    print(f"\033[93mCurrent thread pool size:\033[97m {thread_pool['threads']}\033[0m")
    new_size = input("\033[93mEnter \033[92mnew thread pool size\033[93m:\033[0m ")
    thread_pool['threads'] = int(new_size)
    return thread_pool

def edit_logging(logging):
    print(f"\033[93mCurrent logging enabled:\033[97m {logging['enabled']}\033[0m")
    new_enabled = input("\033[93mEnable \033[92mlogging\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    logging['enabled'] = new_enabled == 'yes'
    return logging

def edit_monitoring_port(monitoring_port):
    print(f"Current monitoring port: {monitoring_port}")
    new_port = input("\033[93mEnter \033[92mnew monitoring port\033[93m:\033[0m ")
    return int(new_port)

def reload_and_restart_udp_service():
    os.system("systemctl restart proxyforwarder")

def display_checkmark(message):
    print(f"{message} \033[92m✓\033[0m")


def edit_udp2raw_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mEdit udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-2): ").strip()

    if choice == "1":
        edit_udp2raw_service_menu()
    elif choice == "2":
        edit_udp2raw_client_service()
    elif choice == "0":
        edit_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def edit_udp2raw_service_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mEdit udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server Config [1]\033[0m")
    print("2)\033[93m Server Config [2]\033[0m")
    print("3)\033[92m Server Config [3]\033[0m")
    print("4)\033[93m Server Config [4]\033[0m")
    print("5)\033[93m Server Config [5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        edit_udp2raw_service1()
    elif choice == "2":
        edit_udp2raw_service2()
    elif choice == "3":
        edit_udp2raw_service3()
    elif choice == "4":
        edit_udp2raw_service4()
    elif choice == "5":
        edit_udp2raw_service5()
    elif choice == "0":
        edit_udp2raw_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def read_udp2raw_service1():
    service_path = "/etc/systemd/system/udp2raw_1.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_udp2raw_service2():
    service_path = "/etc/systemd/system/udp2raw_2.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_udp2raw_service3():
    service_path = "/etc/systemd/system/udp2raw_3.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_udp2raw_service4():
    service_path = "/etc/systemd/system/udp2raw_4.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_udp2raw_service5():
    service_path = "/etc/systemd/system/udp2raw_5.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def parse_udp2raw_execstart(service_content):
    for line in service_content.splitlines():
        if line.startswith("ExecStart"):
            return line.split("ExecStart=")[1].strip()
    return None

def extract_udp2raw_parameters(command):
    parameters = {}

    port_match = re.search(r"-l0.0.0.0:(\d+)", command)
    if port_match:
        parameters["port"] = port_match.group(1)

    password_match = re.search(r'-k "([^"]+)"', command)
    if password_match:
        parameters["password"] = password_match.group(1)

    remote_ip_match = re.search(r"-r (\S+):(\d+)", command)
    if remote_ip_match:
        parameters["remote_ip"] = remote_ip_match.group(1)
        parameters["remote_port"] = remote_ip_match.group(2)

    raw_mode_match = re.search(r"--raw-mode (\S+)", command)
    if raw_mode_match:
        parameters["raw_mode"] = raw_mode_match.group(1)

    return parameters

def prompt_for_edit_udp2raw(parameter_name, current_value, valid_options=None):
    if valid_options:
        print(f"Choose a {parameter_name}:")
        for i, option in enumerate(valid_options, start=1):
            print(f"{i}) {option}")
        
        choice = input(f"\033[93mCurrent value is \033[97m{current_value}. \033[93mEnter the number to change \033[96m(or press Enter to keep current): \033[0m").strip()
        
        if choice:
            try:
                choice = int(choice)
                if 1 <= choice <= len(valid_options):
                    return valid_options[choice - 1]
                else:
                    print(f"Invalid choice. Keeping the current value: {current_value}")
            except ValueError:
                print(f"Invalid input. Keeping the current value: {current_value}")
        return current_value
    return input(f"\033[93mEdit {parameter_name} \033[92m(current value: {current_value}):\033[0m ").strip() or current_value


def update_udp2raw_execstart_server(command, new_parameters):
    command = re.sub(r"-l0.0.0.0:\d+", f"-l0.0.0.0:{new_parameters['port']}", command)  
    command = re.sub(r'-k "[^"]+"', f'-k "{new_parameters["password"]}"', command) 
    command = re.sub(r"-r \S+:\d+", f"-r {new_parameters['remote_ip']}:{new_parameters['remote_port']}", command) 
    command = re.sub(r"--raw-mode \S+", f"--raw-mode {new_parameters['raw_mode']}", command)  

    return command

def save_udp2raw_service_file_server1(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw_1.service", "w") as file:
        file.write(updated_content)

def save_udp2raw_service_file_server2(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw_2.service", "w") as file:
        file.write(updated_content)

def save_udp2raw_service_file_server3(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw_3.service", "w") as file:
        file.write(updated_content)

def save_udp2raw_service_file_server4(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw_4.service", "w") as file:
        file.write(updated_content)

def save_udp2raw_service_file_server5(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw_5.service", "w") as file:
        file.write(updated_content)

def reload_and_restart_udp2raw_service_server1():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw_1"])

    display_checkmark("\033[92mudp2raw_1 service updated and restarted successfully\033[0m")

def reload_and_restart_udp2raw_service_server2():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw_2"])

    display_checkmark("\033[92mudp2raw_2 service updated and restarted successfully\033[0m")

def reload_and_restart_udp2raw_service_server3():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw_3"])

    display_checkmark("\033[92mudp2raw_3 service updated and restarted successfully\033[0m")

def reload_and_restart_udp2raw_service_server4():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw_4"])

    display_checkmark("\033[92mudp2raw_4 service updated and restarted successfully\033[0m")

def reload_and_restart_udp2raw_service_server5():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw_5"])

    display_checkmark("\033[92mudp2raw_5 service updated and restarted successfully\033[0m")

def edit_udp2raw_service1():
    service_content = read_udp2raw_service1()
    if not service_content:
        return

    current_command = parse_udp2raw_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_execstart_server(current_command, current_parameters)
            save_udp2raw_service_file_server1(service_content, updated_command)
            reload_and_restart_udp2raw_service_server1()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_udp2raw_service2():
    service_content = read_udp2raw_service2()
    if not service_content:
        return

    current_command = parse_udp2raw_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_execstart_server(current_command, current_parameters)
            save_udp2raw_service_file_server2(service_content, updated_command)
            reload_and_restart_udp2raw_service_server2()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_udp2raw_service3():
    service_content = read_udp2raw_service3()
    if not service_content:
        return

    current_command = parse_udp2raw_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_execstart_server(current_command, current_parameters)
            save_udp2raw_service_file_server3(service_content, updated_command)
            reload_and_restart_udp2raw_service_server3()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_udp2raw_service4():
    service_content = read_udp2raw_service4()
    if not service_content:
        return

    current_command = parse_udp2raw_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_execstart_server(current_command, current_parameters)
            save_udp2raw_service_file_server4(service_content, updated_command)
            reload_and_restart_udp2raw_service_server4()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_udp2raw_service5():
    service_content = read_udp2raw_service5()
    if not service_content:
        return

    current_command = parse_udp2raw_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return
    
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_execstart_server(current_command, current_parameters)
            save_udp2raw_service_file_server5(service_content, updated_command)
            reload_and_restart_udp2raw_service_server5()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def read_udp2raw_client_service():
    service_path = "/etc/systemd/system/udp2raw.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def parse_udp2raw_client_execstart(service_content):
    for line in service_content.splitlines():
        if line.startswith("ExecStart"):
            return line.split("ExecStart=")[1].strip()
    return None

def extract_udp2raw_client_parameters(command):
    parameters = {}

    port_match = re.search(r"-l0.0.0.0:(\d+)", command)
    if port_match:
        parameters["port"] = port_match.group(1)

    password_match = re.search(r'-k "([^"]+)"', command)
    if password_match:
        parameters["password"] = password_match.group(1)

    remote_ip_match = re.search(r"-r (\S+):(\d+)", command)
    if remote_ip_match:
        parameters["remote_ip"] = remote_ip_match.group(1)
        parameters["remote_port"] = remote_ip_match.group(2)

    raw_mode_match = re.search(r"--raw-mode (\S+)", command)
    if raw_mode_match:
        parameters["raw_mode"] = raw_mode_match.group(1)

    return parameters

def prompt_for_edit_udp2raw(parameter_name, current_value, valid_options=None):
    new_value = input(f"Edit {parameter_name} (current value: {current_value}): ")
    
    if valid_options and new_value not in valid_options:
        print(f"Invalid input. Please choose from {valid_options}")
        return current_value
    
    return new_value.strip() or current_value

def update_udp2raw_client_execstart(command, new_parameters):
    command = re.sub(r"-l0.0.0.0:\d+", f"-l0.0.0.0:{new_parameters['port']}", command)  
    command = re.sub(r'-k "[^"]+"', f'-k "{new_parameters["password"]}"', command)  
    command = re.sub(r"-r \S+:\d+", f"-r {new_parameters['remote_ip']}:{new_parameters['remote_port']}", command)  
    command = re.sub(r"--raw-mode \S+", f"--raw-mode {new_parameters['raw_mode']}", command) 

    return command

def save_udp2raw_client_service_file(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/udp2raw.service", "w") as file:
        file.write(updated_content)

def reload_and_restart_udp2raw_client_service():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "udp2raw"])

    display_checkmark("\033[92mudp2raw client service updated and restarted successfully\033[0m")

def prompt_for_raw_mode(current_value):
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("Choose the Raw Mode:")
    print("1)\033[93m UDP\033[0m")
    print("2)\033[92m ICMP\033[0m")
    print("3)\033[94m FakeTCP\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")
    
    choice = input(f"\033[93mCurrent raw mode:\033[94m {current_value}\033[93m. Choose a new option\033[97m (1, 2, or 3)\033[93m:\033[0m ")
    
    if choice == '1':
        return 'udp'
    elif choice == '2':
        return 'icmp'
    elif choice == '3':
        return 'faketcp'
    else:
        print("ٌWrong choice. Keeping the current value.")
        return current_value
    
def edit_udp2raw_client_service():
    service_content = read_udp2raw_client_service()
    if not service_content:
        return

    current_command = parse_udp2raw_client_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_udp2raw_client_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mudp2raw \033[93mClient Menu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mRaw Mode\033[97m (current: {current_parameters['raw_mode']})\033[0m")
        print("6)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_udp2raw("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_udp2raw("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_udp2raw("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_udp2raw("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["raw_mode"] = prompt_for_raw_mode(current_parameters["raw_mode"])
        elif choice == '6':
            updated_command = update_udp2raw_client_execstart(current_command, current_parameters)
            save_udp2raw_client_service_file(service_content, updated_command)
            reload_and_restart_udp2raw_client_service()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

#speederv2

def edit_udpspeed_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mEdit udpspeed \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-2): ").strip()

    if choice == "1":
        edit_speederv2_service_menu()
    elif choice == "2":
        edit_speederv2_client_service()
    elif choice == "0":
        edit_menu()
    else:
        print("Wrong choice. Please select a valid option.")

def read_speederv2_client_service():
    service_path = "/etc/systemd/system/speederv2.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def parse_speederv2_client_execstart(service_content):
    for line in service_content.splitlines():
        if line.startswith("ExecStart"):
            return line.split("ExecStart=")[1].strip()
    return None

def extract_speederv2_client_parameters(command):
    parameters = {}

    port_match = re.search(r"-l0.0.0.0:(\d+)", command)
    parameters["port"] = port_match.group(1) if port_match else None

    password_match = re.search(r'-k "([^"]+)"', command)
    parameters["password"] = password_match.group(1) if password_match else None

    remote_ip_match = re.search(r"-r([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):(\d+)", command)
    if remote_ip_match:
        parameters["remote_ip"] = remote_ip_match.group(1)
        parameters["remote_port"] = remote_ip_match.group(2)
    else:
        parameters["remote_ip"] = None
        parameters["remote_port"] = None

    mode_match = re.search(r"--mode (\d+)", command)
    parameters["mode"] = mode_match.group(1) if mode_match else None

    fec_match = re.search(r"-f(\d+):(\d+)", command)
    if fec_match:
        parameters["fec_enabled"] = True
        parameters["fec_value"] = f"{fec_match.group(1)}:{fec_match.group(2)}"
    else:
        parameters["fec_enabled"] = False

    return parameters


def prompt_for_edit_speederv2_client(parameter_name, current_value):
    new_value = input(f"Edit {parameter_name} (current value: {current_value}): ")
    return new_value.strip() or current_value

def prompt_for_fec_choice_client(current_fec_status, current_fec_value):
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print(f"Current FEC status: {'Enabled' if current_fec_status else 'Disabled'}")
    print("1)\033[92m Enable FEC \033[97m(-f20:10)\033[0m")
    print("2)\033[93m Disable FEC \033[97m(--disable-fec)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option: ")

    if choice == '1':
        return True, "20:10"  
    elif choice == '2':
        return False, None  
    else:
        print("Wrong choice, keeping current FEC status.")
        return current_fec_status, current_fec_value

def update_speederv2_client_execstart(command, new_parameters):
    command = re.sub(r"-l0.0.0.0:\d+", f"-l0.0.0.0:{new_parameters['port']}", command) 
    command = re.sub(r'-k "[^"]+"', f'-k "{new_parameters["password"]}"', command)  
    command = re.sub(r"-r \S+:\d+", f"-r {new_parameters['remote_ip']}:{new_parameters['remote_port']}", command)  
    command = re.sub(r"--mode \d+", f"--mode {new_parameters['mode']}", command) 

    if new_parameters["fec_enabled"]:
        command = re.sub(r"-f\d+:\d+", f"-f{new_parameters['fec_value']}", command)  
    else:
        command = re.sub(r"-f\d+:\d+", "", command)  
        command = command.replace("--disable-fec", "")  

    if not new_parameters["fec_enabled"] and "--disable-fec" not in command:
        command += " --disable-fec"

    return command

def save_speederv2_client_service_file(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2.service", "w") as file:
        file.write(updated_content)

def reload_and_restart_speederv2_client_service():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2"])

    display_checkmark("\033[92mspeederv2 client service updated and restarted successfully\033[0m")

def edit_speederv2_client_service():
    service_content = read_speederv2_client_service()
    if not service_content:
        return

    current_command = parse_speederv2_client_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_client_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 Client \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2_client("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2_client("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2_client("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2_client("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2_client("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice_client(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_client_execstart(current_command, current_parameters)
            save_speederv2_client_service_file(service_content, updated_command)
            reload_and_restart_speederv2_client_service()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_speederv2_service_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mEdit udpspeed \033[93mServer Menu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server Config [1]\033[0m")
    print("2)\033[93m Server Config [2]\033[0m")
    print("3)\033[92m Server Config [3]\033[0m")
    print("4)\033[93m Server Config [4]\033[0m")
    print("5)\033[93m Server Config [5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-5): ").strip()

    if choice == "1":
        edit_speederv2_service1()
    elif choice == "2":
        edit_speederv2_service2()
    elif choice == "3":
        edit_speederv2_service3()
    elif choice == "4":
        edit_speederv2_service4()
    elif choice == "5":
        edit_speederv2_service5()
    elif choice == "0":
        edit_udpspeed_menu()
    else:
        print("Wrong choice. Please select a valid option.")

def read_speederv2_service1():
    service_path = "/etc/systemd/system/speederv2_1.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_speederv2_service2():
    service_path = "/etc/systemd/system/speederv2_2.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_speederv2_service3():
    service_path = "/etc/systemd/system/speederv2_3.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_speederv2_service4():
    service_path = "/etc/systemd/system/speederv2_4.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def read_speederv2_service5():
    service_path = "/etc/systemd/system/speederv2_5.service"
    if not os.path.exists(service_path):
        print(f"Error: {service_path} not found!")
        return None

    with open(service_path, "r") as file:
        service_content = file.read()

    return service_content

def parse_speederv2_execstart(service_content):
    for line in service_content.splitlines():
        if line.startswith("ExecStart"):
            return line.split("ExecStart=")[1].strip()
    return None

def extract_speederv2_parameters(command):
    parameters = {}

    port_match = re.search(r"-l0.0.0.0:(\d+)", command)
    if port_match:
        parameters["port"] = port_match.group(1)

    password_match = re.search(r'-k "([^"]+)"', command)
    if password_match:
        parameters["password"] = password_match.group(1)

    remote_ip_match = re.search(r"-r([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):(\d+)", command)
    if remote_ip_match:
        parameters["remote_ip"] = remote_ip_match.group(1)
        parameters["remote_port"] = remote_ip_match.group(2)

    mode_match = re.search(r"--mode (\d+)", command)
    if mode_match:
        parameters["mode"] = mode_match.group(1)

    fec_match = re.search(r"-f(\d+):(\d+)", command)
    if fec_match:
        parameters["fec_enabled"] = True
        parameters["fec_value"] = f"{fec_match.group(1)}:{fec_match.group(2)}"

    return parameters

def prompt_for_edit_speederv2(parameter_name, current_value):
    new_value = input(f"Edit {parameter_name} (current value: {current_value}): ")
    return new_value.strip() or current_value

def prompt_for_fec_choice(current_fec_status, current_fec_value):
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print(f"Current FEC status: {'Enabled' if current_fec_status else 'Disabled'}")
    print("1)\033[92m Enable FEC\033[97m (-f20:10)\033[0m")
    print("2)\033[93m Disable FEC\033[97m (--disable-fec)\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option: ")

    if choice == '1':
        return True, "20:10"  
    elif choice == '2':
        return False, None 
    else:
        print("Wrong choice, keeping current FEC status.")
        return current_fec_status, current_fec_value

def update_speederv2_execstart_server(command, new_parameters):
    command = re.sub(r"-l0.0.0.0:\d+", f"-l0.0.0.0:{new_parameters['port']}", command)  
    command = re.sub(r'-k "[^"]+"', f'-k "{new_parameters["password"]}"', command)  
    command = re.sub(r"-r \S+:\d+", f"-r {new_parameters['remote_ip']}:{new_parameters['remote_port']}", command)  
    command = re.sub(r"--mode \d+", f"--mode {new_parameters['mode']}", command)  

    if new_parameters["fec_enabled"]:
        command = re.sub(r"-f\d+:\d+", f"-f{new_parameters['fec_value']}", command) 
    else:
        command = re.sub(r"-f\d+:\d+", "", command)  
        command = command.replace("--disable-fec", "") 

    if not new_parameters["fec_enabled"] and "--disable-fec" not in command:
        command += " --disable-fec"

    return command

def save_speederv2_service_file_server1(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2_1.service", "w") as file:
        file.write(updated_content)

def save_speederv2_service_file_server2(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2_2.service", "w") as file:
        file.write(updated_content)

def save_speederv2_service_file_server3(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2_3.service", "w") as file:
        file.write(updated_content)

def save_speederv2_service_file_server4(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2_4.service", "w") as file:
        file.write(updated_content)

def save_speederv2_service_file_server5(service_content, updated_execstart):
    print("\nUpdated command:")
    print(updated_execstart)

    updated_content = re.sub(r"ExecStart=.*", f"ExecStart={updated_execstart}", service_content)
    
    with open("/etc/systemd/system/speederv2_5.service", "w") as file:
        file.write(updated_content)

def reload_and_restart_speederv2_service_server1():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2_1"])

    display_checkmark("\033[92mspeederv2_1 service updated and restarted successfully\033[0m")

def reload_and_restart_speederv2_service_server2():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2_2"])

    display_checkmark("\033[92mspeederv2_2 service updated and restarted successfully\033[0m")

def reload_and_restart_speederv2_service_server3():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2_3"])

    display_checkmark("\033[92mspeederv2_3 service updated and restarted successfully\033[0m")

def reload_and_restart_speederv2_service_server4():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2_4"])

    display_checkmark("\033[92mspeederv2_4 service updated and restarted successfully\033[0m")

def reload_and_restart_speederv2_service_server5():
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "restart", "speederv2_1"])

    display_checkmark("\033[92mspeederv2_5 service updated and restarted successfully\033[0m")

def edit_speederv2_service1():
    service_content = read_speederv2_service1()
    if not service_content:
        return

    current_command = parse_speederv2_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_execstart_server(current_command, current_parameters)
            save_speederv2_service_file_server1(service_content, updated_command)
            reload_and_restart_speederv2_service_server1()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_speederv2_service2():
    service_content = read_speederv2_service2()
    if not service_content:
        return

    current_command = parse_speederv2_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_execstart_server(current_command, current_parameters)
            save_speederv2_service_file_server2(service_content, updated_command)
            reload_and_restart_speederv2_service_server2()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_speederv2_service3():
    service_content = read_speederv2_service3()
    if not service_content:
        return

    current_command = parse_speederv2_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_execstart_server(current_command, current_parameters)
            save_speederv2_service_file_server3(service_content, updated_command)
            reload_and_restart_speederv2_service_server3()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_speederv2_service4():
    service_content = read_speederv2_service4()
    if not service_content:
        return

    current_command = parse_speederv2_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_execstart_server(current_command, current_parameters)
            save_speederv2_service_file_server4(service_content, updated_command)
            reload_and_restart_speederv2_service_server4()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_speederv2_service5():
    service_content = read_speederv2_service5()
    if not service_content:
        return

    current_command = parse_speederv2_execstart(service_content)
    if not current_command:
        print("Error: Could not find ExecStart in the service file.")
        return

    current_parameters = extract_speederv2_parameters(current_command)
    if not current_parameters:
        print("Error: Could not extract parameters from the command.")
        return

    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mSpeederv2 \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print(f"1)\033[93m Edit \033[92mPort\033[97m (current: {current_parameters['port']})\033[0m")
        print(f"2)\033[93m Edit \033[92mPassword\033[97m (current: {current_parameters['password']})\033[0m")
        print(f"3)\033[93m Edit \033[92mRemote IP\033[97m (current: {current_parameters['remote_ip']})\033[0m")
        print(f"4)\033[93m Edit \033[92mRemote Port\033[97m (current: {current_parameters['remote_port']})\033[0m")
        print(f"5)\033[93m Edit \033[92mMode\033[97m (current: {current_parameters['mode']})\033[0m")
        print(f"6)\033[93m Edit \033[92mFEC (current: {'Enabled' if current_parameters['fec_enabled'] else 'Disabled'})\033[0m")
        print("7)\033[92m Save and Apply Changes\033[0m")
        print("0) Exit")
        
        choice = input("\nChoose an option: ")

        if choice == '1':
            current_parameters["port"] = prompt_for_edit_speederv2("Port", current_parameters["port"])
        elif choice == '2':
            current_parameters["password"] = prompt_for_edit_speederv2("Password", current_parameters["password"])
        elif choice == '3':
            current_parameters["remote_ip"] = prompt_for_edit_speederv2("Remote IP", current_parameters["remote_ip"])
        elif choice == '4':
            current_parameters["remote_port"] = prompt_for_edit_speederv2("Remote Port", current_parameters["remote_port"])
        elif choice == '5':
            current_parameters["mode"] = prompt_for_edit_speederv2("Mode", current_parameters["mode"])
        elif choice == '6':
            current_parameters["fec_enabled"], current_parameters["fec_value"] = prompt_for_fec_choice(
                current_parameters["fec_enabled"], current_parameters.get("fec_value")
            )
        elif choice == '7':
            updated_command = update_speederv2_execstart_server(current_command, current_parameters)
            save_speederv2_service_file_server5(service_content, updated_command)
            reload_and_restart_speederv2_service_server5()
            break
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def edit_tinyvpn_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mEdit tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to edit menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to edit (0-2): ").strip()

    if choice == "1":
        edit_tinyvpn_service()
    elif choice == "2":
        edit_tinyvpn_client_service()
    elif choice == "0":
        edit_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mRestart \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TinyVPN\033[0m")
    print("2)\033[92m UDP2RAW\033[0m")
    print("3)\033[94m UDPSpeeder\033[0m")
    print("4)\033[93m ProxyForwarder\033[0m")
    print("5)\033[92m Tinymapper\033[0m")
    print("6)\033[93m UDP2RAW + UDPSPeeder\033[0m")
    print("0)\033[94m back to main menu\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    choice = input("Choose an option to restart (0-6): ").strip()

    if choice == "1":
        restart_menu_tinyvpn()
    elif choice == "2":
        restart_menu_udp2raw()
    elif choice == "3":
        restart_menu_speederv2()
    elif choice == "4":
        restart_proxyforwarder()
    elif choice == "5":
        restart_tinymapper_menu()
    elif choice == "6":
        restart_menu_udp2raw_and_speederv2_menu()
    elif choice == "0":
        return  
    else:
        print("Invalid choice. Please select a valid option.")


#udpspeed + udp2raw
def restart_menu_udp2raw_and_speederv2_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw + udpspeeder \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[93m Client\033[0m")
    print("0)\033[94m back to restart menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-2): ").strip()

    if choice == "1":
        restart_udp2raw_udpspeed_server_menu()
    elif choice == "2":
        restart_udp2raw_udpspeed_client_menu()
    elif choice == "0":
        restart_menu() 
    else:
        print("Invalid choice. Please select a valid option.")

def restart_udp2raw_udpspeed_server_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw + udpspeed \033[93mServer\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server[1]\033[0m")
    print("2)\033[93m Server[2]\033[0m")
    print("3)\033[92m Server[3]\033[0m")
    print("4)\033[93m Server[4]\033[0m")
    print("5)\033[93m Server[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udp2raw_server1()
        restart_udpspeeder_server1()
    elif choice == "2":
        restart_udp2raw_server2()
        restart_udpspeeder_server2()
    elif choice == "3":
        restart_udp2raw_server3()
        restart_udpspeeder_server3()
    elif choice == "4":
        restart_udp2raw_server4()
        restart_udpspeeder_server4()
    elif choice == "5":
        restart_udp2raw_server5()
        restart_udpspeeder_server5()
    elif choice == "0":
        restart_menu_udp2raw_and_speederv2_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_udp2raw_udpspeed_client_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw + udpspeed \033[93mClient\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Client[1]\033[0m")
    print("2)\033[93m Client[2]\033[0m")
    print("3)\033[92m Client[3]\033[0m")
    print("4)\033[93m Client[4]\033[0m")
    print("5)\033[93m Client[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udp2raw_client()
        restart_udpspeeder_client()
    elif choice == "2":
        restart_udp2raw_client()
        restart_udpspeeder_client()
    elif choice == "3":
        restart_udp2raw_client()
        restart_udpspeeder_client()
    elif choice == "4":
        restart_udp2raw_client()
        restart_udpspeeder_client()
    elif choice == "5":
        restart_udp2raw_client()
        restart_udpspeeder_client()
    elif choice == "0":
        restart_menu_udp2raw_and_speederv2_menu()
    else:
        print("Invalid choice. Please select a valid option.")


def restart_tinymapper_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart tinymapper \033[93mClient\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Config[1]\033[0m")
    print("2)\033[93m Config[2]\033[0m")
    print("3)\033[92m Config[3]\033[0m")
    print("4)\033[93m Config[4]\033[0m")
    print("5)\033[93m Config[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_tinymapper1()
    elif choice == "2":
        restart_tinymapper2()
    elif choice == "3":
        restart_tinymapper3()
    elif choice == "4":
        restart_tinymapper4()
    elif choice == "5":
        restart_tinymapper5()
    elif choice == "0":
        restart_menu()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_menu_tinyvpn():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[93m Client\033[0m")
    print("0)\033[94m back to restart menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-2): ").strip()

    if choice == "1":
        restart_tinyvpn_server()
    elif choice == "2":
        restart_tinyvpn_client()
    elif choice == "0":
        restart_menu() 
    else:
        print("Invalid choice. Please select a valid option.")


def restart_menu_udp2raw():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[93m Client\033[0m")
    print("0)\033[94m back to restart menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-2): ").strip()

    if choice == "1":
        restart_udp2raw_server_menu()
    elif choice == "2":
        restart_udp2raw_client_menu()
    elif choice == "0":
        restart_menu() 
    else:
        print("Invalid choice. Please select a valid option.")

def restart_udp2raw_server_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw \033[93mServer\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server[1]\033[0m")
    print("2)\033[93m Server[2]\033[0m")
    print("3)\033[92m Server[3]\033[0m")
    print("4)\033[93m Server[4]\033[0m")
    print("5)\033[93m Server[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udp2raw_server1()
    elif choice == "2":
        restart_udp2raw_server2()
    elif choice == "3":
        restart_udp2raw_server3()
    elif choice == "4":
        restart_udp2raw_server4()
    elif choice == "5":
        restart_udp2raw_server5()
    elif choice == "0":
        restart_menu_udp2raw()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_udp2raw_client_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udp2raw \033[93mClient\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Client[1]\033[0m")
    print("2)\033[93m Client[2]\033[0m")
    print("3)\033[92m Client[3]\033[0m")
    print("4)\033[93m Client[4]\033[0m")
    print("5)\033[93m Client[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udp2raw_client()
    elif choice == "2":
        restart_udp2raw_client()
    elif choice == "3":
        restart_udp2raw_client()
    elif choice == "4":
        restart_udp2raw_client()
    elif choice == "5":
        restart_udp2raw_client()
    elif choice == "0":
        restart_menu_udp2raw()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_menu_speederv2():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udpspeeder\033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[93m Client\033[0m")
    print("0)\033[94m back to restart menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-2): ").strip()

    if choice == "1":
        restart_udpspeed_server_menu()
    elif choice == "2":
        restart_udpspeed_client_menu()
    elif choice == "0":
        restart_menu() 
    else:
        print("Invalid choice. Please select a valid option.")
        
def restart_udpspeed_server_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udpspeed \033[93mServer\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server[1]\033[0m")
    print("2)\033[93m Server[2]\033[0m")
    print("3)\033[92m Server[3]\033[0m")
    print("4)\033[93m Server[4]\033[0m")
    print("5)\033[93m Server[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udpspeeder_server1()
    elif choice == "2":
        restart_udpspeeder_server2()
    elif choice == "3":
        restart_udpspeeder_server3()
    elif choice == "4":
        restart_udpspeeder_server4()
    elif choice == "5":
        restart_udpspeeder_server5()
    elif choice == "0":
        restart_menu_speederv2()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_udpspeed_client_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mRestart Udpspeed \033[93mClient\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Client[1]\033[0m")
    print("2)\033[93m Client[2]\033[0m")
    print("3)\033[92m Client[3]\033[0m")
    print("4)\033[93m Client[4]\033[0m")
    print("5)\033[93m Client[5]\033[0m")
    print("0)\033[94m back to previous menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to restart (0-5): ").strip()

    if choice == "1":
        restart_udpspeeder_client()
    elif choice == "2":
        rrestart_udpspeeder_client()
    elif choice == "3":
        restart_udpspeeder_client()
    elif choice == "4":
        restart_udpspeeder_client()
    elif choice == "5":
        restart_udpspeeder_client()
    elif choice == "0":
        restart_menu_speederv2()
    else:
        print("Invalid choice. Please select a valid option.")

def restart_tinyvpn_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting TinyVPN Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinyvpn"

    try:
        subprocess.run(["systemctl", "stop", service_name], check=True)
        print("\033[92mTinyVPN service stopped successfully.\033[0m")

        subprocess.run(["systemctl", "start", service_name], check=True)
        print("\033[92mTinyVPN service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting TinyVPN service: {e}\033[0m")
        display_notification("\033[91mFailed to restart TinyVPN service.\033[0m")
        return

    display_checkmark("\033[92mTinyVPN server restarted successfully.\033[0m")

def restart_tinyvpn_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting TinyVPN Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinyvpn"

    try:
        subprocess.run(["systemctl", "stop", service_name], check=True)
        print("\033[92mTinyVPN client service stopped successfully.\033[0m")

        subprocess.run(["systemctl", "start", service_name], check=True)
        print("\033[92mTinyVPN client service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting TinyVPN client service: {e}\033[0m")
        display_notification("\033[91mFailed to restart TinyVPN client service.\033[0m")
        return

    display_checkmark("\033[92mTinyVPN client restarted successfully.\033[0m")

def restart_udp2raw_server1():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw_1"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udp2raw_server2():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw_2"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udp2raw_server3():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw_3"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udp2raw_server4():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw_4"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udp2raw_server5():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw_5"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udp2raw_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDP2RAW Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "udp2raw"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW client service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW client service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW client service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW client restarted successfully.\033[0m")


def restart_udpspeeder_server1():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2_1"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udpspeeder_server2():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2_2"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udpspeeder_server3():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2_3"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udpspeeder_server4():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2_4"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udpspeeder_server5():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Server...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2_5"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDP2RAW service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting UDP2RAW service: {e}\033[0m")
        display_notification("\033[91mFailed to restart UDP2RAW service.\033[0m")
        return

    display_checkmark("\033[92mUDP2RAW server restarted successfully.\033[0m")

def restart_udpspeeder_client():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting UDPspeeder Client...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "speederv2"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mUDPspeeder client service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mUDPspeeder client restarted successfully.\033[0m")

def restart_proxyforwarder():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Proxyforwarder...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "proxyforwarder"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mProxyforwarder service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mProxyforwarder restarted successfully.\033[0m")

def restart_tinymapper1():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinymapper_1"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mTinymapper service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mTinymapper restarted successfully.\033[0m")

def restart_tinymapper2():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinymapper_2"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mTinymapper service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mTinymapper restarted successfully.\033[0m")

def restart_tinymapper3():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinymapper_3"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mTinymapper service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mTinymapper restarted successfully.\033[0m")

def restart_tinymapper4():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinymapper_4"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mTinymapper service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mTinymapper restarted successfully.\033[0m")

def restart_tinymapper5():
    print("\033[93m───────────────────────────────────────\033[0m")
    display_notification("\033[93mRestarting Tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    service_name = "tinymapper_5"

    try:

        subprocess.run(["systemctl", "restart", service_name], check=True)
        print("\033[92mTinymapper service started successfully.\033[0m")

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("\033[92mSystemd daemon reloaded successfully.\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"\033[91mError restarting service: {e}\033[0m")
        display_notification("\033[91mFailed to restart service.\033[0m")
        return

    display_checkmark("\033[92mTinymapper restarted successfully.\033[0m")

def uninstall_udp2raw_and_speederv2():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDP2RAW & Udpspeeder\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower()
    if confirm == "yes":
        try:
            num_ports = int(input("\033[93mHow many \033[92mports do you have\033[93m? \033[0m").strip())
        except ValueError:
            print("\033[91mError: Invalid input. Please enter a valid number.\033[0m")
            return

        for port_num in range(1, num_ports + 1):
            display_notification(f"\033[93mUninstalling\033[96m Config {port_num}\033[93m...\033[0m")

            udp2raw_service_name = f"udp2raw_{port_num}"
            udp2raw_service_path = f"/etc/systemd/system/{udp2raw_service_name}.service"
            udp2raw_binary_path = "/usr/local/bin/udp2raw"

            try:
                subprocess.run(["systemctl", "stop", udp2raw_service_name], check=True)
                subprocess.run(["systemctl", "disable", udp2raw_service_name], check=True)
            except subprocess.CalledProcessError:
                print(f"\033[91mWarning: Failed to stop or disable {udp2raw_service_name} (might not exist).\033[0m")

            if os.path.exists(udp2raw_service_path):
                os.remove(udp2raw_service_path)
                display_checkmark(f"\033[92mRemoved UDP2RAW service file: {udp2raw_service_path}\033[0m")
            else:
                print(f"\033[91mWarning: UDP2RAW service file for {udp2raw_service_name} not found.\033[0m")

            if os.path.exists(udp2raw_binary_path):
                os.remove(udp2raw_binary_path)
                display_checkmark(f"\033[92mRemoved UDP2RAW binary file: {udp2raw_binary_path}\033[0m")
            else:
                print(f"\033[91mWarning: UDP2RAW binary file for {udp2raw_service_name} not found.\033[0m")

            speederv2_service_name = f"speederv2_{port_num}"
            speederv2_service_path = f"/etc/systemd/system/{speederv2_service_name}.service"
            speederv2_binary_path = "/usr/local/bin/speederv2"

            try:
                subprocess.run(["systemctl", "stop", speederv2_service_name], check=True)
                subprocess.run(["systemctl", "disable", speederv2_service_name], check=True)
            except subprocess.CalledProcessError:
                print(f"\033[91mWarning: Failed to stop or disable {speederv2_service_name} (might not exist).\033[0m")

            if os.path.exists(speederv2_service_path):
                os.remove(speederv2_service_path)
                display_checkmark(f"\033[92mRemoved Speederv2 service file: {speederv2_service_path}\033[0m")
            else:
                print(f"\033[91mWarning: Speederv2 service file for {speederv2_service_name} not found.\033[0m")

            if os.path.exists(speederv2_binary_path):
                os.remove(speederv2_binary_path)
                display_checkmark(f"\033[92mRemoved Speederv2 binary file: {speederv2_binary_path}\033[0m")
            else:
                print(f"\033[91mWarning: Speederv2 binary file for {speederv2_service_name} not found.\033[0m")

        default_udp2raw_service_path = "/etc/systemd/system/udp2raw.service"
        default_udp2raw_binary_path = "/usr/local/bin/udp2raw"

        try:
            if os.path.exists(default_udp2raw_service_path):
                os.remove(default_udp2raw_service_path)
                display_checkmark(f"\033[92mRemoved default UDP2RAW service file: {default_udp2raw_service_path}\033[0m")
            else:
                print("\033[91mWarning: Default UDP2RAW service file not found.\033[0m")

            if os.path.exists(default_udp2raw_binary_path):
                os.remove(default_udp2raw_binary_path)
                display_checkmark(f"\033[92mRemoved default UDP2RAW binary file: {default_udp2raw_binary_path}\033[0m")
            else:
                print("\033[91mWarning: Default UDP2RAW binary file not found.\033[0m")
        except Exception as e:
            print(f"\033[91mError removing default UDP2RAW files: {e}\033[0m")

        default_speederv2_service_path = "/etc/systemd/system/speederv2.service"
        default_speederv2_binary_path = "/usr/local/bin/speederv2"

        try:
            if os.path.exists(default_speederv2_service_path):
                os.remove(default_speederv2_service_path)
                display_checkmark(f"\033[92mRemoved default Speederv2 service file: {default_speederv2_service_path}\033[0m")
            else:
                print("\033[91mWarning: Default Speederv2 service file not found.\033[0m")

            if os.path.exists(default_speederv2_binary_path):
                os.remove(default_speederv2_binary_path)
                display_checkmark(f"\033[92mRemoved default Speederv2 binary file: {default_speederv2_binary_path}\033[0m")
            else:
                print("\033[91mWarning: Default Speederv2 binary file not found.\033[0m")
        except Exception as e:
            print(f"\033[91mError removing default Speederv2 files: {e}\033[0m")

        display_checkmark("\033[92mUninstallation completed successfully\033[0m")
    else:
        display_error("\033[91mUninstallation canceled\033[0m")


def uninstall_tinymapper():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    display_notification("\033[93mUninstalling Tinymapper...\033[0m")

    try:
        num_ports = int(input("\033[93mHow many \033[92mports do you have\033[93m? \033[0m").strip())
    except ValueError:
        print("\033[91mError: Invalid input. Please enter a valid number.\033[0m")
        return

    for i in range(1, num_ports + 1):
        service_name = f"tinymapper_{i}"
        service_path = f"/etc/systemd/system/{service_name}.service"

        try:
            subprocess.run(["systemctl", "stop", service_name], check=True)
            subprocess.run(["systemctl", "disable", service_name], check=True)
        except subprocess.CalledProcessError:
            print(f"\033[91mWarning: Failed to stop or disable {service_name} (might not exist).\033[0m")

        try:
            if os.path.exists(service_path):
                os.remove(service_path)
                display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
            else:
                print(f"\033[91mWarning: Service file for {service_name} not found.\033[0m")
        except Exception as e:
            print(f"\033[91mError removing service file: {e}\033[0m")

    binary_path = "/usr/local/bin/tinymapper"
    try:
        if os.path.exists(binary_path):
            os.remove(binary_path)
            display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
        else:
            print("\033[91mWarning: Tinymapper binary not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing binary: {e}\033[0m")

    daemon_service_path = "/etc/systemd/system/tinymapper_daemon.service"
    try:
        if os.path.exists(daemon_service_path):
            os.remove(daemon_service_path)
            display_checkmark(f"\033[92mRemoved daemon service file: {daemon_service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon service file '{daemon_service_path}' not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing daemon service file: {e}\033[0m")

    daemon_script_path = "/usr/local/bin/tinymapper_daemon.sh"
    try:
        if os.path.exists(daemon_script_path):
            os.remove(daemon_script_path)
            display_checkmark(f"\033[92mRemoved daemon script: {daemon_script_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon script '{daemon_script_path}' not found.\033[0m")
    except Exception as e:
        print(f"\033[91mError removing daemon script: {e}\033[0m")

    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
    except subprocess.CalledProcessError:
        print("\033[91mWarning: Failed to reload systemd daemon.\033[0m")

    display_checkmark("\033[92mTinymapper uninstalled successfully\033[0m")



def uninstall_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstall \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TinyVPN\033[0m")
    print("2)\033[92m UDP2RAW\033[0m")
    print("3)\033[94m UDPSpeeder\033[0m")
    print("4)\033[93m ProxyForwarder\033[0m")
    print("5)\033[92m Tinymapper\033[0m")
    print("6)\033[93m UDP2RAW + UDPSPeeder\033[0m")
    print("0)\033[94m back to main menu\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")

    choice = input("Choose an option to uninstall (0-6): ").strip()

    if choice == "1":
        uninstall_tinyvpn()
    elif choice == "2":
        uninstall_udp2raw()
    elif choice == "3":
        uninstall_speederv2()
    elif choice == "4":
        uninstall_proxy_forwarders()
    elif choice == "5":
        uninstall_tinymapper()
    elif choice == "6":
        uninstall_udp2raw_and_speederv2_menu()
    elif choice == "0":
        return  
    else:
        print("Invalid choice. Please select a valid option.")

def uninstall_speederv2_server():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    display_notification("\033[93mUninstalling Udpspeeder...\033[0m")
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDPSpeeder\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower()
    
    if confirm == "yes":
        try:
            num_clients = int(input("\033[93mHow many \033[92mclients do you have\033[93m?\033[0m "))

            for client_num in range(1, num_clients + 1):
                print(f"\033[93mUninstalling \033[96mConfig {client_num}...\033[0m")

                service_name = f"speederv2_{client_num}"
                service_path = f"/etc/systemd/system/{service_name}.service"
                binary_path = f"/usr/local/bin/speederv2"

                try:
                    subprocess.run(["systemctl", "stop", service_name], check=True)
                    subprocess.run(["systemctl", "disable", service_name], check=True)
                except subprocess.CalledProcessError:
                    print(f"\033[91mWarning: Failed to stop or disable {service_name} (might not exist).\033[0m")

                if os.path.exists(service_path):
                    os.remove(service_path)
                    display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
                else:
                    print(f"\033[91mWarning: Service file for {service_name} not found.\033[0m")

                if os.path.exists(binary_path):
                    os.remove(binary_path)
                    display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
                else:
                    print(f"\033[91mWarning: Binary file for {service_name} not found.\033[0m")

            default_service_path = "/etc/systemd/system/speederv2.service"
            default_binary_path = "/usr/local/bin/speederv2"

            if os.path.exists(default_service_path):
                os.remove(default_service_path)
                display_checkmark(f"\033[92mRemoved default Speederv2 service file: {default_service_path}\033[0m")

            if os.path.exists(default_binary_path):
                os.remove(default_binary_path)
                display_checkmark(f"\033[92mRemoved default Speederv2 binary file: {default_binary_path}\033[0m")

            speederv_daemon_service_path = "/etc/systemd/system/speederv_daemon.service"
            speederv_daemon_script_path = "/usr/local/bin/speederv_daemon.sh"

            if os.path.exists(speederv_daemon_service_path):
                os.remove(speederv_daemon_service_path)
                display_checkmark(f"\033[92mRemoved daemon service file: {speederv_daemon_service_path}\033[0m")

            if os.path.exists(speederv_daemon_script_path):
                os.remove(speederv_daemon_script_path)
                display_checkmark(f"\033[92mRemoved daemon script: {speederv_daemon_script_path}\033[0m")

            display_checkmark("\033[92mUninstallation completed successfully\033[0m")

        except ValueError:
            print("\033[91mError: Invalid input for the number of clients. Please enter a number.\033[0m")

        except Exception as e:
            print(f"\033[91mError during uninstallation: {e}\033[0m")

    else:
        display_error("\033[91mUninstallation canceled\033[0m")


def uninstall_speederv2_client():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    display_notification("\033[93mUninstalling Udpspeeder...\033[0m")
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDPSpeeder\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower()

    if confirm == "yes":
        service_name = "speederv2"
        service_path = f"/etc/systemd/system/{service_name}.service"
        binary_path = f"/usr/local/bin/speederv2"

        try:
            subprocess.run(["systemctl", "stop", service_name], check=True)
            subprocess.run(["systemctl", "disable", service_name], check=True)
        except subprocess.CalledProcessError:
            print(f"\033[91mWarning: Failed to stop or disable {service_name} (might not exist).\033[0m")

        if os.path.exists(service_path):
            os.remove(service_path)
            display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Service file for {service_name} not found.\033[0m")

        if os.path.exists(binary_path):
            os.remove(binary_path)
            display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
        else:
            print(f"\033[91mWarning: Binary file for {service_name} not found.\033[0m")

        speederv_daemon_service_path = "/etc/systemd/system/speederv_daemon.service"
        speederv_daemon_script_path = "/usr/local/bin/speederv_daemon.sh"

        if os.path.exists(speederv_daemon_service_path):
            os.remove(speederv_daemon_service_path)
            display_checkmark(f"\033[92mRemoved daemon service file: {speederv_daemon_service_path}\033[0m")

        if os.path.exists(speederv_daemon_script_path):
            os.remove(speederv_daemon_script_path)
            display_checkmark(f"\033[92mRemoved daemon script: {speederv_daemon_script_path}\033[0m")

        display_checkmark("\033[92mUninstallation completed successfully\033[0m")

    else:
        display_error("\033[91mUninstallation canceled\033[0m")


def uninstall_tinyvpn():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mTinyVPN?\033[93m (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower()
    if confirm == "yes":
        try:
            subprocess.run(["systemctl", "stop", "tinyvpn"], check=True)
            subprocess.run(["systemctl", "disable", "tinyvpn"], check=True)
            print("\033[92mStopped and disabled TinyVPN service\033[0m")
            stop_delete_keepalive()
        except subprocess.CalledProcessError as e:
            print(f"\033[91mWarning: Failed to stop or disable TinyVPN service. {e}\033[0m")

        service_file = "/etc/systemd/system/tinyvpn.service"
        if os.path.exists(service_file):
            os.remove(service_file)
            print(f"\033[92mSuccessfully removed the service file: {service_file}\033[0m")
        else:
            print(f"\033[91mWarning: Service file '{service_file}' not found.\033[0m")

        binary_path = "/usr/local/bin/tinyvpn"
        if os.path.exists(binary_path):
            os.remove(binary_path)
            print(f"\033[92mSuccessfully removed the binary: {binary_path}\033[0m")
        else:
            print(f"\033[91mWarning: Binary '{binary_path}' not found.\033[0m")

        tinyvpn_daemon_service_path = "/etc/systemd/system/tinyvpn_daemon.service"
        if os.path.exists(tinyvpn_daemon_service_path):
            os.remove(tinyvpn_daemon_service_path)
            print(f"\033[92mSuccessfully removed the TinyVPN daemon service file: {tinyvpn_daemon_service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon service file '{tinyvpn_daemon_service_path}' not found.\033[0m")

        tinyvpn_daemon_script_path = "/usr/local/bin/tinyvpn_daemon.sh"
        if os.path.exists(tinyvpn_daemon_script_path):
            os.remove(tinyvpn_daemon_script_path)
            print(f"\033[92mSuccessfully removed the TinyVPN daemon script: {tinyvpn_daemon_script_path}\033[0m")
        else:
            print(f"\033[91mWarning: Daemon script '{tinyvpn_daemon_script_path}' not found.\033[0m")

        display_checkmark("\033[92mTinyVPN uninstalled successfully\033[0m")
    else:
        display_error("\033[91mTinyVPN uninstallation canceled\033[0m")
        


def uninstall_udp2raw():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstall udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[93m Client\033[0m")
    print("0)\033[94m back to uninstall menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to uninstall (0-2): ").strip()

    if choice == "1":
        uninstall_udp2raw_server()
    elif choice == "2":
        uninstall_udp2raw_client()
    elif choice == "0":
        uninstall_menu() 
    else:
        print("Invalid choice. Please select a valid option.")

def uninstall_udp2raw_server():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDP2RAW? \033[93m(\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    if confirm == "yes":
        num_ports = int(input("\033[93mHow many\033[92m ports do you have\033[93m? \033[0m"))

        for port_num in range(1, num_ports + 1):
            print(f"\033[93mUninstalling \033[96mConfig {port_num}...\033[0m")

            try:
                service_name = f"udp2raw_{port_num}"
                subprocess.run(["systemctl", "stop", service_name], check=True)
                subprocess.run(["systemctl", "disable", service_name], check=True)

                service_path = f"/etc/systemd/system/{service_name}.service"
                binary_path = f"/usr/local/bin/udp2raw_{port_num}"

                if os.path.exists(service_path):
                    os.remove(service_path)
                    display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
                else:
                    print(f"Service file for {service_name} not found.")

                if os.path.exists(binary_path):
                    os.remove(binary_path)
                    display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
                else:
                    print(f"Binary file for {service_name} not found.")

            except subprocess.CalledProcessError as e:
                print(f"\033[91mError: Failed to stop or disable {service_name}. {e}\033[0m")
            except Exception as e:
                print(f"\033[91mError during uninstallation of {service_name}: {e}\033[0m")

        default_service_path = "/etc/systemd/system/udp2raw.service"
        default_binary_path = "/usr/local/bin/udp2raw"
        udp2raw_daemon_service_path = "/etc/systemd/system/udp2raw_daemon.service"
        udp2raw_daemon_script_path = "/usr/local/bin/udp2raw_daemon.sh"

        try:
            if os.path.exists(default_service_path):
                os.remove(default_service_path)
                display_checkmark(f"\033[92mRemoved default UDP2RAW service file: {default_service_path}\033[0m")

            if os.path.exists(default_binary_path):
                os.remove(default_binary_path)
                display_checkmark(f"\033[92mRemoved default UDP2RAW binary file: {default_binary_path}\033[0m")

            if os.path.exists(udp2raw_daemon_service_path):
                os.remove(udp2raw_daemon_service_path)
                display_checkmark(f"\033[92mRemoved daemon service file: {udp2raw_daemon_service_path}\033[0m")

            if os.path.exists(udp2raw_daemon_script_path):
                os.remove(udp2raw_daemon_script_path)
                display_checkmark(f"\033[92mRemoved daemon script: {udp2raw_daemon_script_path}\033[0m")

            display_checkmark("\033[92muninstallation completed successfully\033[0m")

        except Exception as e:
            print(f"\033[91mError during removal of default UDP2RAW files: {e}\033[0m")
    else:
        display_error("\033[91muninstallation canceled\033[0m")


def uninstall_udp2raw_client():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDP2RAW Client\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m)\033[0m: ").strip().lower()
    if confirm == "yes":
        try:
            service_name = "udp2raw"
            subprocess.run(["systemctl", "stop", service_name], check=True)
            subprocess.run(["systemctl", "disable", service_name], check=True)

            service_path = f"/etc/systemd/system/{service_name}.service"
            binary_path = f"/usr/local/bin/udp2raw"

            if os.path.exists(service_path):
                os.remove(service_path)
                display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
            else:
                print(f"Service file for {service_name} not found.")

            if os.path.exists(binary_path):
                os.remove(binary_path)
                display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
            else:
                print(f"Binary file for {service_name} not found.")

            udp2raw_daemon_service_path = "/etc/systemd/system/udp2raw_daemon.service"
            udp2raw_daemon_script_path = "/usr/local/bin/udp2raw_daemon.sh"

            if os.path.exists(udp2raw_daemon_service_path):
                os.remove(udp2raw_daemon_service_path)
                display_checkmark(f"\033[92mRemoved daemon service file: {udp2raw_daemon_service_path}\033[0m")

            if os.path.exists(udp2raw_daemon_script_path):
                os.remove(udp2raw_daemon_script_path)
                display_checkmark(f"\033[92mRemoved daemon script: {udp2raw_daemon_script_path}\033[0m")

            display_checkmark("\033[92mUninstallation completed successfully\033[0m")

        except subprocess.CalledProcessError as e:
            print(f"\033[91mError: Failed to stop or disable {service_name}. {e}\033[0m")

        except Exception as e:
            print(f"\033[91mError during uninstallation: {e}\033[0m")
    else:
        display_error("\033[91mUninstallation canceled\033[0m")



def uninstall_udp2raw_and_speederv2_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUdpspeeder + udp2raw uninstall Menu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to uninstall menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to uninstall (0-2): ").strip()

    if choice == "1":
        uninstall_udp2raw_and_speederv2()
    elif choice == "2":
        uninstall_udp2raw_and_speederv2_client()
    elif choice == "0":
        uninstall_menu() 
    else:
        print("Wrong choice. Please select a valid option.")


def uninstall_udp2raw_and_speederv2_client():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstalling...\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    confirm = input("\033[93mAre you sure you want to \033[91muninstall \033[92mUDP2RAW & Speederv2 Client\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower()
    if confirm == "yes":
        display_notification("\033[93mUninstalling UDP2RAW & Speederv2...\033[0m")
        remove_default_files("/etc/systemd/system/udp2raw.service", "/usr/local/bin/udp2raw")
        remove_default_files("/etc/systemd/system/speederv2.service", "/usr/local/bin/speederv2")

        display_checkmark("\033[92mUninstallation completed successfully\033[0m")
    else:
        display_error("\033[91mUninstallation canceled\033[0m")

def remove_service_and_binary(service_name, binary_path, service_dir):
    service_path = f"{service_dir}/{service_name}.service"
    try:
        if os.path.exists(service_path):
            os.remove(service_path)
            display_checkmark(f"\033[92mRemoved service file: {service_path}\033[0m")
        else:
            print(f"\033[91mWarning: {service_name} service file not found.\033[0m")

        if os.path.exists(binary_path):
            os.remove(binary_path)
            display_checkmark(f"\033[92mRemoved binary file: {binary_path}\033[0m")
        else:
            print(f"\033[91mWarning: {binary_path} not found.\033[0m")

    except Exception as e:
        print(f"\033[91mError removing {service_name}: {e}\033[0m")

def remove_default_files(service_path, binary_path):
    try:
        if os.path.exists(service_path):
            os.remove(service_path)
            display_checkmark(f"\033[92mRemoved default service file: {service_path}\033[0m")
        else:
            print(f"\033[91mWarning: Default service file not found.\033[0m")

        if os.path.exists(binary_path):
            os.remove(binary_path)
            display_checkmark(f"\033[92mRemoved default binary file: {binary_path}\033[0m")
        else:
            print(f"\033[91mWarning: Default binary file not found.\033[0m")

    except Exception as e:
        print(f"\033[91mError removing default files: {e}\033[0m")


def uninstall_speederv2():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUdpspeeder uninstall Menu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m Server\033[0m")
    print("2)\033[92m Client\033[0m")
    print("0)\033[94m back to uninstall menu\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Choose an option to uninstall (0-2): ").strip()

    if choice == "1":
        uninstall_speederv2_server()
    elif choice == "2":
        uninstall_speederv2_client()
    elif choice == "0":
        uninstall_menu() 
    else:
        print("Wrong choice. Please select a valid option.")


def speederv2_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUdpspeeder \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    while True:
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0)\033[94m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_speederv2_server()  
        elif choice == "2":
            speederv2_client_menu()  
        elif choice == "0":
            break  
        else:
            print("Wrong option. choose a valid number")

def speederv2_client_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUdpspeeder \033[96mClient \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Client\033[97m[1]\033[0m")
        print("2)\033[93m Client\033[97m[2]\033[0m")
        print("3)\033[93m Client\033[97m[3]\033[0m")
        print("4)\033[93m Client\033[97m[4]\033[0m")
        print("5)\033[93m Client\033[97m[5]\033[0m")
        print("0) \033[94mback to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-5): ").strip()

        if choice == "1":
            setup_speederv2_client()  
        elif choice == "2":
            setup_speederv2_client()  
        elif choice == "3":
            setup_speederv2_client()  
        elif choice == "4":
            setup_speederv2_client()  
        elif choice == "5":
            setup_speederv2_client()  
        elif choice == "0":
            break  
        else:
            print("Wrong option. choose a valid number")

def tinyvpn_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mTinyVpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m TinyVPN Server\033[0m")
        print("2)\033[92m TinyVPN Client\033[0m")
        print("0)\033[93m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_tinyvpn_server()  
        elif choice == "2":
            setup_tinyvpn_client()  
        elif choice == "0":
            break  
        else:
            print("Wrong option. Please choose a valid number.")

def tinyvpn_udp2raw_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mTinyvpn + Udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0)\033[94m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_tinyvpn_server() 
            setup_udp2raw_server()
        elif choice == "2":
            setup_tinyvpn_client() 
            setup_udp2raw_client()
        elif choice == "0":
            break  
        else:
            print("Wrong option. choose a valid number")


def udpspeeder_udp2raw_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mUdpspeeder + Udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Setup Server")
        print("2)\033[92m Setup Client")
        print("0)\033[94m back to main menu")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_server_udp2raw_updspeeder()
        elif choice == "2":
            speederv2_udp2raw_client_menu()
        elif choice == "0":
            break  
        else:
            print("Wrong option. Please choose a valid number")

def speederv2_udp2raw_client_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mUdpspeeder + Udp2raw \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Client\033[97m[1]\033[0m")
        print("2)\033[93m Client\033[97m[2]\033[0m")
        print("3)\033[93m Client\033[97m[3]\033[0m")
        print("4)\033[93m Client\033[97m[4]\033[0m")
        print("5)\033[93m Client\033[97m[5]\033[0m")
        print("0)\033[94m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-5): ").strip()

        if choice == "1":
            setup_client_udp2raw_updspeeder()
        elif choice == "2":
            setup_client_udp2raw_updspeeder() 
        elif choice == "3":
            setup_client_udp2raw_updspeeder() 
        elif choice == "4":
            setup_client_udp2raw_updspeeder() 
        elif choice == "5":
            setup_client_udp2raw_updspeeder() 
        elif choice == "0":
            break  
        else:
            print("Wrong option. Please choose a valid number")

PROXY_FORWARDER_FILES = {
    "tcp": "https://github.com/Azumi67/proxyforwarder/releases/download/1.00/tcp_forwarder",
    "udp": "https://github.com/Azumi67/proxyforwarder/releases/download/1.00/udp_forwarder",
}
PROXYFORWARDER_DIR = "/usr/local/bin/proxyforwarder"
SRC_DIR = os.path.join(PROXYFORWARDER_DIR, "src")
CONFIG_PATH = os.path.join(SRC_DIR, "config.yaml")
TCP_FORWARDER_PATH = os.path.join(SRC_DIR, "tcp_forwarder")
UDP_FORWARDER_PATH = os.path.join(SRC_DIR, "udp_forwarder")

def download_proxyforwarder():
    repo_url = "https://github.com/Azumi67/proxyforwarder.git"
    install_dir = "/usr/local/bin/proxyforwarder"
    
    if not os.path.exists(install_dir):
        print("\033[93m──────────────────────────────────────\033[0m")
        display_notification("\033[93mCloning ProxyForwarder repo...\033[0m")
        print("\033[93m──────────────────────────────────────\033[0m")
        subprocess.run(["git", "clone", repo_url, install_dir], check=True)
        display_checkmark("\033[92mProxyForwarder downloaded successfully\033[0m")
    else:
        print("ProxyForwarder already exists.")
    


def download_proxyforwarder_binary(protocol):

    if protocol not in PROXY_FORWARDER_FILES:
        print("Wrong protocol selected. Choose either 'tcp' or 'udp'.")
        return
    
    install_dir = "/usr/local/bin/proxyforwarder/src"
    os.makedirs(install_dir, exist_ok=True)
    file_path = f"{install_dir}/{protocol}_forwarder"
    
    if not os.path.exists(file_path):
        print("\033[93m──────────────────────────────────────\033[0m")
        print(f"Downloading {protocol} forwarder binary...")
        print("\033[93m──────────────────────────────────────\033[0m")
        subprocess.run(["wget", "-q", "--show-progress", PROXY_FORWARDER_FILES[protocol], "-O", file_path], check=True)
        subprocess.run(["chmod", "+x", file_path], check=True)  
        display_checkmark(f"\033[92mDownloaded {protocol} forwarder to {file_path}\033[0m")
    else:
        print(f"ProxyForwarder {protocol} binary already exists at {file_path}. Skipping download.")


def create_proxyforwarder_service_tcp():
    service_file = "/etc/systemd/system/proxyforwarder.service"
    exec_path = f"{TCP_FORWARDER_PATH} {CONFIG_PATH}"
    
    service_content = f"""
[Unit]
Description=ProxyForwarder TCP Service
After=network.target

[Service]
ExecStart={exec_path}
Restart=always
TimeoutSec=30
LimitNOFILE=65535  

[Install]
WantedBy=multi-user.target
"""

    with open(service_file, "w") as f:
        f.write(service_content)

    display_checkmark(f"\033[92mProxyForwarder TCP service created at {service_file}\033[0m")

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "proxyforwarder"], check=True)
    subprocess.run(["systemctl", "start", "proxyforwarder"], check=True)

    display_checkmark("\033[92mProxyForwarder TCP service started\033[0m")

def restart_proxyforwarder_daemon():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for proxyforwarder...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600 
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60  
            break
        else:
            print("\033[91mInvalid choice. select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}  
    systemctl restart proxyforwarder
done
    """

    bash_script_path = "/usr/local/bin/proxyforwarder_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=proxyforwarder Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/proxyforwarder_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "proxyforwarder_daemon.service"])
    subprocess.run(["systemctl", "start", "proxyforwarder_daemon.service"])

    display_checkmark(f"\033[92mproxyforwarder restart daemon set up successfully.\033[0m")

def setup_tcp_proxyforwarder():
    print("\033[93m──────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling TCP ProxyForwarder...\033[0m")
    print("\033[93m──────────────────────────────────────\033[0m")

    os.makedirs(SRC_DIR, exist_ok=True)

    if not os.path.exists(PROXYFORWARDER_DIR):
        display_notification("\033[93mCloning ProxyForwarder repo...\033[0m")
        subprocess.run(["git", "clone", "https://github.com/Azumi67/proxyforwarder.git", PROXYFORWARDER_DIR], check=True)

    if not os.path.exists(TCP_FORWARDER_PATH):
        display_notification("\033[93mDownloading TCP ProxyForwarder binary...\033[0m")
        subprocess.run(["wget", "-q", "--show-progress",
                        "https://github.com/Azumi67/proxyforwarder/releases/download/1.00/tcp_forwarder",
                        "-O", TCP_FORWARDER_PATH], check=True)
        subprocess.run(["chmod", "+x", TCP_FORWARDER_PATH], check=True)
    print("\033[93m──────────────────────────────────────\033[0m")

    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)

    config = {"forwarders": []}
    
    while True:
        port_type = input("\033[93mDo you want to configure: \033[97m1)\033[92m Single port\033[97m 2) \033[96mPort range\033[93m:\033[0m ").strip()

        if port_type == '1': 
            ip_type = input("\033[93mChoose IP version:\033[97m 1) \033[92mIPv4 \033[97m2)\033[96m IPv6\033[93m:\033[0m ").strip()
            listen_address = "0.0.0.0" if ip_type == '1' else "::"

            listen_port = int(input("\033[93mEnter \033[92mlocal port\033[93m:\033[0m ").strip())
            target_address = input("\033[93mEnter \033[92mtarget address\033[93m:\033[0m ").strip()
            target_port = int(input("\033[93mEnter \033[92mtarget port\033[93m:\033[0m ").strip())

            config["forwarders"].append({
                "listen_address": listen_address,
                "listen_port": listen_port,
                "target_address": target_address,
                "target_port": target_port
            })

        elif port_type == '2': 
            ip_type = input("\033[93mChoose IP version:\033[97m 1) \033[92mIPv4 \033[97m2) \033[96mIPv6\033[93m:\033[0m ").strip()
            listen_address = "0.0.0.0" if ip_type == '1' else "::"

            target_address = input("\033[93mEnter \033[92mtarget address\033[93m:\033[0m ").strip()
            start_port = int(input("\033[93mEnter \033[92mstarting port\033[93m:\033[0m ").strip())
            end_port = int(input("\033[93mEnter \033[92mending port\033[93m:\033[0m ").strip())

            config["forwarders"].append({
                "listen_address": listen_address,
                "target_address": target_address,
                "port_range": {"start": start_port, "end": end_port}
            })

        else:
            print("Wrong input. Please choose 1 for single port or 2 for port range.")
            continue

        if input("\033[93mDo you want to \033[96madd \033[92manother port\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m):\033[0m ").strip().lower() != 'yes':
            break

    config.update({
        "thread_pool": {
            "threads": int(input("\033[93mEnter \033[92mCPU thread\033[93m count\033[97m (default 2)\033[93m:\033[0m ").strip() or 2)
        },
        "max_connections": int(input("\033[93mEnter \033[92mmax_connections \033[97m(default 200)\033[93m:\033[0m ").strip() or 200),
        "retry_attempts": int(input("\033[93mEnter \033[92mretry_attempts\033[97m (default 5)\033[93m:\033[0m ").strip() or 5),
        "retry_delay": int(input("\033[93mEnter \033[92mretry_delay in seconds\033[97m (default 10)\033[93m:\033[0m ").strip() or 10),
        "tcp_no_delay": input("\033[93mEnable \033[92mTCP No Delay? \033[97m(true/false, default false)\033[93m:\033[0m ").strip().lower() in ['true', '1', 'yes'],
        "buffer_size": int(input("\033[93mEnter \033[92mbuffer_size \033[97m(default 8092, max 65535)\033[93m:\033[0m ").strip() or 8092),
        "monitoring_port": int(input("\033[93mEnter \033[92mmonitoring port \033[97m(default 8080)\033[93m:\033[0m ").strip() or 8080),

        "timeout": {
            "connection": int(input("\033[93mEnter connection\033[92m timeout in seconds \033[97m(default 3000)\033[93m:\033[0m ").strip() or 3000)
        },

        "health_check": {
            "enabled": input("\033[93mEnable \033[92mhealth_check?\033[97m (true/false, default true)\033[93m:\033[0m ").strip().lower() in ['true', '1', 'yes'],
            "interval": int(input("\033[93mEnter \033[92mhealth_check \033[96minterval in seconds \033[97m(default 300)\033[93m:\033[0m ").strip() or 300)
        },

        "tcp_keep_alive": {
            "enabled": input("\033[93mEnable \033[92mTCP keep_alive?\033[97m (true/false, default true)\033[93m:\033[0m ").strip().lower() in ['true', '1', 'yes'],
            "idle": int(input("\033[93mEnter \033[92mTCP keep_alive idle time \033[97m(default 60)\033[93m:\033[0m ").strip() or 60),
            "interval": int(input("\033[93mEnter \033[92mTCP keep_alive interval \033[97m(default 10)\033[93m:\033[0m ").strip() or 10),
            "count": int(input("\033[93mEnter \033[92mTCP keep_alive count \033[97m(default 5)\033[93m:\033[0m ").strip() or 5)
        },

        "logging": {
            "enabled": input("\033[93mEnable \033[92mlogging? (true/false, default true)\033[93m:\033[0m ").strip().lower() in ['true', '1', 'yes'],
            "file": input("\033[93mEnter \033[92mlogging \033[93mfile name \033[97m(default logfile.log)\033[93m:\033[0m ").strip() or "logfile.log",
            "level": input("\033[93mEnter logging level \033[97m(default INFO)\033[93m:\033[0m ").strip() or "INFO"
        }
    })

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    display_checkmark(f"\033[92mProxyForwarder config saved at: {CONFIG_PATH}\033[0m")
    create_proxyforwarder_service_tcp()
    restart_proxyforwarder_daemon()



def create_proxyforwarder_service_udp():
    service_file = "/etc/systemd/system/proxyforwarder.service"
    exec_path = f"/usr/local/bin/proxyforwarder/src/udp_forwarder /usr/local/bin/proxyforwarder/src/config.yaml"
    
    service_content = f"""
    [Unit]
    Description=ProxyForwarder UDP Service
    After=network.target

    [Service]
    WorkingDirectory=/usr/local/bin/proxyforwarder/src
    ExecStart={exec_path}
    Restart=always
    TimeoutSec=30
    LimitNOFILE=65535  

    [Install]
    WantedBy=multi-user.target
    """

    with open(service_file, "w") as f:
        f.write(service_content)

    print(f"ProxyForwarder service created at {service_file}")

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "proxyforwarder"], check=True)
    subprocess.run(["systemctl", "restart", "proxyforwarder"], check=True)

    display_checkmark("\033[92mProxyForwarder UDP service started\033[0m")


def setup_udp_proxyforwarder():
    print("\033[93m──────────────────────────────────────\033[0m")
    display_notification("\033[93mInstalling UDP ProxyForwarder...\033[0m")
    print("\033[93m──────────────────────────────────────\033[0m")

    os.makedirs(SRC_DIR, exist_ok=True)

    if not os.path.exists(PROXYFORWARDER_DIR):
        display_notification("\033[93mCloning ProxyForwarder repo...\033[0m")
        subprocess.run(["git", "clone", "https://github.com/Azumi67/proxyforwarder.git", PROXYFORWARDER_DIR], check=True)

    if not os.path.exists(UDP_FORWARDER_PATH):
        display_notification("\033[93mDownloading UDP ProxyForwarder binary...\033[0m")
        subprocess.run(["wget", "-q", "--show-progress",
                        "https://github.com/Azumi67/proxyforwarder/releases/download/1.00/udp_forwarder",
                        "-O", UDP_FORWARDER_PATH], check=True)
        subprocess.run(["chmod", "+x", UDP_FORWARDER_PATH], check=True)
    print("\033[93m──────────────────────────────────────\033[0m")

    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)

    config = {"srcAddrPorts": [], "dstAddrPorts": []}

    num_ports = int(input("\033[93mHow many \033[92mports\033[93m do you want?\033[0m ").strip())

    for i in range(1, num_ports + 1):
        print("\033[93m──────────────────────────────────────\033[0m")
        print(f"\033[93mConfiguring \033[96mConfig {i}...\033[0m")
        print("\033[93m──────────────────────────────────────\033[0m")

        src_port = input(f"\033[93mEnter\033[92m local port \033[93mfor \033[96mConfig {i}:\033[0m ").strip()

        dst_address = input(f"\033[93mEnter \033[92mdestination address\033[93m for \033[96mConfig {i}:\033[0m ").strip()
        dst_port = input(f"\033[93mEnter \033[92mdestination port \033[93mfor \033[96mConfig {i}:\033[0m ").strip()

        config["srcAddrPorts"].append(f"0.0.0.0:{src_port}")  
        config["dstAddrPorts"].append(f"{dst_address}:{dst_port}") 

    config.update({
        "timeout": int(input("\033[93mEnter \033[92mtimeout for idle connections\033[97m (default 3000s)\033[93m:\033[0m ").strip() or 3000), 
        "buffer_size": int(input("\033[93mEnter \033[92mbuffer size \033[97m(default 8092, max 65530)\033[93m:\033[0m ").strip() or 8092),  
        "thread_pool": {
            "threads": int(input("\033[93mEnter \033[92mnumber of CPU threads\033[97m (default 2)\033[93m:\033[0m ").strip() or 2)  
        },

        "logging": {
            "enabled": input("\033[93mEnable \033[92mlogging? \033[97m(true/false, default true)\033[93m:\033[0m ").strip().lower() in ['true', '1', 'yes'],
            "file": input("\033[93mEnter \033[92mlog file name \033[97m(default logfile.log)\033[93m:\033[0m ").strip() or "logfile.log",
            "level": input("\033[93mEnter \033[92mlog level \033[97m(default INFO, options TRACE, DEBUG, INFO, WARN, ERROR)\033[93m:\033[0m ").strip() or "INFO"
        },
    })

    monitoring_enabled = input("\033[93mDo you want to enable monitoring? \033[92m(yes/no)\033[93m:\033[0m ").strip().lower()
    if monitoring_enabled in ['yes', 'y']:
        monitoring_port = input("\033[93mEnter the \033[92mmonitoring port\033[93m (default 8080):\033[0m ").strip()
        config["monitoring_port"] = int(monitoring_port) if monitoring_port else 8080
    else:
        config["monitoring_port"] = ""  

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    display_checkmark(f"\033[92mProxyForwarder config saved at {CONFIG_PATH}\033[0m")
    create_proxyforwarder_service_udp()
    restart_proxyforwarder_daemon()


def setup_proxyforwarder():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mProxyforwarder \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    print("1)\033[93m TCP\033[0m")
    print("2)\033[92m UDP\033[0m")
    print("\033[93m╰───────────────────────────────────────╯\033[0m")

    choice = input("Enter your choice (1-2): ").strip()

    download_proxyforwarder()

    if choice == "1":
        download_proxyforwarder_binary("tcp") 
        setup_tcp_proxyforwarder() 
    elif choice == "2":
        download_proxyforwarder_binary("udp") 
        setup_udp_proxyforwarder()  
    else:
        print("Wrong choice. Please enter 1 or 2.")


def proxyforwarder_tinyvpn_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mProxy + Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    print("\033[93m╭───────────────────────────────────────╮\033[0m")
    while True:
        print("1)\033[93m Server\033[0m")
        print("2)\033[93m Client\033[0m")
        print("0)\033[94m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_tinyvpn_server() 
        elif choice == "2":
            setup_tinyvpn_client() 
            setup_proxyforwarder()
        elif choice == "0":
            break 
        else:
            print("Wrong option. Please choose a valid number")

def tinymapper_tinyvpn_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mTinymapper + Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0)\033[94m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            setup_tinyvpn_server() 
        elif choice == "2":
            setup_tinyvpn_client() 
            download_and_setup_tinymapper()
        elif choice == "0":
            break  
        else:
            print("Wrong option. Please choose a valid number")

def proxyforwarder_geneve_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[92mTinymapper + Tinyvpn \033[93mMenu\033[0m")
    print(
        '\033[92m "-"\033[93m═══════════════════════════════════════════════════\033[0m'
    )
    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("1)\033[93m Server\033[0m")
        print("2)\033[92m Client\033[0m")
        print("0)\033[93m back to main menu\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        choice = input("Choose an option (0-2): ").strip()

        if choice == "1":
            kharejm1_gen_menu()  
        elif choice == "2":
            iranm1_gen_menu()  
            setup_proxyforwarder()
        elif choice == "0":
            break 
        else:
            print("Wrong option. Please choose a valid number")


def genkhm1_ping():
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    try:
        print("\033[96mPlease Wait, Azumi is pinging...")
        subprocess.run(
            ["ping", "-c", "2", "66.200.2.1"], check=True, stdout=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(Fore.LIGHTRED_EX + "Pinging failed:", e, Style.RESET_ALL)


def genirm1_ping():
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    try:
        print("\033[96mPlease Wait, Azumi is pinging...")
        subprocess.run(
            ["ping", "-c", "2", "66.200.1.1"], check=True, stdout=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(Fore.LIGHTRED_EX + "Pinging failed:", e, Style.RESET_ALL)


def ping_kh_service():
    service_content = """[Unit]
Description=keepalive
After=network.target

[Service]
ExecStart=/bin/bash /etc/ping_sys.sh
Restart=always

[Install]
WantedBy=multi-user.target
"""

    service_file_path = "/etc/systemd/system/ping_gen.service"
    with open(service_file_path, "w") as service_file:
        service_file.write(service_content)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "ping_gen.service"])
    sleep(1)
    subprocess.run(["systemctl", "restart", "ping_gen.service"])


def gen_job():
    file_path = "/etc/sys.sh"

    try:

        subprocess.run(
            f"(crontab -l | grep -v '{file_path}') | crontab -",
            shell=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            f"(crontab -l ; echo '@reboot /bin/bash {file_path}') | crontab -",
            shell=True,
            capture_output=True,
            text=True,
        )

        display_checkmark("\033[92mCronjob added successfully!\033[0m")
    except subprocess.CalledProcessError as e:
        print("\033[91mFailed to add cronjob:\033[0m", e)


def ufw(ip_address):
    subprocess.run(["sudo", "ufw", "allow", "from", ip_address])


def delufw(ip_address):
    subprocess.run(["sudo", "ufw", "delete", "allow", "from", ip_address])


def ipv4_address():
    result = subprocess.run(
        ["curl", "-s", "https://ipinfo.io/ip"], capture_output=True, text=True
    )
    return result.stdout.strip()


def kharejm1_gen_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mKharej server \033[92mMethod 1\033[0m")
    print('\033[92m "-"\033[93m═══════════════════════════\033[0m')
    display_notification("\033[93mConfiguring Kharej server...\033[0m")

    if os.path.isfile("/etc/sys.sh"):
        os.remove("/etc/sys.sh")

    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    geneve_ipk1_version1()



def geneve_ipk1_version1():
    remote_ip = input("\033[93mEnter \033[92mIRAN\033[93m IPV4 address: \033[0m")
    ufw(remote_ip)
    ufw("66.200.1.1")
    ufw("66.200.1.2")

    subprocess.run(
        [
            "sudo",
            "ip",
            "link",
            "add",
            "name",
            "azumigen",
            "type",
            "geneve",
            "id",
            "1000",
            "remote",
            remote_ip,
        ],
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["sudo", "ip", "link", "set", "azumigen", "up"], stdout=subprocess.DEVNULL
    )
    subprocess.run(
        ["sudo", "ip", "addr", "add", "66.200.1.1/32", "dev", "azumigen"],
        stdout=subprocess.DEVNULL,
    )

    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    display_notification("\033[93mAdding commands...\033[0m")
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")

    with open("/etc/sys.sh", "w") as f:
        f.write(
            f"sudo ip link add name azumigen type geneve id 1000 remote {remote_ip}\n"
        )
        f.write("sudo ip link set azumigen up\n")
        f.write("sudo ip addr add 66.200.1.1/32 dev azumigen\n")

    set_mtu = input(
        "\033[93mDo you want to set the \033[92mMTU\033[96m [Geneve]\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m"
    )

    if set_mtu.lower() == "yes" or set_mtu.lower() == "y":
        mtu_value = input(
            "\033[93mEnter the desired\033[92m MTU value\033[93m: \033[0m"
        )
        mtu_command = f"ip link set dev azumigen mtu {mtu_value}\n"
        with open("/etc/sys.sh", "a") as f:
            f.write(mtu_command)
        subprocess.run(mtu_command, shell=True, check=True)
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    display_checkmark("\033[92mConfiguration is done!\033[0m")

    gen_job()
    display_checkmark("\033[92mkeepalive service Configured!\033[0m")

    genkhm1_ping()
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    print("\033[93mCreated IP Addresses (Kharej):\033[0m")
    print("\033[92m" + "+---------------------------+" + "\033[0m")
    print("\033[92m" + "        66.200.1.1\033[0m")
    print("\033[92m" + "+---------------------------+" + "\033[0m")

    script_content = """#!/bin/bash
ip_address="66.200.1.2"
max_pings=5
interval=2
while true
do
    for ((i = 1; i <= max_pings; i++))
    do
        ping_result=$(ping -c 1 $ip_address | grep "time=" | awk -F "time=" "{print $2}" | awk -F " " "{print $1}" | cut -d "." -f1)
        if [ -n "$ping_result" ]; then
            echo "Ping successful! Response time: $ping_result ms"
        else
            echo "Ping failed!"
        fi
    done
    echo "Waiting for $interval seconds..."
    sleep $interval
done
"""

    with open("/etc/ping_sys.sh", "w") as script_file:
        script_file.write(script_content)

    os.chmod("/etc/ping_sys.sh", 0o755)
    ping_kh_service()

    print("\033[92mKharej Server Configuration Completed!\033[0m")


def iranm1_gen_menu():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mIran server\033[92m Method 1\033[0m")
    print( '\033[92m "-"\033[93m═══════════════════════════\033[0m')
    display_notification("\033[93mConfiguring for Iran server...\033[0m")

    if os.path.isfile("/etc/sys.sh"):
        os.remove("/etc/sys.sh")

    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    geneve_ipi_version1()


def geneve_ipi_version1():
    remote_ip = input("\033[93mEnter \033[92mKharej\033[93m IPV4 address: \033[0m")
    ufw(remote_ip)
    ufw("66.200.1.1")
    ufw("66.200.1.2")

    subprocess.run(
        [
            "sudo",
            "ip",
            "link",
            "add",
            "name",
            "azumigen",
            "type",
            "geneve",
            "id",
            "1000",
            "remote",
            remote_ip,
        ],
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["sudo", "ip", "link", "set", "azumigen", "up"], stdout=subprocess.DEVNULL
    )
    subprocess.run(
        ["sudo", "ip", "addr", "add", "66.200.1.2/30", "dev", "azumigen"],
        stdout=subprocess.DEVNULL,
    )

    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    display_notification("\033[93mAdding commands...\033[0m")
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")

    with open("/etc/sys.sh", "w") as f:
        f.write(
            f"sudo ip link add name azumigen type geneve id 1000 remote {remote_ip}\n"
        )
        f.write("sudo ip link set azumigen up\n")
        f.write("sudo ip addr add 66.200.1.2/30 dev azumigen\n")

    set_mtu = input(
        "\033[93mDo you want to set the \033[92mMTU\033[96m [Geneve]\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m"
    )

    if set_mtu.lower() == "yes" or set_mtu.lower() == "y":
        mtu_value = input(
            "\033[93mEnter the desired\033[92m MTU value\033[93m: \033[0m"
        )
        mtu_command = f"ip link set dev azumigen mtu {mtu_value}\n"
        with open("/etc/sys.sh", "a") as f:
            f.write(mtu_command)
        subprocess.run(mtu_command, shell=True, check=True)

    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    display_checkmark("\033[92mConfiguration is done!\033[0m")

    gen_job()

    display_checkmark("\033[92mkeepalive service Configured!\033[0m")

    genirm1_ping()
    print("\033[93m─────────────────────────────────────────────────────────\033[0m")
    print("\033[93mCreated IP Addresses (IRAN):\033[0m")
    print("\033[92m" + "+---------------------------+" + "\033[0m")
    print("\033[92m" + "        66.200.1.2\033[0m")
    print("\033[92m" + "+---------------------------+" + "\033[0m")

    script_content = """#!/bin/bash
ip_address="66.200.1.1"
max_pings=5
interval=2
while true
do
    for ((i = 1; i <= max_pings; i++))
    do
        ping_result=$(ping -c 1 $ip_address | grep "time=" | awk -F "time=" "{print $2}" | awk -F " " "{print $1}" | cut -d "." -f1)
        if [ -n "$ping_result" ]; then
            echo "Ping successful! Response time: $ping_result ms"
        else
            echo "Ping failed!"
        fi
    done
    echo "Waiting for $interval seconds..."
    sleep $interval
done
"""

    with open("/etc/ping_sys.sh", "w") as script_file:
        script_file.write(script_content)

    os.chmod("/etc/ping_sys.sh", 0o755)
    ping_kh_service()

    print("\033[92mIRAN Server Configuration Completed!\033[0m")

def restart_tinymapper_daemon_server():
    print("\033[93m───────────────────────────────────────\033[0m")
    print("\033[93mSetting up Custom Daemon for tinymapper...\033[0m")
    print("\033[93m───────────────────────────────────────\033[0m")
    
    enable_timer = input("\033[93mDo you want to \033[92menable \033[93mthe \033[96mreset timer\033[93m? (\033[92myes\033[93m/\033[91mno\033[93m): \033[0m").strip().lower()
    
    if enable_timer not in ["yes", "y"]:
        print("\033[91mReset timer not enabled. Exiting...\033[0m")
        return
    
    num_ports = int(input("\033[93mHow many \033[92mports\033[93m do you have? \033[0m").strip())
    

    while True:
        print("\033[93m╭───────────────────────────────────────╮\033[0m")
        print("\n\033[93mSelect the time unit for restart interval:\033[0m")
        print("1) \033[93mHours\033[0m")
        print("2) \033[92mMinutes\033[0m")
        print("\033[93m╰───────────────────────────────────────╯\033[0m")
        
        time_unit_choice = input("\033[93mEnter your choice (1 or 2): \033[0m").strip()

        if time_unit_choice == "1":
            time_unit = "hours"
            time_multiplier = 3600  
            break
        elif time_unit_choice == "2":
            time_unit = "minutes"
            time_multiplier = 60  
            break
        else:
            print("\033[91mInvalid choice. Select 1 for hours or 2 for minutes.\033[0m")
    
    interval = input(f"\033[93mEnter the number of {time_unit} for restart interval: \033[0m").strip()
    
    if not interval.isdigit() or int(interval) <= 0:
        print("\033[91mPlease enter a valid number.\033[0m")
        return

    interval = int(interval)

    total_seconds = interval * time_multiplier

    restart_commands = []
    for port_num in range(1, num_ports + 1):
        restart_commands.append(f"systemctl restart tinymapper_{port_num}")

    bash_script = f"""
#!/bin/bash

while true; do
    sleep {total_seconds}
    {"; ".join(restart_commands)}
done
    """

    bash_script_path = "/usr/local/bin/tinymapper_daemon.sh"
    
    with open(bash_script_path, "w") as f:
        f.write(bash_script)

    os.chmod(bash_script_path, 0o755)

    service_file = f"""
[Unit]
Description=tinymapper Custom Restart Daemon
After=network.target

[Service]
ExecStart={bash_script_path}
Restart=always
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
    """

    service_file_path = "/etc/systemd/system/tinymapper_daemon.service"
    
    with open(service_file_path, "w") as f:
        f.write(service_file)

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "tinymapper_daemon.service"])
    subprocess.run(["systemctl", "start", "tinymapper_daemon.service"])

    print("\033[92mTinymapper restart daemon set up successfully.\033[0m")

def download_and_setup_tinymapper():
    print("\033[93m───────────────────────────────────────\033[0m")
    download_links = {
        'amd64': 'https://github.com/Azumi67/Wangyu_azumi_UDP/releases/download/cores/tinymapper_amd64',
        'arm': 'https://github.com/Azumi67/Wangyu_azumi_UDP/releases/download/cores/tinymapper_arm'
    }
    
    system_arch = platform.architecture()[0]
    if '64' in system_arch:
        arch = 'amd64'
    elif '32' in system_arch:
        arch = 'arm'
    else:
        raise Exception("Unsupported architecture!")

    download_url = download_links[arch]
    download_path = '/usr/local/bin/tinymapper'

    if os.path.exists(download_path):
        print(f"tinymapper already exists at {download_path}, skipping download.")
    else:
        display_notification(f"\033[93mDownloading tinymapper for {arch}...\033[0m")
        urllib.request.urlretrieve(download_url, download_path)

        print("\033[96mMaking tinymapper executable...\033[0m")
        subprocess.run(['chmod', '+x', download_path])
    print("\033[93m───────────────────────────────────────\033[0m")

    try:
        num_ports = int(input("\033[93mHow many \033[92mports\033[93m would you like to configure?\033[0m ").strip())
    except ValueError:
        print("Invalid number. Please enter a valid integer.")
        return

    forwarders = []

    for i in range(num_ports):
        print("\033[93m─────────────────────────────────────\033[0m")
        print(f"\033[93mConfiguring \033[96mport {i+1}...\033[0m")
        print("\033[93m─────────────────────────────────────\033[0m")
        ip_version = input("\033[93mChoose IP version: \033[97m1)\033[93m IPv4\033[97m 2)\033[92m IPv6:\033[0m ").strip()
        if ip_version == '1':
            local_address = input("\033[93mEnter \033[92mlocal address\033[97m (default 0.0.0.0)\033[93m:\033[0m ").strip() or "0.0.0.0"
        elif ip_version == '2':
            local_address = input("\033[93mEnter \033[92mlocal IPv6 address\033[97m (default [::])\033[93m:\033[0m ").strip() or "[::]"
        else:
            print("Invalid choice. Skipping this port configuration.")
            continue

        local_port = input("\033[93mEnter \033[92mlocal port\033[93m:\033[0m ").strip()
        while not local_port.isdigit():
            display_error("Local port must be a number.")
            local_port = input("\033[93mEnter \033[92mlocal port\033[93m:\033[0m ").strip()
        
        remote_address = input("\033[93mEnter \033[92mremote address\033[93m:\033[0m ").strip()
        remote_port = input("\033[93mEnter \033[92mremote port\033[93m:\033[0m ").strip()
        while not remote_port.isdigit():
            display_error("Remote port must be a number.")
            remote_port = input("\033[93mEnter \033[92mremote port:\033[0m ").strip()

        proto_type = input("\033[93mChoose protocol: \033[97m1) \033[93mTCP \033[97m2)\033[92m UDP \033[97m3)\033[94m Both\033[93m:\033[0m ").strip()
        if proto_type == '1':
            protocol_args = "-t"
        elif proto_type == '2':
            protocol_args = "-u"
        elif proto_type == '3':
            protocol_args = "-t -u"
        else:
            print("Wrong protocol choice. Skipping configuration.")
            continue

        forwarder = {
            "listen_address": local_address,
            "listen_port": local_port,
            "target_address": remote_address,
            "target_port": remote_port,
            "protocol": protocol_args
        }
        forwarders.append(forwarder)

    for i, forwarder in enumerate(forwarders):
        local_address = forwarder["listen_address"]
        local_port = forwarder["listen_port"]
        remote_address = forwarder["target_address"]
        remote_port = forwarder["target_port"]
        protocol_args = forwarder["protocol"]

        tinymapper_command = f"/usr/local/bin/tinymapper -l {local_address}:{local_port} -r {remote_address}:{remote_port} {protocol_args}"

        service_content = f"""
        [Unit]
        Description=Tinymapper Service for Port {i+1}

        [Service]
        ExecStart={tinymapper_command}
        Restart=always

        [Install]
        WantedBy=multi-user.target
        """

        service_path = f"/etc/systemd/system/tinymapper_{i+1}.service"
        with open(service_path, "w") as service_file:
            service_file.write(service_content)

        print(f"\033[93mService configuration created at {service_path}\033[0m")

        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", f"tinymapper_{i+1}"])
        subprocess.run(["systemctl", "restart", f"tinymapper_{i+1}"])

        display_checkmark(f"\033[92mTinymapper service for Config {i+1} has been started.\033[0m")
        restart_tinymapper_daemon_server()



def main():
    show_menu()  

if __name__ == "__main__":
    main()
