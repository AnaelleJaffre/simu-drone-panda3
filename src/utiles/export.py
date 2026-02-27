import csv
import os
from typing import Dict, Iterable, List, Optional


def ecrire_lignes_csv(
    chemin_dossier: str,
    nom_fichier: str,
    lignes: Iterable[Dict[str, object]],
    entetes: Optional[List[str]] = None,
    encodage: str = "utf-8"
) -> str:
    """
    Ecrit des lignes dict -> CSV (creation si besoin, append sinon).
    Retourne le chemin complet du fichier.
    """
    # assurer le dossier
    os.makedirs(chemin_dossier, exist_ok=True)

    chemin_fichier = os.path.join(chemin_dossier, nom_fichier)
    fichier_existe = os.path.exists(chemin_fichier)

    # deduire les entetes au besoin
    if entetes is None:
        # prendre les cles de la premiere ligne
        lignes = list(lignes)
        if len(lignes) == 0:
            return chemin_fichier
        entetes = list(lignes[0].keys())

    # ecriture
    mode = "a" if fichier_existe else "w"
    with open(chemin_fichier, mode, newline="", encoding=encodage) as f:
        writer = csv.DictWriter(f, fieldnames=entetes)
        if not fichier_existe:
            writer.writeheader()
        for l in lignes:
            writer.writerow(l)

    return chemin_fichier