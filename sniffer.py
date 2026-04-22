import pyshark
import asyncio
import json
import logging
from typing import Set

logger = logging.getLogger(__name__)

# Maintain active websocket connections to broadcast to the UI
connected_clients: Set[asyncio.WebSocket] = set()

INTERFACE = "eth0"  # Will be wlan0 later

def start_sniffer():
    """
    Start sniffing network traffic asynchronously in the background.
    """
    logger.info(f"Starting packet sniffer on {INTERFACE}")
    # Filter for DNS (port 53) and HTTPS (port 443 for SNI)
    capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter="port 53 or port 443")
    
    # We run apply_on_packets asynchronously since this runs in the main event loop
    loop = asyncio.get_event_loop()
    loop.create_task(capture.apply_on_packets(process_packet))


async def process_packet(packet):
    """
    Callback for each captured packet. Looks for DNS queries or TLS SNI.
    """
    target_domain = None
    source_ip = None

    try:
        if 'IP' in packet:
            source_ip = packet.ip.src

        # Check for DNS
        if 'DNS' in packet:
             target_domain = packet.dns.qry_name
        
        # Check for TLS (SNI for HTTPS)
        elif 'TLS' in packet:
             # PyShark parses the SNI extension if present
             if hasattr(packet.tls, 'handshake_extensions_server_name'):
                 target_domain = getattr(packet.tls, 'handshake_extensions_server_name')

        if target_domain and source_ip:
             # Basic device name extraction based on IP or MAC could be added here
             # For now, use the IP address as the device name
             device_name = f"Device_{source_ip}"
             
             data = {
                 "source_device_name": device_name,
                 "target_domain": target_domain,
                 "timestamp": packet.sniff_time.isoformat()
             }
             
             await broadcast_traffic(data)
             
    except Exception as e:
        logger.debug(f"Error processing packet: {e}")

async def broadcast_traffic(data: dict):
    """
    Send the parsed JSON data to all connected WebSocket clients (Wall of Sheep).
    """
    if connected_clients:
        message = json.dumps(data)
        # Send concurrently to all clients
        await asyncio.gather(
             *(client.send_text(message) for client in connected_clients),
             return_exceptions=True
        )
