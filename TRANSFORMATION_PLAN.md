# Falling Pickaxe to Digging Game - Complete Transformation Plan

## Phase 1: Asset Creation
- [ ] Create character sprites for digger
- [ ] Design dirt layer textures (5 difficulty levels)
- [ ] Create rock sprites for all 10 Mohs hardness levels
- [ ] Design gem sprites (10 types matching Mohs scale)
- [ ] Create tool/shovel sprites for all upgrade levels
- [ ] Design enemy sprites (moles, worms, beetles)
- [ ] Create power-up sprites (fruits, vegetables, flowers)
- [ ] Design new background for underground setting

## Phase 2: Sound Design
- [ ] Record/source digging sound effects
- [ ] Create rock breaking sounds (varying pitch)
- [ ] Add gem collection sound effects
- [ ] Create enemy movement/threat sounds
- [ ] Add power-up pickup sound effects
- [ ] Create tool upgrade celebration sounds

## Phase 3: Core Mechanics
- [ ] Replace pickaxe physics with character movement
- [ ] Implement controlled digging system (speed-based)
- [ ] Add horizontal movement (1-3 spaces left/right)
- [ ] Create dirt layer generation with difficulty scaling
- [ ] Implement rock placement and hardness system

## Phase 4: Loot System
- [ ] Create gem generation and rarity system
- [ ] Implement gem collection and inventory management
- [ ] Build tool upgrade system with exponential improvements
- [ ] Add gem-to-tool upgrade conversion (10 gems = 1 upgrade)

## Phase 5: Enemy System
- [ ] Create enemy AI for pacing movement
- [ ] Implement enemy pocket generation (every 10-15 layers)
- [ ] Add collision detection for gem theft mechanic
- [ ] Create rarest gem loss system on enemy contact

## Phase 6: Power-ups
- [ ] Implement fruit/vegetable power-up system
- [ ] Add flower bonus effects (gem detection, attraction)
- [ ] Create power-up spawn and collection mechanics
- [ ] Implement temporary effect timers and buffs

## Phase 7: World Generation
- [ ] Replace chunk system with layered digging world
- [ ] Implement depth-based difficulty progression
- [ ] Create randomized content placement algorithms
- [ ] Add procedural underground cavern generation

## Phase 8: UI/HUD Updates
- [ ] Replace ore counter with gem inventory display
- [ ] Add tool level and efficiency indicators
- [ ] Create depth and layer progress display
- [ ] Add power-up status and timer displays

## Phase 9: Chat Integration
- [ ] Update chat commands for new mechanics
- [ ] Add commands for direction changes (left/right movement)
- [ ] Implement tool upgrade chat triggers
- [ ] Create power-up activation chat commands

## Phase 10: Camera System
- [ ] Modify camera to follow character smoothly
- [ ] Implement depth-based camera positioning
- [ ] Add screen shake for rock breaking

## Phase 11: Particle Effects
- [ ] Create dirt particle effects for digging
- [ ] Add rock break particle explosions
- [ ] Implement gem sparkle and collection effects
- [ ] Create power-up activation visual effects

## Phase 12: Performance Optimization
- [ ] Optimize rendering for underground layers
- [ ] Implement efficient collision detection
- [ ] Create LOD system for distant content

## Phase 13: Testing & Polish
- [ ] Test all chat command integrations
- [ ] Balance gem rarity and spawn rates
- [ ] Fine-tune enemy difficulty and placement
- [ ] Test tool upgrade progression balance

## Phase 14: Final Integration
- [ ] Update settings system for new game mechanics
- [ ] Integrate streaming system with new visuals
- [ ] Update notification system for new achievements
- [ ] Test complete game loop and progression

## Key Files to Modify

### Core Game Files
- `src/main.py` - Main game loop and mechanics
- `src/pickaxe.py` → `src/character.py` - Character movement and digging
- `src/chunk.py` → `src/world.py` - World generation and layer system
- `src/hud.py` - UI updates for new systems

### New Files to Create
- `src/gems.py` - Gem system and rarity management
- `src/enemies.py` - Enemy AI and behavior
- `src/powerups.py` - Power-up effects and timers
- `src/tools.py` - Tool upgrade system
- `src/digging.py` - Digging mechanics and physics

### Asset Directories
- `src/assets/character/` - Character sprites
- `src/assets/dirt/` - Dirt layer textures
- `src/assets/rocks/` - Rock sprites (Mohs scale)
- `src/assets/gems/` - Gem sprites
- `src/assets/tools/` - Tool upgrade sprites
- `src/assets/enemies/` - Enemy sprites
- `src/assets/powerups/` - Power-up sprites
- `src/assets/sounds/digging/` - Digging sound effects
- `src/assets/sounds/gems/` - Gem collection sounds
- `src/assets/sounds/enemies/` - Enemy sounds

## Estimated Timeline
- **Phases 1-2 (Assets & Sounds)**: 2-3 weeks
- **Phase 3 (Core Mechanics)**: 1-2 weeks
- **Phases 4-6 (Game Systems)**: 2-3 weeks
- **Phases 7-8 (World & UI)**: 1-2 weeks
- **Phases 9-11 (Integration & Effects)**: 1-2 weeks
- **Phases 12-14 (Polish & Testing)**: 1 week

**Total estimated time**: 8-13 weeks for complete transformation