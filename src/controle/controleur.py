import math
import numpy as np
from typing import List, Tuple
from utiles.constantes import physique as phys, specifications_drone as spec_drone
from controle.pid import PID, CoefficientsPID


class Controleur:
    """Controle l'altitude via feedforward (mg) + PID (correction en Newton)."""

    def __init__(self, consigne: float, coefficients: CoefficientsPID) -> None:
        """Initialise le PID, les limites, et les constantes physiques du drone."""
        self.masse: float = phys["MASSE"]
        self.g: float = 9.81
        self.factor_poussee: float = phys["POUSSEE"]
        self.nb_helices: int = spec_drone["NB_HELICES"]

        self.vmin: float = phys["VITESSE_HELICE_MIN"]
        self.vmax: float = phys["VITESSE_HELICE_MAX"]

        # Limites du PID pour Z (en Newton)
        limite_sortie = 0.6 * self.masse * self.g
        limites_sortie = (-limite_sortie, limite_sortie)
        limite_integrale = self.masse * self.g
        limites_integrale = (-limite_integrale, limite_integrale)

        self.pid_z = PID(
            coefficients,
            consigne=consigne[2],
            limites_sortie=limites_sortie,
            limites_integrale=limites_integrale,
            derivee_sur_mesure=True
        )

        # PID position pour x et y (m -> rad)
        coefficients_position = CoefficientsPID(
            proportionnel=1,
            integral=0.03,
            derive=0.3
        )

        self.pid_pos_x = PID(
            coefficients_position,
            consigne=0.0,                     # objectif: x = 0 m
            limites_sortie=(-0.4, 0.4),       # angle cible max ~ 20 deg
            limites_integrale=(-0.1, 0.1),
            derivee_sur_mesure=True
        )

        self.pid_pos_y = PID(
            coefficients_position,
            consigne=0.0,                     # objectif: y = 0 m
            limites_sortie=(-0.4, 0.4),
            limites_integrale=(-0.1, 0.1),
            derivee_sur_mesure=True
        )

        # PID attitude pour roll/pitch (rad -> moment)
        coefficients_attitude = CoefficientsPID(
            proportionnel=1.2,
            integral=0.0,
            derive=0.05
        )

        self.pid_att_pitch = PID(
            coefficients_attitude,
            consigne=0.0,                     # angle cible en rad
            limites_sortie=(-0.5, 0.5),       # moment abstrait
            limites_integrale=(0.0, 0.0),
            derivee_sur_mesure=True
        )

        self.pid_att_roll = PID(
            coefficients_attitude,
            consigne=0.0,
            limites_sortie=(-0.5, 0.5),
            limites_integrale=(0.0, 0.0),
            derivee_sur_mesure=True
        )

    
    def lire_termes_pid(self) -> Tuple[float, float, float]:
        """Lit les derniers termes PID (P, I, D)."""
        return self.pid_z.lire_derniers_termes()

    def reinitialiser(self, position_initiale: List) -> None:
        """Reinitialise l'etat interne du PID a une position donnee."""
        self.pid_pos_x.reinitialiser(position_initiale[0])
        self.pid_pos_y.reinitialiser(position_initiale[1])
        self.pid_z.reinitialiser(position_initiale[2])

    def _mixeur_quad(self, u_t: float, L: float, M: float, N: float) -> Tuple[float, float, float, float]:
        """
        Mixeur reproduisant exactement l'ancien comportement :
        0 : arriere
        1 : gauche
        2 : avant
        3 : droite

        u_t = vitesse commune (rad/s)
        L   = corr_roll   (rad/s)
        M   = corr_pitch  (rad/s)
        N   = corr_yaw (pour l'instant 0)
        """

        u0 = u_t - M + N      # arriere
        u1 = u_t + L - N      # gauche
        u2 = u_t + M + N      # avant
        u3 = u_t - L - N      # droite

        return u0, u1, u2, u3

    def _stabiliser_attitude(self, orientation_rpy: np.ndarray) -> Tuple[float, float]:
        """Retourne une correction minimale roll/pitch."""

        roll, pitch, yaw = orientation_rpy
        k: float = 0.2  # gain faible
        corr_roll: float = -k * roll
        corr_pitch: float = -k * pitch

        return corr_roll, corr_pitch
    

    def _vitesse_commune_altitude(self, altitude_mesuree: float, dt: float) -> Tuple[float, float, float, float]:
        """Calcule la vitesse commune via PID Z et retourne (vitesse, p, i, d)."""

        correction: float = self.pid_z(altitude_mesuree, dt)  # N
        f_total: float = max(0.0, self.masse * self.g + correction)  # N
        f_helice: float = f_total / float(self.nb_helices)

        if self.factor_poussee > 0.0:
            vitesse: float = math.sqrt(f_helice / self.factor_poussee)  # rad/s
        else:
            vitesse = 0.0

        # bornage commun
        vitesse = min(self.vmax, max(self.vmin, vitesse))
        p, i, d = self.lire_termes_pid()

        return vitesse, float(p), float(i), float(d)

    def appliquer_controle(
        self,
        altitude_mesuree: float,
        orientation_rpy: np.ndarray,
        position_xyz: np.ndarray,
        dt: float,
        pid_actif: bool,
        moteurs_forces_utilisateur: List[bool],
        vitesses_angulaires_actuelles: List[float],
    ) -> Tuple[List[float], float, float, float, float]:
        """Fusionne PID altitude + mixage quad en unités réelles (rad/s).
        Retourne (vitesses_angulaires, p, i, d, consigne)."""

        consigne: float = float(self.pid_z.consigne)

        # --- 1. PID Z -> vitesse commune (rad/s) ---
        if pid_actif:
            vitesse_commune, p, i, d = self._vitesse_commune_altitude(
                altitude_mesuree, dt
            )
            u_t: float = vitesse_commune
        else:
            p = i = d = 0.0
            u_t = float(sum(vitesses_angulaires_actuelles) / 4.0)

        # --- 2. Cascade XY - etape 1 : PID position -> angle cible (rad)
        angle_cible_x = self.pid_pos_x(position_xyz[0], dt)
        angle_cible_y = self.pid_pos_y(position_xyz[1], dt)

        # mise a jour de la consigne des PID attitude
        self.pid_att_pitch.consigne = angle_cible_x
        self.pid_att_roll.consigne  = angle_cible_y

        # mesure d'angle actuelle
        angle_mesure_x = 0.0
        angle_mesure_y = 0.0

        # --- 2. - etape 2 : PID attitude -> moments L/M
        moment_M = self.pid_att_pitch(angle_mesure_x, dt)
        moment_L = self.pid_att_roll(angle_mesure_y, dt)

        # gain faible pour eviter des valeurs trop violentes
        k_att: float = 0.03
        L: float = -k_att * moment_L
        M: float = -k_att * moment_M
        N: float = 0.0

        # --- 3. Mixage quad ---
        u0, u1, u2, u3 = self._mixeur_quad(u_t, L, M, N)
        vitesses_calculees: list[float] = [u0, u1, u2, u3]

        # --- 4. Motor override + bornage ---
        vitesses_finales: list[float] = vitesses_angulaires_actuelles[:]
        for idx in range(4):
            if not moteurs_forces_utilisateur[idx]:
                v = vitesses_calculees[idx]
                v = min(self.vmax, max(self.vmin, v))
                vitesses_finales[idx] = v

        return vitesses_finales, float(p), float(i), float(d), consigne
