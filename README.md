# Mini-projet | Simulation de drone

Ce projet vise à simuler un drone dans un environnement simple sujet à perturbations. L'idée est de mettre en place une loi de commande pour asservir le drone en position.

Ce projet est créé dans le cadre de la recherche, chez [SII](https://sii-group.com/fr-FR).

## Initialisation

Si vous souhaitez lancer la simulation, voici comment faire : 

1. Ouvrez un éditeur de code, tel que [Visual Studio Code](https://code.visualstudio.com/) par exemple.

2. Ouvrez-y un terminal.

3. Entrez les commandes comme décrit ci-après, en les adaptant selon votre configuration.

## Commandes

**Note :** ces commandes sont adaptées à un environnement Windows.

1. Créez un environnement virtuel sur votre machine.
   ```
   python -m venv drone_sim_env
   ```

2. Activez l’environnement virtuel.
    ```
    powershell -ExecutionPolicy Bypass
    .\drone_sim_env\Scripts\Activate.ps1 
    ```

3. Installez les packages requis.
    ```
    pip install -r requirements.txt
    ```
    **Note :** si vous devez mettre pip à jour, faites‑le. Vous devrez ensuite entrer de nouveau la commande.

4. Naviguez jusqu'au dossier source.
    ```
    cd src
    ```

5. Lancez le scripte principal.
    ```
    python main.py
    ```
