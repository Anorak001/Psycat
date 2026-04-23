# Psycat - Social Engineering & Network Surveillance Educational Tool

## Overview

**Psycat** is an educational cybersecurity application designed to demonstrate common social engineering attack vectors and network surveillance techniques. This project simulates a rogue Wi-Fi access point with a captive portal that implements two attack paths: credential phishing and traffic surveillance.

## ⚠️ Disclaimer

This tool is **strictly for educational purposes only** in controlled, authorized environments. Unauthorized access to computer networks is illegal. Users are responsible for ensuring they have proper authorization before testing or deploying this tool.

## Project Structure

```
.
├── main.py              # FastAPI backend server (REST API & WebSocket)
├── network.py           # Linux iptables & traffic control (tc) commands
├── sniffer.py           # PyShark packet sniffing & processing
├── requirements.txt     # Python dependencies
├── static/              # Frontend HTML/CSS/JS files
│   ├── index.html       # Login page (captive portal splash screen)
│   ├── premium.html     # Premium Wi-Fi phishing form
│   ├── dashboard.html   # Wall of Sheep (live traffic display)
│   └── gotcha.html      # Security warning page
└── LICENSE              # MIT License
```

## Key Features

### 1. **Dual Attack Paths**

#### Path A: Premium Wi-Fi Phishing Trap
- Users attempt to login with credentials for "Premium High-Speed" access
- Credentials are captured and stored in ephemeral RAM
- Internet access is explicitly denied
- User receives "Gotcha!" warning showing the vulnerability

#### Path B: Guest Wi-Fi Surveillance
- Users connect as "Guest" with 1 Mbps throttled access
- Real internet access is granted (via iptables NAT)
- Network bandwidth is limited using Linux traffic control (`tc`)
- Packet sniffing begins in the background
- Live traffic is displayed in the "Wall of Sheep" dashboard

### 2. **Network Management**
- **IP Forwarding**: Routes and NATs guest traffic through the access point
- **Bandwidth Throttling**: Limits guest connections to 1 Mbps using Linux `tc` (traffic control)
- **Access Control**: Explicitly denies or grants internet access per IP address using `iptables`

### 3. **Packet Sniffing & Real-Time Monitoring**
- Uses **PyShark** to capture DNS queries and TLS SNI (Server Name Indication)
- Extracts target domains from network traffic
- Broadcasts captured traffic via WebSocket to connected clients
- "Wall of Sheep" dashboard displays live network activity

### 4. **Web-Based UI**
- **Captive Portal**: Responsive HTML5 interface with Tailwind CSS
- **Real-Time Updates**: WebSocket connection for live traffic streaming
- **Multi-page Flow**: Splash page → Authentication → Dashboard

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI (async Python web framework) |
| **Web Server** | Uvicorn (ASGI server) |
| **Real-Time Communication** | WebSocket (FastAPI native) |
| **Packet Analysis** | PyShark (Python wrapper for Wireshark) |
| **Network Control** | Linux iptables & tc (traffic control) |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JavaScript |

## Requirements

### System Requirements
- **OS**: Linux (Kali Linux recommended for pre-installed tools)
- **Python**: 3.8+
- **Privileges**: Root access (for iptables & packet sniffing)
- **Network Interface**: Must have interface to configure (default: `eth0`, configurable to `wlan0`)

### Python Dependencies
```
fastapi==0.136.1
uvicorn==0.46.0
pyshark==0.6
websockets==16.0
```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Psycat.git
cd Psycat
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Linux-specific) Install Wireshark
PyShark requires Wireshark for packet capture:
```bash
# Ubuntu/Debian
sudo apt-get install wireshark

# Kali Linux
sudo apt-get install wireshark-common
```

## Usage

### Running the Application

```bash
source venv/bin/activate
python main.py
```

The application will start on `http://0.0.0.0:8000`

**Access the UI**:
- Navigate to `http://localhost:8000` in a web browser
- You'll see the captive portal splash page

### Configuration

Key configurable parameters in the code:

**Network Interface** (`network.py` & `sniffer.py`):
```python
INTERFACE = "eth0"  # Change to "wlan0" for wireless access point
```

**Packet Sniffing Filter** (`sniffer.py`):
```python
capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter="port 53 or port 443")
```

**Bandwidth Limit** (`main.py`):
```python
background_tasks.add_task(throttle_bandwidth, client_ip, rate="1mbit")
```

**Server Port** (`main.py`):
```python
uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

## API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Redirect to captive portal splash page |
| POST | `/api/auth/premium` | Phishing credential capture |
| POST | `/api/auth/guest` | Guest Wi-Fi access (throttled) |

### WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ws/traffic` | Live traffic stream (Wall of Sheep) |

**WebSocket Message Format**:
```json
{
  "source_device_name": "Device_192.168.1.100",
  "target_domain": "example.com",
  "timestamp": "2026-04-23T10:30:45.123456"
}
```

## How It Works

### Attack Flow Diagram

