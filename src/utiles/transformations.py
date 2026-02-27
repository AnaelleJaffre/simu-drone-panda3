import numpy as np
import math
from typing import Tuple


def produit_vectoriel_gyroscopique(
    omega: np.ndarray,
    inerties: Tuple[float, float, float]
) -> np.ndarray:
    """
    Retourne le terme gyroscopique : omega * (I * omega).

    omega : vitesse angulaire (wx, wy, wz)
    inerties : (Ix, Iy, Iz)
    """
    Ix, Iy, Iz = inerties

    # I * omega
    Iomega = np.array([Ix * omega[0],
                       Iy * omega[1],
                       Iz * omega[2]])

    # Produit vectoriel
    return np.cross(omega, Iomega)


def matrice_rotation(angles: np.ndarray) -> np.ndarray:
    """
    Genere la matrice de rotation 3x3 correspondant aux angles d'Euler :
    - roll  : rotation autour de l'axe X
    - pitch : rotation autour de l'axe Y
    - yaw   : rotation autour de l'axe Z

    Le modele utilise la composition standard :
        R = Rz(yaw) * Ry(pitch) * Rx(roll)

    Cette matrice permet de convertir un vecteur exprime dans le repere drone vers le repere monde.
    """
    roll, pitch, yaw = angles

    cr = math.cos(roll)
    sr = math.sin(roll)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)

    Rz = np.array([
        [cy, -sy, 0.0],
        [sy,  cy, 0.0],
        [0.0, 0.0, 1.0]
    ])

    Ry = np.array([
        [cp, 0.0, sp],
        [0.0, 1.0, 0.0],
        [-sp, 0.0, cp]
    ])

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cr, -sr],
        [0.0, sr,  cr]
    ])

    return Rz @ Ry @ Rx
