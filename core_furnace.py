import pygame
import random
import math
from enum import Enum

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PLAYER = (255, 140, 0)  # 橙色
COLOR_PLATFORM = (60, 60, 70)  # 深灰色
COLOR_CRAWLER = (220, 50, 50)  # 红色
COLOR_GHOST = (150, 50, 200, 180)  # 半透明紫色
COLOR_FIRE = (255, 220, 50)  # 黄色火焰
COLOR_EMBER = (255, 200, 80)  # 余烬黄色
COLOR_HEAT_BAR = (255, 80, 40)  # 热量条颜色
COLOR_FUEL_BAR = (50, 150, 255)  # 燃料条颜色
COLOR_TEXT = (255, 255, 255)  # 白色文字

# 游戏状态枚举
class GameState(Enum):
    RUNNING = 1
    GAME_OVER = 2


class GameData:
    """存储所有游戏状态的类"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.score = 0
        self.heat = 100
        self.max_heat = 100
        self.fuel = 50
        self.max_fuel = 100
        self.camera_y = 0  # 相机Y偏移
        self.highest_y = SCREEN_HEIGHT  # 玩家达到的最高位置（Y坐标越小越高）


class Platform(pygame.sprite.Sprite):
    """平台类 - 深灰色矩形"""
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(COLOR_PLATFORM)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Player(pygame.sprite.Sprite):
    """玩家类 - 核心熔炉（橙色圆形）"""
    def __init__(self, x, y):
        super().__init__()
        self.radius = 20
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLOR_PLAYER, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # 物理属性
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 6
        self.jump_power = -14
        self.gravity = 0.4
        self.on_ground = False
    
    def update(self, platforms):
        # 获取按键状态
        keys = pygame.key.get_pressed()
        
        # 左右移动
        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        
        # 跳跃（只有在接触平台时才能跳）
        if (keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
        
        # 应用重力
        self.vel_y += self.gravity
        
        # 更新水平位置
        self.rect.x += self.vel_x
        
        # 水平碰撞检测
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right
        
        # 更新垂直位置
        self.rect.y += self.vel_y
        self.on_ground = False
        
        # 垂直碰撞检测
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
        
        # 屏幕边界限制
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH


class FireProjectile(pygame.sprite.Sprite):
    """火焰投射物 - 黄色矩形"""
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.width = 12
        self.height = 6
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(COLOR_FIRE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # 计算方向
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            self.vel_x = (dx / distance) * 10
            self.vel_y = (dy / distance) * 10
        else:
            self.vel_x = 10
            self.vel_y = 0
    
    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        # 移除超出屏幕的火焰
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class Crawler(pygame.sprite.Sprite):
    """爬行敌人 - 红色方块，在平台上移动"""
    def __init__(self, platform):
        super().__init__()
        self.size = 24
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(COLOR_CRAWLER)
        self.rect = self.image.get_rect()
        
        self.platform = platform
        self.rect.midbottom = platform.rect.midtop
        
        self.speed = 2
        self.direction = random.choice([-1, 1])
    
    def update(self):
        self.rect.x += self.speed * self.direction
        
        # 在平台边缘转向
        if self.rect.left <= self.platform.rect.left:
            self.direction = 1
            self.rect.left = self.platform.rect.left
        elif self.rect.right >= self.platform.rect.right:
            self.direction = -1
            self.rect.right = self.platform.rect.right


class Ghost(pygame.sprite.Sprite):
    """幽灵敌人 - 半透明紫色方块，从顶部下落"""
    def __init__(self, x, y):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image.fill(COLOR_GHOST)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.speed = 3
    
    def update(self):
        self.rect.y += self.speed


class Ember(pygame.sprite.Sprite):
    """余烬 - 旋转的黄色小菱形，收集后加分"""
    def __init__(self, x, y):
        super().__init__()
        self.size = 16
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        self.angle = 0
        self.rotation_speed = 5
    
    def update(self):
        self.angle += self.rotation_speed
        # 绘制旋转的菱形
        self.image.fill((0, 0, 0, 0))
        points = []
        for i in range(4):
            rad = math.radians(self.angle + i * 90)
            px = self.size // 2 + math.cos(rad) * (self.size // 2 - 2)
            py = self.size // 2 + math.sin(rad) * (self.size // 2 - 2)
            points.append((px, py))
        pygame.draw.polygon(self.image, COLOR_EMBER, points)


class MapManager:
    """地图管理器 - 程序化生成向上延伸的关卡"""
    def __init__(self):
        self.platforms = pygame.sprite.Group()
        self.highest_platform_y = SCREEN_HEIGHT
        self.generate_initial_platforms()
    
    def reset(self):
        self.platforms.empty()
        self.highest_platform_y = SCREEN_HEIGHT
        self.generate_initial_platforms()
    
    def generate_initial_platforms(self):
        # 生成底部平台
        ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
        self.platforms.add(ground)
        
        # 生成初始平台
        for i in range(5):
            self.generate_platform()
    
    def generate_platform(self):
        width = random.randint(120, 220)
        # 确保平台在水平方向上有一定重叠，让玩家更容易跳上去
        prev_platform = None
        for p in self.platforms:
            if p.rect.y == self.highest_platform_y:
                prev_platform = p
                break
        
        if prev_platform:
            # 新平台在水平方向上靠近前一个平台
            min_x = max(0, prev_platform.rect.centerx - 200)
            max_x = min(SCREEN_WIDTH - width, prev_platform.rect.centerx + 200 - width)
            x = random.randint(int(min_x), int(max_x))
        else:
            x = random.randint(50, SCREEN_WIDTH - width - 50)
        
        # 减小垂直间距，让跳跃更容易
        y = self.highest_platform_y - random.randint(60, 100)
        
        platform = Platform(x, y, width, 15)
        self.platforms.add(platform)
        self.highest_platform_y = y
        
        return platform
    
    def update(self, player, camera_y, enemies, embers):
        # 当玩家接近屏幕顶部时生成新平台
        # camera_y是负值，表示相机向上移动的距离
        player_screen_y = player.rect.centery - camera_y
        
        # 当玩家到达屏幕上半部分时生成新平台
        if player_screen_y < SCREEN_HEIGHT * 0.6:
            # 生成新平台，直到高出相机视野200像素
            while self.highest_platform_y > camera_y - 200:
                platform = self.generate_platform()
                
                # 随机生成敌人或余烬
                if random.random() < 0.4:
                    if random.random() < 0.5:
                        crawler = Crawler(platform)
                        enemies.add(crawler)
                    else:
                        ghost = Ghost(random.randint(0, SCREEN_WIDTH - 30), camera_y - 50)
                        enemies.add(ghost)
                
                # 随机生成余烬（燃料补充）
                if random.random() < 0.3:
                    ember = Ember(platform.rect.centerx, platform.rect.top - 25)
                    embers.add(ember)
        
        # 移除屏幕底部的旧平台
        for platform in self.platforms:
            if platform.rect.top > camera_y + SCREEN_HEIGHT + 100:
                platform.kill()


class Game:
    """游戏主类 - 管理主循环、事件处理和状态切换"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CoreFurnace - 核心熔炉")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 24)
        self.font_large = pygame.font.SysFont("simhei", 48)
        
        self.game_data = GameData()
        self.state = GameState.RUNNING
        
        self.reset_game()
    
    def reset_game(self):
        """重置游戏状态"""
        self.game_data.reset()
        
        # 创建玩家（位于屏幕下半部分）
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        
        # 创建地图管理器
        self.map_manager = MapManager()
        
        # 创建精灵组
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.embers = pygame.sprite.Group()
        
        self.state = GameState.RUNNING
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                    self.reset_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.state == GameState.RUNNING:
                    self.fire_projectile()
        
        return True
    
    def fire_projectile(self):
        """发射火焰投射物"""
        if self.game_data.fuel >= 10:
            self.game_data.fuel -= 10
            mouse_x, mouse_y = pygame.mouse.get_pos()
            fire = FireProjectile(self.player.rect.centerx, self.player.rect.centery, 
                                  mouse_x, mouse_y + self.game_data.camera_y)
            self.projectiles.add(fire)
    
    def update(self):
        if self.state != GameState.RUNNING:
            return
        
        # 更新玩家
        self.map_manager.platforms.update()
        self.player.update(self.map_manager.platforms)
        
        # 更新相机位置 - 当玩家向上移动时，相机跟随
        target_camera_y = self.player.rect.centery - SCREEN_HEIGHT * 0.7
        if target_camera_y < self.game_data.camera_y:
            self.game_data.camera_y = target_camera_y
        
        # 更新地图
        self.map_manager.update(self.player, self.game_data.camera_y, 
                                self.enemies, self.embers)
        
        # 更新敌人
        self.enemies.update()
        
        # 更新投射物
        self.projectiles.update()
        
        # 更新余烬
        self.embers.update()
        
        # 移除超出屏幕的敌人
        for enemy in self.enemies:
            if enemy.rect.top > self.game_data.camera_y + SCREEN_HEIGHT + 100:
                enemy.kill()
        
        # 移除超出屏幕的余烬
        for ember in self.embers:
            if ember.rect.top > self.game_data.camera_y + SCREEN_HEIGHT + 100:
                ember.kill()
        
        # 碰撞检测
        self.check_collisions()
        
        # 检查游戏结束条件
        self.check_game_over()
    
    def check_collisions(self):
        # 玩家与敌人碰撞
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.game_data.heat -= 20
            enemy.kill()
        
        # 火焰与敌人碰撞
        for projectile in self.projectiles:
            hit_enemies = pygame.sprite.spritecollide(projectile, self.enemies, True)
            if hit_enemies:
                projectile.kill()
                self.game_data.score += 10
        
        # 玩家与余烬碰撞
        for ember in pygame.sprite.spritecollide(self.player, self.embers, True):
            self.game_data.score += 50
            # 收集余烬补充燃料
            self.game_data.fuel = min(self.game_data.max_fuel, self.game_data.fuel + 15)
    
    def check_game_over(self):
        # 掉出屏幕底部（考虑相机偏移）
        player_screen_y = self.player.rect.centery - self.game_data.camera_y
        if player_screen_y > SCREEN_HEIGHT + 100:
            self.state = GameState.GAME_OVER
        
        # 热量耗尽
        if self.game_data.heat <= 0:
            self.game_data.heat = 0
            self.state = GameState.GAME_OVER
    
    def draw(self):
        self.screen.fill(COLOR_BACKGROUND)
        
        # 计算绘制偏移
        offset_y = -self.game_data.camera_y
        
        # 绘制平台
        for platform in self.map_manager.platforms:
            screen_rect = platform.rect.copy()
            screen_rect.y += offset_y
            if -50 < screen_rect.y < SCREEN_HEIGHT + 50:
                self.screen.blit(platform.image, screen_rect)
        
        # 绘制敌人
        for enemy in self.enemies:
            screen_rect = enemy.rect.copy()
            screen_rect.y += offset_y
            if -50 < screen_rect.y < SCREEN_HEIGHT + 50:
                self.screen.blit(enemy.image, screen_rect)
        
        # 绘制余烬
        for ember in self.embers:
            screen_rect = ember.rect.copy()
            screen_rect.y += offset_y
            if -50 < screen_rect.y < SCREEN_HEIGHT + 50:
                self.screen.blit(ember.image, screen_rect)
        
        # 绘制投射物
        for projectile in self.projectiles:
            screen_rect = projectile.rect.copy()
            screen_rect.y += offset_y
            if -50 < screen_rect.y < SCREEN_HEIGHT + 50:
                self.screen.blit(projectile.image, screen_rect)
        
        # 绘制玩家
        player_screen_rect = self.player.rect.copy()
        player_screen_rect.y += offset_y
        self.screen.blit(self.player.image, player_screen_rect)
        
        # 绘制UI
        self.draw_ui()
        
        # 绘制游戏结束画面
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_ui(self):
        # 热量条
        heat_width = 150
        heat_height = 20
        heat_x = 10
        heat_y = 10
        
        pygame.draw.rect(self.screen, (50, 50, 50), (heat_x, heat_y, heat_width, heat_height))
        current_heat_width = int(heat_width * (self.game_data.heat / self.game_data.max_heat))
        pygame.draw.rect(self.screen, COLOR_HEAT_BAR, (heat_x, heat_y, current_heat_width, heat_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (heat_x, heat_y, heat_width, heat_height), 2)
        
        heat_text = self.font.render(f"热量: {self.game_data.heat}/{self.game_data.max_heat}", 
                                     True, COLOR_TEXT)
        self.screen.blit(heat_text, (heat_x + heat_width + 10, heat_y - 2))
        
        # 燃料条
        fuel_width = 150
        fuel_height = 20
        fuel_x = 10
        fuel_y = 40
        
        pygame.draw.rect(self.screen, (50, 50, 50), (fuel_x, fuel_y, fuel_width, fuel_height))
        current_fuel_width = int(fuel_width * (self.game_data.fuel / self.game_data.max_fuel))
        pygame.draw.rect(self.screen, COLOR_FUEL_BAR, (fuel_x, fuel_y, current_fuel_width, fuel_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (fuel_x, fuel_y, fuel_width, fuel_height), 2)
        
        fuel_text = self.font.render(f"燃料: {self.game_data.fuel}/{self.game_data.max_fuel}", 
                                     True, COLOR_TEXT)
        self.screen.blit(fuel_text, (fuel_x + fuel_width + 10, fuel_y - 2))
        
        # 分数
        score_text = self.font.render(f"分数: {self.game_data.score}", True, COLOR_TEXT)
        self.screen.blit(score_text, (SCREEN_WIDTH - 150, 10))
    
    def draw_game_over(self):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束文字
        game_over_text = self.font_large.render("游戏结束", True, (255, 80, 80))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        # 最终得分
        score_text = self.font.render(f"最终得分: {self.game_data.score}", True, COLOR_TEXT)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(score_text, score_rect)
        
        # 重新开始提示
        restart_text = self.font.render("按 R 键重新开始", True, (150, 255, 150))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(restart_text, restart_rect)
    
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
