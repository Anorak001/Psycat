# Psycat VM & Raspberry Pi Setup Guide

## Current Situation

You're running in a **Kali Linux VM** and want to:
- ✓ Set up Psycat captive portal locally
- ✓ NOT interfere with your VM's internet connection
- ✓ Prepare for deployment on Raspberry Pi later

---

## Part 1: Safe VM Setup (Current Environment)

### Option A: Virtual Network Interface (SAFEST - Recommended)

This creates an isolated virtual network that won't touch your main connection.

#### Step 1: Check Current Network Interfaces

```bash
# See all network interfaces
ip link show

# See IP addresses
ip addr show

# Typical output:
# eth0 or wlan0 - Your main internet connection (DO NOT USE)
# lo - Loopback (127.0.0.1)
```

#### Step 2: Create Virtual Network Interfaces

Create multiple virtual interfaces so clients can connect to your AP while you keep internet:

```bash
# Create virtual interface for captive portal
sudo ip link add veth0 type veth peer name veth1

# Create bridge interface (acts as your virtual AP)
sudo ip link add vbr0 type bridge

# Add virtual interface to bridge
sudo ip link set veth0 master vbr0

# Bring interfaces up
sudo ip link set vbr0 up
sudo ip link set veth0 up
sudo ip link set veth1 up

# Assign IP to bridge (This is your virtual AP's IP)
sudo ip addr add 192.168.100.1/24 dev vbr0

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
```

#### Step 3: Update Psycat Configuration

Edit `network.py` and `sniffer.py`:

```python
# network.py - Line 4
INTERFACE = "vbr0"  # Changed from "eth0"

# sniffer.py - Line 11
INTERFACE = "vbr0"  # Changed from "eth0"
```

#### Step 4: Create DHCP Server (for virtual clients)

Install and configure dnsmasq:

```bash
# Install dnsmasq
sudo apt-get install dnsmasq

# Create config file
sudo nano /etc/dnsmasq.conf.d/psycat

# Add this content:
interface=vbr0
dhcp-range=192.168.100.50,192.168.100.200,12h
dhcp-option=option:router,192.168.100.1
dhcp-option=option:dns-server,8.8.8.8,8.8.4.4
log-queries
log-facility=/var/log/dnsmasq.log

# Start dnsmasq
sudo systemctl start dnsmasq
sudo systemctl enable dnsmasq
```

#### Step 5: Enable IP Masquerading (for bridged clients to access real internet)

```bash
# Route virtual interface traffic through your main connection
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE  # or wlan0
sudo iptables -A FORWARD -i vbr0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o vbr0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Save iptables rules
sudo apt-get install iptables-persistent
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

#### Step 6: Run Psycat

```bash
cd /home/kali/Documents/Github/psycat/Psycat
source venv/bin/activate
sudo python main.py  # Must be root for iptables/packet sniffing
```

---

### Option B: Use Existing Interface with Network Namespace (Advanced)

Create isolated network namespace:

```bash
# Create network namespace
sudo ip netns add psycat_ns

# Create veth pair
sudo ip link add veth-host type veth peer name veth-ns

# Move veth-ns to namespace
sudo ip link set veth-ns netns psycat_ns

# Configure host side
sudo ip addr add 192.168.100.1/24 dev veth-host
sudo ip link set veth-host up

# Configure namespace side
sudo ip netns exec psycat_ns ip addr add 192.168.100.2/24 dev veth-ns
sudo ip netns exec psycat_ns ip link set veth-ns up

# Run Psycat inside namespace
sudo ip netns exec psycat_ns python main.py
```

---

### Option C: Docker Container (Future - Simplest)

```dockerfile
# Dockerfile
FROM kalilinux/kali-latest

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    wireshark dnsmasq \
    iptables iproute2

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python3", "main.py"]
```

Run with:
```bash
docker run --privileged -p 8000:8000 psycat:latest
```

---

## Part 2: Interface Decision Matrix

| Interface | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **eth0/wlan0** (main) | ❌ NO | Real connection | **Interferes with internet** |
| **vbr0** (virtual bridge) | ✅ YES (Best) | Isolated, safe | Need setup overhead |
| **lo** (loopback) | Limited testing | Safe | Only localhost access |
| **docker** | Future | Portable | Requires Docker |
| **VM NAT adapter** | ✅ Possible | VM-native | VM-specific config |

---

## Part 3: Testing Your Setup

### Test 1: Verify Interface is Up

```bash
# Check virtual interface
ip addr show vbr0

# Expected output:
# 5: vbr0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
#     inet 192.168.100.1/24 scope global vbr0
```

### Test 2: Test FastAPI Locally

```bash
# Terminal 1
source venv/bin/activate
sudo python main.py

# Terminal 2
curl http://localhost:8000/
# Should see redirect to /static/index.html
```

### Test 3: Test WebSocket Connection

```bash
# Install websocat
sudo apt-get install websocat

# Test WebSocket
websocat ws://127.0.0.1:8000/ws/traffic

# Should accept connection (wait a few seconds, then Ctrl+C)
```

### Test 4: Simulate Client Connection

```bash
# Create a virtual client interface
sudo ip link add vclient0 type veth peer name vclient1

# Connect to bridge
sudo ip link set vclient1 master vbr0
sudo ip link set vclient0 up
sudo ip link set vclient1 up

# Get DHCP IP (from dnsmasq)
sudo dhclient vclient0

# Check IP assigned
ip addr show vclient0

