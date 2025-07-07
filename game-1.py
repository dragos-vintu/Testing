import pygame
import random
import json
import os
import math

# Try to import numpy for sound generation
try:
    import numpy as np
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False
    print("NumPy not found. Sound will be disabled. Install with: pip install numpy")

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 149, 237)
YELLOW = (255, 215, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (147, 112, 219)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DOVE_BLUE = (0, 123, 194)
FRESH_GREEN = (134, 188, 37)

class SoundEffects:
    def __init__(self):
        self.sample_rate = 22050
        self.music_position = 0
        
    def generate_tone(self, frequency, duration, volume=0.5):
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        for i in range(frames):
            sample = int(volume * 32767 * np.sin(2 * np.pi * frequency * i / self.sample_rate))
            arr[i] = [sample, sample]
        return pygame.sndarray.make_sound(arr)
    
    def generate_spray_sound(self):
        # Whoosh sound - white noise with envelope
        duration = 0.15
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            # White noise
            noise = np.random.randint(-16383, 16383)
            # Envelope (fade in and out)
            envelope = np.sin(np.pi * i / frames)
            sample = int(noise * envelope * 0.3)
            arr[i] = [sample, sample]
            
        return pygame.sndarray.make_sound(arr)
    
    def generate_background_music(self):
        # Create an original atmospheric electronic track
        duration = 8.0  # 8 second loop
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        # Time array
        t = np.linspace(0, duration, frames)
        
        # Bass line - deep, pulsing bass
        bass_freq = 55  # Low A
        bass_pattern = np.array([1, 0, 0, 1, 0, 0, 1, 0])
        bass_envelope = np.zeros(frames)
        
        for i in range(len(t)):
            beat_pos = int((i / self.sample_rate) * 2) % len(bass_pattern)
            if bass_pattern[beat_pos]:
                bass_envelope[i] = np.exp(-(i % (self.sample_rate // 2)) / (self.sample_rate / 10))
        
        bass = np.sin(2 * np.pi * bass_freq * t) * bass_envelope * 8000
        
        # Atmospheric pad - subtle chord progression
        pad = np.zeros(frames)
        chord_freqs = [
            [130.8, 164.8, 196.0],  # C major
            [146.8, 174.6, 220.0],  # D minor
            [98.0, 123.5, 146.8],   # G major
            [110.0, 138.6, 164.8]   # A minor
        ]
        
        chord_duration = frames // 4
        for i, chord in enumerate(chord_freqs):
            start = i * chord_duration
            end = (i + 1) * chord_duration
            if end > frames:
                end = frames
            
            for freq in chord:
                pad[start:end] += np.sin(2 * np.pi * freq * t[start:end]) * 1000
                # Add subtle vibrato
                vibrato = np.sin(2 * np.pi * 5 * t[start:end]) * 2
                pad[start:end] += np.sin(2 * np.pi * (freq + vibrato) * t[start:end]) * 500
        
        # Hi-hat pattern
        hihat = np.zeros(frames)
        hihat_pattern = [1, 0, 1, 0, 1, 0, 1, 1]
        
        for i in range(len(t)):
            beat_pos = int((i / self.sample_rate) * 8) % len(hihat_pattern)
            if hihat_pattern[beat_pos]:
                # White noise burst for hi-hat
                burst_length = min(1000, frames - i)
                if burst_length > 0:
                    hihat[i:i+burst_length] = np.random.normal(0, 1000, burst_length) * np.exp(-np.linspace(0, 5, burst_length))
        
        # Synth lead - subtle melodic element
        lead = np.zeros(frames)
        lead_notes = [
            (0, 1, 261.6),      # C
            (1, 1.5, 293.7),    # D
            (1.5, 2.5, 329.6),  # E
            (2.5, 3, 293.7),    # D
            (3, 4, 261.6),      # C
            (4, 5, 246.9),      # B
            (5, 6, 220.0),      # A
            (6, 8, 196.0)       # G
        ]
        
        for start_beat, end_beat, freq in lead_notes:
            start_sample = int(start_beat * self.sample_rate)
            end_sample = int(end_beat * self.sample_rate)
            if end_sample > frames:
                end_sample = frames
            
            # Calculate actual note length
            note_length = end_sample - start_sample
            if note_length <= 0:
                continue
                
            # Create envelope with exact length
            attack = note_length // 4
            sustain = note_length // 2
            release = note_length - attack - sustain
            
            envelope = np.concatenate([
                np.linspace(0, 1, attack),
                np.ones(sustain),
                np.linspace(1, 0, release)
            ])
            
            # Ensure envelope matches exactly
            if len(envelope) != note_length:
                envelope = envelope[:note_length]
            
            lead[start_sample:end_sample] += (
                np.sin(2 * np.pi * freq * t[start_sample:end_sample]) * 
                envelope * 2000
            )
        
        # Mix all elements
        mixed = bass + pad + hihat + lead
        
        # Apply compression and limiting
        mixed = np.tanh(mixed / 15000) * 15000
        
        # Stereo effect - slight delay on right channel
        delay_samples = int(0.01 * self.sample_rate)
        left_channel = mixed
        right_channel = np.roll(mixed, delay_samples)
        
        # Convert to stereo
        arr[:, 0] = left_channel.astype(np.int16)
        arr[:, 1] = right_channel.astype(np.int16)
        
        return pygame.sndarray.make_sound(arr)
    
    def generate_explosion_sound(self):
        # Explosion - low frequency noise burst
        duration = 0.3
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            # Low frequency noise
            noise = np.random.randint(-32767, 32767)
            # Decay envelope
            envelope = (1 - i / frames) ** 2
            # Add some low frequency modulation
            mod = np.sin(2 * np.pi * 50 * i / self.sample_rate)
            sample = int(noise * envelope * 0.4 * (0.5 + 0.5 * mod))
            arr[i] = [sample, sample]
            
        return pygame.sndarray.make_sound(arr)
    
    def generate_bad_odor_sound(self):
        # Grumbling sound - low frequency with wobble
        duration = 0.5
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        base_freq = 80
        for i in range(frames):
            # Wobbling frequency
            wobble = np.sin(2 * np.pi * 5 * i / self.sample_rate) * 20
            freq = base_freq + wobble
            sample = int(16383 * np.sin(2 * np.pi * freq * i / self.sample_rate))
            # Add some noise
            noise = np.random.randint(-2000, 2000)
            arr[i] = [sample + noise, sample + noise]
            
        return pygame.sndarray.make_sound(arr)
    
    def generate_level_complete_sound(self):
        # Victory fanfare - ascending tones
        sound_array = []
        frequencies = [261, 329, 392, 523]  # C, E, G, C
        
        for freq in frequencies:
            tone = self.generate_tone(freq, 0.15, 0.3)
            sound_array.append(tone)
            
        return sound_array
    
    def generate_game_over_sound(self):
        # Descending tones
        duration = 0.8
        frames = int(duration * self.sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            # Descending frequency
            freq = 400 * (1 - i / frames * 0.5)
            sample = int(16383 * np.sin(2 * np.pi * freq * i / self.sample_rate))
            # Decay
            envelope = (1 - i / frames)
            arr[i] = [int(sample * envelope), int(sample * envelope)]
            
        return pygame.sndarray.make_sound(arr)

class Player(pygame.sprite.Sprite):
    def __init__(self, spray_image_path=None, joystick=None):
        super().__init__()
        
        # Try to load the spray image
        if spray_image_path and os.path.exists(spray_image_path):
            try:
                original_image = pygame.image.load(spray_image_path)
                # Scale the image to appropriate size - 2x wider!
                self.width = 120
                self.height = 90
                self.image = pygame.transform.scale(original_image, (self.width, self.height))
            except:
                self.create_default_sprite()
        else:
            self.create_default_sprite()
            
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed = 5
        self.shoot_cooldown = 0
        self.joystick = joystick
        
    def create_default_sprite(self):
        # Fallback to drawn sprite if image can't be loaded - 2x wider!
        self.width = 120
        self.height = 90
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Enhanced deodorant drawing - scaled for wider bottle
        # Can body with gradient effect
        for i in range(80):
            color_value = 128 + i * 1.5
            pygame.draw.rect(self.image, (color_value, color_value, color_value), 
                           (20 + i//8, 25, 80 - i//4, 55))
        
        # Dove blue section - wider
        pygame.draw.rect(self.image, DOVE_BLUE, (25, 30, 70, 45))
        
        # Cap with metallic shine - wider
        pygame.draw.ellipse(self.image, (180, 180, 180), (10, 5, 100, 25))
        pygame.draw.ellipse(self.image, (220, 220, 220), (15, 8, 90, 20))
        pygame.draw.ellipse(self.image, WHITE, (25, 10, 70, 10))
        
        # Nozzle - centered on wider bottle
        pygame.draw.rect(self.image, (60, 60, 60), (57, 0, 6, 10))
        pygame.draw.rect(self.image, BLACK, (59, 0, 2, 8))
        
        # Dove logo - centered on wider bottle
        font = pygame.font.Font(None, 20)
        text = font.render("DOVE", True, WHITE)
        text_rect = text.get_rect(center=(60, 45))
        self.image.blit(text, text_rect)
        
        # "MEN+care" text - centered on wider bottle
        small_font = pygame.font.Font(None, 14)
        men_text = small_font.render("MEN+care", True, WHITE)
        men_rect = men_text.get_rect(center=(60, 58))
        self.image.blit(men_text, men_rect)
        
    def update(self):
        keys = pygame.key.get_pressed()

        # Movement via keyboard
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

        # Movement via joystick axis (X axis)
        if self.joystick:
            x_axis = self.joystick.get_axis(0)
            if abs(x_axis) > 0.2:
                self.rect.x += int(x_axis * self.speed)

        # Keep player within screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # Cooldown timer for shooting handled in shoot()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
    def shoot(self):
        if self.shoot_cooldown == 0:
            bullet = Bullet(self.rect.centerx, self.rect.top)
            self.shoot_cooldown = 15
            return bullet
        return None

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 12
        self.height = 20
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.draw_spray()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 8
        
    def draw_spray(self):
        # Enhanced spray particle effect
        for i in range(5):
            y = i * 4
            size = 12 - i * 2
            alpha = 255 - i * 40
            
            # Outer glow
            glow_surf = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*FRESH_GREEN, alpha//2), 
                             ((size + 4)//2, (size + 4)//2), (size + 4)//2)
            self.image.blit(glow_surf, (6 - (size + 4)//2, y - 2))
            
            # Core spray
            pygame.draw.circle(self.image, (*WHITE, alpha), (6, y + 2), size//2)
            
    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Odor(pygame.sprite.Sprite):
    def __init__(self, x, y, odor_type=0):
        super().__init__()
        self.odor_type = odor_type
        self.size = 45
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.wobble = random.random() * math.pi * 2  # FIXED: Move this before draw_odor()
        self.draw_odor()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # Remove individual movement - will be controlled by game formation logic
        self.points = (odor_type + 1) * 10
        
    def draw_odor(self):
        # Clear the image
        self.image.fill((0, 0, 0, 0))
        
        # Different odor cloud designs based on type
        colors = [(50, 150, 50), (147, 112, 219), (255, 140, 0), (200, 50, 50)]
        color = colors[self.odor_type % len(colors)]
        
        # Animated wavy odor cloud with more detail
        wave = math.sin(self.animation_frame + self.wobble) * 3
        
        # Multiple cloud layers for depth
        cloud_layers = [
            {"pos": (22 + wave, 12), "size": 15, "alpha": 180},
            {"pos": (12, 22 - wave), "size": 14, "alpha": 200},
            {"pos": (32, 22 + wave), "size": 14, "alpha": 200},
            {"pos": (22 - wave, 32), "size": 15, "alpha": 180},
            {"pos": (22, 22), "size": 18, "alpha": 255}
        ]
        
        for layer in cloud_layers:
            pos = layer["pos"]
            size = layer["size"]
            alpha = layer["alpha"]
            
            # Outer glow
            glow_color = (*color, alpha//3)
            pygame.draw.circle(self.image, glow_color, pos, size + 3)
            
            # Main cloud
            cloud_color = (*color, alpha)
            pygame.draw.circle(self.image, cloud_color, pos, size)
            
        # Animated face
        eye_offset = math.sin(self.animation_frame * 2) * 1
        
        # Eyes
        pygame.draw.circle(self.image, BLACK, (17, 20 + int(eye_offset)), 3)
        pygame.draw.circle(self.image, BLACK, (28, 20 + int(eye_offset)), 3)
        
        # Angry eyebrows
        pygame.draw.line(self.image, BLACK, (14, 16), (19, 18), 2)
        pygame.draw.line(self.image, BLACK, (26, 18), (31, 16), 2)
        
        # Grumpy mouth
        mouth_wave = math.sin(self.animation_frame * 3) * 1
        pygame.draw.arc(self.image, BLACK, 
                       (15, 24 + int(mouth_wave), 15, 8), 0, math.pi, 2)
        
    def update(self):
        # Only handle animation - movement is controlled by game formation logic
        self.animation_frame += self.animation_speed
        self.draw_odor()
        
    def move_formation(self, dx, dy):
        """Move this odor as part of the formation"""
        self.rect.x += dx
        self.rect.y += dy

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.size = random.randint(3, 10)
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        
        # Glowing particle
        pygame.draw.circle(self.image, (*color, 100), (self.size, self.size), self.size)
        pygame.draw.circle(self.image, (*color, 255), (self.size, self.size), self.size//2)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = random.uniform(-4, 4)
        self.vel_y = random.uniform(-6, -1)
        self.gravity = 0.3
        self.lifetime = 40
        self.max_lifetime = 40
        
    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += self.gravity
        self.lifetime -= 1
        
        # Fade out
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.image.set_alpha(alpha)
        
        if self.lifetime <= 0:
            self.kill()

class Game:
    def __init__(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
        # Query the current desktop resolution and create a full screen window
        info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Dove Fresh Invaders - Defeat the Bad Odors!")
        self.clock = pygame.time.Clock()
        self.joystick = None
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Initialize sound effects
        if SOUND_ENABLED:
            self.sound_fx = SoundEffects()
            self.spray_sound = self.sound_fx.generate_spray_sound()
            self.explosion_sound = self.sound_fx.generate_explosion_sound()
            self.bad_odor_sound = self.sound_fx.generate_bad_odor_sound()
            self.level_complete_sounds = self.sound_fx.generate_level_complete_sound()
            self.game_over_sound = self.sound_fx.generate_game_over_sound()
            
            # Background music
            self.background_music = self.sound_fx.generate_background_music()
            self.music_channel = pygame.mixer.Channel(0)
            self.music_volume = 0.3
            
            # Start music immediately on menu screen
            self.music_channel.play(self.background_music, loops=-1)
            self.music_channel.set_volume(self.music_volume)
        else:
            self.sound_enabled = False
        
        # Game state
        self.state = "MENU"
        self.score = 0
        self.level = 1
        self.lives = 3
        self.high_scores = self.load_high_scores()
        self.combo = 0
        self.combo_timer = 0
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.odors = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        
        # Player
        self.player = None
        
        # Odor movement - formation based
        self.odor_direction = 1
        self.odor_speed = 1
        self.odor_move_timer = 0
        self.odor_move_delay = 30  # Move every 30 frames initially
        
        # Background stars
        self.stars = []
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(0.5, 2),
                'size': random.randint(1, 3)
            })
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick initialized: {self.joystick.get_name()}")
        else:
            self.joystick = None
    def load_high_scores(self):
        try:
            with open("high_scores.json", "r") as f:
                return json.load(f)
        except:
            return []
            
    def save_high_scores(self):
        with open("high_scores.json", "w") as f:
            json.dump(self.high_scores[:10], f)
            
    def add_high_score(self, score):
        self.high_scores.append(score)
        self.high_scores.sort(reverse=True)
        self.high_scores = self.high_scores[:10]
        self.save_high_scores()
        
    def create_odor_wave(self):
        # Progressive difficulty: more enemies and faster movement
        base_rows = 3
        base_cols = 8
        
        # Increase rows and columns with level, but cap them
        rows = min(base_rows + (self.level - 1) // 2, 6)
        cols = min(base_cols + (self.level - 1), 12)
        
        # Increase speed with each level
        self.odor_speed = 1 + (self.level - 1) * 0.3
        # Decrease move delay (faster movement) with each level
        self.odor_move_delay = max(10, 30 - (self.level - 1) * 2)
        
        # Play bad odor sound when wave appears
        if SOUND_ENABLED:
            self.bad_odor_sound.play()
        
        for row in range(rows):
            for col in range(cols):
                x = 80 + col * 60
                y = 50 + row * 50
                odor_type = min(row, 3)  # Different types for different rows
                odor = Odor(x, y, odor_type)
                self.odors.add(odor)
                self.all_sprites.add(odor)
                
    def create_explosion(self, x, y, color):
        for _ in range(15):
            particle = Particle(x, y, color)
            self.particles.add(particle)
            self.all_sprites.add(particle)
            
    def start_game(self):
        self.state = "PLAYING"
        self.score = 0
        self.level = 1
        self.lives = 3
        self.combo = 0
        self.combo_timer = 0
        
        # Reset formation movement
        self.odor_direction = 1
        self.odor_speed = 1
        self.odor_move_timer = 0
        self.odor_move_delay = 30
        
        # Clear all sprites
        self.all_sprites.empty()
        self.odors.empty()
        self.bullets.empty()
        self.particles.empty()
        
        # Create player and pass active joystick (if any)
        # In a real implementation, you would pass the actual image path here
        self.player = Player("dove_spray.png", joystick=self.joystick)
        self.all_sprites.add(self.player)
        
        # Create first wave
        self.create_odor_wave()
        
        # Music is already playing from menu, just ensure it's at the right volume
        if SOUND_ENABLED and self.music_channel.get_volume() == 0:
            self.music_channel.set_volume(self.music_volume)
        
    def update(self):
        if self.state == "PLAYING":
            # Update all sprites
            self.all_sprites.update()
            
            # Update combo timer
            if self.combo_timer > 0:
                self.combo_timer -= 1
            else:
                self.combo = 0
            
            # Update background stars
            for star in self.stars:
                star['y'] += star['speed']
                if star['y'] > SCREEN_HEIGHT:
                    star['y'] = 0
                    star['x'] = random.randint(0, SCREEN_WIDTH)
            
            # Player shooting
            keys = pygame.key.get_pressed()
            shoot_pressed = keys[pygame.K_SPACE]
            if self.joystick:
                shoot_pressed = shoot_pressed or self.joystick.get_button(0)
            if shoot_pressed:
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                    if SOUND_ENABLED:
                        self.spray_sound.play()
                    
            # Check collisions
            for bullet in self.bullets:
                hit_odors = pygame.sprite.spritecollide(bullet, self.odors, True)
                if hit_odors:
                    bullet.kill()
                    for odor in hit_odors:
                        # Combo system
                        self.combo += 1
                        self.combo_timer = 60
                        
                        # Score with combo multiplier
                        score_gained = odor.points * min(self.combo, 5)
                        self.score += score_gained
                        
                        self.create_explosion(odor.rect.centerx, odor.rect.centery, FRESH_GREEN)
                        if SOUND_ENABLED:
                            self.explosion_sound.play()
                        
            # Check if odors hit player
            hit_player = pygame.sprite.spritecollide(self.player, self.odors, True)
            if hit_player:
                self.lives -= 1
                self.combo = 0
                self.create_explosion(self.player.rect.centerx, self.player.rect.centery, RED)
                if SOUND_ENABLED:
                    self.explosion_sound.play()
                
                if self.lives <= 0:
                    self.game_over()
                    
            # Formation movement for odors (like classic Space Invaders)
            self.odor_move_timer += 1
            if self.odor_move_timer >= self.odor_move_delay:
                self.odor_move_timer = 0
                
                # Check if formation should change direction
                hit_edge = False
                for odor in self.odors:
                    if (self.odor_direction > 0 and odor.rect.right >= SCREEN_WIDTH - 20) or \
                       (self.odor_direction < 0 and odor.rect.left <= 20):
                        hit_edge = True
                        break
                
                if hit_edge:
                    # Change direction and drop down
                    self.odor_direction *= -1
                    # Move all odors down
                    for odor in self.odors:
                        odor.move_formation(0, 30)
                    # Increase speed slightly after each direction change
                    self.odor_speed += 0.1
                    if self.odor_move_delay > 5:
                        self.odor_move_delay -= 1
                else:
                    # Move formation horizontally
                    move_distance = int(self.odor_direction * self.odor_speed * 8)
                    for odor in self.odors:
                        odor.move_formation(move_distance, 0)
                    
            # Check if odors reached bottom
            for odor in self.odors:
                if odor.rect.bottom >= self.player.rect.top:
                    self.game_over()
                    break
                    
            # Next level when all odors destroyed
            if len(self.odors) == 0:
                self.level += 1
                
                # Play victory sounds
                if SOUND_ENABLED:
                    for i, sound in enumerate(self.level_complete_sounds):
                        pygame.time.wait(150)
                        sound.play()
                
                # Reset formation movement for new level
                self.odor_direction = 1
                self.odor_move_timer = 0
                
                # Create new wave with increased difficulty
                self.create_odor_wave()
                
                # Bonus points for completing level
                self.score += 100 * self.level
                
    def game_over(self):
        self.state = "GAME_OVER"
        self.add_high_score(self.score)
        if SOUND_ENABLED:
            self.game_over_sound.play()
            # Fade out music
            self.music_channel.fadeout(1000)
        
    def draw_menu(self):
        self.screen.fill(DOVE_BLUE)
        
        # Animated background
        for star in self.stars:
            pygame.draw.circle(self.screen, WHITE, 
                             (int(star['x']), int(star['y'])), star['size'])
        
        # Title with shadow
        shadow = self.font.render("DOVE FRESH INVADERS", True, BLACK)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH//2 + 2, 102))
        self.screen.blit(shadow, shadow_rect)
        
        title = self.font.render("DOVE FRESH INVADERS", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Defeat the Bad Odors!", True, FRESH_GREEN)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        instructions = [
            "Use ARROW KEYS to move",
            "Press SPACE to spray",
            "Press ENTER to start",
            "Press M to toggle music",
            "Press ESC to quit"
        ]
        
        y = 220
        for instruction in instructions:
            text = self.small_font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text, text_rect)
            y += 30
            
        # High scores
        y = 380
        high_score_title = self.small_font.render("HIGH SCORES", True, YELLOW)
        high_score_rect = high_score_title.get_rect(center=(SCREEN_WIDTH//2, y))
        self.screen.blit(high_score_title, high_score_rect)
        
        y += 30
        for i, score in enumerate(self.high_scores[:5]):
            score_text = self.small_font.render(f"{i+1}. {score:,}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(score_text, score_rect)
            y += 25
            
        # Music indicator on menu
        if SOUND_ENABLED:
            music_status = "♪ ON" if self.music_channel.get_volume() > 0 else "♪ OFF"
            music_color = GREEN if self.music_channel.get_volume() > 0 else RED
        else:
            music_status = "♪ DISABLED"
            music_color = GRAY
        music_text = self.small_font.render(music_status, True, music_color)
        self.screen.blit(music_text, (SCREEN_WIDTH - 80, 20))
            
    def draw_game(self):
        self.screen.fill(BLACK)
        
        # Draw animated background stars
        for star in self.stars:
            color = (star['size'] * 80, star['size'] * 80, star['size'] * 80)
            pygame.draw.circle(self.screen, color, 
                             (int(star['x']), int(star['y'])), star['size'])
        
        # Draw sprites
        self.all_sprites.draw(self.screen)
        
        # Draw UI with better styling
        # Score
        score_text = self.font.render(f"Score: {self.score:,}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Combo indicator
        if self.combo > 1:
            combo_color = YELLOW if self.combo < 5 else ORANGE
            combo_text = self.small_font.render(f"COMBO x{self.combo}!", True, combo_color)
            self.screen.blit(combo_text, (10, 70))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, 25))
        self.screen.blit(level_text, level_rect)
        
        # Difficulty indicator
        difficulty_text = self.small_font.render(f"Speed: {self.odor_speed:.1f} | Delay: {self.odor_move_delay}", True, YELLOW)
        difficulty_rect = difficulty_text.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(difficulty_text, difficulty_rect)
        
        # Lives
        lives_text = self.font.render(f"Lives: ", True, WHITE)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 200, 10))
        
        # Draw deodorant icons for lives
        for i in range(self.lives):
            x = SCREEN_WIDTH - 100 + i * 25
            pygame.draw.rect(self.screen, GRAY, (x, 15, 15, 20))
            pygame.draw.rect(self.screen, DOVE_BLUE, (x + 2, 18, 11, 14))
            
        # Music indicator
        if SOUND_ENABLED:
            music_status = "♪ ON" if self.music_channel.get_volume() > 0 else "♪ OFF"
            music_color = GREEN if self.music_channel.get_volume() > 0 else RED
        else:
            music_status = "♪ DISABLED"
            music_color = GRAY
        music_text = self.small_font.render(music_status, True, music_color)
        self.screen.blit(music_text, (SCREEN_WIDTH - 80, 70))
            
    def draw_game_over(self):
        self.screen.fill(BLACK)
        
        # Animated background
        for star in self.stars:
            pygame.draw.circle(self.screen, WHITE, 
                             (int(star['x']), int(star['y'])), star['size'])
        
        # Game over text with pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.002)) * 0.3 + 0.7
        game_over_color = (int(255 * pulse), 0, 0)
        
        game_over_text = self.font.render("GAME OVER", True, game_over_color)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        score_text = self.font.render(f"Final Score: {self.score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        self.screen.blit(score_text, score_rect)
        
        # Check if new high score
        if self.high_scores and self.score >= self.high_scores[0]:
            high_score_text = self.font.render("NEW HIGH SCORE!", True, YELLOW)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(high_score_text, high_score_rect)
        
        # Instructions
        restart_text = self.small_font.render("Press ENTER to play again", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 380))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = self.small_font.render("Press ESC for main menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, 410))
        self.screen.blit(menu_text, menu_rect)
        
    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            self.draw_game()
        elif self.state == "GAME_OVER":
            self.draw_game_over()
            
        pygame.display.flip()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                # Music toggle works in any state
                if event.key == pygame.K_m and SOUND_ENABLED:
                    if self.music_channel.get_volume() > 0:
                        self.music_channel.set_volume(0)
                    else:
                        self.music_channel.set_volume(self.music_volume)
                        
                if self.state == "MENU":
                    if event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        
                elif self.state == "PLAYING":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()