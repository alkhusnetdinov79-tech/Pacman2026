"""Game rules independent of display and sound (Python 3.6+)."""
import random
from collections import deque

MAZE = (
    '###################',
    '#o.......#.......o#',
    '#.##.###.#.###.##.#',
    '#.................#',
    '#.##.#.#####.#.##.#',
    '#....#...#...#....#',
    '####.###.#.###.####',
    '#....#.......#....#',
    '#.##.#.##.##.#.##.#',
    '#......#...#......#',
    '#.####.#...#.####.#',
    '#......#...#......#',
    '#.##.#.#####.#.##.#',
    '#....#...#...#....#',
    '####.###.#.###.####',
    '#.................#',
    '#.##.###.#.###.##.#',
    '#o.#.....#.....#.o#',
    '##.#.#.#####.#.#.##',
    '#....#...#...#....#',
    '#.######.#.######.#',
    '#.................#',
    '###################',
)
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
PLAYER_START = (9, 15)
GHOST_STARTS = ((9, 9), (8, 10), (10, 10), (9, 11))


class Game(object):
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.width, self.height = len(MAZE[0]), len(MAZE)
        self.floor = {(x, y) for y, row in enumerate(MAZE)
                      for x, char in enumerate(row) if char != '#'}
        self.score, self.lives, self.level = 0, 3, 1
        self.state = 'ready'
        self.load_level()

    def load_level(self):
        self.pellets = set(self.floor)
        self.power_pellets = {(x, y) for y, row in enumerate(MAZE)
                              for x, char in enumerate(row) if char == 'o'}
        self.pellets.difference_update(self.power_pellets)
        self.pellets.difference_update((PLAYER_START,) + GHOST_STARTS)
        self.reset_positions()

    def reset_positions(self):
        self.player = PLAYER_START
        self.direction = (0, 0)
        self.wanted = (0, 0)
        self.ghosts = list(GHOST_STARTS)
        self.ghost_previous = [None] * 4
        self.power_ticks, self.combo, self.ticks = 0, 0, 0
        self.invulnerable = 12

    def start(self):
        if self.state == 'ready':
            self.state = 'playing'
        elif self.state == 'won':
            self.level += 1
            self.load_level()
            self.state = 'playing'

    def toggle_pause(self):
        if self.state == 'playing':
            self.state = 'paused'
        elif self.state == 'paused':
            self.state = 'playing'

    def steer(self, direction):
        if direction in DIRECTIONS:
            self.wanted = direction

    def neighbor(self, pos, direction):
        return (pos[0] + direction[0], pos[1] + direction[1])

    def legal_moves(self, pos):
        return [self.neighbor(pos, d) for d in DIRECTIONS
                if self.neighbor(pos, d) in self.floor]

    def distances(self, target):
        target = min(self.floor, key=lambda p: abs(p[0] - target[0]) + abs(p[1] - target[1]))
        result, queue = {target: 0}, deque([target])
        while queue:
            pos = queue.popleft()
            for nxt in self.legal_moves(pos):
                if nxt not in result:
                    result[nxt] = result[pos] + 1
                    queue.append(nxt)
        return result

    def collide(self, events):
        for index, pos in enumerate(self.ghosts):
            if pos != self.player:
                continue
            if self.power_ticks:
                self.combo += 1
                self.score += 200 * (2 ** min(self.combo - 1, 3))
                self.ghosts[index] = GHOST_STARTS[index]
                self.ghost_previous[index] = None
                events.append('ghost')
            elif not self.invulnerable:
                self.lives -= 1
                events.append('death')
                self.reset_positions()
                self.state = 'ready' if self.lives else 'over'
                return True
        return False

    def step(self):
        if self.state != 'playing':
            return []
        events = []
        self.ticks += 1
        self.power_ticks = max(0, self.power_ticks - 1)
        self.invulnerable = max(0, self.invulnerable - 1)
        if self.neighbor(self.player, self.wanted) in self.floor:
            self.direction = self.wanted
        nxt = self.neighbor(self.player, self.direction)
        if nxt in self.floor:
            self.player = nxt
        if self.player in self.pellets:
            self.pellets.remove(self.player)
            self.score += 10
            events.append('eat')
        if self.player in self.power_pellets:
            self.power_pellets.remove(self.player)
            self.score += 50
            self.power_ticks, self.combo = 65, 0
            events.append('power')
        if self.collide(events):
            return events
        # Ghosts move two out of every three ticks, or every other tick while frightened.
        if self.ticks % (2 if self.power_ticks else 3) != 0:
            for index, pos in enumerate(self.ghosts):
                options = self.legal_moves(pos)
                forward = [p for p in options if p != self.ghost_previous[index]]
                options = forward or options
                if not options:
                    continue
                if self.power_ticks:
                    nxt = self.rng.choice(options)
                else:
                    targets = [self.player,
                               (self.player[0] + self.direction[0] * 3,
                                self.player[1] + self.direction[1] * 3),
                               (1, 1) if self.ticks % 100 < 25 else self.player,
                               (17, 21) if abs(pos[0] - self.player[0]) + abs(pos[1] - self.player[1]) < 5 else self.player]
                    distances = self.distances(targets[index])
                    self.rng.shuffle(options)
                    nxt = min(options, key=lambda p: distances.get(p, 999))
                self.ghost_previous[index], self.ghosts[index] = pos, nxt
            if self.collide(events):
                return events
        if not self.pellets and not self.power_pellets:
            self.state = 'won'
            self.score += 1000
            events.append('win')
        return events
