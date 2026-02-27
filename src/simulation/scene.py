from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, CardMaker, WindowProperties
from typing import Tuple
from utiles.constantes import scene, physique, specifications_interface as spec_int
import math
import sys

class Scene(ShowBase):
    def __init__(self) -> None:
        """Initialise la scène, le decor, la camera et les contrôles."""
        super().__init__()

        props = WindowProperties()
        props.setOrigin(200, 200)  # X = 300px, Y = 200px (exemple)
        props.setSize(spec_int["TAILLE_FENETRE"][0])
        self.win.requestProperties(props)

        self._creer_sol()
        self.setBackgroundColor(1, 1, 1, 1)

        for nom, data in scene["zones"].items():
            x1, x2, y1, y2 = data["POSITION"]
            self._creer_zone(nom, x1, x2, y1, y2, data["COULEUR"])

        self.disableMouse()

        # Paramètres camera
        self.distance_camera: float = 20.0
        self.angle_camera_x: float = 20.0
        self.angle_camera_y: float = 30.0
        self.position_cible: Vec3 = Vec3(0, 0, 2)

        # Bindings
        self.accept("wheel_up", self._zoom_in)
        self.accept("wheel_down", self._zoom_out)
        self.accept("arrow_left", self.tourner_gauche)
        self.accept("arrow_right", self.tourner_droite)
        self.accept("q", self._quitter)

        # Task camera
        self.taskMgr.add(self._maj_camera, "majCamera")


    # Quitter
    def _quitter(self) -> None:
        """Quitte proprement le programme."""
        print("\nArret du programme...")
        sys.exit()


    # Orientation camera
    def tourner_gauche(self) -> None:
        """Pivote la camera vers la gauche."""
        self.angle_camera_y -= 6

    def tourner_droite(self) -> None:
        """Pivote la camera vers la droite."""
        self.angle_camera_y += 6


    # Zoom camera
    def _zoom_in(self) -> None:
        """Rapproche la camera du centre."""
        self.distance_camera = max(5.0, self.distance_camera - 1.0)

    def _zoom_out(self) -> None:
        """Eloigne la camera du centre."""
        self.distance_camera = min(80.0, self.distance_camera + 1.0)


    # Mise a jour camera
    def _maj_camera(self, task) -> int:
        """Met a jour la position orbitale de la camera."""
        rx = math.radians(self.angle_camera_x)
        ry = math.radians(self.angle_camera_y)

        cx = self.position_cible.x + self.distance_camera * math.cos(rx) * math.sin(ry)
        cy = self.position_cible.y - self.distance_camera * math.cos(rx) * math.cos(ry)
        cz = self.position_cible.z + self.distance_camera * math.sin(rx)

        self.camera.setPos(cx, cy, cz)
        self.camera.lookAt(self.position_cible)

        return task.cont


    # Sol
    def _creer_sol(self) -> None:
        """Cree le sol principal de la scène."""
        cm = CardMaker("sol")
        cm.setFrame(-50, 50, -50, 50)
        sol = self.render.attachNewNode(cm.generate())
        sol.setP(-90)
        sol.setZ(physique["HAUTEUR_SOL"])
        sol.setColor(1, 1, 1, 1)


    # Zones colorees
    def _creer_zone(
        self,
        nom: str,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
        couleur: Tuple[float, float, float, float],
        hauteur_z: float = 0.1
    ) -> None:
        """Cree une zone rectangulaire coloree sur le sol."""
        cm = CardMaker(nom)
        cm.setFrame(xmin, xmax, ymin, ymax)

        zone = self.render.attachNewNode(cm.generate())
        zone.setP(-90)
        zone.setZ(physique["HAUTEUR_SOL"] + 0.01)
        zone.setPos(0, 0, hauteur_z)
        zone.setColor(*couleur)