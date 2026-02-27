import numpy as np
from typing import Iterable
from utiles.constantes import (
    physique as phys,
    specifications_simulation as spec_sim,
    specifications_drone as spec_drone
)
from utiles.transformations import produit_vectoriel_gyroscopique, matrice_rotation


class PhysiqueDrone:
    def __init__(self) -> None:
        """Initialise l'etat physique complet du drone."""
        self.position_xyz: np.ndarray = np.array(phys["POSITION_INITIALE"], dtype=float)
        self.vitesse_xyz: np.ndarray = np.zeros(3)

        self.orientation_rpy: np.ndarray = np.zeros(3)
        self.vitesse_angulaire_rpy: np.ndarray = np.zeros(3)

        # Modele moteur (1er ordre)
        self.vitesses_helices_reelles: np.ndarray = np.array(
            spec_sim["VITESSES_ROTATION_HELICES"], dtype=float
        )
        self.tau_moteur: float = phys["TAU_MOTEUR"]

        # Parametre drone
        self.surface_drone_lateral: float = 2 * spec_drone["LONGUEUR_BRAS"] * spec_drone["HAUTEUR_DRONE"]
        self.surface_drone_dessus: float = (2 * spec_drone["LONGUEUR_BRAS"])**2
        self.coeffs_trainee: np.ndarray = np.array(spec_drone["COEFFS_TRAINEE"])

        # Parametres physiques
        self.masse: float = phys["MASSE"]
        self.poussee: float = phys["POUSSEE"]
        self.Ix, self.Iy, self.Iz = phys["INERTIE"]
        self.L: float = spec_drone["LONGUEUR_BRAS"]
        self.k_yaw: float = phys["K_YAW"]
        self.amortissement_ang: float = phys["AMORTISSEMENT_ANGULAIRE"]
        self.frottement_ang: float = phys["FROTTEMENT_ANGULAIRE"]
        self.inertie_rotor: float = phys["INERTIE_ROTOR"]
        self.densite_air: float = phys["DENSITE_AIR"]   
        self.frottements: np.ndarray = np.array(
            [phys["FROTTEMENTS"]["lineaire"],
            phys["FROTTEMENTS"]["quadratique"]],
            dtype=float
        )

        # Sens de rotation (+1 / -1 par helice)
        self.sens: np.ndarray = np.array(spec_sim["SENS_HELICES"], dtype=float)

        # Verification de crash
        self.crash: bool = False


    # 1) Dynamique moteur
    def _maj_moteurs(self, vitesses_cibles: np.ndarray, dt: float) -> None:
        """Met à jour les vitesses reelles des moteurs (1er ordre)."""
        self.vitesses_helices_reelles += (
            (vitesses_cibles - self.vitesses_helices_reelles) * dt / self.tau_moteur
        )


    # 2) Trainee
    def _calcul_trainee(self) -> np.ndarray:
        """Retourne la trainee."""

        # Calcul de la vitesse du drone dans le repere corps
        R = matrice_rotation(self.orientation_rpy) # corps -> monde
        v_corps: np.ndarray = R.T @ self.vitesse_xyz # monde -> corps
        
        # Surfaces et self.coeffs_trainee par axe (repere corps)
        surface_corps: np.ndarray = np.array([
            self.surface_drone_lateral,   # axe X corps
            self.surface_drone_lateral,   # axe Y corps
            self.surface_drone_dessus     # axe Z corps (montee/descente)
        ], dtype=float)

        # Force resultante de trainee
        trainee: np.ndarray = -0.5 * self.densite_air * surface_corps * self.coeffs_trainee * np.abs(v_corps) * v_corps
        
        return R @ trainee # reconversion dans le repere monde


    # 3) Poussees
    def _calcul_poussees(self) -> np.ndarray:
        """Retourne les poussees T[i] = k_f * w_i^2."""
        w2 = self.vitesses_helices_reelles ** 2
        return self.poussee * w2


    # 4) Moments
    def _calcul_moments(self, T: np.ndarray) -> np.ndarray:
        """Calcule les moments (tau_x, tau_y, tau_z) dans le repère corps."""
        
        # Couples aerodynamiques
        tau_x = self.L * (T[1] - T[3])
        tau_y = self.L * (T[2] - T[0])
        tau_z = self.k_yaw * np.dot(self.sens, T)

        # Couple gyroscopique des rotors
        Lz = np.sum(self.inertie_rotor * self.vitesses_helices_reelles * self.sens)
        moment_cinetique = np.array([0.0, 0.0, Lz])
        couples_gyro = np.cross(self.vitesse_angulaire_rpy, moment_cinetique)
        
        return np.array([tau_x, tau_y, tau_z]) + couples_gyro


    # 5) Dynamique angulaire
    def _maj_dynamique_angulaire(self, tau: np.ndarray, dt: float) -> None:
        """Intègre les vitesses et angles à partir des moments appliques."""
        gyro = produit_vectoriel_gyroscopique(self.vitesse_angulaire_rpy, (self.Ix, self.Iy, self.Iz))

        # Amortissement
        amort = self.amortissement_ang * self.vitesse_angulaire_rpy

        # Acceleration_omega = (tau - gyro - amort)/I
        alpha = (tau - gyro - amort) / np.array([self.Ix, self.Iy, self.Iz])

        self.vitesse_angulaire_rpy += alpha * dt
        self.orientation_rpy       += self.vitesse_angulaire_rpy * dt


    # 6) Dynamique lineaire
    def _maj_dynamique_lineaire(self, T: np.ndarray, dt: float) -> None:
        """Integre la dynamique lineaire dans le repere monde."""
        
        # Poussee dans le repere corps
        pouss_corps = np.array([0.0, 0.0, np.sum(T)]) # la rotation actuelle incline la poussee : composantes horizontales reelles

        # Conversion en repere monde
        R = matrice_rotation(self.orientation_rpy)
        pouss_monde = R @ pouss_corps
        
        # Trainee aerodynamique
        trainee = self._calcul_trainee()

        # Poids
        poids = np.array([0.0, 0.0, -9.81 * self.masse])

        # Frottements, surtout pour eviter les derives en XY
        k_lineaire, k_quadratique = self.frottements
        F_frottements = -k_lineaire * self.vitesse_xyz -k_quadratique * np.linalg.norm(self.vitesse_xyz) * self.vitesse_xyz

        # Somme des forces
        forces = pouss_monde + poids + trainee + F_frottements

        acc = forces / self.masse
        self.vitesse_xyz += acc * dt
        self.position_xyz += self.vitesse_xyz * dt
        

    # 7) Gestion du sol et stabilisation
    def _gestion_sol_et_stabilisation(self, dt: float) -> None:
        """Gère collision sol + stabilisation artificielle de l'attitude."""
        hauteur_min = phys["HAUTEUR_SOL"] + 0.2

        if self.position_xyz[2] < hauteur_min:

            # Drone au sol, en position horizontale
            self.position_xyz[2] = hauteur_min
            self.orientation_rpy[0] = 0.0  # roll
            self.orientation_rpy[1] = 0.0  # pitch

            vitesse_xy = self.vitesse_xyz[:2]

            # Frottements horizontaux au sol
            if np.linalg.norm(vitesse_xy) > 1e-4:
                force_frottement_xy = - self.frottement_ang * vitesse_xy
                self.vitesse_xyz[:2] += force_frottement_xy * dt
            if np.linalg.norm(vitesse_xy) < 1e-1:
                self.vitesse_xyz[2] = 0
                self.vitesse_angulaire_rpy[2] = 0 

            # Amortissement : il n'a plus de vitesse angulaire
            self.vitesse_angulaire_rpy[2] *= np.exp(-self.k_yaw * dt)

            # Rebond si l'impact est assez violent
            if self.vitesse_xyz[2] < -phys["SEUIL_REBOND"]:
                self.vitesse_xyz[2] = -self.vitesse_xyz[2] * phys["COEFF_REBOND"]
            else:
                self.vitesse_xyz[2] = 0.0

            self.crash = True
            
        else:
            self.crash = False


    # Fonction principale
    def etape_simulation(self, vitesses_helices: Iterable[float], dt: float) -> None:
        """Pipeline complet : moteurs, forces, moments, dynamique."""

        vitesses_cibles = np.asarray(vitesses_helices, dtype=float)

        self._maj_moteurs(vitesses_cibles, dt)
        T   = self._calcul_poussees()
        tau = self._calcul_moments(T)        

        self._maj_dynamique_angulaire(tau, dt)
        self._maj_dynamique_lineaire(T, dt)
        self._gestion_sol_et_stabilisation(dt)
