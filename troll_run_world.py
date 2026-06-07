#!/usr/bin/env python3
"""
Troll Run World
A Mario-style side-scrolling endless runner in pure Python + Pygame.
Jump over mushrooms, collect coins, run as far as you can!
"""

import pygame
import random
import math
import os
import json
from array import array

# =============================================================================
# CONFIG
# =============================================================================
WIDTH, HEIGHT = 800, 480
FPS = 60
TITLE = "Troll Run World"

# Colors (bright Mario-inspired palette)
SKY_BLUE = (92, 148, 252)
SKY_TOP = (70, 130, 230)
HILL_DARK = (34, 139, 34)
HILL_LIGHT = (50, 160, 50)
HILL_FAR = (76, 153, 76)
GROUND_GREEN = (76, 175, 80)
GROUND_BROWN = (139, 90, 43)
MUSHROOM_RED = (220, 53, 69)
MUSHROOM_WHITE = (255, 245, 238)
MUSHROOM_STEM = (245, 222, 179)
COIN_GOLD = (255, 200, 40)
COIN_DARK = (180, 140, 20)
TROLL_GREEN = (46, 139, 87)
TROLL_DARK = (34, 85, 51)
TROLL_SKIN = (144, 238, 144)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
UI_GOLD = (255, 215, 0)

# Physics & gameplay
PLAYER_X = 170
GROUND_Y = 385
GRAVITY = 0.82
JUMP_VELOCITY = -15.5
DOUBLE_JUMP_VELOCITY = -13.0
MAX_FALL_SPEED = 14.0
START_SPEED = 3.2
MAX_SPEED = 7.8
SPEED_INCREASE = 0.0008   # per frame while playing

HIGHSCORE_FILE = os.path.join(os.path.expanduser("~"), ".troll_run_highscore.json")

# =============================================================================
# PROCEDURAL SOUND (no external files)
# =============================================================================
def _make_tone(freq, duration_ms, volume=0.5, wave="square"):
    sample_rate = 22050
    n = int(sample_rate * duration_ms / 1000)
    amp = int(32767 * max(0.1, min(1.0, volume)))
    buf = array("h")
    period = sample_rate / max(30, freq)

    for i in range(n):
        t = i / sample_rate
        if wave == "sine":
            val = int(amp * math.sin(2 * math.pi * freq * t))
        elif wave == "saw":
            val = int(amp * (2 * ((t * freq) % 1) - 1))
        else:
            val = amp if (i % int(period)) < (period / 2) else -amp
        fade = 1.0 - (i / max(1, n))
        buf.append(int(val * (0.5 + 0.5 * fade)))

    return pygame.mixer.Sound(buffer=buf.tobytes())


class SoundBank:
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
        except Exception:
            self.enabled = False
            return

        self.jump = _make_tone(520, 140, 0.38, "sine")
        self.double = _make_tone(680, 110, 0.32, "sine")
        self.coin = _make_tone(880, 70, 0.26, "sine")
        self.coin2 = _make_tone(1180, 55, 0.22, "sine")
        self.hit = _make_tone(110, 320, 0.55, "saw")
        self.hit2 = _make_tone(75, 240, 0.45, "square")
        self.land = _make_tone(240, 60, 0.18, "square")
        self.start = _make_tone(620, 160, 0.35, "sine")

    def play(self, snd):
        if self.enabled and snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_jump(self, is_double=False):
        self.play(self.double if is_double else self.jump)

    def play_coin(self):
        self.play(self.coin)
        if self.enabled:
            pygame.time.set_timer(pygame.USEREVENT + 10, 48, loops=1)

    def play_hit(self):
        self.play(self.hit)
        if self.enabled:
            pygame.time.set_timer(pygame.USEREVENT + 11, 65, loops=1)


SOUNDS = SoundBank()

# =============================================================================
# PARTICLES
# =============================================================================
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "color", "size", "kind")

    def __init__(self, x, y, vx, vy, life, color, size=3, kind="normal"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.color = color
        self.size = size
        self.kind = kind

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.vx *= 0.96
        self.life -= 1
        if self.kind == "dust":
            self.vy *= 0.92

    def draw(self, surf):
        if self.life <= 0:
            return
        a = max(30, int(255 * (self.life / 28.0)))
        s = max(1, int(self.size * (self.life / 26.0) + 0.6))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), s)


