from typing import Any, Optional
from pathlib import Path

from PyQt5.QtCore import QSize, QTimer, Qt
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget, QVBoxLayout, QGridLayout, QGroupBox, QSizePolicy

from interface.widgets import GrapheAltitude, GraphePid, WidgetPanda, BoutonPid, CurseurCamera, JaugeAltitude, ZoneControleMoteurs
from utiles.constantes import specifications_interface as spec_int, physique as phys

class FenetrePrincipale(QWidget):
    """Fenetre principale de l'interface."""
    def __init__(self, scene: Any, simulateur: Any, chemin_style: Optional[Path] = None) -> None:
        super().__init__()

        # Liaison simulateur
        self.simulateur: Any = simulateur

        # Fenetre
        self.setWindowTitle(spec_int["TITRE_FENETRE"])
        self.setObjectName("FenetrePrincipale")
        largeur, hauteur = spec_int["TAILLE_FENETRE"]
        self.setFixedSize(QSize(int(largeur), int(hauteur)))

        # Zones
        self._creer_zone_3d(scene)
        self._creer_zone_controles()
        self._creer_zone_graphique()

        # Grille principale
        self._configurer_grille()

        # Connexions
        self.bouton_pid.clicked.connect(self._basculer_pid)  # type: ignore[arg-type]
        # self.simulateur.altitude_changee.connect(self.jauge_altitude.mettre_a_jour)  # type: ignore[attr-defined]
        self.simulateur.pid_mis_a_jour.connect(self.graphe_altitude.recevoir_pid)  # type: ignore[attr-defined]
        self.simulateur.pid_mis_a_jour.connect(self.graphe_pid.recevoir_pid)  # type: ignore[attr-defined]
        self.simulateur.vitesses_moteurs_mises_a_jour.connect(self.zone_controle_moteurs.mettre_a_jour_affichage_moteurs)
        
        # Style
        self._charger_style_qss(chemin_style)

    # ----------------- Slots / actions -----------------
    def _basculer_pid(self) -> None:
        etat = self.bouton_pid.basculer()
        self.simulateur.pid_actif = bool(etat)

    def showEvent(self, event):
        super().showEvent(event)

        if not hasattr(self, "_placement_fait"):
            self._placement_fait = True

            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self._placer_a_cote_de_panda3d)
            timer.start(300)   # 300 ms

    def _reinitialiser_simulation(self) -> None:
        """Appelle la methode de reset du simulateur."""
        self.simulateur.initialiser_simulation()
    
    # ----------------- Utilitaires -----------------
    def _placer_a_cote_de_panda3d(self) -> None:
        try:
            import ctypes, ctypes.wintypes  # type: ignore

            handle = base.win.getWindowHandle().getIntHandle()  # type: ignore[name-defined]
            user32 = ctypes.windll.user32
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(handle, ctypes.byref(rect))

            panda_x = rect.left
            panda_y = rect.top
            panda_w = rect.right - rect.left
            self.move(panda_x + panda_w, panda_y)
        except Exception:
            # On ignore tout probleme de placement (en particulier hors Windows)
            pass

    def _charger_style_qss(self, chemin_style: Optional[Path]) -> None:
        try:
            if chemin_style is None:
                chemin_style = (Path(__file__).resolve().parents[1] / "utiles" / "style.qss")
            if chemin_style.exists():
                contenu = chemin_style.read_text(encoding="utf-8")
                self.setStyleSheet(contenu)
        except Exception:
            pass
    
