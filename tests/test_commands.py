#!/usr/bin/env python3
"""
Test script to verify digging game commands work correctly.
This tests the core command functionality without YouTube chat.
"""

import sys
import os
sys.path.append('src')

from main import handle_command
from character import Character
from world import World

def test_commands():
    """Test that the implemented commands work with the digging game"""
    
    print("🧪 Testing Digging Game Commands")
    print("=" * 40)
    
    # Create test character and world
    character = Character(0, 0)
    world = World()
    
    print(f"Initial character position: ({character.grid_x}, {character.grid_y})")
    print(f"Initial dig speed: {character.dig_speed}")
    print(f"Initial tool efficiency: {character.tool_efficiency}")
    
    # Test 1: Speed commands
    print("\n1. Testing speed commands...")
    handle_command("fast", "TestUser")
    print(f"After 'fast' command: {character.dig_speed}")
    
    handle_command("slow", "TestUser") 
    print(f"After 'slow' command: {character.dig_speed}")
    
    # Test 2: Movement commands
    print("\n2. Testing movement commands...")
    initial_x = character.grid_x
    handle_command("left", "TestUser")
    print(f"Position after 'left': ({character.grid_x}, {character.grid_y}) (change: {character.grid_x - initial_x})")
    
    handle_command("right2", "TestUser")
    print(f"Position after 'right2': ({character.grid_x}, {character.grid_y})")
    
    # Test 3: Tool upgrade commands  
    print("\n3. Testing tool upgrade commands...")
    print(f"Initial gem inventory: {character.gem_inventory}")
    
    # Give character some gems to test upgrades
    for i in range(15):
        character.collect_gem("diamond_gem")
    
    print(f"After collecting gems: {character.gem_inventory['diamond_gem']} diamond gems")
    print(f"Tool efficiency before upgrade: {character.tool_efficiency}")
    
    handle_command("upgrade diamond_gem", "TestUser")
    print(f"Tool efficiency after upgrade: {character.tool_efficiency}")
    
    print("\n✅ Command system test complete!")
    print("\nImplemented commands:")
    print("- left, right, left2, left3, right2, right3 (movement)")
    print("- fast, slow (dig speed)")  
    print("- upgrade <gem_type> (tool upgrades)")
    print("- rainbow, shield, freeze (visual effects - placeholders)")

if __name__ == "__main__":
    test_commands()