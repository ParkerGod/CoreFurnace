# -*- coding: utf-8 -*-
import pygame
import math
import random
from enum import Enum

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

COLOR_ORANGE = (255, 140, 0)
COLOR_DARK_GRAY = (80, 80, 80)
COLOR_RED = (220, 50, 50)
COLOR_PURPLE = (150, 50, 200)
COLOR_YELLOW = (255, 220, 50)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_HEAT = (255, 100, 50)
COLOR_FUEL = (50, 150, 255)
COLOR_BG = (30, 30, 40)


class GameState(Enum):
    RUNNING = 1
    GAME_OVER = 2


class GameData:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.score = 0
        self.heat = 100
        self.max_heat = 100
        self.fuel = 50
        self.max_fuel = 100
        self.state = GameState.RUNNING
        self.camera_y = 0
        self.highest_y = 0


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height=20):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(COLOR_DARK_GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = width
        self.height = height
    
    def update_position(self, dy):
        self.rect.y += dy


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.radius = 20
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLOR_ORANGE, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.x = float(x)
        self.y = float(y)
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.jump_power = -12
        self.gravity = 0.5
        self.on_ground = False
        self.ground_platform = None
    
    def update(self, platforms):
        keys = pygame.key.get_pressed()
        
        self.vx = 0
        if keys[pygame.K_a]:
            self.vx = -self.speed
        if keys[pygame.K_d]:
            self.vx = self.speed
        
        if keys[pygame.K_w] or keys[pygame.K_SPACE]:
            if self.on_ground:
                self.vy = self.jump_power
                self.on_ground = False
                self.ground_platform = None
        
        self.vy += self.gravity
        if self.vy > 15:
            self.vy = 15
        
        self.x += self.vx
        self.rect.centerx = int(self.x)
        
        if self.rect.left < 0:
            self.rect.left = 0
            self.x = float(self.rect.centerx)
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.x = float(self.rect.centerx)
        
        self.y += self.vy
        self.rect.centery = int(self.y)
        
        self.on_ground = False
        self.ground_platform = None
        
        for platform in platforms:
            if self.vy >= 0:
                player_bottom = self.rect.bottom
                player_prev_bottom = player_bottom - self.vy
                platform_top = platform.rect.top
                
                if (self.rect.right > platform.rect.left and 
                    self.rect.left < platform.rect.right):
                    if player_prev_bottom <= platform_top <= player_bottom:
                        self.rect.bottom = platform_top
                        self.y = float(self.rect.centery)
                        self.vy = 0
                        self.on_ground = True
                        self.ground_platform = platform
                        break
    
    def update_position(self, dy):
        self.y += dy
        self.rect.centery = int(self.y)


class Flame(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.width = 15
        self.height = 8
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(COLOR_YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            self.vx = (dx / distance) * 12
            self.vy = (dy / distance) * 12
        else:
            self.vx = 12
            self.vy = 0
    
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class Crawler(pygame.sprite.Sprite):
    def __init__(self, x, y, platform):
        super().__init__()
        self.size = 25
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(COLOR_RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y
        self.platform = platform
        self.speed = 2
        self.direction = random.choice([-1, 1])
    
    def update(self):
        self.rect.x += self.speed * self.direction
        
        if self.platform:
            if self.rect.left <= self.platform.rect.left:
                self.rect.left = self.platform.rect.left
                self.direction = 1
            elif self.rect.right >= self.platform.rect.right:
                self.rect.right = self.platform.rect.right
                self.direction = -1
    
    def update_position(self, dy):
        self.rect.y += dy


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        ghost_color = (150, 50, 200, 180)
        pygame.draw.rect(self.image, ghost_color, (0, 0, self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = 3
    
    def update(self):
        self.rect.y += self.speed
    
    def update_position(self, dy):
        self.rect.y += dy


class Ember(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 12
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.original_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(self.original_image, COLOR_YELLOW, [
            (self.size // 2, 0),
            (self.size, self.size // 2),
            (self.size // 2, self.size),
            (0, self.size // 2)
        ])
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.angle = 0
        self.rotation_speed = 5
    
    def update(self):
        self.angle += self.rotation_speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def update_position(self, dy):
        self.rect.y += dy


class MapManager:
    def __init__(self, game):
        self.game = game
        self.platforms = pygame.sprite.Group()
        self.platform_spawn_y = SCREEN_HEIGHT - 50
        self.min_gap = 50
        self.max_gap = 90
        self.min_width = 120
        self.max_width = 280
        self.last_platform_x = SCREEN_WIDTH // 2 - 100
        self.last_platform_width = 200
    
    def generate_initial(self):
        platform = Platform(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50, 200)
        self.platforms.add(platform)
        self.game.all_sprites.add(platform)
        self.last_platform_x = SCREEN_WIDTH // 2 - 100
        self.last_platform_width = 200
        
        y = SCREEN_HEIGHT - 50
        for i in range(8):
            y -= random.randint(self.min_gap, self.max_gap)
            width = random.randint(self.min_width, self.max_width)
            x = self._get_valid_platform_x(width)
            platform = Platform(x, y, width)
            self.platforms.add(platform)
            self.game.all_sprites.add(platform)
            self.last_platform_x = x
            self.last_platform_width = width
            
            if random.random() < 0.4:
                crawler = Crawler(x + random.randint(10, width - 35), y, platform)
                self.game.enemies.add(crawler)
                self.game.all_sprites.add(crawler)
            
            if random.random() < 0.2:
                ember = Ember(x + width // 2, y - 20)
                self.game.embers.add(ember)
                self.game.all_sprites.add(ember)
        
        self.platform_spawn_y = y
    
    def _get_valid_platform_x(self, width):
        last_center = self.last_platform_x + self.last_platform_width // 2
        max_jump_distance = 200
        min_x = max(0, last_center - max_jump_distance - width // 2)
        max_x = min(SCREEN_WIDTH - width, last_center + max_jump_distance - width // 2)
        if min_x >= max_x:
            min_x = 0
            max_x = SCREEN_WIDTH - width
        return random.randint(int(min_x), int(max_x))
    
    def update(self, player):
        if player.rect.top < SCREEN_HEIGHT // 3:
            scroll_amount = SCREEN_HEIGHT // 3 - player.rect.top
            
            for sprite in self.game.all_sprites:
                if hasattr(sprite, 'update_position'):
                    sprite.update_position(scroll_amount)
            
            self.game.data.camera_y += scroll_amount
            
            while self.platform_spawn_y > player.rect.top - SCREEN_HEIGHT:
                self.platform_spawn_y -= random.randint(self.min_gap, self.max_gap)
                width = random.randint(self.min_width, self.max_width)
                x = self._get_valid_platform_x(width)
                platform = Platform(x, self.platform_spawn_y, width)
                self.platforms.add(platform)
                self.game.all_sprites.add(platform)
                self.last_platform_x = x
                self.last_platform_width = width
                
                if random.random() < 0.5:
                    crawler = Crawler(x + random.randint(10, width - 35), self.platform_spawn_y, platform)
                    self.game.enemies.add(crawler)
                    self.game.all_sprites.add(crawler)
                
                if random.random() < 0.25:
                    ember = Ember(x + width // 2, self.platform_spawn_y - 20)
                    self.game.embers.add(ember)
                    self.game.all_sprites.add(ember)
            
            self.cleanup_offscreen()
    
    def cleanup_offscreen(self):
        for platform in self.platforms:
            if platform.rect.top > SCREEN_HEIGHT + 50:
                platform.kill()
        
        for enemy in self.game.enemies:
            if enemy.rect.top > SCREEN_HEIGHT + 50:
                enemy.kill()
        
        for ember in self.game.embers:
            if ember.rect.top > SCREEN_HEIGHT + 50:
                ember.kill()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CoreFurnace")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
        self.data = GameData()
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.flames = pygame.sprite.Group()
        self.embers = pygame.sprite.Group()
        
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.all_sprites.add(self.player)
        
        self.map_manager = MapManager(self)
        self.map_manager.generate_initial()
        
        self.ghost_spawn_timer = 0
        self.ghost_spawn_interval = 180
        
        self.fuel_regen_timer = 0
        self.fuel_regen_interval = 30
    
    def reset(self):
        self.data.reset()
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.flames.empty()
        self.embers.empty()
        
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.all_sprites.add(self.player)
        
        self.map_manager = MapManager(self)
        self.map_manager.generate_initial()
        
        self.ghost_spawn_timer = 0
        self.fuel_regen_timer = 0
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.data.state == GameState.RUNNING:
                    if self.data.fuel >= 10:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        flame = Flame(self.player.rect.centerx, self.player.rect.centery,
                                     mouse_x, mouse_y)
                        self.flames.add(flame)
                        self.all_sprites.add(flame)
                        self.data.fuel -= 10
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.data.state == GameState.GAME_OVER:
                    self.reset()
        
        return True
    
    def spawn_ghost(self):
        x = random.randint(30, SCREEN_WIDTH - 30)
        ghost = Ghost(x, -30)
        self.enemies.add(ghost)
        self.all_sprites.add(ghost)
    
    def update(self):
        if self.data.state != GameState.RUNNING:
            return
        
        self.player.update(self.map_manager.platforms)
        self.map_manager.update(self.player)
        
        self.flames.update()
        self.enemies.update()
        self.embers.update()
        
        self.ghost_spawn_timer += 1
        if self.ghost_spawn_timer >= self.ghost_spawn_interval:
            self.ghost_spawn_timer = 0
            self.spawn_ghost()
        
        self.fuel_regen_timer += 1
        if self.fuel_regen_timer >= self.fuel_regen_interval:
            self.fuel_regen_timer = 0
            if self.data.fuel < self.data.max_fuel:
                self.data.fuel = min(self.data.fuel + 1, self.data.max_fuel)
        
        self.check_collisions()
        
        if self.player.rect.top > SCREEN_HEIGHT:
            self.data.state = GameState.GAME_OVER
        
        if self.data.heat <= 0:
            self.data.state = GameState.GAME_OVER
        
        current_height = int(self.data.camera_y / 10)
        if current_height > self.data.highest_y:
            self.data.highest_y = current_height
            self.data.score = self.data.highest_y
    
    def check_collisions(self):
        for flame in self.flames:
            hit_enemies = pygame.sprite.spritecollide(flame, self.enemies, True)
            if hit_enemies:
                flame.kill()
        
        hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, True)
        if hit_enemies:
            self.data.heat -= 20 * len(hit_enemies)
        
        hit_embers = pygame.sprite.spritecollide(self.player, self.embers, True)
        for ember in hit_embers:
            self.data.score += 10
    
    def draw_ui(self):
        bar_width = 150
        bar_height = 20
        padding = 10
        
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, 
                        (padding, padding, bar_width + 4, bar_height + 4))
        heat_width = int((self.data.heat / self.data.max_heat) * bar_width)
        pygame.draw.rect(self.screen, COLOR_HEAT, 
                        (padding + 2, padding + 2, heat_width, bar_height))
        
        heat_label = self.small_font.render("Heat", True, COLOR_WHITE)
        self.screen.blit(heat_label, (padding + bar_width + 10, padding + 2))
        
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, 
                        (padding, padding + bar_height + 10, bar_width + 4, bar_height + 4))
        fuel_width = int((self.data.fuel / self.data.max_fuel) * bar_width)
        pygame.draw.rect(self.screen, COLOR_FUEL, 
                        (padding + 2, padding + bar_height + 12, fuel_width, bar_height))
        
        fuel_label = self.small_font.render("Fuel", True, COLOR_WHITE)
        self.screen.blit(fuel_label, (padding + bar_width + 10, padding + bar_height + 12))
        
        score_text = self.font.render(f"Score: {self.data.score}", True, COLOR_WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH - 150, padding))
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, COLOR_RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        score_text = self.font.render(f"Final Score: {self.data.score}", True, COLOR_WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)
        
        restart_text = self.small_font.render("Press R to Restart", True, COLOR_YELLOW)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        self.screen.fill(COLOR_BG)
        self.all_sprites.draw(self.screen)
        self.draw_ui()
        
        if self.data.state == GameState.GAME_OVER:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
