from core.events import LOG
from .actor import Actor

def attack(attacker: Actor, defender: Actor, *, apply_poison: bool = False) -> bool:
    """Повертає True, якщо захисник помер."""
    base = max(1, attacker.atk - defender.df)
    died = defender.take_damage(base)
    if apply_poison:
        defender.add_status("poison", ticks=3, dmg=1)
        LOG.add(f"{defender.name} отруєно!")
    if died:
        LOG.add(f"{attacker.name} вбиває {defender.name} ({base}).")
    else:
        LOG.add(f"{attacker.name} б'є {defender.name} на {base}. [{defender.hp}/{defender.max_hp}]")
    return died