# Interface

Ce dossier englobe toute la partie dédiée à l'interface PyQt5. Le programme principal qui génère la fenêtre est situé dans le fichier  [`fenetre.py`](fenetre.py). C'est ici que sont appelés les widgets et la feuille de style associée. 

## Architecture

Ce dossier est composé de 2 scriptes principaux :

- **fenetre.py** | Génère la fenêtre PyQt5.
  
- **widgets.py** | Définit les différents widgets utilisés dans la fenêtre.

Voici un visuel de l'architecture du dossier : 
```
interface
├── __init__.py
├── README.md
├── fenetre.py
└── widgets.py
```

## Fenetre

[`fenetre.py`](fenetre.py)

Gère l’interface graphique principale grâce à la classe `FenetrePrincipale` : affichage 3d Panda, boutons, contrôles PID, jauges, sliders de moteurs, style visuel et positionnement de la fenêtre Qt.

### Logique fonctionnelle

1. **Simulation 3D** | Panda3d exécute en boucle la tâche `tacheSimulation` du simulateur. Cela met à jour la physique du drône, son altitude, et le modèle 3D, qui est ensuite affiché chaque instant.

2.  **Autres widgets** | Les widgets Qt (PID, caméra, moteurs) appellent des méthodes du simulateur. Le simulateur modifie les vitesses des hélices, l’orientation de la caméra, l’activation PID.

3.  **Conteneurisation** | `FenetrePrincipale` sert de conteneur : elle rassemble les widgets, charge le style, et place la fenêtre à côté de celle de Panda3d.


Cette classe génère l’interface complète, fait le lien entre Panda3d et PyQt5 et propose à l’utilisateur un contrôle sur le drône et la caméra.

### Table des fonctions

| Fonction                      | Entrée                                | Sortie | Description                                                                                           |
| ----------------------------- | ------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `__init__()`                  | `scene`, `simulateur`, `chemin_style` | `None` | Initialise la fenêtre Qt, crée les widgets (3d, PID, caméra, altitude, moteurs) et applique le style. |
| `_basculer_pid()`             | —                                     | `None` | Active ou désactive le PID via le bouton PID.                                                         |
| `_placer_a_cote_de_panda3d()` | —                                     | `None` | Positionne la fenêtre Qt à droite de la fenêtre Panda3d (Windows uniquement).                         |
| `_charger_style_qss()`        | `chemin_style`                        | `None` | Charge et applique le fichier QSS de style si disponible.                                             |

Tu pourras l’intégrer directement dans ta documentation Markdown.

## Widgets

[`widgets.py`](`widgets.py`)

Ensemble de widgets Qt spécialisés utilisés par l’interface : intégration de la fenêtre Panda3D dans Qt, sliders caméra et moteurs, bouton PID, jauge d’altitude, et zone groupée de contrôle des quatre hélices.

Chaque widget assure une interaction directe entre l’utilisateur via Qt et la simulation sur Panda3D.

### Logique fonctionnelle

1.  **Intégration Panda3D via Qt**  
    `WidgetPanda` encapsule la fenêtre Panda3D dans un widget Qt.  
    Il rattache la fenêtre 3D au widget via `WindowProperties` et utilise un `QTimer` pour avancer le moteur Panda3D (`taskMgr.step()`), simulant \~60 FPS.

2.  **Contrôle caméra**  
    `CurseurCamera` lit le déplacement horizontal du slider.  
    Dès que le delta dépasse une zone morte, il appelle `simulateur.tourner_gauche()` ou `simulateur.tourner_droite()`.

3.  **Contrôle des moteurs**  
    `ZoneControleMoteurs` crée quatre sliders verticaux (`CurseurMoteur`).  
    Chaque slider appelle automatiquement `simulateur.fixer_vitesse_helice(index, valeur)`.

4.  **Affichage de l’altitude**  
    Lorsque le simulateur émet un signal Qt `altitude_changee`.  
    `JaugeAltitude` convertit cette altitude en valeur de jauge et affiche la hauteur en mètres.

