# Contrôle

Ce dossier englobe toute la partie dédiée à l'asservissement du drône. Le programme principal qui le met en place est situé dans le fichier  [`controleur.py`](controleur.py).

Pour l'instant, seul un asservissement sur l'altitude est mis en place.

## Architecture

Ce dossier est composé de 2 scriptes principaux :

- **controleur.py** | Définit une loi de contrôle pour le drône.
  
- **pid.py** | Composant mathématique qui prend une consigne, lit une mesure, en calcule l'erreur, applique un PID et retourne la correction associée.

Voici un visuel de l'architecture du dossier : 
```
interface
├── __init__.py
├── README.md
├── controleur.py
└── pid.py
```

## PID

[`pid.py`](pid.py)

La classe PID (Proportionnelle - Intégrale - Dérivée) définit un bloc de régulation appelé en interne pour les calculs, totalement indépendant du drône. Elle calcule une correction numérique en fonction d'une consigne, d’une mesure et d’un pas de temps.  

**Objectif :** transformer l'erreur en une force correctrice via les termes P, I et D.

### Logique fonctionnelle

1.  **Erreur** | Calcul de l'erreur :  `erreur = consigne - mesure`.
2.  **Terme intégral** | Accumulation de l’erreur dans le temps avec limites anti-windup.
3.  **Terme dérivé** | Calcul de la dérivée de la mesure ou de l’erreur selon la configuration.
4.  **Sortie PID** | Combination de P + I + D pour produire une force correctrice.
5.  **Saturation** | La sortie est bornée par `limites_sortie`.

La commande générée par le PID est donnée par :

$\qquad
u(t) = K_p e(t) \;+\; K_i \displaystyle\int_0^t e(\tau)\,d\tau \;+\; K_d \,\frac{d e(t)}{dt}
$

où :
- $e(t) = c(t) - m(t)$ est l’erreur (consigne – mesure),
- $K_p, K_i, K_d$ sont les coefficients proportionnel, intégral et dérivé.


#### Terme proportionnel

Il dépend directement de l’erreur instantanée :

$\qquad u_p(t) = K_p\,e(t)$

Plus l’erreur est grande, plus la réponse est immédiate.

#### Terme intégral

Il cumule l’erreur dans le temps, afin d’éliminer l’erreur permanente :

$\qquad u_i(t) = K_i \displaystyle\int_0^t e(\tau)\,d\tau$

Dans le code, l’intégrale est calculée numériquement :

$\qquad I(t+\Delta t) = I(t) + e(t)\,\Delta t$

avec une saturation :

$\qquad I = \mathrm{clip}(I, I_{\min}, I_{\max})$

pour empêcher l’intégrale de diverger lorsque la sortie est saturée.

#### Terme dérivé

Il anticipe l’évolution de l’erreur en mesurant sa vitesse de variation. On utilise une dérivée sur la mesure :  
$\qquad u_d(t) = -K_d\,\dfrac{d\,m(t)}{dt}$  

Dans le code, elle est calculée par différentiation finie :

$\qquad
\frac{d m}{dt} \approx \frac{m(t) - m(t-\Delta t)}{\Delta t}
$

**Note :** le programme choisit une dérivée sur l'erreur si la dérivée sur la mesure n'existe pas.

#### Sortie finale du PID

La commande totale est :

$\qquad u(t) = u_p(t) + u_i(t) + u_d(t)$

soit :

$\qquad u(t) = K_p\,e(t) + K_i\,I(t) + K_d\,D(t)$

Elle est ensuite **bornée** entre des limites :

$\qquad
u(t) = \mathrm{clip}\big(u(t), u_{\min}, u_{\max}\big)
$

#### Mise à jour des variables internes

Après calcul :

- l’erreur précédente devient $e(t)$,
- la mesure précédente devient $m(t)$,
- l’intégrale accumulée est conservée.

Ainsi, à chaque appel du PID, on calcule :

- l’erreur actuelle,
- l’intégrale mise à jour,
- la dérivée,
- puis la commande.

## Contrôleur

`controleur.py`

La classe `Controleur` implémente une architecture en cascade pour réguler la position et l’attitude d’un drone quadricoptère.  
Elle combine trois étages :

