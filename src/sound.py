import pygame

class SoundManager:
    def __init__(self):
        self.audio_available = False
        try:
            pygame.mixer.init()  # Initialize the mixer
            pygame.mixer.set_num_channels(128)
            self.audio_available = True
            print("Audio system initialized successfully")
        except pygame.error as e:
            print(f"Audio initialization failed: {e}")
            print("Running in silent mode - no audio will be played")
        self.sounds = {}

    def load_sound(self, name, path, volume=1.0):
        """Load a sound and set its volume"""
        if not self.audio_available:
            return
        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(volume)
            self.sounds[name] = sound
        except pygame.error as e:
            print(f"Failed to load sound {name}: {e}")

    def play_sound(self, name, loop=False):
        """Play a loaded sound"""
        if not self.audio_available or name not in self.sounds:
            return
        try:
            self.sounds[name].play(loops=-1 if loop else 0)
        except pygame.error as e:
            print(f"Failed to play sound {name}: {e}")

    def stop_sound(self, name):
        """Stop a playing sound"""
        if not self.audio_available or name not in self.sounds:
            return
        try:
            self.sounds[name].stop()
        except pygame.error as e:
            print(f"Failed to stop sound {name}: {e}")

    def stop_all(self):
        """Stop all sounds"""
        if not self.audio_available:
            return
        try:
            pygame.mixer.stop()
        except pygame.error as e:
            print(f"Failed to stop all sounds: {e}")
