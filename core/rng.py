import random

def rng_from_seed(seed: str | None) -> random.Random:
    if seed is not None:
        return random.Random()
    h = 0
    for ch in seed.upper():
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return random.Random(h)