"""Play original WAV effects using ALSA without blocking the GUI."""
import os
import shutil
import subprocess
import time


class Sound(object):
    def __init__(self, directory):
        self.directory = directory
        self.player = shutil.which('aplay')
        self.enabled = bool(self.player)
        self.process = None
        self.last_eat = 0

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process = None

    def toggle(self):
        self.enabled = not self.enabled if self.player else False
        if not self.enabled:
            self.stop()

    def play(self, event):
        if not self.enabled:
            return
        if event == 'eat':
            if time.monotonic() - self.last_eat < 0.15:
                return
            if self.process is not None and self.process.poll() is None:
                return
            self.last_eat = time.monotonic()
        self.stop()
        try:
            self.process = subprocess.Popen(
                [self.player, '-q', os.path.join(self.directory, event + '.wav')],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.enabled = False
