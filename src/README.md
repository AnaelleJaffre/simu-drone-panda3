# Documentation développeur

Bienvenue.

Vous trouverez ici toutes les ressources disponnibles concernant ce mini-projet de simulation de drône en Python.

## Architecture projet

Le dossier source comprend un scripte principal, nommé [`main.py`](main.py). Il sert à lancer le projet dans sa globalité. Pour se faire, il utilise les quatre packages créés :
- **Simulation** | Lance la simulation du drone en 3D. Implémente les lois de la physique appliquées au drône, pour simuler un comportement réaliste.
  
- **Interface** | Permet d'instancier une interface utilisateur, via laquelle il est possible d'agir sur la simulation.
  
- **Controle** | Contient les lois d'asservissement des moteurs du drône, pour le soumettre à une consigne donnée.
  
- **Utiles** | Contient un logger pour les tests, le fichier des constantes utilisées au cours du projet, le style de l'interface et des fonctions utiles.

Voici un visuel de l'architecture du dossier source : 
```
src
|
├── controle
│   ├── __init__.py
│   ├── controleur.py
│   └── pid.py
|
├── interface
│   ├── __init__.py
│   ├── fenetre.py
│   └── widgets.py
|
├── simulation
│   ├── __init__.py
│   ├── drone.py
│   ├── physique.py
│   ├── scene.py
│   └── simulateur.py
|
├── utiles
│   ├── __init__.py
│   ├── constantes.py
│   ├── export.py           # Non utilisé
│   ├── logger.py
│   ├── memoire_tampon.py
│   ├── transformations.py
│   └── style.qss
|
├── main.py
└── README.md
```

## Pogramme principal

Le scripte [`main.py`](main.py) permet de lancer la totalité du projet, soit l'interface PyQt5 en relation avec la simulation du drône sur panda3d.

L’objectif du script est de :
- créer et configurer l’environnement de simulation,
- démarrer Panda3D,
- lancer l’interface graphique PyQt5,
- connecter les modules ensemble.

### Table des fonctions

| Fonction | Entrée | Sortie | Description |
|----------|--------|---------|-------------|
| `build_simulation()` | __ | (scene, simulateur) | instancie la scène Panda3d, le modèle 3d du drône, le moteur physique et le simulateur Panda3d |
| `main()` | argv : arguments de ligne de commande | code de sortie de app.exec_() | configure l’application Qt, crée la fenêtre et démarre la boucle d’événements |

### Dépendances
- PyQt5 | Librairie utilisée pour générer l'interface. Sert à encapsuler Panda3D dans un widget Qt, et permet un contrôle de l'utilisateur sur la simulation.

- Panda3d | Librairie utilisée pour simuler le drône dans un environnement 3D.
