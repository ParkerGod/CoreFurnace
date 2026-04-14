# -*- coding: utf-8 -*-
import pygame
import math
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.42

class GameData:
    def __init__(self):
        self.score = 0
        self.heat = 100
        self.max_heat = 100
        self.fuel = 50
        self.max_fuel = 100
        self.game_over = False
        self.scroll_offset = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data
        self.radius = 25
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 140, 0), (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 100
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.speed = 5
        self.jump_power = 14

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_a]:
            self.vel_x = -self.speed
        if keys[pygame.K_d]:
            self.vel_x = self.speed

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False

        self.vel_y += GRAVITY
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom + 20:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, game_data):
        super().__init__()
        self.game_data = game_data
        self.image = pygame.Surface((width, height))
        self.image.fill((60, 60, 60))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.base_y = y

    def update(self):
        self.rect.y = self.base_y + self.game_data.scroll_offset

class MapManager:
    def __init__(self, game_data, fuel_packs_group):
        self.game_data = game_data
        self.platforms = pygame.sprite.Group()
        self.fuel_packs_group = fuel_packs_group
        self.last_platform_y = SCREEN_HEIGHT - 50
        self.generate_initial_platforms()

    def generate_initial_platforms(self):
        self.platforms.add(Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, self.game_data))
        for i in range(8):
            self.add_platform(self.last_platform_y - random.randint(60, 90))

    def add_platform(self, y):
        width = random.randint(100, 200)
        x = random.randint(0, SCREEN_WIDTH - width)
        platform = Platform(x, y, width, 20, self.game_data)
        self.platforms.add(platform)
        self.last_platform_y = y
        if random.random() < 0.35:
            fuel_x = x + width // 2
            fuel_y = y - 25
            self.fuel_packs_group.add(FuelPack(fuel_x, fuel_y, self.game_data))

    def update(self, player):
        if player.rect.centery < SCREEN_HEIGHT // 3:
            scroll_amount = (SCREEN_HEIGHT // 3 - player.rect.centery)
            self.game_data.scroll_offset += scroll_amount
            player.rect.y += scroll_amount

        self.platforms.update()

        while self.last_platform_y + self.game_data.scroll_offset > -100:
            self.add_platform(self.last_platform_y - random.randint(60, 90))

        for platform in self.platforms:
            if platform.rect.top > SCREEN_HEIGHT + 100:
                platform.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((15, 8))
        self.image.fill((255, 220, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        angle = math.atan2(target_y - y, target_x - x)
        self.speed = 12
        self.vel_x = math.cos(angle) * self.speed
        self.vel_y = math.sin(angle) * self.speed

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()

class Crawler(pygame.sprite.Sprite):
    def __init__(self, platform, game_data):
        super().__init__()
        self.game_data = game_data
        self.image = pygame.Surface((30, 30))
        self.image.fill((220, 40, 40))
        self.rect = self.image.get_rect()
        self.platform = platform
        self.rect.bottom = platform.rect.top
        self.rect.x = platform.rect.x
        self.direction = 1
        self.speed = 2

    def update(self):
        self.rect.y = self.platform.rect.top - 30
        self.rect.x += self.direction * self.speed
        if self.rect.left <= self.platform.rect.left:
            self.direction = 1
        if self.rect.right >= self.platform.rect.right:
            self.direction = -1

class Ghost(pygame.sprite.Sprite):
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data
        self.image = pygame.Surface((25, 25), pygame.SRCALPHA)
        self.image.fill((180, 80, 180, 180))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - 25)
        self.rect.y = -50
        self.speed = 3

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT + 50:
            self.kill()

class Ember(pygame.sprite.Sprite):
    def __init__(self, x, y, game_data):
        super().__init__()
        self.game_data = game_data
        self.size = 12
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.angle = 0
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update_image(self):
        self.image.fill((0, 0, 0, 0))
        center = self.size
        points = [
            (center, center - self.size),
            (center + self.size, center),
            (center, center + self.size),
            (center - self.size, center)
        ]
        rotated = []
        cos_a = math.cos(math.radians(self.angle))
        sin_a = math.sin(math.radians(self.angle))
        for x, y in points:
            rx = (x - center) * cos_a - (y - center) * sin_a + center
            ry = (x - center) * sin_a + (y - center) * cos_a + center
            rotated.append((rx, ry))
        pygame.draw.polygon(self.image, (255, 200, 0), rotated)

    def update(self):
        self.angle += 3
        self.update_image()

class FuelPack(pygame.sprite.Sprite):
    def __init__(self, x, y, game_data):
        super().__init__()
        self.game_data = game_data
        self.size = 15
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (0, 160, 255), (0, 0, self.size * 2, self.size * 2))
        pygame.draw.rect(self.image, (0, 220, 255), (4, 4, self.size * 2 - 8, self.size * 2 - 8))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.base_y = y

    def update(self):
        self.rect.y = self.base_y + self.game_data.scroll_offset
        if self.rect.top > SCREEN_HEIGHT + 100:
            self.kill()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Core Furnace")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.chinese_font = pygame.font.SysFont("microsoftyahei", 48)
        self.reset_game()

    def reset_game(self):
        self.game_data = GameData()
        self.player = Player(self.game_data)
        self.fuel_packs = pygame.sprite.Group()
        self.map_manager = MapManager(self.game_data, self.fuel_packs)
        self.projectiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.embers = pygame.sprite.Group()
        self.enemy_spawn_timer = 0
        self.ghost_spawn_timer = 0
        self.ember_spawn_timer = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_data.game_over:
                    self.reset_game()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_data.game_over:
                if event.button == 1:
                    if self.game_data.fuel >= 10:
                        self.game_data.fuel -= 10
                        mx, my = pygame.mouse.get_pos()
                        proj = Projectile(self.player.rect.centerx, self.player.rect.centery, mx, my)
                        self.projectiles.add(proj)
        return True

    def spawn_enemies(self):
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= 180:
            self.enemy_spawn_timer = 0
            platforms = list(self.map_manager.platforms.sprites())
            if len(platforms) > 2:
                platform = random.choice(platforms[1:])
                if platform.rect.bottom < SCREEN_HEIGHT:
                    crawler = Crawler(platform, self.game_data)
                    self.enemies.add(crawler)

        self.ghost_spawn_timer += 1
        if self.ghost_spawn_timer >= 120:
            self.ghost_spawn_timer = 0
            ghost = Ghost(self.game_data)
            self.enemies.add(ghost)

    def spawn_embers(self):
        self.ember_spawn_timer += 1
        if self.ember_spawn_timer >= 90:
            self.ember_spawn_timer = 0
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(-100, 0)
            ember = Ember(x, y, self.game_data)
            self.embers.add(ember)

    def check_collisions(self):
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, True):
            self.game_data.heat -= 20

        for proj in self.projectiles:
            for enemy in pygame.sprite.spritecollide(proj, self.enemies, True):
                proj.kill()

        for ember in pygame.sprite.spritecollide(self.player, self.embers, True):
            self.game_data.score += 50
            self.game_data.fuel = min(self.game_data.fuel + 10, self.game_data.max_fuel)

        for fuel_pack in pygame.sprite.spritecollide(self.player, self.fuel_packs, True):
            self.game_data.fuel = min(self.game_data.fuel + 25, self.game_data.max_fuel)

    def check_game_over(self):
        if self.player.rect.top > SCREEN_HEIGHT or self.game_data.heat <= 0:
            self.game_data.game_over = True

    def draw_ui(self):
        pygame.draw.rect(self.screen, (100, 100, 100), (20, 20, 200, 20))
        heat_width = (self.game_data.heat / self.game_data.max_heat) * 200
        pygame.draw.rect(self.screen, (255, 100, 0), (20, 20, heat_width, 20))
        heat_text = self.font.render("Heat", True, (255, 255, 255))
        self.screen.blit(heat_text, (20, 45))

        pygame.draw.rect(self.screen, (100, 100, 100), (20, 70, 200, 20))
        fuel_width = (self.game_data.fuel / self.game_data.max_fuel) * 200
        pygame.draw.rect(self.screen, (0, 180, 255), (20, 70, fuel_width, 20))
        fuel_text = self.font.render("Fuel", True, (255, 255, 255))
        self.screen.blit(fuel_text, (20, 95))

        score_text = self.font.render(f"Score: {self.game_data.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (SCREEN_WIDTH - 150, 20))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.chinese_font.render("游戏结束", True, (255, 50, 50))
        score_text = self.chinese_font.render(f"最终得分: {self.game_data.score}", True, (255, 255, 255))
        restart_text = self.chinese_font.render("按 R 键重新开始", True, (200, 200, 200))

        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 200))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 280))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 340))

    def update(self):
        if not self.game_data.game_over:
            self.player.update(self.map_manager.platforms)
            self.map_manager.update(self.player)
            self.projectiles.update()
            self.enemies.update()
            self.embers.update()
            self.fuel_packs.update()
            self.spawn_enemies()
            self.spawn_embers()
            self.check_collisions()
            self.check_game_over()

    def draw(self):
        self.screen.fill((20, 20, 30))
        self.map_manager.platforms.draw(self.screen)
        self.fuel_packs.draw(self.screen)
        self.embers.draw(self.screen)
        self.enemies.draw(self.screen)
        self.projectiles.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_ui()
        if self.game_data.game_over:
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
