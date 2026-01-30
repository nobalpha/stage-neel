# Client Web du Réseau Européen

Un outil de visualisation et de simulation web interactif pour le réseau électrique européen utilisant l'algorithme de Lanczos.

## Fonctionnalités

- **Visualisation Cartographique Interactive** : Voir le réseau européen sur une carte à thème sombre avec des nœuds colorés par poids (échelle de couleur Viridis)
- **Simulation en Temps Réel** : Exécuter l'algorithme de Lanczos et voir les résultats instantanément
- **Configuration des Points d'Extrémité** : Sélectionner les bus d'entrée (source) et de sortie (puits)
- **Suppression d'Éléments** : Supprimer des nœuds ou des lignes et observer l'effet sur le réseau
- **Graphiques en Direct** : Suivre les valeurs κ², β, résistance effective et ψ²
- **Panneau de Statistiques** : Suivre les statistiques du réseau et les éléments supprimés

## Installation

1. Naviguer vers le répertoire web_client :

```bash
cd web_client
```

2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Exécution de l'Application

1. Démarrer le serveur Flask :

```bash
python app.py
```

2. Ouvrir votre navigateur et naviguer vers :

```
http://localhost:5000
```

## Utilisation

### Configuration des Points d'Extrémité

1. Utiliser le menu déroulant **Bus d'Entrée** pour sélectionner le nœud source de puissance
2. Utiliser le menu déroulant **Bus de Sortie** pour sélectionner le nœud puits de puissance
3. Cliquer sur **Appliquer Points d'Extrémité** pour reconfigurer et simuler

### Suppression d'Éléments

- Utiliser le menu déroulant **Supprimer Ligne** pour sélectionner et supprimer des lignes de transmission
- Utiliser le menu déroulant **Supprimer Nœud** pour sélectionner et supprimer des nœuds de bus
- Alternativement, cliquer sur n'importe quel nœud sur la carte et utiliser le bouton "Supprimer" dans la popup

### Exécution des Simulations

- Cliquer sur **Exécuter Simulation** pour relancer l'algorithme de Lanczos avec la configuration actuelle
- Cliquer sur **Réinitialiser Réseau** pour restaurer le réseau à son état original

## Architecture

```
web_client/
├── app.py              # Backend Flask avec API REST
├── requirements.txt    # Dépendances Python
├── README.md          # Ce fichier
└── static/
    ├── index.html     # Page HTML principale
    ├── styles.css     # Styles CSS
    └── app.js         # JavaScript frontend
```

## Points d'Accès API

| Point d'Accès           | Méthode | Description                              |
| ----------------------- | ------- | ---------------------------------------- |
| `/api/init`             | POST    | Initialiser le réseau                    |
| `/api/simulate`         | POST    | Exécuter la simulation                   |
| `/api/set_endpoints`    | POST    | Définir les bus entrée/sortie            |
| `/api/remove_line`      | POST    | Supprimer une ligne de transmission      |
| `/api/remove_node`      | POST    | Supprimer un nœud de bus                 |
| `/api/reset`            | POST    | Réinitialiser le réseau à l'état initial |
| `/api/get_buses`        | GET     | Obtenir la liste de tous les bus         |
| `/api/get_lines`        | GET     | Obtenir la liste de toutes les lignes    |
| `/api/simulation_stats` | GET     | Obtenir les statistiques de simulation   |

## Dépendances

- **Flask** : Framework web
- **Flask-CORS** : Partage de ressources cross-origin
- **NumPy** : Calculs numériques
- **NetworkX** : Opérations sur les graphes
- **PyPSA** : Analyse des systèmes électriques
- **Pandas** : Manipulation de données

## Bibliothèques Frontend (CDN)

- **Leaflet** : Cartes interactives
- **Chart.js** : Visualisation de données
- **Tom Select** : Menus déroulants avec recherche