# =============================================================================
# GAME OBJECTS
# =============================================================================
class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = PLAYER_X
        self.y = GROUND_Y - 10
        self.vy = 0.0
        self.on_ground = True
        self.double_jump_available = True
        self.frame = 0
        self.width = 28
        self.height = 42

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.double_jump_available = True
            SOUNDS.play_jump(False)
            return True
        elif self.double_jump_available:
            self.vy = DOUBLE_JUMP_VELOCITY
            self.double_jump_available = False
            SOUNDS.play_jump(True)
            return True
        return False

    def cut_jump(self):
        """Variable jump height - call when jump button released while rising"""
        if self.vy < -4:
            self.vy *= 0.48

    def update(self, speed, particles=None):
        self.frame += 1

        # Apply gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        self.y += self.vy

        # Ground collision
        if self.y >= GROUND_Y:
            if not self.on_ground and self.vy > 3 and particles is not None:
                # landing dust
                for _ in range(5):
                    particles.append(Particle(
                        self.x + random.randint(-6, 8),
                        GROUND_Y + 2,
                        random.uniform(-1.2, 1.2),
                        random.uniform(-0.8, -0.1),
                        random.randint(14, 22),
                        (120, 90, 50),
                        3, "dust"
                    ))
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
            self.double_jump_available = True

    def get_rect(self):
        return pygame.Rect(self.x - 12, self.y - self.height + 6, self.width, self.height)

    def draw(self, surf):
        px, py = self.x, self.y
        running = self.on_ground
        phase = self.frame / 5.0

        # Shadow
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (px - 14, GROUND_Y + 1, 28, 7))

        if running:
            # Legs running
            leg = math.sin(phase) * 5
            pygame.draw.line(surf, TROLL_DARK, (px - 5, py - 6), (px - 8 + leg, py + 6), 5)
            pygame.draw.line(surf, TROLL_DARK, (px + 5, py - 6), (px + 8 - leg, py + 6), 5)
            # Body
            pygame.draw.rect(surf, TROLL_GREEN, (px - 9, py - 22, 18, 18), border_radius=3)
            # Arms
            arm = math.cos(phase) * 4.5
            pygame.draw.line(surf, TROLL_DARK, (px - 8, py - 18), (px - 14 + arm, py - 10), 4)
            pygame.draw.line(surf, TROLL_DARK, (px + 8, py - 18), (px + 14 - arm, py - 10), 4)
        else:
            # Jumping pose
            pygame.draw.line(surf, TROLL_DARK, (px - 4, py - 8), (px - 7, py + 2), 5)
            pygame.draw.line(surf, TROLL_DARK, (px + 4, py - 8), (px + 7, py + 2), 5)
            pygame.draw.rect(surf, TROLL_GREEN, (px - 9, py - 22, 18, 18), border_radius=3)
            pygame.draw.line(surf, TROLL_DARK, (px - 8, py - 18), (px - 13, py - 12), 4)
            pygame.draw.line(surf, TROLL_DARK, (px + 8, py - 18), (px + 13, py - 12), 4)

        # Head
        pygame.draw.circle(surf, TROLL_SKIN, (int(px), int(py - 28)), 11)
        # Wild troll hair
        for i in range(5):
            hx = px - 8 + i * 4
            hy = py - 36 + math.sin(i + self.frame / 7) * 1.5
            pygame.draw.circle(surf, TROLL_DARK, (int(hx), int(hy)), 4)
        # Big nose
        pygame.draw.ellipse(surf, (60, 120, 70), (px - 3, py - 29, 6, 5))
        # Ears
        pygame.draw.ellipse(surf, TROLL_SKIN, (px - 13, py - 31, 6, 8))
        pygame.draw.ellipse(surf, TROLL_SKIN, (px + 7, py - 31, 6, 8))
        # Eyes
        pygame.draw.circle(surf, BLACK, (int(px - 4), int(py - 30)), 2)
        pygame.draw.circle(surf, BLACK, (int(px + 4), int(py - 30)), 2)
        # Eyebrows (troll expression)
        pygame.draw.line(surf, TROLL_DARK, (px - 7, py - 34), (px - 1, py - 33), 2)
        pygame.draw.line(surf, TROLL_DARK, (px + 1, py - 33), (px + 7, py - 34), 2)

        # Little belt / detail
        pygame.draw.rect(surf, (101, 67, 33), (px - 9, py - 12, 18, 4))


