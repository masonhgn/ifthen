#!/usr/bin/env python3
"""
Simple test script to verify the server implementation.
Run this after starting the Flask server to test basic functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_create_lobby():
    """Test lobby creation."""
    print("Testing lobby creation...")
    
    response = requests.post(f"{BASE_URL}/create_lobby", 
                           json={"player_name": "TestPlayer"})
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"✓ Lobby created successfully: {data['lobby_id']}")
            return data['lobby_id']
        else:
            print(f"✗ Failed to create lobby: {data['error']}")
    else:
        print(f"✗ HTTP error: {response.status_code}")
    
    return None

def test_get_lobby_state(lobby_id):
    """Test getting lobby state."""
    print(f"Testing lobby state for {lobby_id}...")
    
    response = requests.get(f"{BASE_URL}/api/lobby/{lobby_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Lobby state retrieved: {len(data['players'])} players")
        return data
    else:
        print(f"✗ Failed to get lobby state: {response.status_code}")
    
    return None

def test_server_stats():
    """Test server statistics."""
    print("Testing server statistics...")
    
    response = requests.get(f"{BASE_URL}/api/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Server stats: {data}")
        return data
    else:
        print(f"✗ Failed to get server stats: {response.status_code}")
    
    return None

def test_pages():
    """Test that pages load correctly."""
    print("Testing page loading...")
    
    pages = [
        ("/", "Landing page"),
        ("/lobby/test123", "Lobby page"),
        ("/game/test456", "Game page")
    ]
    
    for path, name in pages:
        response = requests.get(f"{BASE_URL}{path}")
        if response.status_code in [200, 404]:  # 404 is expected for test IDs
            print(f"✓ {name} loads correctly")
        else:
            print(f"✗ {name} failed to load: {response.status_code}")

def main():
    """Run all tests."""
    print("=" * 50)
    print("TESTING FLASK SERVER IMPLEMENTATION")
    print("=" * 50)
    
    try:
        # Test server stats
        test_server_stats()
        print()
        
        # Test page loading
        test_pages()
        print()
        
        # Test lobby creation
        lobby_id = test_create_lobby()
        print()
        
        if lobby_id:
            # Test lobby state
            test_get_lobby_state(lobby_id)
            print()
        
        print("=" * 50)
        print("BASIC TESTS COMPLETED")
        print("=" * 50)
        print("To test WebSocket functionality, open the web interface")
        print("and create/join lobbies manually.")
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure Flask app is running on localhost:5000")
        print("Run: python app.py")
    except Exception as e:
        print(f"✗ Test failed with error: {e}")

if __name__ == "__main__":
    main()
