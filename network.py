import subprocess
import logging

logger = logging.getLogger(__name__)

INTERFACE = "wlan0" # Virtual bridge for VM testing (wlan0 for Raspberry Pi)

def grant_internet_access(ip_address: str):
    """
    Grants internet access by inserting an 'ACCEPT' rule at the top of the PREROUTING chain.
    This tells the firewall to completely ignore this IP and let it pass through normally.
    """
    try:
        # A single rule: If traffic comes from this IP, ACCEPT it immediately (bypassing the DNAT trap)
        subprocess.run(["iptables", "-t", "nat", "-I", "PREROUTING", "1", "-s", ip_address, "-j", "ACCEPT"], check=True)
        logger.info(f"Granted full internet access to {ip_address}. Bypassing all traps.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to grant internet access to {ip_address}: {e}")


def throttle_bandwidth(ip_address: str, rate: str = "1mbit"):
    """
    Throttles the bandwidth for a specific IP address using traffic control (tc).
    """
    try:
        # Note: tc commands can be complex, this is a simplified example. 
        # In a real setup, you'd likely use a classes/filters hierarchy.
        
        # Ensure root qdisc exists (replace if exists)
        subprocess.run(["tc", "qdisc", "replace", "dev", INTERFACE, "root", "handle", "1:", "htb"], check=False)
        
        # Add a class with the specified rate
        # We use a static classid 1:1 for simplicity in this demo, but it should be unique per IP ideally.
        subprocess.run(["tc", "class", "replace", "dev", INTERFACE, "parent", "1:", "classid", "1:1", "htb", "rate", rate], check=True)
        
        # Add a filter to direct traffic to this class
        subprocess.run(["tc", "filter", "replace", "dev", INTERFACE, "protocol", "ip", "parent", "1:0", "prio", "1", "u32", "match", "ip", "dst", ip_address, "flowid", "1:1"], check=True)
        
        logger.info(f"Throttled bandwidth for {ip_address} to {rate} on {INTERFACE}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to throttle bandwidth for {ip_address}: {e}")

def deny_internet_access(ip_address: str):
    """
    Explicitly denies internet access.
    """
    try:
         subprocess.run(["iptables", "-A", "FORWARD", "-s", ip_address, "-j", "DROP"], check=True)
         logger.info(f"Denied internet access to {ip_address}")
    except subprocess.CalledProcessError as e:
         logger.error(f"Failed to deny internet access for {ip_address}: {e}")
