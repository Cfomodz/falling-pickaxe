import time
from typing import Dict, Optional, Tuple, List
import pygame

class BlockPointSystem:
    """Manages point values for different block types based on rarity"""
    
    # Block types ordered by rarity (common to rare)
    BLOCK_RARITIES = [
        # Common blocks (1 point)
        ["stone", "cobblestone", "dirt", "grass_block"],
        # Uncommon blocks (2 points)
        ["coal_ore", "diorite", "granite", "andesite", "mossy_cobblestone"],
        # Rare blocks (4 points)
        ["iron_ore", "copper_ore"],
        # Very rare blocks (8 points)
        ["gold_ore", "redstone_ore", "lapis_ore"],
        # Epic blocks (16 points)
        ["diamond_ore"],
        # Legendary blocks (32 points)
        ["emerald_ore", "ancient_debris"],
        # Mythic blocks (64 points)
        ["obsidian", "mega_tnt", "golden_block"],
        # Godlike blocks (128 points)
        ["bedrock"]
    ]
    
    def __init__(self):
        self.point_values = {}
        self._initialize_point_values()
        
    def _initialize_point_values(self):
        """Initialize point values as powers of 2 based on rarity"""
        for rarity_level, blocks in enumerate(self.BLOCK_RARITIES):
            point_value = 2 ** rarity_level  # 1, 2, 4, 8, 16, 32, 64...
            for block in blocks:
                self.point_values[block] = point_value
                
    def get_points(self, block_type: str) -> int:
        """Get point value for a block type"""
        # Default to 1 point for unknown blocks
        return self.point_values.get(block_type, 1)


class PlayerCooldownManager:
    """Manages per-player, per-command cooldowns"""
    
    def __init__(self, cooldown_seconds: int = 60):
        self.cooldown_seconds = cooldown_seconds
        self.cooldowns: Dict[str, Dict[str, float]] = {}  # player -> command -> timestamp
        
    def can_use_command(self, player: str, command: str) -> Tuple[bool, float]:
        """
        Check if player can use a command
        Returns: (can_use, remaining_cooldown_seconds)
        """
        current_time = time.time()
        
        if player not in self.cooldowns:
            self.cooldowns[player] = {}
            
        if command not in self.cooldowns[player]:
            return True, 0
            
        last_use = self.cooldowns[player][command]
        elapsed = current_time - last_use
        
        if elapsed >= self.cooldown_seconds:
            return True, 0
        else:
            remaining = self.cooldown_seconds - elapsed
            return False, remaining
            
    def use_command(self, player: str, command: str):
        """Record that a player used a command"""
        if player not in self.cooldowns:
            self.cooldowns[player] = {}
        self.cooldowns[player][command] = time.time()
        
    def get_all_cooldowns(self, player: str) -> Dict[str, float]:
        """Get all cooldown times remaining for a player"""
        if player not in self.cooldowns:
            return {}
            
        current_time = time.time()
        remaining = {}
        
        for command, last_use in self.cooldowns[player].items():
            elapsed = current_time - last_use
            if elapsed < self.cooldown_seconds:
                remaining[command] = self.cooldown_seconds - elapsed
                
        return remaining
    
    def clear_all_cooldowns(self):
        """Clear all cooldowns - useful for game restart"""
        self.cooldowns.clear()


