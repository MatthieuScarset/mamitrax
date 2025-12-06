import pygame
import random
import sys
import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 100, 220)
YELLOW = (255, 215, 0)
GRAY = (150, 150, 150)
DARK_GRAY = (80, 80, 80)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
PINK = (255, 192, 203)
BROWN = (139, 69, 19)
TAN = (210, 180, 140)

# Game settings
PLAYER_SPEED = 5
RIVAL_BASE_SPEED = 4
GRAVITY = 0.8
JUMP_POWER = -20
FINISH_LINE = 8000


class EntityType(Enum):
    PLAYER = 1
    GRUMPY_GRANDMA = 2
    SPEEDY_GRANDPA = 3
    ANGRY_KAREN = 4
    SLOW_LARRY = 5


@dataclass
class Racer:
    x: float
    y: float
    width: int
    height: int
    speed: float
    color: Tuple[int, int, int]
    entity_type: EntityType
    velocity_y: float = 0
    on_ground: bool = True
    name: str = ""
    base_speed: float = 0


@dataclass
class Item:
    x: float
    y: float
    width: int
    height: int
    item_type: str  # "coin", "speed_boost", "energy_drink"
    color: Tuple[int, int, int]


@dataclass
class Trap:
    x: float
    y: float
    width: int
    height: int
    trap_type: str  # "slippery_floor", "banana_peel", "yelling_karen"
    color: Tuple[int, int, int]


class MamitraxGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mamitrax - Supermarket Racing!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 72)
        self.promo_font = pygame.font.Font(None, 28)
        
        # Load images
        self.images = self.load_images()
        
        # Load promotional texts
        self.promos = self.load_promos()
        self.supermarket_name = self.promos.get('supermarket_name', 'MAMITRAX')
        self.promo_texts = self.promos.get('promos', [])
        random.shuffle(self.promo_texts)  # Randomize order
        
        # Game state
        self.running = True
        self.game_over = False
        self.won = False
        self.items_collected = 0
        self.camera_x = 0
        
        # Boost tracking
        self.boost_active = False
        self.boost_start_time = 0
        self.boost_duration = 0
        
        # Ground level
        self.ground_y = SCREEN_HEIGHT - 80
        
        # Player
        self.player = Racer(
            x=100,
            y=self.ground_y - 75,
            width=60,
            height=75,
            speed=PLAYER_SPEED,
            color=GREEN,
            entity_type=EntityType.PLAYER,
            name="You",
            base_speed=PLAYER_SPEED
        )
        
        # Rival racers
        self.rivals: List[Racer] = []
        self.spawn_rivals()
        
        # Items to collect
        self.items: List[Item] = []
        self.spawn_items()
        
        # Traps (slow down player)
        self.traps: List[Trap] = []
        self.spawn_traps()
        
        # Trap effect tracking
        self.trap_active = False
        self.trap_start_time = 0
        self.trap_duration = 2000  # 2 seconds
        
        # Obstacles (shelves, carts, etc)
        self.obstacles: List[pygame.Rect] = []
        self.spawn_obstacles()

    def load_images(self):
        """Load all game images"""
        images = {
            'characters': {},
            'items': {},
            'backgrounds': {},
            'ui': {}
        }
        
        # Helper function to load and scale image
        def load_image(path, width, height):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (width, height))
            except:
                return None
        
        # Load character sprites
        char_paths = {
            'player': 'images/characters/player.png',
            'grumpy_grandma': 'images/characters/grumpy_grandma.png',
            'speedy_grandpa': 'images/characters/speedy_grandpa.png',
            'angry_karen': 'images/characters/angry_karen.png',
            'slow_larry': 'images/characters/slow_larry.png',
        }
        
        for name, path in char_paths.items():
            images['characters'][name] = load_image(path, 90, 120)
        
        # Load item sprites
        item_paths = {
            'coin': ('images/items/coin.png', 20, 20),
            'speed_boost': ('images/items/speed_boost.png', 25, 25),
            'energy_drink': ('images/items/energy_drink.png', 20, 30),
        }
        
        for name, (path, w, h) in item_paths.items():
            images['items'][name] = load_image(path, w, h)
        
        # Load background elements
        bg_paths = {
            'shelf_unit': ('images/backgrounds/shelf_unit.png', 80, 120),
            'floor_tiles': ('images/backgrounds/floor_tiles.png', 80, 80),
        }
        
        for name, (path, w, h) in bg_paths.items():
            images['backgrounds'][name] = load_image(path, w, h)
        
        # Load UI elements
        ui_paths = {
            'cart_obstacle': ('images/ui/shopping_cart_obstacle.png', 50, 40),
            'victory': ('images/ui/victory_banner.png', 400, 300),
            'defeat': ('images/ui/defeat_banner.png', 400, 300),
        }
        
        for name, (path, w, h) in ui_paths.items():
            images['ui'][name] = load_image(path, w, h)
        
        return images
    
    def load_promos(self):
        """Load promotional texts from JSON file"""
        try:
            with open('promos.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  promos.json not found. Run 'python generate_promos.py' to create it.")
            # Fallback promos
            return {
                'supermarket_name': 'MAMITRAX',
                'promos': [
                    "2 FOR 1: Complaining about millennials - Now 100% FREE!",
                    "SPECIAL: Reading glasses on every aisle",
                    "MEGA SALE: Facebook conspiracy theories",
                    "HOT DEAL: Patience lessons for the young",
                    "LIMITED: Newspapers - Remember paper?",
                ]
            }
        except json.JSONDecodeError:
            print("⚠️  Error reading promos.json. Using defaults.")
            return {
                'supermarket_name': 'MAMITRAX',
                'promos': ["SPECIAL OFFERS INSIDE!"]
            }

    def spawn_rivals(self):
        """Spawn rival boomer racers with different personalities"""
        rival_types = [
            (EntityType.GRUMPY_GRANDMA, "Grumpy Grandma", PINK, 3.5),
            (EntityType.SPEEDY_GRANDPA, "Speedy Grandpa", LIGHT_BLUE, 5.0),
            (EntityType.ANGRY_KAREN, "Angry Karen", ORANGE, 4.5),
            (EntityType.SLOW_LARRY, "Slow Larry", TAN, 3.0),
        ]
        
        for i, (entity_type, name, color, speed) in enumerate(rival_types):
            rival = Racer(
                x=80 + random.randint(-20, 20),
                y=self.ground_y - 75,
                width=60,
                height=75,
                speed=speed,
                color=color,
                entity_type=entity_type,
                name=name,
                base_speed=speed
            )
            self.rivals.append(rival)

    def spawn_items(self):
        """Spawn collectible items throughout the supermarket"""
        item_types = [
            ("coin", YELLOW, 15),
            ("speed_boost", BLUE, 10),
            ("energy_drink", RED, 8),
        ]
        
        for x in range(500, FINISH_LINE, 600):  # Reduced frequency: 300 -> 600
            # Random vertical position
            y_positions = [
                self.ground_y - 30,  # on ground
                self.ground_y - 150,  # mid air
                self.ground_y - 250,  # high up
            ]
            y = random.choice(y_positions)
            item_type, color, size = random.choice(item_types)
            
            item = Item(
                x=x + random.randint(-50, 50),
                y=y,
                width=size,
                height=size,
                item_type=item_type,
                color=color
            )
            self.items.append(item)

    def spawn_traps(self):
        """Spawn traps that slow down the player"""
        trap_types = [
            ("slippery_floor", LIGHT_BLUE, 50, 30),
            ("banana_peel", YELLOW, 25, 15),
            ("yelling_karen", PINK, 40, 60),
        ]
        
        for x in range(800, FINISH_LINE, 700):
            trap_type, color, width, height = random.choice(trap_types)
            
            trap = Trap(
                x=x + random.randint(-100, 100),
                y=self.ground_y - height,
                width=width,
                height=height,
                trap_type=trap_type,
                color=color
            )
            self.traps.append(trap)

    def spawn_obstacles(self):
        """Spawn obstacles like shelves and carts"""
        for x in range(800, FINISH_LINE, 800):  # Reduced frequency: 400 -> 800
            # Shopping cart obstacle
            obstacle = pygame.Rect(
                x + random.randint(-100, 100),
                self.ground_y - 40,
                50,
                40
            )
            self.obstacles.append(obstacle)

    def handle_input(self):
        """Handle player input"""
        keys = pygame.key.get_pressed()
        
        # Move right (always moving forward)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.x += self.player.speed
        
        # Move left (slow down / go back a bit)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.x -= self.player.speed * 0.5
        
        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.player.on_ground:
            self.player.velocity_y = JUMP_POWER
            self.player.on_ground = False
        
        # Keep player in reasonable bounds
        self.player.x = max(0, self.player.x)

    def apply_physics(self, racer: Racer):
        """Apply gravity and ground collision to racer"""
        # Apply gravity
        racer.velocity_y += GRAVITY
        racer.y += racer.velocity_y
        
        # Ground collision
        if racer.y >= self.ground_y - racer.height:
            racer.y = self.ground_y - racer.height
            racer.velocity_y = 0
            racer.on_ground = True
        else:
            racer.on_ground = False

    def update_entities(self):
        """Update all entity positions"""
        # Update player physics
        self.apply_physics(self.player)
        
        # Update rivals with AI
        for rival in self.rivals:
            # Basic AI: move forward with occasional jumps
            rival.x += rival.speed + random.uniform(-0.5, 0.5)
            
            # Random jumping
            if rival.on_ground and random.random() < 0.02:
                rival.velocity_y = JUMP_POWER
                rival.on_ground = False
            
            # Apply physics to rival
            self.apply_physics(rival)
        
        # Update camera to follow player
        self.camera_x = self.player.x - 200

    def check_boost_expiration(self):
        """Check if boost duration has expired and reset speed"""
        if self.boost_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.boost_start_time >= self.boost_duration:
                # Boost expired, reset to base speed
                self.player.speed = self.player.base_speed
                self.boost_active = False
    
    def check_trap_expiration(self):
        """Check if trap slow effect has expired and reset speed"""
        if self.trap_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.trap_start_time >= self.trap_duration:
                # Trap expired, reset to base speed
                self.player.speed = self.player.base_speed
                self.trap_active = False
    
    def check_collisions(self):
        """Check for collisions with items and obstacles"""
        player_rect = pygame.Rect(self.player.x, self.player.y, 
                                  self.player.width, self.player.height)
        
        # Check collision with items
        for item in self.items[:]:
            item_rect = pygame.Rect(item.x, item.y, item.width, item.height)
            if player_rect.colliderect(item_rect):
                self.items.remove(item)
                self.items_collected += 1
                
                # Apply item effects
                if item.item_type == "coin":
                    pass  # Just counts towards score
                elif item.item_type == "speed_boost":
                    self.boost_active = True
                    self.boost_start_time = pygame.time.get_ticks()
                    self.boost_duration = random.randint(1000, 3000)  # 1-3 seconds
                    self.player.speed = min(self.player.speed + 2, 12)
                elif item.item_type == "energy_drink":
                    self.boost_active = True
                    self.boost_start_time = pygame.time.get_ticks()
                    self.boost_duration = random.randint(1000, 3000)  # 1-3 seconds
                    self.player.speed = self.player.base_speed + 4
        
        # Check collision with traps (slows you down for 2 seconds)
        for trap in self.traps[:]:
            trap_rect = pygame.Rect(trap.x, trap.y, trap.width, trap.height)
            if player_rect.colliderect(trap_rect):
                if not self.trap_active:  # Don't re-trigger if already trapped
                    self.traps.remove(trap)
                    self.trap_active = True
                    self.trap_start_time = pygame.time.get_ticks()
                    self.player.speed = max(self.player.base_speed * 0.3, 1.5)  # 30% speed
        
        # Check collision with obstacles (slows you down)
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle):
                self.player.speed = max(self.player.base_speed - 2, 2)
                self.player.x -= 5  # Push back a bit

    def check_win_condition(self):
        """Check if player reached the finish line"""
        if self.player.x >= FINISH_LINE:
            self.won = True
            self.game_over = True
            # Check if any rival beat us
            for rival in self.rivals:
                if rival.x >= FINISH_LINE and rival.x > self.player.x:
                    self.won = False

    def draw_background(self):
        """Draw the supermarket with big signage"""
        # Simple ceiling
        self.screen.fill((240, 240, 245))
        
        # Big supermarket name and promo texts in the background
        text_spacing = 800
        for i, x in enumerate(range(int(-self.camera_x * 0.15) % text_spacing - text_spacing, SCREEN_WIDTH + text_spacing, text_spacing)):
            # Alternate between supermarket name and promo text
            if i % 2 == 0:
                # Big supermarket name
                name_text = self.big_font.render(self.supermarket_name, True, BLACK)
                name_rect = name_text.get_rect(center=(x, 180))
                
                # Background rectangle for readability
                bg_rect = name_rect.inflate(40, 20)
                pygame.draw.rect(self.screen, (255, 255, 255, 230), bg_rect, border_radius=10)
                pygame.draw.rect(self.screen, BLACK, bg_rect, 4, border_radius=10)
                
                # Draw name
                self.screen.blit(name_text, name_rect)
                
                # Tagline under it
                tagline = self.small_font.render("Where Boomers Shop!", True, BLACK)
                tagline_rect = tagline.get_rect(center=(x, 220))
                self.screen.blit(tagline, tagline_rect)
            else:
                # Random promo text
                if self.promo_texts:
                    promo_index = (i // 2) % len(self.promo_texts)
                    promo = self.promo_texts[promo_index]
                    
                    # Wrap text if too long
                    max_width = 600
                    words = promo.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        test_surface = self.promo_font.render(test_line, True, BLACK)
                        if test_surface.get_width() <= max_width:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Draw promo text
                    total_height = len(lines) * 35
                    start_y = 180 - total_height // 2
                    
                    for line_idx, line in enumerate(lines):
                        promo_text = self.promo_font.render(line, True, BLACK)
                        promo_rect = promo_text.get_rect(center=(x, start_y + line_idx * 35))
                        
                        # Background for readability
                        bg_rect = promo_rect.inflate(30, 15)
                        pygame.draw.rect(self.screen, (255, 255, 200), bg_rect, border_radius=8)
                        pygame.draw.rect(self.screen, BLACK, bg_rect, 3, border_radius=8)
                        
                        self.screen.blit(promo_text, promo_rect)
        
        # Ceiling lights (simple and clean)
        light_spacing = 200
        for x in range(int(-self.camera_x * 0.3) % light_spacing - light_spacing, SCREEN_WIDTH + light_spacing, light_spacing):
            # Light fixture
            pygame.draw.rect(self.screen, (255, 255, 240), (x + 40, 30, 120, 40), border_radius=5)
            pygame.draw.rect(self.screen, (220, 220, 200), (x + 40, 30, 120, 40), 2, border_radius=5)
        
        # Simple floor - clean checkerboard
        tile_width = 80
        tile_height = SCREEN_HEIGHT - self.ground_y
        
        for x in range(int(-self.camera_x) % tile_width - tile_width, SCREEN_WIDTH, tile_width):
            world_x = x + self.camera_x
            is_dark = (int(world_x) // tile_width) % 2 == 0
            
            # Simple floor colors
            base_color = (230, 230, 230) if is_dark else (245, 245, 245)
            
            # Draw tile
            pygame.draw.rect(self.screen, base_color, (x, self.ground_y, tile_width, tile_height))
            pygame.draw.rect(self.screen, (200, 200, 200), (x, self.ground_y, tile_width, tile_height), 1)
        
        # Fruit stands and special displays (foreground layer)
        stand_spacing = 600
        for x in range(int(-self.camera_x * 0.7) % stand_spacing - stand_spacing, SCREEN_WIDTH + stand_spacing, stand_spacing):
            stand_type = int((x + self.camera_x) / stand_spacing) % 3
            if stand_type == 0:
                self.draw_fruit_stand(x, self.ground_y - 100)
            elif stand_type == 1:
                self.draw_demo_table(x, self.ground_y - 90)
            else:
                self.draw_shelf(x, self.ground_y - 150, 70, 120, 1.0)
        
        # Draw ground line
        pygame.draw.line(self.screen, (180, 180, 180), (0, self.ground_y), (SCREEN_WIDTH, self.ground_y), 3)
    
    def draw_fruit_stand(self, x, y):
        """Draw a fruit and vegetable stand"""
        # Wooden base/table
        pygame.draw.rect(self.screen, (139, 90, 43), (x, y + 60, 90, 40))
        pygame.draw.rect(self.screen, (101, 67, 33), (x, y + 60, 90, 40), 3)
        
        # Crate boxes
        crate_color = (160, 120, 80)
        pygame.draw.rect(self.screen, crate_color, (x + 5, y, 35, 30))
        pygame.draw.rect(self.screen, (120, 90, 60), (x + 5, y, 35, 30), 2)
        pygame.draw.rect(self.screen, crate_color, (x + 50, y, 35, 30))
        pygame.draw.rect(self.screen, (120, 90, 60), (x + 50, y, 35, 30), 2)
        
        # Fruits (left crate - apples/red)
        fruit_positions = [(x + 12, y + 8), (x + 20, y + 8), (x + 28, y + 8),
                          (x + 12, y + 18), (x + 20, y + 18), (x + 28, y + 18)]
        for fx, fy in fruit_positions:
            pygame.draw.circle(self.screen, (220, 20, 20), (fx, fy), 6)
            pygame.draw.circle(self.screen, (180, 10, 10), (fx - 2, fy - 2), 2)
        
        # Vegetables (right crate - green)
        for fx, fy in [(x + 57, y + 8), (x + 65, y + 8), (x + 73, y + 8),
                       (x + 57, y + 18), (x + 65, y + 18), (x + 73, y + 18)]:
            pygame.draw.circle(self.screen, (50, 180, 50), (fx, fy), 6)
            pygame.draw.circle(self.screen, (30, 140, 30), (fx - 2, fy - 2), 2)
        
        # Price signs
        pygame.draw.rect(self.screen, (255, 255, 200), (x + 8, y + 32, 25, 12))
        pygame.draw.rect(self.screen, BLACK, (x + 8, y + 32, 25, 12), 1)
        pygame.draw.rect(self.screen, (255, 255, 200), (x + 53, y + 32, 25, 12))
        pygame.draw.rect(self.screen, BLACK, (x + 53, y + 32, 25, 12), 1)
        
        # Second row of crates
        pygame.draw.rect(self.screen, crate_color, (x + 5, y + 50, 35, 30))
        pygame.draw.rect(self.screen, (120, 90, 60), (x + 5, y + 50, 35, 30), 2)
        pygame.draw.rect(self.screen, crate_color, (x + 50, y + 50, 35, 30))
        pygame.draw.rect(self.screen, (120, 90, 60), (x + 50, y + 50, 35, 30), 2)
        
        # Oranges (bottom left)
        for fx, fy in [(x + 12, y + 58), (x + 20, y + 58), (x + 28, y + 58),
                       (x + 12, y + 68), (x + 20, y + 68), (x + 28, y + 68)]:
            pygame.draw.circle(self.screen, (255, 165, 0), (fx, fy), 6)
            pygame.draw.circle(self.screen, (220, 140, 0), (fx - 2, fy - 2), 2)
        
        # Bananas (bottom right - yellow)
        for fx, fy in [(x + 57, y + 58), (x + 65, y + 58), (x + 73, y + 58),
                       (x + 57, y + 68), (x + 65, y + 68), (x + 73, y + 68)]:
            pygame.draw.ellipse(self.screen, (255, 230, 0), (fx - 4, fy - 3, 12, 6))
            pygame.draw.ellipse(self.screen, (220, 200, 0), (fx - 4, fy - 3, 12, 6), 1)
    
    def draw_demo_table(self, x, y):
        """Draw a demonstration table with a person giving free samples"""
        # Table
        pygame.draw.rect(self.screen, (200, 180, 160), (x, y + 50, 80, 50))
        pygame.draw.rect(self.screen, (150, 130, 110), (x, y + 50, 80, 50), 3)
        
        # Tablecloth
        pygame.draw.rect(self.screen, (255, 255, 255), (x + 5, y + 45, 70, 10))
        
        # Sample plates
        for px in [x + 15, x + 35, x + 55]:
            pygame.draw.circle(self.screen, (230, 230, 230), (px, y + 60), 8)
            pygame.draw.circle(self.screen, (200, 200, 200), (px, y + 60), 8, 1)
            # Food sample (cheese cubes)
            pygame.draw.rect(self.screen, (255, 220, 100), (px - 3, y + 57, 6, 6))
        
        # Demonstrator person (simple stick figure style)
        person_x = x + 40
        person_y = y
        
        # Head
        pygame.draw.circle(self.screen, (255, 220, 180), (person_x, person_y), 10)
        pygame.draw.circle(self.screen, BLACK, (person_x, person_y), 10, 2)
        
        # Eyes
        pygame.draw.circle(self.screen, BLACK, (person_x - 4, person_y - 2), 2)
        pygame.draw.circle(self.screen, BLACK, (person_x + 4, person_y - 2), 2)
        
        # Smile
        pygame.draw.arc(self.screen, BLACK, (person_x - 5, person_y - 2, 10, 8), 3.14, 0, 2)
        
        # Body (apron)
        pygame.draw.rect(self.screen, (100, 180, 100), (person_x - 12, person_y + 10, 24, 35), border_radius=3)
        
        # Arms (holding a tray)
        pygame.draw.line(self.screen, (255, 220, 180), (person_x - 12, person_y + 20), (person_x - 20, person_y + 30), 4)
        pygame.draw.line(self.screen, (255, 220, 180), (person_x + 12, person_y + 20), (person_x + 20, person_y + 30), 4)
        
        # Sign "FREE SAMPLES!"
        pygame.draw.rect(self.screen, (255, 200, 200), (x + 10, y + 70, 60, 15), border_radius=2)
        pygame.draw.rect(self.screen, RED, (x + 10, y + 70, 60, 15), 2, border_radius=2)
    
    def draw_shelf(self, x, y, width, height, scale):
        """Draw a supermarket shelf with products at given scale for depth"""
        # Metallic shelf frame
        pygame.draw.rect(self.screen, (160, 160, 160), (x, y, width, height))
        pygame.draw.rect(self.screen, (120, 120, 120), (x, y, width, height), int(3 * scale))
        
        # Price tags/shelf labels
        num_shelves = 4
        shelf_height = height // num_shelves
        
        product_sets = [
            [(220, 20, 20), (200, 0, 0), (180, 20, 20)],           # Red products (tomato sauce, etc)
            [(20, 150, 20), (0, 180, 0), (50, 200, 50)],           # Green products (vegetables)
            [(255, 200, 0), (255, 150, 0), (230, 180, 0)],         # Yellow/Orange (cereals, snacks)
            [(30, 100, 200), (50, 150, 255), (20, 80, 180)],       # Blue products (water, cleaning)
        ]
        
        for shelf_idx in range(num_shelves):
            shelf_y = y + (shelf_idx * shelf_height) + int(8 * scale)
            
            # Metal shelf board
            pygame.draw.rect(self.screen, (180, 180, 180), (x, shelf_y, width, int(3 * scale)))
            
            # Price label strip
            pygame.draw.rect(self.screen, (255, 255, 200), (x + 2, shelf_y - int(4 * scale), width - 4, int(3 * scale)))
            
            # Products on this shelf
            colors = product_sets[shelf_idx % len(product_sets)]
            product_width = int(12 * scale)
            product_height = int(18 * scale)
            
            for col, px in enumerate(range(x + int(6 * scale), x + width - int(6 * scale), int(14 * scale))):
                if px + product_width > x + width:
                    break
                    
                color = colors[col % len(colors)]
                product_y = shelf_y - product_height - int(2 * scale)
                
                # Product package
                pygame.draw.rect(self.screen, color, (px, product_y, product_width, product_height), border_radius=int(2 * scale))
                pygame.draw.rect(self.screen, BLACK, (px, product_y, product_width, product_height), max(1, int(2 * scale)))
                
                # Brand label on product
                label_height = int(5 * scale)
                pygame.draw.rect(self.screen, WHITE, (px + 2, product_y + 2, product_width - 4, label_height))

    def draw_racer(self, racer: Racer):
        """Draw a racer with screen coordinates"""
        screen_x = racer.x - self.camera_x
        
        # Don't draw if off screen
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
            return
        
        # Get character image
        char_img = None
        if racer.entity_type == EntityType.PLAYER:
            char_img = self.images['characters']['player']
        elif racer.entity_type == EntityType.GRUMPY_GRANDMA:
            char_img = self.images['characters']['grumpy_grandma']
        elif racer.entity_type == EntityType.SPEEDY_GRANDPA:
            char_img = self.images['characters']['speedy_grandpa']
        elif racer.entity_type == EntityType.ANGRY_KAREN:
            char_img = self.images['characters']['angry_karen']
        elif racer.entity_type == EntityType.SLOW_LARRY:
            char_img = self.images['characters']['slow_larry']
        
        # Draw character image or fallback to simple shapes
        if char_img:
            # Center the image on the racer position
            img_x = screen_x - (char_img.get_width() - racer.width) // 2
            img_y = racer.y - (char_img.get_height() - racer.height) // 2
            self.screen.blit(char_img, (img_x, img_y))
        else:
            # Fallback: simple shapes
            # Body
            pygame.draw.rect(self.screen, racer.color, 
                            (screen_x, racer.y, racer.width, racer.height), border_radius=5)
            
            # Head
            head_color = (255, 220, 180)
            pygame.draw.circle(self.screen, head_color, 
                              (int(screen_x + racer.width // 2), int(racer.y + 15)), 12)
            
            # Eyes (grumpy look)
            pygame.draw.line(self.screen, BLACK, 
                            (int(screen_x + racer.width // 2 - 5), int(racer.y + 13)),
                            (int(screen_x + racer.width // 2 - 5), int(racer.y + 15)), 2)
            pygame.draw.line(self.screen, BLACK, 
                            (int(screen_x + racer.width // 2 + 5), int(racer.y + 13)),
                            (int(screen_x + racer.width // 2 + 5), int(racer.y + 15)), 2)
            
            # Cart
            cart_y = racer.y + racer.height - 20
            pygame.draw.rect(self.screen, DARK_GRAY, 
                            (screen_x - 5, cart_y, racer.width + 10, 20), border_radius=3)
            
            # Wheels
            pygame.draw.circle(self.screen, BLACK, (int(screen_x + 5), int(cart_y + 20)), 5)
            pygame.draw.circle(self.screen, BLACK, (int(screen_x + racer.width - 5), int(cart_y + 20)), 5)
        
        # Name tag above head (for rivals)
        if racer.entity_type != EntityType.PLAYER:
            name_text = self.tiny_font.render(racer.name, True, BLACK)
            text_rect = name_text.get_rect(center=(screen_x + racer.width // 2, racer.y - 15))
            # Add background for better readability
            bg_rect = text_rect.inflate(10, 4)
            pygame.draw.rect(self.screen, (255, 255, 255, 200), bg_rect, border_radius=3)
            self.screen.blit(name_text, text_rect)
        
        # Speed indicator for player
        if racer.entity_type == EntityType.PLAYER:
            speed_text = self.tiny_font.render(f"Speed: {racer.speed:.1f}", True, BLUE)
            text_rect = speed_text.get_rect(center=(screen_x + racer.width // 2, racer.y - 15))
            bg_rect = text_rect.inflate(10, 4)
            pygame.draw.rect(self.screen, (255, 255, 255, 200), bg_rect, border_radius=3)
            self.screen.blit(speed_text, text_rect)

    def draw_item(self, item: Item):
        """Draw collectible item"""
        screen_x = item.x - self.camera_x
        
        if screen_x < -50 or screen_x > SCREEN_WIDTH + 50:
            return
        
        # Get item image
        item_img = self.images['items'].get(item.item_type)
        
        if item_img:
            # Draw with image
            img_x = screen_x + (item.width - item_img.get_width()) // 2
            img_y = item.y + (item.height - item_img.get_height()) // 2
            self.screen.blit(item_img, (img_x, img_y))
            
            # Add a subtle glow effect
            glow_surface = pygame.Surface((item_img.get_width() + 10, item_img.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*item.color, 50), 
                             (glow_surface.get_width() // 2, glow_surface.get_height() // 2), 
                             max(item_img.get_width(), item_img.get_height()) // 2 + 5)
            self.screen.blit(glow_surface, (img_x - 5, img_y - 5))
            self.screen.blit(item_img, (img_x, img_y))
        else:
            # Fallback: simple shapes
            if item.item_type == "coin":
                pygame.draw.circle(self.screen, item.color, 
                                 (int(screen_x + item.width // 2), int(item.y + item.height // 2)), 
                                 item.width // 2)
                pygame.draw.circle(self.screen, ORANGE, 
                                 (int(screen_x + item.width // 2), int(item.y + item.height // 2)), 
                                 item.width // 2 - 3)
            elif item.item_type == "speed_boost":
                # Arrow shape
                points = [
                    (screen_x + item.width // 2, item.y),
                    (screen_x + item.width, item.y + item.height // 2),
                    (screen_x + item.width // 2, item.y + item.height),
                    (screen_x, item.y + item.height // 2)
                ]
                pygame.draw.polygon(self.screen, item.color, points)
            elif item.item_type == "energy_drink":
                # Can shape
                pygame.draw.rect(self.screen, item.color, 
                               (screen_x, item.y, item.width, item.height), border_radius=3)
                pygame.draw.rect(self.screen, WHITE, 
                               (screen_x + 2, item.y + 2, item.width - 4, item.height - 4))
    
    def draw_trap(self, trap: Trap):
        """Draw trap with visual indicators"""
        screen_x = trap.x - self.camera_x
        
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
            return
        
        # Draw different trap types
        if trap.trap_type == "slippery_floor":
            # Wet floor sign
            pygame.draw.polygon(self.screen, YELLOW, [
                (screen_x + trap.width // 2, trap.y),
                (screen_x + trap.width, trap.y + trap.height),
                (screen_x, trap.y + trap.height)
            ])
            pygame.draw.polygon(self.screen, BLACK, [
                (screen_x + trap.width // 2, trap.y),
                (screen_x + trap.width, trap.y + trap.height),
                (screen_x, trap.y + trap.height)
            ], 2)
            # Exclamation mark
            pygame.draw.line(self.screen, BLACK, 
                           (screen_x + trap.width // 2, trap.y + 8),
                           (screen_x + trap.width // 2, trap.y + 18), 3)
            pygame.draw.circle(self.screen, BLACK,
                             (screen_x + trap.width // 2, trap.y + 23), 2)
            
        elif trap.trap_type == "banana_peel":
            # Banana shape
            pygame.draw.ellipse(self.screen, YELLOW, 
                              (screen_x, trap.y, trap.width, trap.height))
            pygame.draw.ellipse(self.screen, (200, 180, 0), 
                              (screen_x, trap.y, trap.width, trap.height), 2)
            # Brown spots
            for spot_x, spot_y in [(5, 3), (15, 8), (8, 10)]:
                pygame.draw.circle(self.screen, (100, 70, 0),
                                 (screen_x + spot_x, trap.y + spot_y), 2)
            
        elif trap.trap_type == "yelling_karen":
            # Angry face
            pygame.draw.circle(self.screen, PINK, 
                             (screen_x + trap.width // 2, trap.y + 20), 18)
            pygame.draw.circle(self.screen, BLACK,
                             (screen_x + trap.width // 2, trap.y + 20), 18, 2)
            
            # Angry eyes
            pygame.draw.line(self.screen, BLACK,
                           (screen_x + trap.width // 2 - 8, trap.y + 15),
                           (screen_x + trap.width // 2 - 5, trap.y + 18), 2)
            pygame.draw.line(self.screen, BLACK,
                           (screen_x + trap.width // 2 + 5, trap.y + 18),
                           (screen_x + trap.width // 2 + 8, trap.y + 15), 2)
            
            # Angry mouth (yelling)
            pygame.draw.arc(self.screen, BLACK,
                          (screen_x + trap.width // 2 - 8, trap.y + 20, 16, 12),
                          0, 3.14, 3)
            
            # Speech bubble indicators
            for i, offset in enumerate([35, 42, 49]):
                size = 5 - i
                pygame.draw.circle(self.screen, WHITE,
                                 (screen_x + trap.width // 2 + 15, trap.y + offset - 20), size)
                pygame.draw.circle(self.screen, BLACK,
                                 (screen_x + trap.width // 2 + 15, trap.y + offset - 20), size, 1)
    
    def draw_obstacles(self):
        """Draw obstacles"""
        cart_img = self.images['ui']['cart_obstacle']
        
        for obstacle in self.obstacles:
            screen_x = obstacle.x - self.camera_x
            
            if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
                continue
            
            # Draw cart image or fallback
            if cart_img:
                self.screen.blit(cart_img, (screen_x, obstacle.y))
            else:
                # Fallback: simple cart
                pygame.draw.rect(self.screen, DARK_GRAY, 
                               (screen_x, obstacle.y, obstacle.width, obstacle.height), border_radius=3)
                pygame.draw.rect(self.screen, GRAY, 
                               (screen_x + 5, obstacle.y + 5, obstacle.width - 10, obstacle.height - 10))

    def draw_ui(self):
        """Draw UI elements"""
        # Items collected
        items_text = self.font.render(f"Items: {self.items_collected}", True, BLACK)
        self.screen.blit(items_text, (10, 10))
        
        # Distance progress
        progress = min(100, (self.player.x / FINISH_LINE) * 100)
        progress_text = self.small_font.render(f"Progress: {int(progress)}%", True, BLACK)
        self.screen.blit(progress_text, (10, 50))
        
        # Progress bar
        bar_width = 300
        bar_height = 25
        pygame.draw.rect(self.screen, GRAY, (10, 80, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (10, 80, int(bar_width * progress / 100), bar_height))
        pygame.draw.rect(self.screen, BLACK, (10, 80, bar_width, bar_height), 2)
        
        # Show finish line marker on progress bar
        finish_marker_x = 10 + bar_width - 2
        pygame.draw.line(self.screen, RED, (finish_marker_x, 80), (finish_marker_x, 105), 4)
        
        # Controls hint
        hint_text = self.small_font.render("RIGHT/D: Run  SPACE/W: Jump", True, DARK_GRAY)
        self.screen.blit(hint_text, (SCREEN_WIDTH - 300, 10))
        
        # Leaderboard - show positions
        leaderboard_y = SCREEN_HEIGHT - 150
        leaderboard_text = self.small_font.render("Race Position:", True, BLACK)
        self.screen.blit(leaderboard_text, (10, leaderboard_y))
        
        # Sort all racers by x position
        all_racers = [self.player] + self.rivals
        sorted_racers = sorted(all_racers, key=lambda r: r.x, reverse=True)
        
        for i, racer in enumerate(sorted_racers[:5]):  # Show top 5
            position = i + 1
            name = racer.name if racer.entity_type != EntityType.PLAYER else "YOU"
            color = GREEN if racer.entity_type == EntityType.PLAYER else BLACK
            pos_text = self.tiny_font.render(f"{position}. {name}", True, color)
            self.screen.blit(pos_text, (15, leaderboard_y + 25 + i * 20))

    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Find player's final position
        all_racers = [self.player] + self.rivals
        sorted_racers = sorted(all_racers, key=lambda r: r.x, reverse=True)
        player_position = sorted_racers.index(self.player) + 1
        
        # Draw victory/defeat banner
        if player_position == 1:
            banner_img = self.images['ui']['victory']
            if banner_img:
                banner_x = (SCREEN_WIDTH - banner_img.get_width()) // 2
                banner_y = (SCREEN_HEIGHT - banner_img.get_height()) // 2 - 50
                self.screen.blit(banner_img, (banner_x, banner_y))
            
            title = self.font.render("YOU WON!", True, YELLOW)
            subtitle = self.small_font.render("First to the checkout! Those boomers didn't stand a chance!", True, GREEN)
        elif player_position <= 3:
            title = self.font.render("PODIUM FINISH!", True, ORANGE)
            subtitle = self.small_font.render(f"You got {player_position}{'st' if player_position==2 else 'rd'} place! Not bad!", True, LIGHT_BLUE)
        else:
            banner_img = self.images['ui']['defeat']
            if banner_img:
                banner_x = (SCREEN_WIDTH - banner_img.get_width()) // 2
                banner_y = (SCREEN_HEIGHT - banner_img.get_height()) // 2 - 50
                self.screen.blit(banner_img, (banner_x, banner_y))
            
            title = self.font.render("RACE OVER", True, RED)
            subtitle = self.small_font.render(f"You finished {player_position}th. Those boomers got you!", True, GRAY)
        
        items_msg = self.small_font.render(f"Items Collected: {self.items_collected}", True, WHITE)
        restart = self.small_font.render("Press R to Restart or Q to Quit", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(items_msg, (SCREEN_WIDTH // 2 - items_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

    def run(self):
        """Main game loop"""
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key == pygame.K_r:
                            # Restart game
                            self.__init__()
                        elif event.key == pygame.K_q:
                            self.running = False
            
            if not self.game_over:
                # Game logic
                self.handle_input()
                self.update_entities()
                self.check_boost_expiration()
                self.check_trap_expiration()
                self.check_collisions()
                self.check_win_condition()
                
                # Drawing
                self.draw_background()
                
                # Draw obstacles
                self.draw_obstacles()
                
                # Draw traps
                for trap in self.traps:
                    self.draw_trap(trap)
                
                # Draw items
                for item in self.items:
                    self.draw_item(item)
                
                # Draw all racers
                for rival in self.rivals:
                    self.draw_racer(rival)
                self.draw_racer(self.player)
                
                # Draw finish line
                finish_screen_x = FINISH_LINE - self.camera_x
                if finish_screen_x < SCREEN_WIDTH + 100:
                    pygame.draw.rect(self.screen, RED, (finish_screen_x, 0, 10, SCREEN_HEIGHT))
                    pygame.draw.rect(self.screen, WHITE, (finish_screen_x, 0, 10, SCREEN_HEIGHT), 2)
                    finish_text = self.font.render("CHECKOUT", True, RED)
                    self.screen.blit(finish_text, (finish_screen_x - 50, 50))
                
                self.draw_ui()
            else:
                # Draw game over screen
                self.draw_background()
                self.draw_obstacles()
                for rival in self.rivals:
                    self.draw_racer(rival)
                self.draw_racer(self.player)
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


def main():
    game = MamitraxGame()
    game.run()


if __name__ == "__main__":
    main()
