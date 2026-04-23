import subprocess
import logging

logger = logging.getLogger(__name__)

INTERFACE = "vbr0" # Virtual bridge for VM testing (wlan0 for Raspberry Pi)

def grant_internet_access(ip_address: str):
    """
    Grants internet access to a specific IP address by modifying iptables.
    Since this is a simulated environment, we assume IP forwarding is enabled
    and we NAT the traffic out the INTERFACE.
    """
    try:
        # Example NAT rule (requires routing/NAT setup to be valid)
        subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", ip_address, "-o", INTERFACE, "-j", "MASQUERADE"], check=True)
        subprocess.run(["iptables", "-A", "FORWARD", "-s", ip_address, "-j", "ACCEPT"], check=True)
        subprocess.run(["iptables", "-A", "FORWARD", "-d", ip_address, "-j", "ACCEPT"], check=True)
        logger.info(f"Granted internet access to {ip_address} on {INTERFACE}")
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
