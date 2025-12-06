import pygame
import random
import sys
import os
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
PLAYER_SPEED = 6
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


class MamitraxGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mamitrax - Supermarket Racing!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        # Load images
        self.images = self.load_images()
        
        # Game state
        self.running = True
        self.game_over = False
        self.won = False
        self.items_collected = 0
        self.camera_x = 0
        
        # Ground level
        self.ground_y = SCREEN_HEIGHT - 80
        
        # Player
        self.player = Racer(
            x=100,
            y=self.ground_y - 50,
            width=40,
            height=50,
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
            images['characters'][name] = load_image(path, 60, 80)
        
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
                y=self.ground_y - 50,
                width=40,
                height=50,
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
        
        for x in range(500, FINISH_LINE, 300):
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

    def spawn_obstacles(self):
        """Spawn obstacles like shelves and carts"""
        for x in range(800, FINISH_LINE, 400):
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
                    self.player.speed = min(self.player.speed + 1, 12)
                elif item.item_type == "energy_drink":
                    self.player.speed = self.player.base_speed + 3
        
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
        """Draw the supermarket with aisles"""
        # Simple ceiling
        self.screen.fill((240, 240, 245))
        
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
        
        # Draw only ONE layer of shelves (simpler)
        shelf_spacing = 220
        for x in range(int(-self.camera_x * 0.6) % shelf_spacing - shelf_spacing, SCREEN_WIDTH + shelf_spacing, shelf_spacing):
            self.draw_shelf(x, self.ground_y - 150, 70, 120, 1.0)
        
        # Draw ground line
        pygame.draw.line(self.screen, (180, 180, 180), (0, self.ground_y), (SCREEN_WIDTH, self.ground_y), 3)
    
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
                self.check_collisions()
                self.check_win_condition()
                
                # Drawing
                self.draw_background()
                
                # Draw obstacles
                self.draw_obstacles()
                
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
