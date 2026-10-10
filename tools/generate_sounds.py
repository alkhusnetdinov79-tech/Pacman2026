#!/usr/bin/env python3
"""Generate original, short PCM effects. No external audio assets."""
import math
from pathlib import Path
import struct
import wave

RATE = 22050
EFFECTS = {
    'eat': [(780, .04), (520, .04)],
    'power': [(330, .1), (440, .1), (660, .15), (880, .15)],
    'ghost': [(660, .06), (880, .06), (1320, .12)],
    'death': [(660, .12), (520, .12), (390, .12), (260, .16), (130, .25)],
    'win': [(523, .12), (659, .12), (784, .12), (1047, .3)],
    'start': [(262, .1), (330, .1), (392, .1), (523, .2)],
}


def generate(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, notes in EFFECTS.items():
        data = bytearray()
        for frequency, duration in notes:
            count = int(RATE * duration)
            for i in range(count):
                envelope = min(1.0, i / (RATE * .008), (count - i) / (RATE * .025))
                value = int(10000 * envelope * math.sin(2 * math.pi * frequency * i / RATE))
                data.extend(struct.pack('<h', value))
        with wave.open(str(directory / (name + '.wav')), 'wb') as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(RATE)
            handle.writeframes(data)


if __name__ == '__main__':
    generate(Path(__file__).resolve().parent.parent / 'assets' / 'sounds')
