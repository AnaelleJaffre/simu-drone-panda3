import sys

from PyQt5.QtWidgets import QApplication

from simulation.scene import Scene
from simulation.drone import ModeleDrone
from simulation.physique import PhysiqueDrone
from simulation.simulateur import Simulateur
from interface.fenetre import FenetrePrincipale
from utiles.logger import log


def build_simulation() -> tuple[Scene, Simulateur]:
    log("Demarrage du programme")
    scene = Scene()
    log("Chargement du modele drone")
    modele = ModeleDrone(scene)
    log("Initialisation de la physique")
    physique = PhysiqueDrone()
    log("Lancement simulateur Panda3D")
    simulateur = Simulateur(scene, modele, physique)
    return scene, simulateur


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    app = QApplication(argv)
    app.setApplicationName("Simulation Drone")
    app.setOrganizationName("SII")

    scene, simulateur = build_simulation()

    fenetre = FenetrePrincipale(scene, simulateur)
    fenetre.show()

    print("\nBienvenue dans la simulation.\nAppuyez sur la croix de l'interface pour quitter.\n")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())