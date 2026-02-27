from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CoefficientsPID:
    """Conteneur simple pour les coefficients PID."""
    proportionnel: float
    integral: float
    derive: float


class PID:
    """Controleur PID avec saturation et derivee sur la mesure en option."""

    def __init__(
        self,
        coefficients: CoefficientsPID,
        consigne: float = 0.0,
        limites_sortie: Tuple[Optional[float], Optional[float]] = (None, None),
        limites_integrale: Tuple[Optional[float], Optional[float]] = (None, None),
        derivee_sur_mesure: bool = True
    ) -> None:
        """Initialise les parametres du PID, les limites et l'etat interne."""
        self.coeff = coefficients
        self.consigne = float(consigne)

        self.sortie_min, self.sortie_max = limites_sortie
        self.integrale_min, self.integrale_max = limites_integrale
        self.derivee_sur_mesure = derivee_sur_mesure

        self.erreur_precedente: float = 0.0
        self.mesure_precedente: Optional[float] = None
        self.integrale: float = 0.0

        # Sauvegarde
        self.derniers_termes: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def reinitialiser(self, valeur_initiale: float = 0.0) -> None:
        """Reinitialise l'etat interne du PID a partir d'une valeur initiale."""
        self.erreur_precedente = self.consigne - valeur_initiale
        self.mesure_precedente = valeur_initiale
        self.integrale = 0.0

    def __call__(self, mesure: float, dt: float) -> float:
        """Calcule la sortie PID pour une mesure et un pas de temps donnes."""
        erreur = self.consigne - mesure
        print(f"Erreur : {erreur} = {self.consigne} (consigne) - {mesure} (mesure)")

        # Terme integral (avec saturation anti‑windup simple)
        self.integrale += erreur * dt
        if self.integrale_min is not None:
            self.integrale = max(self.integrale_min, self.integrale)
        if self.integrale_max is not None:
            self.integrale = min(self.integrale_max, self.integrale)

        # Terme derive (sur la mesure ou sur l'erreur)
        if self.mesure_precedente is None or dt <= 1e-2:
            derivee = 0.0
        else:
            d_mesure = (mesure - self.mesure_precedente) / dt
            d_erreur = (erreur - self.erreur_precedente) / dt
            derivee = -d_mesure if self.derivee_sur_mesure else d_erreur
            

        # Sortie PID
        sortie = (
            self.coeff.proportionnel * erreur +
            self.coeff.integral * self.integrale +
            self.coeff.derive * derivee
        )

        # Saturation de la sortie
        if self.sortie_min is not None:
            sortie = max(self.sortie_min, sortie)
        if self.sortie_max is not None:
            sortie = min(self.sortie_max, sortie)

        self.erreur_precedente = erreur
        self.mesure_precedente = mesure

        # Termes P, I, D elementaires
        terme_p = max(-100.0, min(100.0, self.coeff.proportionnel * erreur))
        terme_i = max(-100.0, min(100.0, self.coeff.integral * self.integrale))
        terme_d = max(-100.0, min(100.0, self.coeff.derive * derivee))

        # Sortie PID
        sortie = terme_p + terme_i + terme_d
        # borne derivee pour eviter les pics
        sortie = max(-30.0, min(30.0, sortie))
        print("Sortie PID : ", sortie, " = ", terme_p, " + ", terme_i, " + ", terme_d, "\n")

        # Sauvegarde pour l'interface
        self.derniers_termes = (terme_p, terme_i, terme_d)

        return sortie
    
    def lire_derniers_termes(self) -> Tuple[float, float, float]:
        """Retourne les derniers termes P, I, D."""
        return self.derniers_termes