from PyQt5.QtCore import QObject, pyqtSignal
from typing import List
import numpy as np

from direct.showbase.ShowBaseGlobal import globalClock
from utiles.constantes import specifications_simulation as spec_sim, physique as phys
from controle.pid import CoefficientsPID
from controle.controleur import Controleur


class Simulateur(QObject):
    altitude_changee = pyqtSignal(float)
    pid_mis_a_jour = pyqtSignal(float, float, float, float, float) # ordre: P, I, D, consigne, mesure
    vitesses_moteurs_mises_a_jour = pyqtSignal(list)

    def __init__(self, scene, modele_drone, physique_drone) -> None:
        """Initialise la simulation : physique, PID, modele 3D et boucle de mise à jour."""
        super().__init__()

        self.scene = scene
        self.modele_drone = modele_drone
        self.physique_drone = physique_drone

        # Vecteur vitesses helices (rad/s)
        self.vitesses_helices: List[float] = list(spec_sim["VITESSES_ROTATION_HELICES"])
        self.vitessse_max: float = float(phys["VITESSE_HELICE_MAX"])
        self.moteurs_forces_utilisateur = [False, False, False, False]

        # PID altitude
        coeffs = CoefficientsPID(**spec_sim["PID"]["Z"])
        self.consigne: List[float] = list(spec_sim["CONSIGNE"])
        self.controleur = Controleur(self.consigne, coeffs)
        self.controleur.reinitialiser(self.physique_drone.position_xyz)
        self.pid_actif: bool = True

        # Tâche Panda pour la simulation
        self.scene.taskMgr.add(self.mettre_a_jour_simulation, "tacheSimulation")

    # ============================
    # Communication entre la fenetre PyQt5 et la scene panda3D
    # ============================

    def fixer_vitesse_helice(self, index: int, vitesse: float) -> None:
        """Fixe la vitesse d'une helice en la bornant entre 0 et vitessse_max."""
        self.moteurs_forces_utilisateur[index] = True
        self.vitesses_helices[index] = max(0.0, min(self.vitessse_max, float(vitesse)))

    def tourner_gauche(self) -> None:
        """Fait pivoter la camera vers la gauche via la scene."""
        self.scene.tourner_gauche()

    def tourner_droite(self) -> None:
        """Fait pivoter la camera vers la droite via la scene."""
        self.scene.tourner_droite()
    
    # ============================
    # Reinitialisation propre de la simulation
    # ============================

    def initialiser_simulation(self) -> None:
        """Remet la simulation dans son etat initial."""
        try:
            # Position et orientation
            self.physique_drone.position_xyz = np.array([0.0, 0.0, 1.0], dtype=float)
            self.physique_drone.vitesse_xyz = np.array([0.0, 0.0, 0.0], dtype=float)
            self.physique_drone.orientation_rpy = np.array([0.0, 0.0, 0.0], dtype=float)
            self.physique_drone.vitesse_angulaire_rpy = np.array([0.0, 0.0, 0.0], dtype=float)
            self.physique_drone.crash = False

            # Reset PID interne
            x, y, z = self.physique_drone.position_xyz
            self.controleur.reinitialiser([x, y, z])

            # Helices : retour aux vitesses par defaut
            self.vitesses_helices = list(spec_sim["VITESSES_ROTATION_HELICES"])

            # Mise a jour du modele 3D
            self.modele_drone.mettre_a_jour_pose(
                self.physique_drone.position_xyz,
                self.physique_drone.orientation_rpy
            )

        except Exception as err:
            print("Erreur reinitialisation simulation :", err)

    # ============================
    # Gestion de la scene 3D
    # ============================

    def _appliquer_controleur(self, dt: float) -> None:
        altitude: float = float(self.physique_drone.position_xyz[2])

        vitesses_angulaires, p, i, d, consigne = self.controleur.appliquer_controle(
            altitude_mesuree=altitude,
            orientation_rpy=self.physique_drone.orientation_rpy,
            position_xyz=self.physique_drone.position_xyz,
            dt=dt,
            pid_actif=self.pid_actif,
            moteurs_forces_utilisateur=self.moteurs_forces_utilisateur,
            vitesses_angulaires_actuelles=self.vitesses_helices,
        )

        self.vitesses_helices = vitesses_angulaires
        self.pid_mis_a_jour.emit(float(p), float(i), float(d), float(consigne), float(altitude))

    def _simuler_physique(self, dt: float) -> None:
        """Fait avancer la simulation physique du drone."""
        self.physique_drone.etape_simulation(self.vitesses_helices, dt)

    def _emettre_altitude(self) -> None:
        """emet l'altitude actuelle vers Qt."""
        z = float(self.physique_drone.position_xyz[2])
        self.altitude_changee.emit(z)

    def _gerer_crash(self) -> None:
        """Coupe les moteurs en cas de crash."""
        if self.physique_drone.crash:
            self.vitesses_helices = [0.0, 0.0, 0.0, 0.0]

    def _mettre_a_jour_pose_3d(self) -> None:
        """Met à jour le modele 3D du drone (position + orientation)."""
        self.modele_drone.mettre_a_jour_pose(
            self.physique_drone.position_xyz,
            self.physique_drone.orientation_rpy
        )

    def _mettre_a_jour_helices_visuel(self, dt: float) -> None:
        """Applique les vitesses aux helices visuelles et les fait tourner."""
        sens = spec_sim["SENS_HELICES"]

        for i in range(4):
            self.modele_drone.helices[i][1] = self.vitesses_helices[i] * sens[i]

        self.modele_drone.mettre_a_jour_helices(dt)

    # Methode principale
    def mettre_a_jour_simulation(self, task) -> int:
        """Pipeline complet de mise à jour : PID, physique, 3D."""
        dt = globalClock.getDt()

        self._appliquer_controleur(dt)
        self._simuler_physique(dt)
        self._emettre_altitude()
        self._gerer_crash()
        self.vitesses_moteurs_mises_a_jour.emit(list(self.physique_drone.vitesses_helices_reelles))
        
        for i in range(4):
            if self.moteurs_forces_utilisateur[i]:
                if abs(self.vitesses_helices[i] - self.physique_drone.vitesses_helices_reelles[i]) < 0.5:
                    self.moteurs_forces_utilisateur[i] = False

        self._mettre_a_jour_pose_3d()
        self._mettre_a_jour_helices_visuel(dt)

        return task.cont