class PossessionTracker:
    """Tracks who currently possesses the pickaxe and manages scoring"""
    
    def __init__(self):
        self.current_possessor: Optional[str] = None
        self.possession_start_time: float = 0
        self.player_scores: Dict[str, int] = {}
        self.player_blocks_broken: Dict[str, int] = {}
        self.possession_history: List[Tuple[str, float, int]] = []  # (player, duration, points)
        self.point_system = BlockPointSystem()
        
    def take_possession(self, player: str):
        """Transfer possession to a new player"""
        # If the same player already has possession, don't reset the timer
        if self.current_possessor == player:
            return
            
        # Record previous possession
        if self.current_possessor:
            duration = time.time() - self.possession_start_time
            points = self.player_scores.get(self.current_possessor, 0)
            self.possession_history.append((self.current_possessor, duration, points))
            
        # Set new possessor
        self.current_possessor = player
        self.possession_start_time = time.time()
        
        # Initialize player score if needed
        if player not in self.player_scores:
            self.player_scores[player] = 0
            self.player_blocks_broken[player] = 0
            
    def add_block_broken(self, block_type: str) -> int:
        """Add points for a broken block to current possessor"""
        if not self.current_possessor:
            return 0
            
        points = self.point_system.get_points(block_type)
        self.player_scores[self.current_possessor] += points
        self.player_blocks_broken[self.current_possessor] += 1
        return points
        
    def get_current_possession_duration(self) -> float:
        """Get how long current player has possessed the pickaxe"""
        if not self.current_possessor:
            return 0
        return time.time() - self.possession_start_time
        
    def get_top_players(self, count: int = 5) -> List[Tuple[str, int, int]]:
        """Get top players by score
        Returns: List of (player, score, blocks_broken)
        """
        sorted_players = sorted(
            self.player_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:count]
        
        result = []
        for player, score in sorted_players:
            blocks = self.player_blocks_broken.get(player, 0)
            result.append((player, score, blocks))
            
        return result
        
    def get_player_stats(self, player: str) -> Dict:
        """Get detailed stats for a player"""
        return {
            "score": self.player_scores.get(player, 0),
            "blocks_broken": self.player_blocks_broken.get(player, 0),
            "is_current_possessor": self.current_possessor == player,
            "average_points_per_block": (
                self.player_scores.get(player, 0) / max(1, self.player_blocks_broken.get(player, 0))
            )
        }


class CompetitiveGameSystem:
    """Main competitive game system combining all mechanics"""
    
    def __init__(self, cooldown_seconds: int = 60):
        self.cooldown_manager = PlayerCooldownManager(cooldown_seconds)
        self.possession_tracker = PossessionTracker()
        self.last_command_time = time.time()
        self.command_queue: List[Tuple[str, str, float]] = []  # (player, command, timestamp)
        
    def process_command(self, player: str, command: str) -> Dict:
        """
        Process a player command
        Returns dict with status and any relevant info
        """
        # Normalize command
        command_lower = command.lower()
        
        # Check cooldown
        can_use, remaining = self.cooldown_manager.can_use_command(player, command_lower)
        
        if not can_use:
            return {
                "success": False,
                "reason": "cooldown",
                "remaining_seconds": remaining,
                "message": f"{player} must wait {int(remaining)}s to use {command_lower} again"
            }
            
        # Record command use
        self.cooldown_manager.use_command(player, command_lower)
        self.last_command_time = time.time()
        
        # Transfer possession
        previous_possessor = self.possession_tracker.current_possessor
        self.possession_tracker.take_possession(player)
        
        # Add to command queue for processing
        self.command_queue.append((player, command_lower, time.time()))
        
        # Only report as new_possessor if it actually changed
        result = {
            "success": True,
            "previous_possessor": previous_possessor,
            "command": command_lower,
        }
        
        # Only add new_possessor if possession actually changed
        if previous_possessor != player:
            result["new_possessor"] = player
            result["message"] = f"{player} takes control with {command_lower}!"
        else:
            result["message"] = f"{player} continues with {command_lower}"
            
        return result
        
    def on_block_broken(self, block_type: str) -> Dict:
        """Called when a block is broken"""
        points = self.possession_tracker.add_block_broken(block_type)
        
        return {
            "possessor": self.possession_tracker.current_possessor,
            "block_type": block_type,
            "points_earned": points,
            "total_score": self.possession_tracker.player_scores.get(
                self.possession_tracker.current_possessor, 0
            ) if self.possession_tracker.current_possessor else 0
        }
        
    def get_game_state(self) -> Dict:
        """Get current game state for display"""
        return {
            "current_possessor": self.possession_tracker.current_possessor,
            "possession_duration": self.possession_tracker.get_current_possession_duration(),
            "top_players": self.possession_tracker.get_top_players(),
            "total_players": len(self.possession_tracker.player_scores),
            "last_command_age": time.time() - self.last_command_time
        }
        
    def get_player_info(self, player: str) -> Dict:
        """Get detailed info for a specific player"""
        stats = self.possession_tracker.get_player_stats(player)
        cooldowns = self.cooldown_manager.get_all_cooldowns(player)
        
        return {
            **stats,
            "cooldowns": cooldowns
        }
    
    def reset_for_new_game(self):
        """Reset the competitive system for a new game session"""
        self.cooldown_manager.clear_all_cooldowns()
        # Keep scores but clear cooldowns so players can play immediately


# Singleton instance
competitive_system = CompetitiveGameSystem(cooldown_seconds=60)