5.  **Activation / désactivation du PID**  
    `BoutonPid` affiche *PID : ON* ou *PID : OFF*.  
    Lorsqu'on clique, il inverse son état et renvoie un booléen utilisé par `FenetrePrincipale` pour activer ou couper le PID dans le simulateur.

L’ensemble forme une couche d’interface unifiée permettant à l’utilisateur de contrôler la caméra, les moteurs, le PID, et de visualiser l’altitude, tout en affichant le rendu 3D Panda3D dans Qt.

Ce scripte est organisé en un ensemble de widgets, chacun définis par une classe.

### Table des classes

#### WidgetPanda

| Fonction           | Entrée            | Sortie | Description                                                                                 |
| ------------------ | ----------------- | ------ | ------------------------------------------------------------------------------------------- |
| `__init__()`       | `scene`, `parent` | `None` | Intègre la fenêtre Panda3D dans un widget Qt et démarre un timer pour avancer le moteur 3D. |
| `_avancer_panda()` | —                 | `None` | Appelle `base.taskMgr.step()` à chaque tick Qt pour simuler les frames Panda3D.             |

#### CurseurBase

| Fonction     | Entrée                  | Sortie | Description                                                                           |
| ------------ | ----------------------- | ------ | ------------------------------------------------------------------------------------- |
| `__init__()` | `orientation`, `parent` | `None` | Initialise un slider avec gestion de curseur “main fermée / ouverte” pendant le drag. |

#### CurseurCamera

| Fonction             | Entrée                                            | Sortie | Description                                                                                   |
| -------------------- | ------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| `__init__()`         | `amplitude`, `zone_morte`, `simulateur`, `parent` | `None` | Configure un slider caméra horizontal et connecte les déplacements à un contrôle de rotation. |
| `_deplacer_camera()` | `valeur`                                          | `None` | Compare le delta à la zone morte et appelle `simulateur.tourner_gauche/droite`.               |

#### CurseurMoteur

| Fonction             | Entrée                                                            | Sortie | Description                                                                |
| -------------------- | ----------------------------------------------------------------- | ------ | -------------------------------------------------------------------------- |
| `__init__()`         | `index_moteur`, `plage`, `valeur_initiale`, `on_change`, `parent` | `None` | Crée un slider vertical pour un moteur donné et transmet les changements.  |
| `_propager_valeur()` | `on_change`, `valeur`                                             | `None` | Appelle `on_change(index, valeur)` pour propager la vitesse au simulateur. |

#### JaugeAltitude

| Fonction          | Entrée                             | Sortie | Description                                                             |
| ----------------- | ---------------------------------- | ------ | ----------------------------------------------------------------------- |
| `__init__()`      | `minimum_m`, `maximum_m`, `parent` | `None` | Configure une jauge verticale en mètres avec une résolution de 0.01 m.  |
| `mettre_a_jour()` | `metres`                           | `None` | Met à jour la jauge et son affichage en fonction de l’altitude simulée. |

#### BoutonPid

| Fonction              | Entrée                   | Sortie | Description                                                   |
| --------------------- | ------------------------ | ------ | ------------------------------------------------------------- |
| `__init__()`          | `etat_initial`, `parent` | `None` | Configure un bouton PID avec bascule d’état et texte associé. |
| `actif`               | —                        | `bool` | Retourne l’état actuel du PID (ON/OFF).                       |
| `basculer()`          | —                        | `bool` | Inverse l’état du PID et met à jour le texte du bouton.       |
| `_rafraichir_texte()` | —                        | `None` | Met à jour le texte affiché (PID : ON / PID : OFF).           |

#### ZoneControleMoteurs

| Fonction     | Entrée                                                                            | Sortie | Description                                                                              |
| ------------ | --------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `__init__()` | `simulateur`, `vitesses_initiales`, `vitesse_min`, `vitesse_max`, `pas`, `parent` | `None` | Crée quatre sliders moteur, affiche les étiquettes et relie chaque slider au simulateur. |
