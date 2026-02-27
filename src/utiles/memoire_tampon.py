from typing import Deque, Tuple
from collections import deque

class MemoireTamponPid:
    """Tampon glissant faible cout pour 0.5 s de donnees."""
    def __init__(self, fenetre_s: float) -> None:
        self.fenetre_s: float = float(fenetre_s)
        self.deque_donnees: Deque[Tuple[float, float, float, float, float, float]] = deque()
        # tuple: (t, p, i, d, consigne, mesure)

    def ajouter(self, t: float, p: float, i: float, d: float, consigne: float, mesure: float) -> None:
        self.deque_donnees.append((t, p, i, d, consigne, mesure))
        self._purger(t)

    def _purger(self, t_courant: float) -> None:
        t_limite = t_courant - self.fenetre_s
        while self.deque_donnees and self.deque_donnees[0][0] < t_limite:
            self.deque_donnees.popleft()

    def lire_series(self) -> Tuple[list, list, list, list, list, list]:
        t, p, i, d, c, m = [], [], [], [], [], []
        for e in self.deque_donnees:
            t.append(e[0])
            p.append(e[1]); i.append(e[2]); d.append(e[3])
            c.append(e[4]); m.append(e[5])
        return t, p, i, d, c, m