from typing import Any, Callable, Optional, List
from functools import partial
import time
from panda3d.core import WindowProperties

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QSlider, QProgressBar, QLabel, QVBoxLayout, QGridLayout, QGroupBox, QPushButton

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from utiles.memoire_tampon import MemoireTamponPid

import seaborn as sns
sns.set_theme(style="whitegrid", palette="Set2")

# ---------- Widget d'integration Panda3D ----------
class WidgetPanda(QWidget):
    """Conteneur Qt pour afficher la fenetre Panda3D dans un widget."""
    def __init__(self, scene: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene: Any = scene

        # Rattacher la fenetre Panda3D à ce widget
        proprietes = WindowProperties()
        proprietes.setParentWindow(int(self.winId()))
        self.scene.win.requestProperties(proprietes)

        # Avancer la boucle Panda3D via un timer Qt (~60 fps)
        self._minuterie = QTimer(self)
        self._minuterie.timeout.connect(self._avancer_panda)  # type: ignore[arg-type]
        self._minuterie.start(16)

    def _avancer_panda(self) -> None:
        # 'base' est l'instance ShowBase globale fournissant taskMgr
        base.taskMgr.step()  # type: ignore[name-defined]


# ---------- Sliders factorises ----------
class CurseurBase(QSlider):
    """Slider avec gestion unifiee du curseur souris (main ouverte/fermee)."""
    def __init__(self, orientation: Qt.Orientation, parent: Optional[QWidget] = None) -> None:
        super().__init__(orientation, parent)
        self.setCursor(Qt.OpenHandCursor)
        self.sliderPressed.connect(lambda: self.setCursor(Qt.ClosedHandCursor))
        self.sliderReleased.connect(lambda: self.setCursor(Qt.OpenHandCursor))


class CurseurCamera(CurseurBase):
    """Slider horizontal de camera base sur le delta avec zone morte."""
    def __init__(self, amplitude: int, zone_morte: int, simulateur: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(Qt.Horizontal, parent)
        self._simulateur: Any = simulateur
        self._valeur_precedente: int = 0
        self._zone_morte: int = int(zone_morte)

        self.setRange(-int(amplitude), int(amplitude))
        self.setValue(0)
        self.valueChanged.connect(self._deplacer_camera)  # type: ignore[arg-type]

    def _deplacer_camera(self, valeur: int) -> None:
        delta = valeur - self._valeur_precedente
        self._valeur_precedente = valeur
        if delta == 0:
            return
        if -self._zone_morte <= delta <= self._zone_morte:
            return
        if delta > 0:
            self._simulateur.tourner_droite()
        else:
            self._simulateur.tourner_gauche()


class CurseurMoteur(CurseurBase):
    """Slider vertical d'un moteur (helice)."""
    def __init__(
            self,
            index_moteur: int,
            plage: range,
            valeur_initiale: int,
            on_change: Callable[[int, int], None],
            on_press: Callable[[int, bool], None],
            on_release: Callable[[int, bool], None],
            parent: Optional[QWidget] = None,
        ) -> None:
        super().__init__(Qt.Vertical, parent)
        self._index = int(index_moteur)
        self.setRange(plage.start, plage.stop)
        self.setValue(int(valeur_initiale))

        # Important pour un suivi fluide pendant le drag
        self.setTracking(True)  # valueChanged émis pendant le déplacement

        # Commande à chaque mouvement du slider
        self.valueChanged.connect(lambda v: on_change(self._index, int(v)))  # type: ignore[arg-type]

        # Appui / relâche immédiats, sans attendre un mouvement
        self.sliderPressed.connect(lambda: on_press(self._index, True))
        self.sliderReleased.connect(lambda: on_release(self._index, False))
    
    def mousePressEvent(self, event):
        # On indique au simulateur que ce moteur est force par l'utilisateur
        if hasattr(self.parent(), "notifier_moteur_utilisateur"):
            self.parent().notifier_moteur_utilisateur(self._index, True)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # L'utilisateur n'agit plus -> retour au mode normal
        if hasattr(self.parent(), "notifier_moteur_utilisateur"):
            self.parent().notifier_moteur_utilisateur(self._index, False)

        super().mouseReleaseEvent(event)


# ---------- Autres widgets ----------
class JaugeAltitude(QProgressBar):
    """Jauge verticale d'altitude affichee en metres (0–10m par defaut)."""
    def __init__(self, minimum_m: float, maximum_m: float, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._min_m = float(minimum_m)
        self._max_m = float(maximum_m)
        self.setRange(0, int(round((self._max_m - self._min_m) * 100)))  # resolution 0.01 m
        self.setOrientation(Qt.Vertical)
        self.setTextVisible(True)
        self.setFormat("%v")  # on reecrit le texte à chaque mise à jour

    def mettre_a_jour(self, metres: float) -> None:
        metres_clampe = max(self._min_m, min(self._max_m, float(metres)))
        self.setValue(int(round((metres_clampe - self._min_m) * 100)))
        self.setFormat(f"{metres_clampe:.2f}")


class BoutonPid(QPushButton):
    """Bouton à bascule pour activer/desactiver le PID."""
    def __init__(self, etat_initial: bool = True, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._actif: bool = bool(etat_initial)
        self.setCursor(Qt.PointingHandCursor)
        self._rafraichir_texte()

    @property
    def actif(self) -> bool:
        return self._actif

    def basculer(self) -> bool:
        self._actif = not self._actif
        self._rafraichir_texte()
        return self._actif

    def _rafraichir_texte(self) -> None:
        self.setText("PID : ON" if self._actif else "PID : OFF")


class ZoneControleMoteurs(QGroupBox):
    """Zone regroupant les sliders des moteurs + libelles."""
    def __init__(
        self,
        simulateur: Any,
        vitesses_initiales: List[float],
        vitesse_min: int,
        vitesse_max: int,
        pas: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__("Contrôle moteurs", parent)
        self._simulateur = simulateur
        grille = QGridLayout(self)
        self.sliders: List[CurseurMoteur] = []
        self._appuis_utilisateur = [False, False, False, False]

        def fixer_vitesse(index: int, valeur: int) -> None:
            self._simulateur.fixer_vitesse_helice(index, valeur)

        def notifier_appui(index: int, actif: bool) -> None:
            self._appuis_utilisateur[index] = actif
            self._simulateur.moteurs_forces_utilisateur[index] = actif

        plage = range(int(vitesse_min), int(vitesse_max)+1)
        for i in range(len(vitesses_initiales)):
            conteneur = QWidget(self)
            vbox = QVBoxLayout(conteneur)
            vbox.setContentsMargins(30, 6, 6, 6)

            slider = CurseurMoteur(
                index_moteur=i,
                plage=plage,
                valeur_initiale=int(vitesses_initiales[i]),
                on_change=fixer_vitesse,
                on_press=notifier_appui,
                on_release=notifier_appui,
                parent=conteneur,
            )
            etiquette = QLabel(f"Hélice {i}", conteneur)
            etiquette.setAlignment(Qt.AlignHCenter)

            vbox.addWidget(slider, 1)
            vbox.addWidget(etiquette, 0)

            grille.addWidget(conteneur, 0, i)
            self.sliders.append(slider)

    def mettre_a_jour_affichage_moteurs(self, vitesses: list) -> None:
        """Met a jour la position des sliders selon la vitesse reelle."""
        for i, slider in enumerate(self.sliders):
            # Ne jamais forcer le slider si l'utilisateur est en train de glisser
            if self._appuis_utilisateur[i] or slider.isSliderDown():
                continue
            slider.blockSignals(True)
            slider.setValue(int(vitesses[i]))
            slider.blockSignals(False)
    
    def notifier_moteur_utilisateur(self, index: int, actif: bool) -> None:
        self._simulateur.moteurs_forces_utilisateur[index] = actif


class GrapheBase(QWidget):
    """Classe generique pour un graphe temps reel."""
    def __init__(self, ui: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("GrapheBase")

        self.periode_ms = int(ui["GRAPHIQUE_PERIODE_RAFRAICHISSEMENT_MS"])
        self.fenetre_s = float(ui["GRAPHIQUE_FENETRE_MEMOIRE_S"])
        self.fenetre_visu_s = float(ui["GRAPHIQUE_FENETRE_VISU_S"])
        self.epaisseur = float(ui["GRAPHIQUE_EPAISSEUR_TRAIT"])

        self.memoire = MemoireTamponPid(self.fenetre_s)
        self.t0 = time.monotonic()

        # Figure
        self.figure = Figure(figsize=(6, 2.5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Axe unique : les sous-classes peuvent en ajouter d'autres
        self.ax = self.figure.add_subplot(111)

        # Layout
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.canvas)

        # Minuterie
        self._minuterie = QTimer(self)
        self._minuterie.timeout.connect(self._rafraichir)  # type: ignore[arg-type]
        self._minuterie.start(self.periode_ms)

    # Methode commune appelee par le timer
    def _rafraichir(self) -> None:
        self._rafraichir_graphe()
        self.canvas.draw_idle()

    # Méthode à surcharger
    def _rafraichir_graphe(self) -> None:
        raise NotImplementedError

class GraphePid(GrapheBase):
    """Affiche P, I, D en N (axe gauche)."""
    def __init__(self, ui: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(ui, parent)
        self.ymax_pid = float(ui["GRAPHIQUE_PID_YMAX"])

        # Courbes
        self.courbe_p, = self.ax.plot([], [], label="P", linewidth=self.epaisseur)
        self.courbe_i, = self.ax.plot([], [], label="I", linewidth=self.epaisseur)
        self.courbe_d, = self.ax.plot([], [], label="D", linewidth=self.epaisseur)

        self.ax.set_ylabel("PID (N)")
        self.ax.set_ylim(-self.ymax_pid, self.ymax_pid)

        self.ax.legend(loc="upper left", ncol=3, fontsize=8)

    def recevoir_pid(self, p: float, i: float, d: float, consigne: float, mesure: float) -> None:
        t = time.monotonic() - self.t0
        self.memoire.ajouter(t, p, i, d, consigne, mesure)

    def _rafraichir_graphe(self) -> None:
        t, p, i, d, _, _ = self.memoire.lire_series()
        if not t:
            return

        # donnees
        self.courbe_p.set_data(t, p)
        self.courbe_i.set_data(t, i)
        self.courbe_d.set_data(t, d)

        # Axe X
        t_max = t[-1]
        t_min = max(0.0, t_max - self.fenetre_visu_s)
        self.ax.set_xlim(t_min, t_min + self.fenetre_visu_s)

class GrapheAltitude(GrapheBase):
    """Affiche altitude et consigne (axe droit)."""
    def __init__(self, ui: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(ui, parent)
        self.alt_min = float(ui["ALTITUDE_MIN"])
        self.alt_max = float(ui["ALTITUDE_MAX"])

        self.courbe_consigne, = self.ax.plot([], [], label="Consigne", linestyle="--", linewidth=1.2)
        self.courbe_mesure,   = self.ax.plot([], [], label="Altitude", linewidth=1.2)

        self.ax.set_ylabel("Altitude (m)")
        self.ax.set_ylim(self.alt_min, self.alt_max)

        # Legende
        lignes = [self.courbe_consigne, self.courbe_mesure]
        self.ax.legend(lignes, [l.get_label() for l in lignes], loc="upper right", fontsize=8)

    def recevoir_pid(self, p: float, i: float, d: float, consigne: float, mesure: float) -> None:
        t = time.monotonic() - self.t0
        self.memoire.ajouter(t, p, i, d, consigne, mesure)

    def _rafraichir_graphe(self) -> None:
        t, _, _, _, c, m = self.memoire.lire_series()
        if not t:
            return

        self.courbe_consigne.set_data(t, c)
        self.courbe_mesure.set_data(t, m)

        # Axe X
        t_max = t[-1]
        t_min = max(0.0, t_max - self.fenetre_visu_s)
        self.ax.set_xlim(t_min, t_min + self.fenetre_visu_s)
        self.ax.set_xlim(t_min, t_min + self.fenetre_visu_s)