# ----- Creation des sous-zones -----

    def _creer_zone_3d(self, scene: Any) -> None:
        """Zone gauche: rendu panda3d dans un widget Qt."""
        self.widget_3d = WidgetPanda(scene, self)
        self.widget_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _creer_zone_controles(self) -> None:
        """Zone droite: controles UI empiles."""
        conteneur = QGroupBox("Controles", self)
        conteneur.setObjectName("ConteneurControles")
        vbox = QVBoxLayout(conteneur)
        vbox.setContentsMargins(spec_int["GRILLE_ESPACE"], spec_int["GRILLE_ESPACE"], spec_int["GRILLE_ESPACE"], spec_int["GRILLE_ESPACE"])
        vbox.setSpacing(spec_int["GRILLE_ESPACE"])

        # Ligne horizontale : PID et Reinitialiser
        hbox_boutons = QHBoxLayout()
        hbox_boutons.setSpacing(10)  # petit espace entre les deux boutons

        self.bouton_pid = BoutonPid(etat_initial=True, parent=conteneur)
        self.bouton_reinitialiser = QPushButton("Réinitialiser", parent=conteneur)
        self.bouton_reinitialiser.setCursor(Qt.PointingHandCursor)
        self.bouton_reinitialiser.clicked.connect(self._reinitialiser_simulation)  # type: ignore[arg-type]

        hbox_boutons.addWidget(self.bouton_pid)
        hbox_boutons.addWidget(self.bouton_reinitialiser)

        # Ajout dans la verticale
        vbox.addLayout(hbox_boutons)

        # Camera
        self.curseur_camera = CurseurCamera(
            amplitude=spec_int["CAMERA_AMPLITUDE"],
            zone_morte=spec_int["CAMERA_ZONE_MORTE"],
            simulateur=self.simulateur,
            parent=conteneur,
        )
        vbox.addWidget(self.curseur_camera)

        # Altitude
        # self.jauge_altitude = JaugeAltitude(
        #     minimum_m=spec_int["ALTITUDE_MIN"],
        #     maximum_m=spec_int["ALTITUDE_MAX"],
        #     parent=conteneur,
        # )
        # vbox.addWidget(self.jauge_altitude)

        # Moteurs
        vitesses_initiales = getattr(self.simulateur, "vitesses_helices", [0, 0, 0, 0])
        self.zone_controle_moteurs = ZoneControleMoteurs(
            simulateur=self.simulateur,
            vitesses_initiales=vitesses_initiales,
            vitesse_min=phys["VITESSE_HELICE_MIN"],
            vitesse_max=phys["VITESSE_HELICE_MAX"],
            pas=spec_int["PAS_HELICE"],
            parent=conteneur,
        )
        vbox.addWidget(self.zone_controle_moteurs, 1)

        self.conteneur_controles = conteneur
        self.conteneur_controles.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def _creer_zone_graphique(self) -> None:
        """Ligne basse: graphique PID (largeur totale)."""
        self.graphe_pid = GraphePid(spec_int, parent=self)
        self.graphe_altitude = GrapheAltitude(spec_int, parent=self)

        self.simulateur.pid_mis_a_jour.connect(self.graphe_pid.recevoir_pid)
        self.simulateur.pid_mis_a_jour.connect(self.graphe_altitude.recevoir_pid)
        self.graphe_pid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.graphe_altitude.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    # ----- Grille maitre -----

    def _configurer_grille(self) -> None:
        marge_h, marge_g, marge_b, marge_d = spec_int["GRILLE_MARGES"]
        espace = spec_int["GRILLE_ESPACE"]

        grille = QGridLayout(self)
        grille.setContentsMargins(int(marge_g), int(marge_h), int(marge_d), int(marge_b))
        grille.setHorizontalSpacing(int(espace))
        grille.setVerticalSpacing(int(espace))

        # Ligne 0 : panda + controles
        grille.addWidget(self.widget_3d, 0, 0)
        grille.addWidget(self.conteneur_controles, 0, 1)

        # Ligne 1 : graphe PID
        grille.addWidget(self.graphe_pid, 1, 0, 1, 2)

        # Ligne 2 : graphe altitude
        grille.addWidget(self.graphe_altitude, 2, 0, 1, 2)

        # Etirements
        grille.setRowStretch(0, int(spec_int["TAUX_ETIREMENT_LIGNE_HAUT"]))
        grille.setRowStretch(1, 1)
        grille.setRowStretch(2, 1)

        grille.setColumnStretch(0, int(spec_int["TAUX_ETIREMENT_COL_GAUCHE"]))
        grille.setColumnStretch(1, int(spec_int["TAUX_ETIREMENT_COL_DROITE"]))