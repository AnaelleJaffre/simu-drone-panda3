# Unites ----------------------
# Masses : kilogrammes
# Distances : metres
# Vitesses de rotation : radians/seconde
# -----------------------------


# Scene -----------------------

scene = {
    "zones": {
        "SII": {
            "POSITION": (-8, 8, -8, 8),
            "COULEUR": (0.88, 0.93, 1.00, 1)
        },
        "THALES": {
            "POSITION": (-17, -10, -8, 28),
            "COULEUR": (1.00, 0.88, 0.88, 1)
        },
        "DASSAULT": {
            "POSITION": (10, 25, -16, 30),
            "COULEUR": (0.88, 1.00, 0.90, 1)
        },
        "ARIANE": {
            "POSITION": (-8, 8, 10, 55),
            "COULEUR": (1.00, 0.97, 0.82, 1)
        },
        "ORANGE": {
            "POSITION": (-28, 8, -25, -10),
            "COULEUR": (0.78, 0.97, 0.95, 1)
        }
    }
}


# Drone ------------------------

specifications_drone = {
    "LONGUEUR_BRAS": 0.3,
    "HAUTEUR_DRONE": 0.15,
    "EPAISSEUR": 6,
    "COULEUR": (0, 0, 0, 1),
    "EPAISSEUR_HELICES": 2,
    "RAYON_HELICES": 0.15,
    "NB_HELICES" : 4,
    "COEFFS_TRAINEE" : [1.1, 1.1, 0.7],
}


# Physique -----------------------

physique = {
    "POSITION_INITIALE": [0.0, 0.0, 2.0],
    "MASSE": 2.0,
    "POUSSEE": 0.004, # Coeff de poussée k_f, en kg.m
    "HAUTEUR_SOL" : 0.0,
    "VITESSE_HELICE_MIN": 0.0,
    "VITESSE_HELICE_MAX": 60.0,
    "TAU_MOTEUR" : 0.2, # Constante de temps
    "INERTIE" : [0.05, 0.05, 0.09],
    "K_YAW" : 0.04,
    "AMORTISSEMENT_ANGULAIRE" : 0.025,
    "FROTTEMENT_ANGULAIRE": 2,
    "SEUIL_REBOND": 0.4, # vitesse minimale pour déclencher un rebond (m/s)
    "COEFF_REBOND": 0.25, # restitution du choc (0.0 à 1.0)
    "INERTIE_ROTOR": 1e-5, # Pour des petits drones, J_h ~ 1e-6 à 1e-5 kg.m²
    "DENSITE_AIR": 1.225, # kg/m^3 a 15°C
    "FROTTEMENTS": {
        "lineaire":  [0.5, 0.5, 0.002],   # k_lin_x, k_lin_y, k_lin_z
        "quadratique": [0.005, 0.005, 0.0001]    # k_quad_x, k_quad_y, k_quad_z
    },
}


# Simulation ---------------------

specifications_simulation = {
    "VITESSES_ROTATION_HELICES": [58, 38, 58, 38], #rad/s
    "SENS_HELICES" : [1.0, -1.0, 1.0, -1.0],
    "CONSIGNE": [0.0, 0.0, 2.2],
    "PID": {
        "X": {"proportionnel": 0.2, "integral": 1.0, "derive": 3.0},
        "Y": {"proportionnel": 12.0, "integral": 1.0, "derive": 3.0},
        "Z": {"proportionnel": 10.0, "integral": 2.0, "derive": 4.0}
    },
}


# Interface ----------------------

specifications_interface = {
    "RAYON_BORDURE": 5,
    "COULEUR_FOND_CONTROLES": "#ffffff",

    # Switch PID (palette Set2 Seaborn)
    "COULEUR_SWITCH_ACTIF": "#66c2a5",   # vert Set2
    "COULEUR_SWITCH_INACTIF": "#cccccc",
    "COULEUR_TEXTE_SWITCH_ACTIF": "#ffffff",
    "COULEUR_TEXTE_SWITCH_INACTIF": "#000000",

    # Fenetre
    "TITRE_FENETRE": "Simulation drone | Interface PID",
    "TAILLE_FENETRE": (700, 700),

    # Camera (slider horizontal)
    "CAMERA_AMPLITUDE": 250,
    "CAMERA_ZONE_MORTE": 2,

    # Moteurs (sliders verticaux)
    "NOMBRE_HELICES": 4,
    "PAS_HELICE": 2,

    # Altitude
    "ALTITUDE_MIN": 0.0,
    "ALTITUDE_MAX": 10.0,

    # Grille
    "GRILLE_MARGES": (8, 8, 8, 8),   # haut, gauche, bas, droite
    "GRILLE_ESPACE": 8,              # espace entre cellules
    "TAUX_ETIREMENT_LIGNE_HAUT": 2,  # ligne 0 (panda + controles)
    "TAUX_ETIREMENT_LIGNE_BAS": 2,   # ligne 1 (graphique)
    "TAUX_ETIREMENT_COL_GAUCHE": 3,  # panda3d
    "TAUX_ETIREMENT_COL_DROITE": 2,  # controles qt

    # Graphique PID
    "GRAPHIQUE_PERIODE_RAFRAICHISSEMENT_MS": 100,
    "GRAPHIQUE_FENETRE_MEMOIRE_S": 10,
    "GRAPHIQUE_EPAISSEUR_TRAIT": 1.6,
    "GRAPHIQUE_PID_YMAX":  20.0,

    # Fenetre de visualisation en abscisse (secondes)
    "GRAPHIQUE_FENETRE_VISU_S": 10.0,

}