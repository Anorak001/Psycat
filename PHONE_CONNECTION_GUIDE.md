# Connecting Your Real Phone to Psycat (Outside VM)

## Your VM's Network Setup

Based on your current configuration:

```
┌─────────────────────────────────────────────────────────┐
│             YOUR KALI LINUX VM                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  eth0 (Real Network - Connected to Host)               │
│  └─ IP: 10.171.26.71 ← Phone connects here!            │
│  └─ Gateway: 10.171.26.189                             │
│  └─ Access: From your host/phone on same network ✓     │
│                                                         │
│  vbr0 (Virtual Bridge - Internal to VM)                │
│  └─ IP: 192.168.100.1 ← Only inside VM                 │
│  └─ Access: Virtual clients only ✗                     │
│                                                         │
│  Psycat App                                             │
│  └─ Port: 8000                                          │
│  └─ URL: http://10.171.26.71:8000 ← Use THIS!          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Option 1: Direct Connection (Easiest) ✅

### For Your Real Phone

Your phone needs to be on the **same network as your VM's host** (same WiFi/Ethernet).

#### Step 1: Find Your Phone's IP on Host Network
On your phone:
```
Settings → WiFi/Network → Your Network Name
Note: Your IP (e.g., 192.168.x.x or 10.171.26.x)
```

#### Step 2: Open Browser on Phone
```
URL: http://10.171.26.71:8000
```

You should see the captive portal splash page!

---

## Option 2: Through Virtual Bridge (Advanced)

If your phone is a virtual machine inside the VM:

```bash
# On your VM, create a virtual network interface for the phone
sudo ip link add veth-phone type veth peer name veth-br

# Connect to bridge
sudo ip link set veth-br master vbr0

# Bring up interfaces
sudo ip link set veth-phone up
sudo ip link set veth-br up

# Assign IP to the phone interface
sudo ip addr add 192.168.100.50/24 dev veth-phone

# Now phone can access: http://192.168.100.1:8000
```

---

## Option 3: Network Routing (Most Realistic) ✅ RECOMMENDED

### Problem:
- Your phone on host network (10.171.26.x) 
- Psycat listening on vbr0 (192.168.100.x)
- These networks can't reach each other

### Solution: Create routing bridge

```bash
# On your VM, connect eth0 to vbr0 bridge
sudo brctl addif vbr0 eth0

# OR use iptables to route traffic
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8000 -j DNAT --to-destination 192.168.100.1:8000
sudo iptables -t nat -A POSTROUTING -d 192.168.100.0/24 -j MASQUERADE
```

---

## Step-by-Step: Connect Your Real Phone

### Prerequisites:
- Your phone is on same network as VM's host
- Phone can reach 10.171.26.71 (no firewall blocking)
- Psycat is running on the VM

### Steps:

#### 1. Verify VM is Running
```bash
# On your VM
curl http://localhost:8000/

# Should see: HTTP/1.1 307 Temporary Redirect
```

#### 2. Check What Network Your Phone Is On

**On Host Computer (where VM runs):**
```bash
# Find host's IP
ifconfig
# Look for IP like 10.171.26.x or 192.168.x.x
```

**On Your Phone:**
```
Settings → WiFi/Ethernet → Current Network
Look for the network's IP range (first 3 octets)
```

#### 3. Ensure Same Network
- **Host IP**: 10.171.26.71 (or similar)
- **Phone IP**: Should be in 10.171.26.x range
- If different: Connect phone to same WiFi/network as host

#### 4. Open Browser on Phone
```
URL: http://10.171.26.71:8000
```

### Expected Result:
```
✓ Redirect to captive portal
✓ See "City Center Free Wi-Fi" page
✓ Can click "Premium" or "Guest" buttons
✓ Can interact with Psycat from real phone!
```

---

## Testing Connection

### From Your Host Computer:
```bash
# Test if you can reach VM
ping 10.171.26.71