# Test connectivity to Psycat
curl http://192.168.100.1:8000/
```

---

## Part 4: VM Network Configuration (Hypervisor Side)

### VirtualBox Setup

1. **Main Interface (eth0 or wlan0)**: 
   - Network Adapter 1 → NAT or Bridged (for internet)
   
2. **Psycat Interface (vbr0)**:
   - Network Adapter 2 → Internal Network (name: "psycat")
   - This is isolated from your main network

### VMware Setup

1. VM Settings → Network Adapter → Bridged / NAT (internet)
2. VM Settings → Network Adapter 2 → Internal/Custom (psycat)

### Proxmox/KVM Setup

```bash
# List bridges
brctl show

# Create bridge for Psycat
sudo brctl addbr psycat-br0
sudo ip addr add 192.168.100.1/24 dev psycat-br0
sudo ip link set psycat-br0 up
```

---

## Part 5: SAFE Configuration for Psycat

### main.py - Disable Sniffer on Startup (Prevent Interference)

```python
# Line 38-41, comment out packet sniffer initially:
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Backend Service")
    # UNCOMMENT ONLY WHEN READY - requires root + isolated interface
    # start_sniffer()
```

### network.py - Add Safety Check

```python
# Add at top of grant_internet_access()
def grant_internet_access(ip_address: str):
    """
    SAFETY: Only works if INTERFACE is virtual (vbr0)
    """
    if INTERFACE not in ["vbr0", "eth1", "wlan1"]:
        logger.error(f"⚠️ SAFETY CHECK FAILED: Using live interface {INTERFACE}")
        logger.error("   Set INTERFACE to virtual interface (vbr0)")
        return
    
    try:
        subprocess.run(["iptables", ...], check=True)
```

---

## Part 6: Future Raspberry Pi Deployment

When you get your Raspberry Pi, the setup will be simpler:

### Raspberry Pi Setup (Same Code, Different Config)

```bash
# 1. Clone repo
git clone https://github.com/yourusername/Psycat.git
cd Psycat

# 2. Install on Raspberry Pi OS
sudo apt-get install python3-pip wireshark dnsmasq hostapd

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure for wireless (wlan0)
# network.py & sniffer.py:
INTERFACE = "wlan0"

# 5. Set up as real access point
# /etc/hostapd/hostapd.conf
interface=wlan0
ssid=FreeWifi
hw_mode=g
channel=6
wmm_enabled=0

# 6. Run
sudo python main.py
```

---

## Part 7: Quick Start Checklist

### For VM (Right Now)

- [ ] Identify your main internet interface (`eth0`, `wlan0`)
- [ ] Create virtual interface (vbr0) using Option A
- [ ] Update `network.py` and `sniffer.py` to use `vbr0`
- [ ] Install dnsmasq for DHCP
- [ ] Configure iptables for bridging
- [ ] Test local connectivity with `curl`
- [ ] Run `python main.py` with sudo
- [ ] Access `http://192.168.100.1:8000` from virtual client

### For Raspberry Pi (Later)

- [ ] Flash Raspberry Pi OS
- [ ] Install dependencies
- [ ] Configure as real WiFi AP (hostapd + dnsmasq)
- [ ] Update INTERFACE to `wlan0`
- [ ] Deploy Psycat code
- [ ] Test with real WiFi clients

---

## Troubleshooting

### "Address already in use" on port 8000

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill it
sudo kill -9 <PID>

# Or use different port
# Edit main.py: uvicorn.run(..., port=8001)
```

### iptables commands fail

```bash
# Must run as root
sudo python main.py

# Or add iptables to sudoers (risky)
sudo visudo
# Add: %kali ALL=(ALL) NOPASSWD: /sbin/iptables
```

### Packet sniffer has no data

```bash
# Check if Wireshark is installed
which tshark

# If not:
sudo apt-get install wireshark

# Set capabilities
sudo setcap cap_net_admin=ep /usr/bin/dumpcap
```

### Virtual interface disappears after reboot

```bash
# Make persistent with systemd service
sudo nano /etc/systemd/system/psycat-net.service

[Unit]
Description=Psycat Virtual Network Setup
Before=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/psycat-net-setup.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target

# Enable
sudo systemctl enable psycat-net.service
```

---

## Summary: VM vs Raspberry Pi

| Aspect | VM Setup | Raspberry Pi |
|--------|----------|--------------|
| **Interface** | vbr0 (virtual) | wlan0 (real WiFi) |
| **Root needed** | Yes | Yes |
| **Internet interference** | None (isolated) | None (separate AP) |
| **DHCP** | dnsmasq in VM | dnsmasq on Pi |
| **Deployment** | Local testing | Production-ready |
| **Code changes** | Just INTERFACE variable | Just INTERFACE variable |

---

## Next Steps

1. **Choose Option A** (virtual bridge) for safe VM testing
2. Run the checklist above
3. Test with virtual clients
4. When Raspberry Pi arrives, change INTERFACE to `wlan0` and follow RPi setup
5. No code changes needed - just config!

---

## Important Notes

⚠️ **Safety Reminders:**
- Always use isolated interfaces in shared networks
- Never use production internet interfaces for testing
- Run with caution - iptables rules can affect connectivity
- Keep a terminal open to undo rules if needed
- Test in controlled environment first

✓ **This setup:**
- Keeps your VM internet intact
- Creates isolated testing environment
- Is portable to Raspberry Pi
- Requires minimal code changes for migration

