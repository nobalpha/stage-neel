# Analyse de Résilience du Réseau Électrique Européen

Projet de stage à l'Institut Néel (CNRS) — Application de l'algorithme de Lanczos pour l'analyse des réseaux électriques via un formalisme inspiré des marches quantiques.

---

## Formalisme

Le réseau électrique est modélisé comme un graphe où :

- **Nœuds (bus)** : centrales, sous-stations, points de charge
- **Arêtes (lignes)** : lignes de transmission avec poids = impédance
- **Signes (+1/-1)** : encodent la direction du flux de puissance

Le système est représenté par une **matrice Hamiltonienne H** satisfaisant :

```
H|ψ⟩ = P
```

où |ψ⟩ est le vecteur d'état (distribution de puissance).

---

## Variables Principales

| Symbole   | Description                                        |
| --------- | -------------------------------------------------- |
| **β_i**   | Éléments hors-diagonale de la matrice tridiagonale |
| **κ_i**   | Coefficients pour la reconstruction de ψ           |
| **q_i**   | Vecteurs de Lanczos (base orthonormée)             |
| **ψ**     | Distribution de puissance approximative            |
| **R_eff** | Résistance effective entre source et puits         |

---

## Algorithme de Lanczos

Méthode itérative transformant H en matrice tridiagonale T :

```
T = Qᵀ H Q
```

**Étapes :**

1. Initialisation : q₀ = 0, q₁ = vecteur source normalisé
2. Itération : qᵢ₊₁ = H·qᵢ − αᵢ·qᵢ − βᵢ·qᵢ₋₁
3. Calcul de βᵢ = ‖qᵢ₊₁‖, puis normalisation
4. Reconstruction de ψ via les coefficients κᵢ

Permet de calculer efficacement les **résistances effectives** et d'identifier les **lignes critiques**.

---

## Structure du Projet

```
stage/
├── utils.py              # Classes et algorithmes principaux
├── european.ipynb        # Notebook d'analyse du réseau européen
├── reseau_carre.ipynb    # Notebook d'analyse du réseau carré
├── networks/             # Fichiers réseau PyPSA (.nc)
│   ├── elec_s_128.nc      # Réseau 128 nœuds
│   ├── elec_s_512.nc     # Réseau 512 nœuds
│   ├── elec_s_1024.nc     # Réseau 1024 nœuds
└── web_client/           # Interface de visualisation (Flask)
```

---

## Classes Principales

### `HamiltonianGrid` (utils.py)

Classe pour tester l'algorithme sur une **grille carrée** régulière.

```python
grid = HamiltonianGrid(N=100, q_N=50, ix=0, iy=0, iw=1, ex=9, ey=9, ew=-1)
grid.create_network(grid_size=10)
grid.iterate_qs()
```

**Méthodes clés :**

- `create_network(grid_size)` : crée la grille N×N
- `iterate_qs()` : exécute les itérations de Lanczos
- `calculate_effective_resistances()` : calcule R_eff pour toutes les lignes

### `EuropeanGrid` (utils.py)

Classe pour analyser le **réseau électrique européen réel** via PyPSA.

```python
grid = EuropeanGrid(network_path="networks/elec_s_128.nc", q_N=100, source="DE0", sink="FR0")
grid.iterate_qs()
psi = grid.calculate_psi_approx()
```

**Méthodes clés :**

- `load_network()` : charge le réseau PyPSA
- `set_endpoints(source, sink)` : définit source/puits
- `calculate_psi_approx()` : calcule la distribution de puissance
- `remove_line(line_id)` / `remove_node(node_id)` : simule des pannes

---

## Installation

```bash
# Cloner le dépôt
git clone <repo-url>
cd stage

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## Réseaux Disponibles

| Fichier          | Nœuds | Description           |
| ---------------- | ----- | --------------------- |
| `elec_s_128.nc`  | 128   | Résolution moyenne    |
| `elec_s_512.nc`  | 512   | Très haute résolution |
| `elec_s_1024.nc` | 1024  | Résolution maximale   |

---

## Sources de Données

### PyPSA-Eur

Modèle open-source du réseau électrique européen :

- https://github.com/PyPSA/pypsa-eur
- Données ENTSO-E, topologie réelle

### Données Géographiques

- `country_shapes.geojson` : frontières pays
- `regions_onshore_*.geojson` : régions terrestres
- `regions_offshore_*.geojson` : zones maritimes

---

## Références

1. **Algorithme de Lanczos** — Lanczos, C. (1950). "An iteration method for the solution of the eigenvalue problem"
2. **PyPSA** — Brown, T. et al. (2018). "PyPSA: Python for Power System Analysis"
3. **PyPSA-Eur** — Hörsch, J. et al. (2018). "PyPSA-Eur: An open optimisation model of the European transmission system"
4. **Marches Quantiques** — Kempe, J. (2003). "Quantum random walks: An introductory overview"

---

_Stage réalisé à l'Institut Néel — CNRS_
