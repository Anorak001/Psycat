# Psycat Raspberry Pi Setup Guide

This guide will walk you through setting up the Psycat captive portal on your Raspberry Pi 3B.

## Prerequisites

- Raspberry Pi 3B with Raspberry Pi OS installed.
- You are connected to your Raspberry Pi via SSH.
- The project files are on your Raspberry Pi.

---

## Step 1: Install Dependencies

First, we need to install the necessary packages for Psycat to function as a wireless access point and handle network traffic.

```bash
sudo apt-get update
sudo apt-get install -y python3-pip dnsmasq hostapd
pip3 install -r requirements.txt
```

`hostapd` will allow your Raspberry Pi to act as an access point, and `dnsmasq` will handle DHCP and DNS services for devices that connect to it.

---

## Step 2: Configure the Network Interface

We need to tell Psycat to use your Raspberry Pi's wireless interface (`wlan0`).

I will now update `network.py` and `sniffer.py` to use `wlan0`.

---

## Step 3: Configure the Access Point

Next, we need to configure `hostapd` to create the wireless network.

Create a configuration file for `hostapd`:

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add the following content to the file:

```
interface=wlan0
ssid=FreeWifi
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
```

Now, we need to tell the `hostapd` service where to find this configuration file.

```bash
sudo nano /etc/default/hostapd
```

Find the line `#DAEMON_CONF=""` and change it to:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

---

## Step 4: Configure DHCP and DNS

We'll use `dnsmasq` to assign IP addresses to connecting devices.

First, stop `dnsmasq` so we can configure it.
```bash
sudo systemctl stop dnsmasq
```

Rename the default configuration file to avoid conflicts:
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

Now, create a new configuration file:
```bash
sudo nano /etc/dnsmasq.conf
```

Add the following content:
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
server=8.8.8.8
log-queries
log-facility=/var/log/dnsmasq.log
```

---

## Step 5: Configure Static IP for the Pi

Configure a static IP address for the `wlan0` interface on the Pi itself.

```bash
sudo nano /etc/dhcpcd.conf
```

Add the following lines to the end of the file:
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

---

## Step 6: Enable IP Forwarding

This allows traffic to be routed from the wireless clients to the internet (if you choose to connect an ethernet cable for internet access).

```bash
sudo nano /etc/sysctl.conf
```

Uncomment the following line:
```
net.ipv4.ip_forward=1
```

Now, set up NAT to route the traffic.
```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```

To make this rule persistent on reboot, edit `/etc/rc.local`:
```bash
sudo nano /etc/rc.local
```
Add this line above `exit 0`:
```
iptables-restore < /etc/iptables.ipv4.nat
```

---

## Step 7: Run Psycat

Now you are ready to run the application.

First, reboot your Raspberry Pi for all the changes to take effect.
```bash
sudo reboot
```

After rebooting, navigate to your project directory and run the main script:

```bash
cd /path/to/your/project
sudo python3 main.py
```

Your Raspberry Pi should now be broadcasting a "FreeWifi" network. When a device connects, it will be directed to the Psycat captive portal.
