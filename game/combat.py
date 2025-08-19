from core.events import LOG
from .actor import Actor

def attack(attacker: Actor, defender: Actor) -> bool:
    # If defender is dead return TRUE
    base = max(1, attacker.atk - defender.df)
    died = defender.take_damage(base)
    if died:
        LOG.add(f"{attacker.name} defeated {defender.name}! ({base} damage).")
    else:
        LOG.add(f"{attacker.name} attacks {defender.name} for {base} damage.")
    return died