# Check if port 8000 is open
curl http://10.171.26.71:8000 -v
```

### From Your Phone:
```
Open browser → http://10.171.26.71:8000
Should see the captive portal page
```

---

## Troubleshooting

### "Connection Refused" from Phone

**Cause**: Firewall blocking port 8000

**Fix - Allow port 8000 on VM:**
```bash
# Allow incoming connections on port 8000
sudo ufw allow 8000
# OR
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### "Connection Timed Out" from Phone

**Cause**: Phone not on same network as VM

**Fix**: 
```bash
# On phone: Check network settings
Settings → WiFi → Connected Network

# On VM: Check IP
ip addr show eth0 | grep "inet "

# They should be in same subnet (same first 3 numbers)
# 10.171.26.71 ← VM (on 10.171.26.x network)
# 10.171.26.xx ← Phone (should also be on 10.171.26.x)
```

### "Unable to Reach This Page" from Phone

**Cause**: App not running

**Fix**:
```bash
# Check if app is running
netstat -tuln 2>/dev/null | grep 8000

# If not, start it
cd /home/kali/Documents/Github/psycat/Psycat
source venv/bin/activate
python main.py
```

### Phone Connects to Portal But No Internet

**This is expected!** The captive portal is designed to:
- **Premium Path**: Deny internet (show "Gotcha!" warning)
- **Guest Path**: Throttle internet to 1 Mbps

To test:
1. Click "Guest WiFi"
2. Should redirect to "Wall of Sheep" dashboard
3. Check console for connection status

---

## Network Diagram

```
┌────────────────┐
│   YOUR PHONE   │
│  (Real Device) │
│ 192.168.x.x    │
└────────┬───────┘
         │
    [WiFi/Ethernet]
         │
    Your Host Network
    (10.171.26.0/24)
         │
    ┌────┴────────────────┐
    │  ┌─────────────────┐ │
    │  │  YOUR VM (KVM)  │ │
    │  │  10.171.26.71   │ │
    │  │ (eth0 - can     │ │
    │  │  be reached ✓)  │ │
    │  │                 │ │
    │  │ ┌─────────────┐ │ │
    │  │ │ Psycat App  │ │ │
    │  │ │  Port 8000  │ │ │ ← You access here!
    │  │ │ vbr0: 192.. │ │ │
    │  │ └─────────────┘ │ │
    │  └─────────────────┘ │
    └─────────────────────┘
         │
    [From Phone]
    http://10.171.26.71:8000
```

---

## Quick Access URLs

Based on your network:

| Device | URL | Status |
|--------|-----|--------|
| **Phone (real)** | `http://10.171.26.71:8000` | ✅ WORKS |
| **Phone (VM inside)** | `http://192.168.100.1:8000` | ✅ Works if connected to vbr0 |
| **Host Computer** | `http://10.171.26.71:8000` | ✅ WORKS |
| **From VM localhost** | `http://localhost:8000` | ✅ WORKS |

---

## What Happens When Phone Connects

### Premium WiFi Flow:
```
Phone → "City Center Free WiFi" page
       → Click "Premium High-Speed"
       → Enter credentials
       → POST to /api/auth/premium
       → Credentials captured
       → Shows "Gotcha!" warning
       → ❌ No internet access
```

### Guest WiFi Flow:
```
Phone → "City Center Free WiFi" page
       → Click "Guest WiFi"
       → POST to /api/auth/guest
       → Throttled to 1 Mbps
       → ✓ Can browse internet (limited)
       → Redirect to "Wall of Sheep"
       → 🔍 Traffic sniffing active
       → Real-time domain list displayed
```

---

## Summary

**Your Answer:**
- **VM IP accessible from phone**: `10.171.26.71`
- **Port**: `8000`
- **Full URL**: `http://10.171.26.71:8000`
- **Requirement**: Phone must be on same network as VM's host

**Connection will work if:**
1. ✅ Phone on same WiFi/network as host
2. ✅ App is running (`python main.py`)
3. ✅ Port 8000 not blocked by firewall
4. ✅ Phone can ping VM: `ping 10.171.26.71`

---

## For Raspberry Pi Later

When you get your Raspberry Pi:
- It will have a real WiFi interface (wlan0)
- Phone will connect as real WiFi client
- Much simpler setup!
- Just set INTERFACE = "wlan0" and you're done

