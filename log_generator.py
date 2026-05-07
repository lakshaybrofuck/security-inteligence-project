import time
import random
import json
import argparse
import asyncio
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

# ANSI Escape codes for colored output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    MAGENTA = '\033[95m'

API_URL = "http://localhost:8000/api/logs"

EVENT_TYPES = [
    ("failed_login", "medium", "Failed authentication attempt"),
    ("successful_login", "low", "User logged in successfully"),
    ("port_scan", "high", "Port scanning activity detected"),
    ("sql_injection_attempt", "critical", "SQLi pattern blocked in WAF"),
    ("file_access", "low", "File read access"),
    ("outbound_connection", "medium", "Outbound connection established"),
    ("firewall_block", "low", "Traffic blocked by firewall rules")
]

BAD_IP_RANGES = [
    "185.153.196.", # Mock bad actors
    "103.111.42.",
    "45.134.144.",
    "176.10.99."
]

HOSTNAMES = ["web-server-01", "db-cluster-02", "app-node-03", "gateway-01"]

def random_ip(bad=False):
    if bad:
        return random.choice(BAD_IP_RANGES) + str(random.randint(1, 254))
    
    # 30% chance internal IP, 70% chance external
    if random.random() < 0.3:
        return f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"
    else:
        return f"{random.randint(11, 100)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def post_log(log_data):
    try:
        req = urllib.request.Request(API_URL, method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(log_data).encode('utf-8')
        with urllib.request.urlopen(req, data=data) as response:
            if response.status == 200:
                return True
    except urllib.error.URLError as e:
        print(f"{Colors.RED}Failed to connect to SIEM: {e.reason}{Colors.RESET}")
    return False

def print_log(log_data):
    color = Colors.GREEN
    if log_data["severity"] == "medium":
        color = Colors.YELLOW
    elif log_data["severity"] == "high":
        color = Colors.MAGENTA
    elif log_data["severity"] == "critical":
        color = Colors.RED
        
    print(f"{color}[{log_data['timestamp']}] {log_data['source_ip']} -> {log_data['event_type']} ({log_data['severity']}) - {log_data['message']}{Colors.RESET}")

def generate_random_log():
    event, severity, msg = random.choice(EVENT_TYPES)
    bad_actor = random.random() < 0.1 # 10% chance of being from a bad IP
    
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": random_ip(bad=bad_actor),
        "dest_ip": random_ip(bad=False),
        "event_type": event,
        "severity": severity,
        "message": msg,
        "hostname": random.choice(HOSTNAMES),
        "is_threat": bad_actor,
        "raw_log": json.dumps({"user_agent": "Mozilla/5.0", "bytes_out": random.randint(100, 5000)})
    }
    return log

async def simulate_brute_force():
    ip = random_ip(bad=True)
    print(f"{Colors.RED}>>> INITIATING BRUTE FORCE ATTACK FROM {ip}{Colors.RESET}")
    for i in range(7): # 7 attempts (rules trigger at >5 in 60s)
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": ip,
            "dest_ip": "10.0.0.15",
            "event_type": "failed_login",
            "severity": "medium",
            "message": f"Failed authentication attempt for user 'admin' (Attempt {i+1})",
            "hostname": "gateway-01",
            "raw_log": json.dumps({"username": "admin", "protocol": "SSH"})
        }
        post_log(log)
        print_log(log)
        await asyncio.sleep(0.3)

async def simulate_port_scan():
    ip = random_ip(bad=True)
    print(f"{Colors.MAGENTA}>>> INITIATING PORT SCAN FROM {ip}{Colors.RESET}")
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 3306, 3389, 8080] # 14 ports (>10 in 30s triggers rule)
    
    for port in ports:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": ip,
            "dest_ip": "10.0.1.50",
            "event_type": "port_scan",
            "severity": "high",
            "message": f"Connection attempt to port {port}",
            "hostname": "web-server-01",
            "raw_log": json.dumps({"dest_port": port, "protocol": "TCP"})
        }
        post_log(log)
        print_log(log)
        await asyncio.sleep(0.1)

async def simulate_data_exfil():
    ip = "10.0.5.99"
    print(f"{Colors.RED}>>> INITIATING DATA EXFILTRATION FROM {ip}{Colors.RESET}")
    bytes_out = 150 * 1024 * 1024 # 150MB (>100MB triggers rule)
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": ip,
        "dest_ip": random_ip(bad=True),
        "event_type": "outbound_connection",
        "severity": "critical",
        "message": f"Massive outbound data transfer detected",
        "hostname": "db-cluster-02",
        "raw_log": json.dumps({"bytes_out": bytes_out, "protocol": "HTTPS", "user_role": "user"})
    }
    post_log(log)
    print_log(log)

async def simulate_after_hours():
    ip = "10.0.2.14"
    print(f"{Colors.YELLOW}>>> INITIATING AFTER HOURS ADMIN LOGIN FROM {ip}{Colors.RESET}")
    
    # Fake time to 3 AM
    dt = datetime.now(timezone.utc).replace(hour=3, minute=15)
    
    log = {
        "timestamp": dt.isoformat(),
        "source_ip": ip,
        "dest_ip": "10.0.0.5",
        "event_type": "successful_login",
        "severity": "high",
        "message": f"Successful authentication outside business hours",
        "hostname": "app-node-03",
        "raw_log": json.dumps({"username": "sysadmin", "user_role": "admin"})
    }
    post_log(log)
    print_log(log)

async def normal_traffic():
    while True:
        log = generate_random_log()
        post_log(log)
        print_log(log)
        # Random sleep between 0.5 and 2 seconds
        await asyncio.sleep(random.uniform(0.5, 2.0))

async def main():
    parser = argparse.ArgumentParser(description="SIEM Log Generator")
    parser.add_argument("--attack-mode", action="store_true", help="Trigger all attack patterns simultaneously")
    args = parser.parse_args()

    # Create task for normal traffic
    tasks = [asyncio.create_task(normal_traffic())]

    if args.attack_mode:
        print(f"{Colors.RED}{Colors.CYAN}=== INITIATING FULL ATTACK MODE ==={Colors.RESET}")
        tasks.append(asyncio.create_task(simulate_brute_force()))
        tasks.append(asyncio.create_task(simulate_port_scan()))
        tasks.append(asyncio.create_task(simulate_data_exfil()))
        tasks.append(asyncio.create_task(simulate_after_hours()))

    else:
        print(f"{Colors.CYAN}Starting normal traffic generation. Run with --attack-mode to simulate active threats.{Colors.RESET}")

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Generator stopped.{Colors.RESET}")