1. Régulation d’altitude (PID Z → force → vitesse commune) 
2. Régulation de position XY (PID position → angle cible)  
3. Régulation d’attitude (PID attitude → moments L/M → mixeur)

### Logique fonctionnelle

#### Régulation d’altitude

**Méthode :** `_vitesse_commune_altitude`

1. Le PID Z calcule une correction verticale en Newton :  
   $$\Delta F(t) = K_p e(t) + K_i \int e + K_d \frac{de}{dt}$$  
2. La poussée totale appliquée est  
   $$F_{\text{tot}} = mg + \Delta F$$  
3. Chaque hélice fournit  
   $$F_{\text{helice}} = \frac{F_{\text{tot}}}{4}$$  
4. La vitesse angulaire correspondante est obtenue par  
   $$\omega = \sqrt{\frac{F_{\text{helice}}}{k_{\text{poussee}}}}$$  
5. Cette vitesse est bornée entre `vmin` et `vmax`.

#### Régulation XY (cascade position → attitude)

##### Étape 1 — PID position : position → angle cible

**Méthodes :** `pid_pos_x`, `pid_pos_y`

1. Le PID reçoit la position mesurée $x$ ou $y$ en mètres.  
2. Il produit un angle cible en radians :  
   $$\theta_{\text{cible}} = PID_{\text{pos}}(x)$$  
3. L’objectif est de pencher légèrement le drone pour générer une accélération permettant de revenir vers la consigne $(0,0)$.

##### Étape 2 — PID attitude : angle → moment

**Méthodes :** `pid_att_pitch`, `pid_att_roll`

1. Les consignes des PID attitude sont mises à jour :  
   $$\theta_{\text{pitch,cible}} = \theta_{x,\text{cible}}$$  
   $$\theta_{\text{roll,cible}}  = \theta_{y,\text{cible}}$$  
2. La mesure d’angle (pitch/roll) provient de l’état du drone.  
3. Chaque PID attitude calcule un moment virtuel permettant de corriger l’angle :  
   $$M = PID_{\text{att}}(\theta_{\text{mes}})$$  
4. Ces moments sont ensuite réduits par un gain faible puis envoyés au mixeur.

#### Mixage quadricoptère

**Méthode :** `_mixeur_quad`

Pour les moteurs, dans l’ordre 0 (arrière), 1 (gauche), 2 (avant), 3 (droite), on applique :

- $u_t$ : vitesse commune  
- $L$ : correction roll  
- $M$ : correction pitch  
- $N$ : correction yaw (ici nulle)

Grâce au calcul suivant :

- $u_0 = u_t - M + N$  
- $u_1 = u_t + L - N$  
- $u_2 = u_t + M + N$  
- $u_3 = u_t - L - N$

Le mixeur redistribue les corrections d’attitude vers les vitesses moteur.

#### Stabilisation simple

**Méthode :** `_stabiliser_attitude`

1. On récupère $(\text{roll}, \text{pitch}, \text{yaw})$.  
2. On produit une faible correction proportionnelle opposée :  
   $$L = -k \cdot \text{roll}$$  
   $$M = -k \cdot \text{pitch}$$  
3. Cela stabilise le drone lorsque les PID sont désactivés.

#### Application globale du contrôle

**Méthode :** `appliquer_controle`

1. **Altitude**  
   - Si PID actif, on calcule la vitesse commune via `_vitesse_commune_altitude`.  
   - Sinon, on utilise la moyenne des vitesses moteurs.

2. **Cascade XY**  
   - PID position : produit un angle cible $(\theta_x, \theta_y)$.  
   - PID attitude : calcule les moments $(L,M)$ qui corrigent les angles réels.

3. **Mixage quad**  
   - Combine $u_t$, $L$, $M$, $N$ en vitesses individuelles pour chaque hélice.

4. **Bornage + override utilisateur**  
   - Si un moteur n’est pas forcé par l’utilisateur, on applique le résultat du mixeur.  
   - Bornage final dans les limites physiques.

5. **Retour**  
   - Retourne les vitesses moteur finales en rad/s, ainsi que les termes PID du régulateur Z.
