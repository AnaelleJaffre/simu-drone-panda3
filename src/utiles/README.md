# Utiles

Ce dossier contient des fichiers supposés *utiles*.

## Architecture dossier

Voici un visuel de l'architecture du dossier : 
```
utiles
├── __init__.py
├── README.md
├── constantes.py
├── logger.py
├── export.py
└── style.qss
```

## Constantes

Les constantes utilisées dans le projet sont majoritairement regroupées dans le fichier [`constantes.py`](constantes.py). Elles peuvent être modifiées au bon vouloir pour faire quelques petites expérimentations sympas. Aux risques et périls de l'utilisateur qui lance la simulation.

### Structure
Le fichier s'organise en un ensemble de **dictionnaires**, sous la forme suivante : 
```
domaine = {
    "CONSTANTE_1" : valeur,
    "CONSTANTE_2" : valeur,
    ...
    "CONSTANTE_N" : valeur
}
```

Chaque **domaine** correspond au fichier pour lequel a été créé le dictionnaire de constantes.

Il est possible qu'un fichier appelle plusieurs dictionnaires.

## Logger

Le fichier [`logger.py`](logger.py) contient un logger simple, pour afficher des valeurs dans la console lors des tests.

## Style

Le fichier [`style.qss`](style.qss) est la feuille de style associée à l'interface. Elle propose un style en **flat design**, avec une charte graphique simpliste se voulant adaptée au cadre **professionnel**.

La feuille de style est organisée par widget.

## Export de données

Le fichier [`export.py`](export.py) comprend une méthode qui permet d'écrire des lignes dans un fichier csv. Il crée le fichier si ce dernier n'existe pas, sinon il y ajoute des données.