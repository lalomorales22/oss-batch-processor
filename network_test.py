#!/usr/bin/env python3
"""
Network Connectivity Test for OSS Batch Processor
Run this script to diagnose network access issues
"""

import socket
import subprocess
import sys
import time

def get_local_ip():
    """Get the primary local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def get_all_network_interfaces():
    """Get all available network interfaces and their IPs"""
    interfaces = []
    try:
        if sys.platform == "darwin":  # macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        elif sys.platform == "linux":  # Linux
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
        else:  # Windows
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            
        lines = result.stdout.split('\n')
        current_interface = None
        
        for line in lines:
            if sys.platform == "darwin":
                if line and not line.startswith('\t') and not line.startswith(' '):
                    current_interface = line.split(':')[0]
                elif 'inet ' in line and '127.0.0.1' not in line and 'inet 169.254' not in line:
                    ip = line.split('inet ')[1].split(' ')[0]
                    if current_interface:
                        interfaces.append((current_interface, ip))
    except Exception as e:
        print(f"⚠️  Could not get network interfaces: {e}")
    return interfaces

def test_port_availability(port=5001):
    """Test if a port is available"""
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('0.0.0.0', port))
        test_socket.close()
        return True
    except OSError:
        return False

def test_server_connectivity(ip, port=5001):
    """Test if we can connect to the server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_firewall_status():
    """Check macOS firewall status"""
    try:
        result = subprocess.run(['sudo', '/usr/libexec/ApplicationFirewall/socketfilterfw', '--getglobalstate'], 
                              capture_output=True, text=True, timeout=5)
        if "enabled" in result.stdout.lower():
            return "enabled"
        elif "disabled" in result.stdout.lower():
            return "disabled"
        else:
            return "unknown"
    except:
        return "unknown"

def main():
    print("🔍 OSS BATCH PROCESSOR - NETWORK CONNECTIVITY TEST")
    print("=" * 60)
    
    # Get network info
    local_ip = get_local_ip()
    interfaces = get_all_network_interfaces()
    
    print(f"📍 Primary IP Address: {local_ip}")
    
    if interfaces:
        print("\n🌐 Available Network Interfaces:")
        for interface, ip in interfaces:
            print(f"   {interface}: {ip}")
    
    # Test port availability
    print(f"\n🔌 Port 5001 Status:")
    if test_port_availability():
        print("   ✅ Port 5001 is available")
    else:
        print("   ❌ Port 5001 is in use")
        try:
            result = subprocess.run(['lsof', '-i', ':5001'], capture_output=True, text=True)
            if result.stdout:
                print("   🔍 Process using port 5001:")
                print(f"   {result.stdout.strip()}")
        except:
            pass
    
    # Test server connectivity (if running)
    print(f"\n🌍 Server Connectivity Test:")
    if test_server_connectivity('localhost'):
        print("   ✅ Server accessible on localhost:5001")
    else:
        print("   ❌ Server not accessible on localhost:5001")
    
    if local_ip != "localhost":
        if test_server_connectivity(local_ip):
            print(f"   ✅ Server accessible on {local_ip}:5001")
        else:
            print(f"   ❌ Server not accessible on {local_ip}:5001")
    
    # Check firewall
    print(f"\n🛡️  Firewall Status:")
    firewall_status = check_firewall_status()
    if firewall_status == "enabled":
        print("   ⚠️  macOS Firewall is ENABLED")
        print("   💡 Solution: System Preferences → Security & Privacy → Firewall")
        print("      Add Python to allowed apps or disable firewall temporarily")
    elif firewall_status == "disabled":
        print("   ✅ macOS Firewall is disabled")
    else:
        print("   ❓ Could not determine firewall status")
    
    # URLs to try
    print(f"\n📱 URLs to try on your phone/tablet:")
    print(f"   Primary:     http://{local_ip}:5001")
    print(f"   Gallery:     http://{local_ip}:5001/gallery")
    
    if interfaces:
        print("   Alternatives:")
        for interface, ip in interfaces:
            if ip != local_ip and not ip.startswith('169.254'):
                print(f"   {interface}: http://{ip}:5001")
    
    print(f"\n🧪 Quick connectivity test from your phone:")
    print(f"   1. Open terminal/command prompt app")
    print(f"   2. Run: ping {local_ip}")
    print(f"   3. If ping works, try the browser")
    
    print("\n" + "=" * 60)
    print("If issues persist:")
    print("1. Restart your router/WiFi")
    print("2. Try connecting phone to computer's hotspot")
    print("3. Check if both devices are on same network segment")
    print("4. Temporarily disable all firewalls for testing")

if __name__ == "__main__":
    main()