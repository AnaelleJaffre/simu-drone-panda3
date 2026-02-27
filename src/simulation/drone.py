from panda3d.core import NodePath, LineSegs
from utiles.constantes import specifications_drone as spec_drone
from typing import List, Tuple
import math


class ModeleDrone:
    def __init__(self, scene) -> None:
        """Initialise le modèle 3D du drone et ses hélices."""
        self.scene = scene

        self.noeud_drone: NodePath = NodePath("drone")
        self.noeud_drone.reparentTo(scene.render)
        self.noeud_drone.setPos(0, 0, 2)

        self._creer_corps()

        L = spec_drone["LONGUEUR_BRAS"]
        self.positions_helices: List[Tuple[float, float, float]] = [
            ( 0, -L, 0),   # 0 : arriere
            (-L,  0, 0),   # 1 : gauche
            ( 0,  L, 0),   # 2 : avant
            ( L,  0, 0)    # 3 : droite
        ]

        self.helices: List[Tuple[NodePath, float]] = []
        self._creer_helices()

    def _creer_corps(self) -> None:
        """Crée la croix représentant le corps du drone."""
        L = spec_drone["LONGUEUR_BRAS"]
        seg = LineSegs()
        seg.setColor(spec_drone["COULEUR"])

        # Bras X
        seg.moveTo(-L, 0, 0)
        seg.drawTo(L, 0, 0)
        # Bras Y
        seg.moveTo(0, -L, 0)
        seg.drawTo(0, L, 0)

        self.noeud_drone.attachNewNode(seg.create())

    def _creer_helices(self) -> None:
        """Instancie les 4 hélices et les positionne."""
        for x, y, z in self.positions_helices:
            helice = self._generer_helice()
            helice.reparentTo(self.noeud_drone)
            helice.setPos(x, y, z)
            self.helices.append([helice, 0.0])

    def _generer_helice(self) -> NodePath:
        """Génère une hélice stylisée sous forme de croix."""
        R = spec_drone["RAYON_HELICES"]
        seg = LineSegs()
        seg.setThickness(spec_drone["EPAISSEUR_HELICES"])
        seg.setColor(spec_drone["COULEUR"])

        seg.moveTo(-R, 0, 0)
        seg.drawTo(R, 0, 0)
        seg.moveTo(0, -R, 0)
        seg.drawTo(0, R, 0)

        return NodePath(seg.create())

    def mettre_a_jour_pose(
        self,
        position_xyz: Tuple[float, float, float],
        orientation_rpy: Tuple[float, float, float]
    ) -> None:
        """Met à jour position et orientation du drone (roll, pitch, yaw)."""
        x, y, z = position_xyz
        roll, pitch, yaw = orientation_rpy

        self.noeud_drone.setPos(x, y, z)
        # conversion physique (roll=X, pitch=Y, yaw=Z)
        # vers panda (H=z, P=x, R=y)
        self.noeud_drone.setHpr(
            math.degrees(yaw),
            math.degrees(roll),
            math.degrees(pitch)
        )

    def mettre_a_jour_helices(self, dt: float) -> None:
        """Fait tourner les hélices en fonction de leur vitesse (rad/s)."""
        rad2deg = 180 / math.pi
        for helice_np, vitesse in self.helices:
            helice_np.setH(helice_np.getH() + vitesse * rad2deg * dt)