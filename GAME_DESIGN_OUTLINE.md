# Dig Dug-Inspired Interactive Digging Game - Design Outline

## Core Mechanics

### Character Movement
- **Primary movement**: Digging downward (slow/normal/fast speeds)
- **Secondary movement**: Left/right movement by 1-3 spaces
- **Control**: Character controlled by chat commands and auto-mechanics

### Digging System
**Dirt Layers**: Multiple colors representing difficulty levels
- **Light brown (Level 1)**: 1 second dig time
- **Medium brown (Level 2)**: 2 seconds dig time
- **Dark brown (Level 3)**: 3 seconds dig time
- **Clay (Level 4)**: 4 seconds dig time
- **Bedrock (Level 5)**: 5 seconds dig time

### Rock System (Mohs Hardness Scale)
Rocks take 4x longer than same-level dirt to dig through

| Hardness | Mineral | Dig Time | Gem Yield |
|----------|---------|----------|-----------|
| 1 | Talc | 4 seconds | Talc gems |
| 2 | Gypsum | 8 seconds | Gypsum gems |
| 3 | Calcite | 12 seconds | Calcite gems |
| 4 | Fluorite | 16 seconds | Fluorite gems |
| 5 | Apatite | 20 seconds | Apatite gems |
| 6 | Orthoclase | 24 seconds | Orthoclase gems |
| 7 | Quartz | 28 seconds | Quartz gems |
| 8 | Topaz | 32 seconds | Topaz gems |
| 9 | Corundum | 36 seconds | Corundum gems |
| 10 | Diamond | 40 seconds | Diamond gems |

## Loot & Upgrade System

### Gems
- **Random appearance**: Frequency inversely proportional to rarity
- **Upgrade requirement**: 10 gems = tool upgrade of that hardness level
- **Efficiency improvement**: Exponential improvement per upgrade
- **Guaranteed drops**: From rocks of corresponding hardness

### Tool Progression
- **Starting tool**: Wooden Shovel
- **Gem-based upgrades**: Improve digging speed exponentially
- **Material efficiency**: Higher-tier tools dig through harder materials faster

## Bonuses & Power-ups

### Fruits & Vegetables
- **Carrots**: Temporary speed boost
- **Apples**: Health restoration
- **Grapes**: Multi-dig ability
- **Potatoes**: Shield from enemy theft
- **Corn**: Extra gem magnetism

### Flowers
- **Daisies**: Reveal nearby gems
- **Roses**: Attract rare gems
- **Tulips**: Temporary invincibility

## Enemies & Obstacles

### Enemy Pockets
- **Spawn frequency**: Every 10-15 layers (±10 variation)
- **Behavior**: Enemies pace back and forth horizontally
- **Enemy types**:
  - **Moles**: Fast moving, steal common gems
  - **Worms**: Slow moving, steal rare gems
  - **Beetles**: Medium speed, steal random gems

### Enemy Mechanics
- **Theft system**: Hitbox overlap = lose rarest gem currently held
- **Avoidance**: Enemies can be avoided with careful timing
- **Protection**: Some power-ups provide protection from theft

## Environmental Features

### Frequency Rules
- **Rocks**: 3x more frequent than random gems
- **Gems**: Random with rarity-based frequency scaling
- **Enemies**: Every 10-15 layers with randomization
- **Power-ups**: Scattered throughout with medium rarity

### Game Balance
- **Risk vs Reward**: Players can dig through hard rocks for guaranteed gems or rely on random gem spawns
- **Strategy options**: Fast progression vs careful gem hunting
- **Randomization**: All spawn rates include variance to maintain unpredictability