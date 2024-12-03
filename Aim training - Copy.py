import pygame
import random
import math

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1540
SCREEN_HEIGHT = 820
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aim Training")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

pygame.mixer.music.load('background_music.mp3')
shotgun_sound = pygame.mixer.Sound('shotgun_fire.wav')
headshot_sound = pygame.mixer.Sound('headshot.wav')

pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

shotgun_sound.set_volume(0.5)
headshot_sound.set_volume(0.7)

background_img = pygame.image.load('background.png')  # Load the background image
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to fit the screen

def load_image(path, scale=None):
    try:
        image = pygame.image.load(path)
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except pygame.error:
        return pygame.Surface(scale or (50, 50))

shotgun_center = load_image('shotgun_center.png', (300, 100))
shotgun_right = load_image('shotgun_right.png', (300, 100))
shotgun_left = load_image('shotgun_left.png', (300, 100))
crosshair_img = load_image('crosshair.png', (80, 80))
zombie_frames = [load_image(f'zombie_frame_{i}.png', (100, 140)) for i in range(1, 14)]
zombie_death_frames = [load_image(f'zombie_death_{i}.png', (100, 140)) for i in range(1, 6)]
bullet_img = load_image('bullet.png', (20, 10))

gun_x = SCREEN_WIDTH // 2.25
gun_y = SCREEN_HEIGHT - 100
bullets = []
bullet_speed = 25
shot_cooldown = 300
last_shot_time = 0

zombie_speed = 5
zombies = []
zombies_flew = 0
score = 0

font = pygame.font.SysFont('Arial', 28)
game_over_font = pygame.font.SysFont('Arial', 50)
headshot_text = ""
headshot_timer = 0

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        self.vx = (dx / distance) * bullet_speed
        self.vy = (dy / distance) * bullet_speed

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def off_screen(self):
        return self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT

    def draw(self):
        screen.blit(bullet_img, (self.x, self.y))

class Zombie:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.frame_index = 0
        self.death_frame_index = 0
        self.is_dying = False
        self.last_frame_time = pygame.time.get_ticks()

    def move(self):
        if not self.is_dying:
            self.x += self.direction * zombie_speed
            if pygame.time.get_ticks() - self.last_frame_time > 100:
                self.frame_index = (self.frame_index + 1) % len(zombie_frames)
                self.last_frame_time = pygame.time.get_ticks()

    def draw(self):
        if self.is_dying:
            screen.blit(zombie_death_frames[self.death_frame_index], (self.x, self.y))
        else:
            screen.blit(zombie_frames[self.frame_index], (self.x, self.y))

    def collides_with(self, bullet):
        if (self.x < bullet.x < self.x + 100) and (self.y < bullet.y < self.y + 140):
            if bullet.y < self.y + 70:
                return True, 'head'
            else:
                return True, 'body'
        return False, ''

    def die(self):
        self.is_dying = True
        self.death_frame_index = 0
        self.last_frame_time = pygame.time.get_ticks()

    def update_death(self):
        if self.is_dying and pygame.time.get_ticks() - self.last_frame_time > 150:
            self.death_frame_index += 1
            self.last_frame_time = pygame.time.get_ticks()
            if self.death_frame_index >= len(zombie_death_frames):
                return True
        return False

def spawn_zombies():
    count = 1
    if score >= 15:
        count = 3
    elif score >= 10:
        count = 2
    for _ in range(count):
        direction = random.choice([-1, 1])
        x = 0 if direction == 1 else SCREEN_WIDTH - 100
        y = random.randint(SCREEN_HEIGHT // 3, SCREEN_HEIGHT // 2)
        zombies.append(Zombie(x, y, direction))

running = True
game_over = False
clock = pygame.time.Clock()

while running:
    screen.blit(background_img, (0, 0))

    if game_over:
        game_over_text = game_over_font.render("You have lost! 5+ zombies escaped", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        pygame.display.flip()
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if score >= 20:
        zombie_speed = 10
    elif score >= 15:
        zombie_speed = 8
    elif score >= 10:
        zombie_speed = 6

    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - SCREEN_WIDTH // 2

    if abs(dx) < SCREEN_WIDTH // 10:
        current_shotgun = shotgun_center
    elif dx > 0:
        current_shotgun = shotgun_right
    else:
        current_shotgun = shotgun_left

    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE] and pygame.time.get_ticks() - last_shot_time > shot_cooldown:
        last_shot_time = pygame.time.get_ticks()
        shotgun_sound.play()
        bullets.append(Bullet(gun_x + 150, gun_y, mouse_x, mouse_y))

    for bullet in bullets[:]:
        bullet.move()
        if bullet.off_screen():
            bullets.remove(bullet)
        for zombie in zombies[:]:
            if zombie.is_dying:
                continue
            collision, hit_area = zombie.collides_with(bullet)
            if collision:
                bullets.remove(bullet)
                if hit_area == 'head':
                    score += 2
                    headshot_text = "+2 Headshot"
                    headshot_sound.play()
                elif hit_area == 'body':
                    score += 1
                    
                headshot_timer = pygame.time.get_ticks()
                zombie.die()
                break

    for zombie in zombies[:]:
        if zombie.is_dying:
            if zombie.update_death():
                zombies.remove(zombie)
        else:
            zombie.move()
            if zombie.x < -100 or zombie.x > SCREEN_WIDTH + 100:
                zombies.remove(zombie)
                zombies_flew += 1
                if zombies_flew > 5:
                    game_over = True

    if not zombies:
        spawn_zombies()

    for zombie in zombies:
        zombie.draw()
    for bullet in bullets:
        bullet.draw()
    screen.blit(current_shotgun, (gun_x, gun_y))
    screen.blit(crosshair_img, (mouse_x - 40, mouse_y - 40))

    score_text = font.render(f"Score: {score}", True, BLACK)
    zombies_flew_text = font.render(f"Zombies Escaped: {zombies_flew}", True, RED)
    screen.blit(score_text, (10, 10))
    screen.blit(zombies_flew_text, (SCREEN_WIDTH - zombies_flew_text.get_width() - 10, 10))

    if headshot_text and pygame.time.get_ticks() - headshot_timer < 1000:
        headshot_label = font.render(headshot_text, True, YELLOW)
        screen.blit(headshot_label, (SCREEN_WIDTH // 2 - headshot_label.get_width() // 2, SCREEN_HEIGHT // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
