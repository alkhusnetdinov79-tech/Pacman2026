"""Tkinter desktop frontend; compatible with Python 3.6 and Tk 8.6."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk

from .model import Game, MAZE
from .sound import Sound

CELL = 26
TOP = 72
COLORS = ('#ff5867', '#ff9edb', '#5cdde6', '#ffb65c')
BACKGROUND = '#080e20'


def resource_dir():
    local = Path(__file__).resolve().parent.parent / 'assets'
    return local if local.is_dir() else Path('/usr/share/pacman2026/assets')


class App(object):
    def __init__(self, root, smoke=False):
        self.root, self.smoke = root, smoke
        self.game = Game(seed=2026 if smoke else None)
        self.sound = Sound(str(resource_dir() / 'sounds'))
        self.best = self.load_best()
        self.closed = False
        self.after_id = None
        root.title('Pacman2026')
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=self.game.width * CELL,
                                height=self.game.height * CELL + TOP + 76,
                                bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack()
        root.bind('<KeyPress>', self.key)
        root.bind('<FocusOut>', self.focus_out)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.draw_walls()
        self.draw()
        self.after_id = root.after(110, self.tick)
        if smoke:
            self.sound.enabled = False
            root.after(100, lambda: self.key(type('Key', (), {'keysym': 'Return'})()))
            root.after(200, lambda: self.key(type('Key', (), {'keysym': 'Left'})()))
            root.after(900, self.check_smoke)

    def score_path(self):
        return Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local' / 'state'))) / 'pacman2026' / 'score.json'

    def load_best(self):
        if self.smoke:
            return 0
        try:
            value = json.loads(self.score_path().read_text()).get('best', 0)
            return value if isinstance(value, int) and value >= 0 else 0
        except (OSError, ValueError, AttributeError):
            return 0

    def save_best(self):
        if self.smoke:
            return
        temporary = None
        try:
            path = self.score_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', dir=str(path.parent), delete=False) as handle:
                temporary = handle.name
                json.dump({'best': self.best}, handle)
            os.replace(temporary, str(path))
        except OSError:
            pass
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def key(self, event):
        key = event.keysym.lower()
        moves = {'left': (-1, 0), 'a': (-1, 0), 'ф': (-1, 0),
                 'right': (1, 0), 'd': (1, 0), 'в': (1, 0),
                 'up': (0, -1), 'w': (0, -1), 'ц': (0, -1),
                 'down': (0, 1), 's': (0, 1), 'ы': (0, 1)}
        if key in moves:
            self.game.steer(moves[key])
        elif key in ('return', 'kp_enter'):
            before = self.game.state
            self.game.start()
            if before in ('ready', 'won'):
                self.sound.play('start')
        elif key in ('space', 'p', 'з'):
            self.game.toggle_pause()
        elif key in ('m', 'ь'):
            self.sound.toggle()
        elif key in ('r', 'к'):
            self.best = max(self.best, self.game.score)
            self.save_best()
            self.game = Game()
        elif key == 'escape':
            self.close()
            return
        self.draw()

    def focus_out(self, event):
        if self.game.state == 'playing':
            self.game.toggle_pause()
            self.draw()

    def tick(self):
        if self.closed:
            return
        for event in self.game.step():
            self.sound.play(event)
        if self.game.score > self.best:
            self.best = self.game.score
            if self.game.state in ('over', 'won', 'ready'):
                self.save_best()
        self.draw()
        self.after_id = self.root.after(max(65, 110 - (self.game.level - 1) * 5), self.tick)

    def draw_walls(self):
        c = self.canvas
        for y, row in enumerate(MAZE):
            for x, char in enumerate(row):
                if char == '#':
                    x1, y1 = x * CELL + 2, TOP + y * CELL + 2
                    c.create_rectangle(x1, y1, x1 + CELL - 4, y1 + CELL - 4,
                                       fill='#102345', outline='#306bdb', width=2)

    def text(self, x, y, text, size=12, color='#e7efff', anchor='center'):
        return self.canvas.create_text(x, y, text=text, font=('DejaVu Sans', size),
                                       fill=color, anchor=anchor, tags='dynamic')

    def draw(self):
        c, game = self.canvas, self.game
        c.delete('dynamic')
        width = game.width * CELL
        self.text(18, 20, 'PACMAN 2026', 18, '#ffdc55', 'w')
        self.text(width - 18, 20, 'Уровень {}'.format(game.level), 11, anchor='e')
        self.text(18, 51, 'Счёт: {}   Рекорд: {}'.format(game.score, self.best), 11, anchor='w')
        self.text(width - 18, 51, 'Жизни: {}'.format(game.lives), 11, anchor='e')
        for x, y in game.pellets:
            px, py = x * CELL + CELL / 2, TOP + y * CELL + CELL / 2
            c.create_oval(px - 2, py - 2, px + 2, py + 2, fill='#ffe8b0', outline='', tags='dynamic')
        for x, y in game.power_pellets:
            px, py = x * CELL + CELL / 2, TOP + y * CELL + CELL / 2
            radius = 6 if game.ticks % 8 < 4 else 4
            c.create_oval(px - radius, py - radius, px + radius, py + radius, fill='#fff3ce', outline='', tags='dynamic')
        for i, (x, y) in enumerate(game.ghosts):
            px, py = x * CELL + 3, TOP + y * CELL + 3
            color = '#4577ec' if game.power_ticks else COLORS[i]
            if 0 < game.power_ticks < 15 and game.ticks % 4 < 2:
                color = '#e7efff'
            c.create_arc(px, py, px + 20, py + 22, start=0, extent=180, fill=color, outline=color, tags='dynamic')
            c.create_polygon(px, py + 10, px + 20, py + 10, px + 20, py + 21,
                             px + 15, py + 17, px + 10, py + 21, px + 5, py + 17,
                             px, py + 21, fill=color, tags='dynamic')
            for eye in (5, 14):
                c.create_oval(px + eye - 3, py + 6, px + eye + 3, py + 13, fill='white', outline='', tags='dynamic')
                c.create_oval(px + eye - 1, py + 8, px + eye + 2, py + 12, fill='#142447', outline='', tags='dynamic')
        x, y = game.player
        px, py = x * CELL + 2, TOP + y * CELL + 2
        heading = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}.get(game.direction, 0)
        mouth = 12 + 25 * abs(math.sin(game.ticks * 0.8))
        if not game.invulnerable or game.ticks % 2 == 0:
            c.create_arc(px, py, px + 22, py + 22, start=heading + mouth,
                         extent=360 - mouth * 2, fill='#ffdb38', outline='', tags='dynamic')
        bottom = TOP + game.height * CELL
        audio = 'вкл' if self.sound.enabled else 'выкл'
        self.text(width / 2, bottom + 18, 'Стрелки / WASD • Пробел: пауза • M: звук ({})'.format(audio), 10)
        self.text(width / 2, bottom + 43, 'Enter: продолжить • R: новая игра • Esc: выход', 10, '#93a5c8')
        overlays = {'ready': ('ГОТОВЫ?', 'Enter — начать движение'),
                    'paused': ('ПАУЗА', 'Пробел — продолжить'),
                    'won': ('ЛАБИРИНТ ПРОЙДЕН!', 'Enter — следующий уровень'),
                    'over': ('ИГРА ОКОНЧЕНА', 'R — новая игра')}
        if game.state in overlays:
            mid = TOP + game.height * CELL / 2
            c.create_rectangle(25, mid - 60, width - 25, mid + 60,
                               fill=BACKGROUND, outline='#ffdb38', width=2, tags='dynamic')
            title, subtitle = overlays[game.state]
            self.text(width / 2, mid - 20, title, 20, '#ffdb38')
            self.text(width / 2, mid + 20, subtitle, 12)

    def check_smoke(self):
        if self.game.score <= 0 or self.game.player == (9, 15) or not self.canvas.find_withtag('dynamic'):
            print('GUI smoke test FAILED', file=sys.stderr)
            self.close()
            raise RuntimeError('GUI did not execute movement and scoring')
        print('GUI smoke test passed: window, canvas, keyboard, movement, scoring')
        self.close()

    def close(self):
        self.closed = True
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.best = max(self.best, self.game.score)
        self.save_best()
        self.sound.stop()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description='Pacman2026 — игра с оригинальной графикой и звуком')
    parser.add_argument('--smoke-test', action='store_true', help='автоматическая проверка графического запуска')
    options = parser.parse_args()
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print('Не удалось открыть окно. Запустите игру в графической сессии: {}'.format(error), file=sys.stderr)
        return 1
    failures = []
    def callback_error(kind, value, traceback):
        failures.append(str(value))
        print('Ошибка интерфейса: {}'.format(value), file=sys.stderr)
        root.quit()
    root.report_callback_exception = callback_error
    App(root, smoke=options.smoke_test)
    root.mainloop()
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
