# Modélisation des réseaux électriques par une approche quantique

Réalisé par **Sylvain Hoffmann** & **Roni Kolukisayan**

Tuteur de stage : M. Didier Mayou

Projet de stage à l'Institut Néel (CNRS)

## Formalisme

Le réseau électrique est modélisé comme un graphe où :

- **Nœuds (bus)** : centrales, sous-stations, points de charge
- **Arêtes (lignes)** : lignes de transmission avec poids
- **Signes (+1/-1)** : encodent la direction du flux de puissance
- **Poids (B)** : susceptibilité des lignes

Le système est représenté par une **matrice Hamiltonienne H** satisfaisant :

```
H|ψ⟩ = P
```

où |ψ⟩ est le vecteur d'état (distribution de puissance) et P est la puissance injectée/extraite.

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

Méthode itérative representant H dans la base de Krylov par les vecteurs de Lanczos :

**Étapes :**

1. Initialisation : q₀ = 0, q₁ = vecteur source normalisé
2. Itération : qᵢ₊₁ = (1/βᵢ₊₁) ⋅ (H·qᵢ − βᵢ·qᵢ₋₁)
3. Calcul de βᵢ₊₁ = ‖qᵢ₊₁‖, puis normalisation
4. Reconstruction de ψ via les coefficients κᵢ

Permet de calculer efficacement l'effet de la pérturbation par un regard local pour calculer les **résistances effectives** et d'identifier les **lignes critiques**.

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

1. **PyPSA** — Brown, T. et al. (2018). "PyPSA: Python for Power System Analysis"
2. **PyPSA-Eur** — Hörsch, J. et al. (2018). "PyPSA-Eur: An open optimisation model of the European transmission system"
3. **Quantum Analogy of the Power Grid** — Guichard P. (2024) A quantum analogy for the modeling of large power grids

---

_Stage réalisé à l'Institut Néel — CNRS_