class Mushroom:
    __slots__ = ("x", "y", "w", "h", "kind")

    def __init__(self, x, y, kind="medium"):
        self.x = x
        self.y = y
        self.kind = kind
        if kind == "small":
            self.w, self.h = 22, 28
        elif kind == "tall":
            self.w, self.h = 28, 46
        else:
            self.w, self.h = 26, 36

    def update(self, speed):
        self.x -= speed

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h, self.w, self.h)

    def draw(self, surf):
        cx = self.x
        base_y = self.y

        # Stem
        stem_w = int(self.w * 0.42)
        pygame.draw.rect(surf, MUSHROOM_STEM, (cx - stem_w // 2, base_y - int(self.h * 0.55), stem_w, int(self.h * 0.6)), border_radius=3)

        # Cap
        cap_h = int(self.h * 0.58)
        cap_y = base_y - self.h + 4
        pygame.draw.ellipse(surf, MUSHROOM_RED, (cx - self.w // 2, cap_y, self.w, cap_h))

        # White spots
        spot_r = max(3, self.w // 7)
        spots = [(-5, -3), (4, -6), (0, 2), (-7, 4), (6, 3)] if self.kind != "small" else [(-3, 0), (3, -2)]
        for ox, oy in spots:
            pygame.draw.circle(surf, MUSHROOM_WHITE, (int(cx + ox), int(cap_y + cap_h // 2 + oy)), spot_r)

        # Eyes on cap (angry mushroom)
        eye_y = cap_y + cap_h // 2 - 1
        pygame.draw.circle(surf, BLACK, (int(cx - 5), int(eye_y)), 2)
        pygame.draw.circle(surf, BLACK, (int(cx + 5), int(eye_y)), 2)
        # Angry brows
        pygame.draw.line(surf, (30, 30, 30), (cx - 8, eye_y - 3), (cx - 2, eye_y - 4), 2)
        pygame.draw.line(surf, (30, 30, 30), (cx + 2, eye_y - 4), (cx + 8, eye_y - 3), 2)


class Coin:
    __slots__ = ("x", "y", "phase", "bob")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.phase = random.random() * math.pi * 2
        self.bob = random.random() * math.pi * 2

    def update(self, speed):
        self.x -= speed
        self.phase += 0.22
        self.bob += 0.05

    def get_rect(self):
        return pygame.Rect(self.x - 9, self.y - 9, 18, 18)

    def draw(self, surf):
        cx, cy = self.x, self.y + math.sin(self.bob) * 1.8
        # Size changes to simulate spinning
        w = 9 + math.sin(self.phase) * 3.5
        if abs(w) < 2:
            w = 2

        # Glow
        glow = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 40, 55), (14, 14), 13)
        surf.blit(glow, (int(cx - 14), int(cy - 14)))

        # Coin
        pygame.draw.ellipse(surf, COIN_GOLD, (cx - w, cy - 9, w * 2, 18))
        pygame.draw.ellipse(surf, COIN_DARK, (cx - w, cy - 9, w * 2, 18), 2)

        # Inner detail
        if w > 4:
            pygame.draw.circle(surf, COIN_DARK, (int(cx), int(cy)), 3)
            pygame.draw.line(surf, (255, 240, 120), (cx - w * 0.5, cy - 3), (cx + w * 0.35, cy + 3), 2)


# =============================================================================
# BACKGROUND (parallax Mario-style)
# =============================================================================
def draw_background(surf, scroll, frame):
    # Sky gradient
    for y in range(HEIGHT - 120):
        t = y / (HEIGHT - 120)
        r = int(SKY_TOP[0] + (SKY_BLUE[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BLUE[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BLUE[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

    # Far hills (slow)
    far = scroll * 0.35
    for i in range(-1, 5):
        hx = (i * 280 - far) % (WIDTH + 300) - 80
        pygame.draw.ellipse(surf, HILL_FAR, (hx, 210, 320, 180))

    # Mid hills
    mid = scroll * 0.65
    for i in range(-1, 6):
        hx = (i * 240 - mid) % (WIDTH + 260) - 60
        pygame.draw.ellipse(surf, HILL_LIGHT, (hx, 240, 270, 170))

    # Close hills / bushes
    close = scroll * 0.92
    for i in range(-2, 7):
        hx = (i * 190 - close) % (WIDTH + 220) - 40
        pygame.draw.ellipse(surf, HILL_DARK, (hx, 280, 210, 140))
        # Extra bush detail
        pygame.draw.ellipse(surf, (42, 130, 42), (hx + 30, 295, 70, 55))

    # Ground
    pygame.draw.rect(surf, GROUND_GREEN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(surf, GROUND_BROWN, (0, GROUND_Y + 18, WIDTH, HEIGHT - GROUND_Y - 18))

    # Ground lines / dirt texture (scrolling)
    line_off = (scroll * 1.4) % 38
    for i in range(-1, 24):
        lx = (i * 38 - line_off) % (WIDTH + 50) - 10
        pygame.draw.line(surf, (60, 120, 50), (lx, GROUND_Y + 4), (lx + 18, GROUND_Y + 22), 2)

    # Grass tufts on ground
    grass_off = (scroll * 1.1) % 26
    for i in range(30):
        gx = (i * 26 - grass_off) % (WIDTH + 40) - 15
        gy = GROUND_Y + random.randint(0, 3)
        pygame.draw.line(surf, (46, 125, 50), (gx, gy), (gx - 1, gy - 10), 2)
        pygame.draw.line(surf, (46, 125, 50), (gx + 4, gy + 1), (gx + 3, gy - 9), 2)

    # Clouds (very slow)
    cloud_off = (frame * 0.3) % 180
    for i in range(3):
        cx = (i * 290 - cloud_off * 0.6) % (WIDTH + 250) - 60
        cy = 55 + (i % 2) * 28
        pygame.draw.ellipse(surf, (255, 255, 255), (cx, cy, 55, 22))
        pygame.draw.ellipse(surf, (255, 255, 255), (cx + 18, cy - 8, 42, 26))
        pygame.draw.ellipse(surf, (255, 255, 255), (cx + 38, cy + 2, 36, 18))


# =============================================================================
# HIGH SCORE
# =============================================================================
def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as f:
                return int(json.load(f).get("highscore", 0))
    except Exception:
        pass
    return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": int(score)}, f)
    except Exception:
        pass


# =============================================================================
# MAIN GAME
# =============================================================================
# particles list is managed inside main() for each run

def main():
    global particles
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Fonts
    try:
        font_title = pygame.font.SysFont("dejavusans", 52, bold=True)
        font_big = pygame.font.SysFont("dejavusans", 36, bold=True)
        font_med = pygame.font.SysFont("dejavusans", 24, bold=True)
        font_small = pygame.font.SysFont("dejavusans", 18)
        font_score = pygame.font.SysFont("dejavusans", 22, bold=True)
    except Exception:
        font_title = pygame.font.Font(None, 60)
        font_big = pygame.font.Font(None, 42)
        font_med = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 20)
        font_score = pygame.font.Font(None, 24)

    # States
    MENU = 0
    PLAYING = 1
    GAMEOVER = 2
    state = MENU

    highscore = load_highscore()

    player = Player()
    mushrooms = []
    coins = []
    particles = []

    score = 0
    coins_collected = 0
    speed = START_SPEED
    distance = 0.0
    frame = 0
    last_mushroom = 0
    last_coin = 0

    keys = set()

    def reset_game():
        nonlocal mushrooms, coins, score, coins_collected
        nonlocal speed, distance, frame, last_mushroom, last_coin
        player.reset()
        mushrooms.clear()
        coins.clear()
        particles.clear()
        score = 0
        coins_collected = 0
        speed = START_SPEED
        distance = 0.0
        frame = 0
        last_mushroom = 0
        last_coin = 0

    def spawn_mushroom():
        # Varied sizes with safe gaps
        kinds = ["small", "medium", "medium", "tall"]
        kind = random.choice(kinds)
        # Spawn just off right edge
        mx = WIDTH + random.randint(20, 55)
        my = GROUND_Y
        mushrooms.append(Mushroom(mx, my, kind))

    def spawn_coin_group():
        base_x = WIDTH + random.randint(10, 40)
        base_y = GROUND_Y - random.randint(22, 85)
        count = random.randint(1, 4)
        spacing = random.randint(18, 26)
        for i in range(count):
            c = Coin(base_x + i * spacing, base_y + (i % 2) * 6)
            coins.append(c)

    def spawn_single_coin():
        cx = WIDTH + random.randint(5, 35)
        cy = GROUND_Y - random.randint(35, 120)
        coins.append(Coin(cx, cy))

    def add_coin_particles(x, y, n=8):
        for _ in range(n):
            ang = random.uniform(-2.2, -0.6)
            spd = random.uniform(1.8, 3.6)
            vx = math.cos(ang) * spd + random.uniform(-0.6, 0.6)
            vy = math.sin(ang) * spd
            col = random.choice([(255, 215, 60), (255, 235, 100), (255, 190, 30)])
            particles.append(Particle(x, y, vx, vy, random.randint(16, 26), col, random.randint(2, 4)))

    running = True
    paused = False

    # Initial preview objects on menu
    for i in range(2):
        mushrooms.append(Mushroom(420 + i * 160, GROUND_Y, "medium" if i == 0 else "small"))
    coins.append(Coin(520, GROUND_Y - 55))

    while running:
        dt = clock.tick(FPS)
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                keys.add(event.key)

                if event.key == pygame.K_ESCAPE:
                    if state == PLAYING:
                        state = GAMEOVER
                    else:
                        running = False

                if event.key == pygame.K_p and state == PLAYING:
                    paused = not paused

                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if state == MENU:
                        reset_game()
                        state = PLAYING
                        SOUNDS.play(SOUNDS.start)
                        # Spawn first few obstacles
                        mushrooms.append(Mushroom(WIDTH + 60, GROUND_Y, "medium"))
                        coins.append(Coin(WIDTH + 110, GROUND_Y - 50))
                    elif state == PLAYING and not paused:
                        player.jump()
                    elif state == GAMEOVER:
                        reset_game()
                        state = PLAYING
                        SOUNDS.play(SOUNDS.start)
                        mushrooms.append(Mushroom(WIDTH + 50, GROUND_Y, "medium"))

                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if state == PLAYING and not paused and not player.on_ground:
                        player.vy = min(player.vy + 3.5, 9)  # fast fall

            elif event.type == pygame.KEYUP:
                keys.discard(event.key)
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if state == PLAYING and not paused:
                        player.cut_jump()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if state == MENU:
                    reset_game()
                    state = PLAYING
                    SOUNDS.play(SOUNDS.start)
                    mushrooms.append(Mushroom(WIDTH + 60, GROUND_Y, "medium"))
                elif state == PLAYING and not paused:
                    player.jump()
                elif state == GAMEOVER:
                    reset_game()
                    state = PLAYING
                    SOUNDS.play(SOUNDS.start)
                    mushrooms.append(Mushroom(WIDTH + 50, GROUND_Y, "medium"))

            # Sound callbacks
            if event.type == pygame.USEREVENT + 10:
                SOUNDS.play(SOUNDS.coin2)
            if event.type == pygame.USEREVENT + 11:
                SOUNDS.play(SOUNDS.hit2)

        # ===================== UPDATE =====================
        if state == PLAYING and not paused:
            # Player
            player.update(speed, particles)

            # Increase speed slowly
            speed = min(speed + SPEED_INCREASE, MAX_SPEED)

            # Distance & score
            distance += speed * 0.6
            score = int(distance) + coins_collected * 80

            # Spawn mushrooms with safe gaps
            if frame - last_mushroom > max(26, int(48 - speed * 3.2)):
                # Make sure there's enough space from the last one
                last_x = mushrooms[-1].x if mushrooms else 0
                if last_x < WIDTH - 70 or not mushrooms:
                    spawn_mushroom()
                    last_mushroom = frame

            # Spawn coins fairly often
            if frame - last_coin > random.randint(18, 28):
                if random.random() < 0.65:
                    spawn_coin_group()
                else:
                    spawn_single_coin()
                last_coin = frame

            # Update mushrooms
            for m in mushrooms[:]:
                m.update(speed)
                if m.x < -60:
                    mushrooms.remove(m)

            # Update coins
            for c in coins[:]:
                c.update(speed)
                if c.x < -30:
                    coins.remove(c)

            # Update particles
            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

            # Collisions - coins first (more generous)
            pr = player.get_rect()
            for c in coins[:]:
                if pr.colliderect(c.get_rect()):
                    coins.remove(c)
                    coins_collected += 1
                    add_coin_particles(c.x, c.y, random.randint(6, 10))
                    SOUNDS.play_coin()

            # Mushroom collisions
            for m in mushrooms[:]:
                if pr.colliderect(m.get_rect()):
                    state = GAMEOVER
                    SOUNDS.play_hit()
                    if score > highscore:
                        highscore = score
                        save_highscore(highscore)
                    break

            # Running dust
            if player.on_ground and frame % 3 == 0:
                particles.append(Particle(
                    player.x - 12, GROUND_Y + 1,
                    random.uniform(-2.8, -1.0), random.uniform(-0.4, 0.1),
                    random.randint(10, 16), (110, 85, 55), 2, "dust"
                ))

        # ===================== DRAW =====================
        draw_background(screen, distance * 1.6 if state == PLAYING else frame * 0.6, frame)

        # Coins (behind mushrooms)
        for c in coins:
            c.draw(screen)

        # Mushrooms
        for m in mushrooms:
            m.draw(screen)

        # Particles
        for p in particles:
            p.draw(screen)

        # Player
        if state != MENU or (frame // 8) % 2 == 0:
            player.draw(screen)

        # ===================== UI =====================
        if state == PLAYING:
            # Score
            sc = font_score.render(f"{score}", True, UI_GOLD)
            screen.blit(sc, (22, 16))

            # Coins
            cc = font_small.render(f"COINS {coins_collected}", True, (255, 230, 100))
            screen.blit(cc, (WIDTH - cc.get_width() - 18, 18))

            # Small speed indicator
            pct = (speed - START_SPEED) / (MAX_SPEED - START_SPEED)
            bar_w = int(70 * pct)
            pygame.draw.rect(screen, (40, 90, 40), (WIDTH - 92, 42, 70, 5), border_radius=2)
            pygame.draw.rect(screen, (255, 210, 70), (WIDTH - 92, 42, bar_w, 5), border_radius=2)

            if paused:
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 130))
                screen.blit(ov, (0, 0))
                pt = font_big.render("PAUSED", True, WHITE)
                screen.blit(pt, (WIDTH // 2 - pt.get_width() // 2, HEIGHT // 2 - 20))
                ht = font_small.render("Press P to resume", True, (200, 200, 160))
                screen.blit(ht, (WIDTH // 2 - ht.get_width() // 2, HEIGHT // 2 + 18))

        elif state == MENU:
            # Dark overlay
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((10, 30, 20, 145))
            screen.blit(ov, (0, 0))

            # Title
            title = font_title.render("TROLL RUN WORLD", True, (255, 225, 70))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 92))

            # Subtitle
            sub = font_med.render("Jump the mushrooms. Grab the coins.", True, (200, 230, 160))
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 155))

            # Start prompt
            pr = font_big.render("PRESS SPACE OR CLICK TO START", True, (255, 240, 120))
            screen.blit(pr, (WIDTH // 2 - pr.get_width() // 2, HEIGHT - 160))

            # Controls hint
            ctrl = font_small.render("SPACE / UP / W  =  Jump   (Double jump in air)", True, (170, 200, 150))
            screen.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, HEIGHT - 105))

            hs = font_small.render(f"HIGH SCORE: {highscore}", True, (180, 210, 140))
            screen.blit(hs, (WIDTH // 2 - hs.get_width() // 2, HEIGHT - 68))

        elif state == GAMEOVER:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((15, 25, 15, 175))
            screen.blit(ov, (0, 0))

            # Title
            gt = font_title.render("MUSHROOMED!", True, (255, 90, 70))
            screen.blit(gt, (WIDTH // 2 - gt.get_width() // 2, 95))

            # Score
            fs = font_big.render(f"SCORE: {score}", True, WHITE)
            screen.blit(fs, (WIDTH // 2 - fs.get_width() // 2, 165))

            # Stats
            st = font_med.render(f"Distance: {int(distance)}    Coins: {coins_collected}", True, (210, 200, 140))
            screen.blit(st, (WIDTH // 2 - st.get_width() // 2, 210))

            if score >= highscore and score > 50:
                nh = font_med.render("NEW HIGH SCORE!", True, (255, 220, 60))
                screen.blit(nh, (WIDTH // 2 - nh.get_width() // 2, 248))

            hs2 = font_small.render(f"High Score: {highscore}", True, (180, 195, 140))
            screen.blit(hs2, (WIDTH // 2 - hs2.get_width() // 2, 280))

            # Restart
            rp = font_med.render("PRESS SPACE OR CLICK TO RUN AGAIN", True, (255, 225, 90))
            screen.blit(rp, (WIDTH // 2 - rp.get_width() // 2, HEIGHT - 130))

            qt = font_small.render("ESC to quit", True, (160, 170, 140))
            screen.blit(qt, (WIDTH // 2 - qt.get_width() // 2, HEIGHT - 82))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
