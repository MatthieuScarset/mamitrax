import pygame
import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

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
JUMP_POWER = -15
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
        # Sky/ceiling
        self.screen.fill((220, 220, 230))
        
        # Draw floor tiles
        tile_width = 80
        for x in range(int(-self.camera_x) % tile_width - tile_width, SCREEN_WIDTH, tile_width):
            world_x = x + self.camera_x
            color = (200, 200, 200) if (int(world_x) // tile_width) % 2 == 0 else (210, 210, 210)
            pygame.draw.rect(self.screen, color, (x, self.ground_y, tile_width, SCREEN_HEIGHT - self.ground_y))
            pygame.draw.rect(self.screen, GRAY, (x, self.ground_y, tile_width, SCREEN_HEIGHT - self.ground_y), 1)
        
        # Draw shelves in background (parallax effect)
        for x in range(int(-self.camera_x * 0.5) % 200 - 200, SCREEN_WIDTH, 200):
            pygame.draw.rect(self.screen, BROWN, (x, self.ground_y - 120, 60, 100))
            # Shelves with products
            for shelf_y in range(int(self.ground_y - 110), int(self.ground_y - 30), 25):
                pygame.draw.rect(self.screen, TAN, (x + 5, shelf_y, 50, 20))
        
        # Draw ground line
        pygame.draw.line(self.screen, BLACK, (0, self.ground_y), (SCREEN_WIDTH, self.ground_y), 3)

    def draw_racer(self, racer: Racer):
        """Draw a racer with screen coordinates"""
        screen_x = racer.x - self.camera_x
        
        # Don't draw if off screen
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
            return
        
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
            self.screen.blit(name_text, (screen_x - 10, racer.y - 20))
        
        # Speed indicator for player
        if racer.entity_type == EntityType.PLAYER:
            speed_text = self.tiny_font.render(f"Speed: {racer.speed:.1f}", True, BLUE)
            self.screen.blit(speed_text, (screen_x - 10, racer.y - 20))

    def draw_item(self, item: Item):
        """Draw collectible item"""
        screen_x = item.x - self.camera_x
        
        if screen_x < -50 or screen_x > SCREEN_WIDTH + 50:
            return
        
        # Draw item based on type
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
        for obstacle in self.obstacles:
            screen_x = obstacle.x - self.camera_x
            
            if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
                continue
            
            # Shopping cart
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
        
        if player_position == 1:
            title = self.font.render("YOU WON!", True, YELLOW)
            subtitle = self.small_font.render("First to the checkout! Those boomers didn't stand a chance!", True, GREEN)
        elif player_position <= 3:
            title = self.font.render("PODIUM FINISH!", True, ORANGE)
            subtitle = self.small_font.render(f"You got {player_position}{'st' if player_position==2 else 'rd'} place! Not bad!", True, LIGHT_BLUE)
        else:
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
