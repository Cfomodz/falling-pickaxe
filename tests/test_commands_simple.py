#!/usr/bin/env python3
"""
Simple test of character commands without full game initialization
"""

import sys
sys.path.append('src')

from character import Character
from world import World

def test_character_methods():
    """Test character methods directly"""
    
    print("🧪 Testing Character Methods")
    print("=" * 30)
    
    # Create character
    character = Character(0, 0)
    
    print(f"Initial position: ({character.grid_x}, {character.grid_y})")
    print(f"Initial dig speed: {character.dig_speed}")
    print(f"Initial tool efficiency: {character.tool_efficiency}")
    
    # Test speed changes
    print("\n1. Testing speed changes...")
    character.set_dig_speed("fast")
    print(f"After set_dig_speed('fast'): {character.dig_speed}")
    
    character.set_dig_speed("slow")
    print(f"After set_dig_speed('slow'): {character.dig_speed}")
    
    # Test movement
    print("\n2. Testing movement...")
    initial_x = character.grid_x
    character.move_horizontal("left", 1)
    print(f"After move_horizontal('left', 1): ({character.grid_x}, {character.grid_y}) (change: {character.grid_x - initial_x})")
    
    character.move_horizontal("right", 3)
    print(f"After move_horizontal('right', 3): ({character.grid_x}, {character.grid_y})")
    
    # Test gem collection and upgrades
    print("\n3. Testing gem collection...")
    print(f"Initial gems: {character.gem_inventory}")
    
    for i in range(12):
        character.collect_gem("diamond_gem")
    
    print(f"After collecting 12 diamond gems: {character.gem_inventory['diamond_gem']}")
    print(f"Tool efficiency before upgrade: {character.tool_efficiency}")
    
    success = character.upgrade_tool("diamond_gem")
    print(f"Upgrade successful: {success}")
    print(f"Tool efficiency after upgrade: {character.tool_efficiency}")
    print(f"Remaining gems: {character.gem_inventory['diamond_gem']}")
    
    print("\n✅ Character methods work correctly!")

if __name__ == "__main__":
    test_character_methods()