```
User → Connects to Rogue AP → Captive Portal (index.html)
         ↓
         ├── Path A: "Premium" Button
         │   └── Form posts to /api/auth/premium
         │       ├── Credentials captured
         │       ├── Access denied
         │       └── Show "Gotcha!" warning
         │
         └── Path B: "Guest" Button
             └── POST to /api/auth/guest
                 ├── Grant internet access (iptables NAT)
                 ├── Throttle bandwidth (1 Mbps)
                 ├── Start packet sniffing (background)
                 └── Redirect to dashboard.html
                     └── WebSocket connection to /ws/traffic
                         └── Live traffic stream
```

### Credential Capture Process

1. User enters credentials on `/static/premium.html`
2. Form POSTs to `/api/auth/premium`
3. Credentials stored in `captured_creds` dictionary (RAM)
4. Internet access denied via iptables DROP rule
5. User sees security warning page

### Guest Access & Sniffing Process

1. User clicks "Continue as Guest" on index.html
2. JavaScript POSTs to `/api/auth/guest`
3. Backend tasks execute in background:
   - Grant internet routing (iptables MASQUERADE)
   - Limit bandwidth to 1 Mbps (tc qdisc)
4. User redirected to dashboard.html
5. Dashboard establishes WebSocket connection to `/ws/traffic`
6. Sniffer captures DNS (port 53) and TLS SNI (port 443) packets
7. Captured domains broadcast via WebSocket to dashboard
8. Real-time "Wall of Sheep" display shows all visited domains

## Code Components

### main.py
- **FastAPI app initialization** with CORS middleware
- **REST endpoints** for authentication flows
- **WebSocket handler** for real-time traffic broadcasting
- **Background tasks** for network operations
- **Startup event** to initialize packet sniffer (currently commented)

### network.py
- `grant_internet_access()`: iptables NAT rules for routing traffic through AP
- `throttle_bandwidth()`: Linux `tc` (traffic control) commands to limit bandwidth
- `deny_internet_access()`: iptables DROP rules to block traffic

### sniffer.py
- `start_sniffer()`: Initializes PyShark packet capture with BPF filter
- `process_packet()`: Parses DNS queries and TLS SNI extensions
- `broadcast_traffic()`: Sends captured data to all WebSocket clients asynchronously

### static/
- **index.html**: Captive portal splash page with dual login paths
- **premium.html**: Premium Wi-Fi phishing form
- **dashboard.html**: Real-time "Wall of Sheep" traffic display
- **gotcha.html**: Security awareness warning page

## Example Use Cases

### Educational Scenarios
1. **Network Security Class**: Demonstrate social engineering vulnerabilities
2. **Cybersecurity Workshops**: Show how captive portals work and threats
3. **Penetration Testing Training**: Practice authorized security assessments
4. **Security Awareness Training**: Teach users about public Wi-Fi risks

### Authorized Testing
- Test security controls in controlled lab environments
- Validate incident detection systems
- Demonstrate attack vectors to stakeholders

## Known Limitations & TODO

- **Packet Sniffer**: Currently captures DNS/TLS only; can be extended for other protocols
- **Storage**: Credentials stored in ephemeral RAM; no persistence
- **Interface Configuration**: Hardcoded to `eth0`; needs dynamic interface selection
- **Root Privileges**: Requires root for iptables and packet sniffing
- **Single Device**: Limited to single access point; no clustering
- **TLS/SSL Interception**: No HTTPS stripping capability
- **MAC Filtering**: No MAC address based filtering

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Permission Denied (iptables/tc commands)
```bash
# Run with sudo
sudo python main.py
```

### PyShark Not Finding Packets
- Ensure Wireshark is installed
- Verify network interface is correct (eth0 vs wlan0)
- Check BPF filter syntax
- May require: `sudo setcap cap_net_admin=ep /usr/bin/dumpcap`

### WebSocket Connection Failed
- Check browser console for errors
- Verify WebSocket endpoint is reachable
- Ensure firewall allows WebSocket traffic

## Security & Legal Considerations

⚠️ **IMPORTANT REMINDERS**:

1. **Authorization**: Only use this tool in environments where you have explicit written permission
2. **Jurisdiction**: Unauthorized network access is illegal in most jurisdictions
3. **Ethics**: This is for educational purposes in controlled settings only
4. **Liability**: The developers are not responsible for misuse
5. **Compliance**: Follow organizational security policies and laws

## License

MIT License - See [LICENSE](LICENSE) file for details

**Copyright © 2026 MANTHAN R M**

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Comments explain complex logic
- Changes are tested in controlled environments
- Security implications are documented

## References & Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyShark Documentation](https://github.com/KimikoMaying/pyshark)
- [Linux iptables Tutorial](https://www.netfilter.org/projects/iptables/)
- [Linux Traffic Control (tc)](https://linux.die.net/man/8/tc)
- [WebSocket Protocol (RFC 6455)](https://tools.ietf.org/html/rfc6455)
- [OWASP Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## Author

**MANTHAN R M** - [@GitHub](https://github.com/yourusername)

---

**Last Updated**: April 23, 2026  
**Version**: 1.0.0  
**Status**: Educational / Research