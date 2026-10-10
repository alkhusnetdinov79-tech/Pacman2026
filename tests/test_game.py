import unittest
import wave
from pathlib import Path
from pacman2026.model import Game, MAZE, PLAYER_START, GHOST_STARTS

class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=7)

    def safe(self):
        self.game.start()
        self.game.invulnerable = 1000

    def test_maze_reachable(self):
        self.assertTrue(all(len(row) == self.game.width for row in MAZE))
        self.assertEqual(set(self.game.distances(PLAYER_START)), self.game.floor)
        self.assertTrue(set(GHOST_STARTS).issubset(self.game.floor))

    def test_move_eat_score(self):
        self.safe()
        self.game.steer((-1, 0))
        self.assertIn('eat', self.game.step())
        self.assertEqual(self.game.player, (8, 15))
        self.assertEqual(self.game.score, 10)
        self.assertNotIn((8, 15), self.game.pellets)

    def test_wall(self):
        self.safe()
        self.game.player = (1, 1)
        self.game.steer((-1, 0))
        self.game.step()
        self.assertEqual(self.game.player, (1, 1))

    def test_queued_turn(self):
        self.safe()
        self.game.player = (7, 15)
        self.game.direction = (-1, 0)
        self.game.steer((0, -1))
        self.game.step()
        self.assertEqual(self.game.player, (6, 15))
        self.game.player = (4, 15)
        self.game.step()
        self.assertEqual(self.game.player, (4, 14))

    def test_pause(self):
        self.safe()
        self.game.toggle_pause()
        before = (self.game.player, self.game.ticks, self.game.score)
        self.assertEqual(self.game.step(), [])
        self.assertEqual((self.game.player, self.game.ticks, self.game.score), before)
        self.game.toggle_pause()
        self.assertEqual(self.game.state, 'playing')

    def test_power(self):
        self.safe()
        self.game.player = (1, 1)
        self.assertIn('power', self.game.step())
        self.assertEqual(self.game.score, 50)
        self.assertGreater(self.game.power_ticks, 0)

    def test_ghost_combo(self):
        self.safe()
        self.game.power_ticks = 20
        self.game.ghosts[0] = self.game.player
        events = []
        self.game.collide(events)
        self.assertEqual(events, ['ghost'])
        self.assertEqual(self.game.score, 200)
        self.game.ghosts[1] = self.game.player
        self.game.collide(events)
        self.assertEqual(self.game.score, 600)
        self.assertEqual(self.game.lives, 3)

    def test_death_and_game_over(self):
        pellets = set(self.game.pellets)
        for remaining in (2, 1, 0):
            self.game.start()
            self.game.invulnerable = 0
            self.game.ghosts[0] = self.game.player
            self.assertTrue(self.game.collide([]))
            self.assertEqual(self.game.lives, remaining)
            self.assertEqual(self.game.pellets, pellets)
        self.assertEqual(self.game.state, 'over')
        self.game.start()
        self.assertEqual(self.game.state, 'over')

    def test_win_and_next_level(self):
        self.safe()
        self.game.pellets.clear()
        self.game.power_pellets.clear()
        self.assertIn('win', self.game.step())
        self.assertEqual(self.game.state, 'won')
        self.game.start()
        self.assertEqual(self.game.level, 2)
        self.assertEqual(self.game.state, 'playing')
        self.assertTrue(self.game.pellets)

    def test_simulation(self):
        self.safe()
        for tick in range(300):
            self.game.steer(self.game.rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1))))
            self.game.step()
            self.assertIn(self.game.player, self.game.floor)
            self.assertTrue(set(self.game.ghosts).issubset(self.game.floor))

    def test_audio_resources(self):
        directory = Path(__file__).resolve().parent.parent / 'assets' / 'sounds'
        for name in ('start', 'eat', 'power', 'ghost', 'death', 'win'):
            with wave.open(str(directory / (name + '.wav')), 'rb') as sound:
                self.assertEqual(sound.getnchannels(), 1)
                self.assertEqual(sound.getsampwidth(), 2)
                self.assertEqual(sound.getframerate(), 22050)
                self.assertGreater(sound.getnframes(), 1000)

if __name__ == '__main__':
    unittest.main()
