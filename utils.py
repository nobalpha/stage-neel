import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random
from pyvis.network import Network
from networkx.readwrite import json_graph
import json


class HamiltonianGrid(nx.Graph):
    def __init__(self, N, q_N, ix, iy, iw, ex, ey, ew):
        super().__init__()
        self.N = N
        self.q_N = q_N
        self.q_snapshots = {}
        self._nodes = []
        self._lines = []
        self.betas = np.zeros(q_N)

        self.ix, self.iy, self.iw, self.ex, self.ey, self.ew = ix, iy, iw, ex, ey, ew

    def create_network(self, grid_size):

        # 1. Ajout des Bus (Nœuds)
        for r in range(grid_size):
            for c in range(grid_size):
                node_id = f"N_{r}_{c}"
                self.add_node(node_id, name=node_id,
                              type='node', weight=0, pos=(c, -r))

                self._nodes.append(node_id)

        # 2. Ajout des Lignes (Nodes intermédiaires)
        line_count = 0
        for r in range(grid_size):
            for c in range(grid_size):
                # Ligne Horizontale
                if c < grid_size - 1:

                    line_id = f"L_h_{r}_{c}"
                    self.add_node(line_id, name=line_id, type='line',
                                  weight=0, pos=(c + 0.5, -r))
                    # La ligne est connectée aux deux bus adjacents
                    self.add_edge(f"N_{r}_{c}", line_id, sign=+1)
                    self.add_edge(f"N_{r}_{c+1}", line_id, sign=-1)
                    line_count += 1

                # Ligne Verticale
                if r < grid_size - 1:
                    line_id = f"L_v_{r}_{c}"
                    self.add_node(line_id, name=line_id, type='line',
                                  weight=0, pos=(c, -(r + 0.5)))
                    # La ligne est connectée aux deux Bus adjacents
                    self.add_edge(f"N_{r}_{c}", line_id, sign=-1)
                    self.add_edge(f"N_{r+1}_{c}", line_id, sign=+1)
                    line_count += 1

                self._lines.append(line_id)
        self.pos = nx.get_node_attributes(self, 'pos')

        return self

    def draw_network(self, with_labels=False, ax=None, node_size=600, figsize=(18, 10)):
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        weights = nx.get_node_attributes(self, 'weight').values()
        weights = list(map(lambda x: abs(x), weights))
        labels = {}
        for node in self.nodes():
            w = self.nodes[node]["weight"]

            if abs(w) > 0:

                labels[node] = f"{node}\n({w:.2f})"  # Affiche Nom et Poids
            else:
                labels[node] = "0"

            if node == f"N_{self.ix}_{self.iy}":
                labels[node] = f"Ins: {labels[node]}"
            elif node == f"N_{self.ex}_{self.ey}":
                labels[node] = f"Ext: {labels[node]}"

        nx.draw(self, pos=self.pos, ax=ax, node_color=weights, with_labels=False,
                cmap=plt.cm.viridis, node_size=node_size, font_size=9, font_weight="bold")
        if with_labels:
            nx.draw_networkx_labels(self, self.pos, labels=labels,
                                    font_size=8,
                                    font_family='sans-serif',
                                    font_weight="bold")

    def get_edge_sign(self, u, v):

        return self[u][v].get('sign', 1)

    def remove_element(self, type: str, x: int, y: int, o=""):
        type = type.upper()
        if type == "N":
            self.remove_node(f"{type}_{x}_{y}")
        elif type == "L":
            self.remove_node(f"{type}_{o}_{x}_{y}")

    def calculate_q_i(self, i):  # i is q_i
        temp_weights = {}
        next_beta_sq = 0

        if i == 1:
            for node in self.nodes:
                self.nodes[node]["weight"] = 0
            beta_1 = (self.iw**2+self.ew**2)**(1/2)

            insert_id = f"N_{self.ix}_{self.iy}"

            self.nodes[insert_id]["weight"] = self.iw/beta_1

            extract_id = f"N_{self.ex}_{self.ey}"
            self.nodes[extract_id]["weight"] = self.ew/beta_1
            self.q_snapshots[0] = {insert_id: self.iw /
                                   beta_1, extract_id: self.ew/beta_1}
            self.betas[0] = beta_1
            return beta_1

        nodes_to_check = set()
        for node_id in self.q_snapshots[i-2]:
            nodes_to_check.update(self.adj[node_id])

        for node_id in nodes_to_check:
            # H * q1: Sum weights of neighbors from the q1 snapshot
            h_qi = 0
            for neighbor in self.adj[node_id]:
                if neighbor in self.q_snapshots[i-2]:
                    # IMPORTANT: Le signe dépend de la direction neighbor -> node
                    sign = self.get_edge_sign(node_id, neighbor)
                    w = self.q_snapshots[i-2][neighbor]
                    h_qi += w * sign

            if i == 2:
                w_prime = h_qi
            else:

                w_prime = h_qi - self.betas[i - 1 - 1] * \
                    self.q_snapshots[i-2 - 1].get(node_id, 0)

            if w_prime != 0:
                temp_weights[node_id] = w_prime
                next_beta_sq += w_prime**2

        # Calculate normalization factor
        beta_i = next_beta_sq**(0.5)
        for node in self.nodes:
            # Ensure origin and all others are zero
            self.nodes[node]["weight"] = 0
        # Normalize and store ONLY nodes with values
        self.q_snapshots[i-1] = {}
        for node_id, weight in temp_weights.items():
            norm_weight = weight / beta_i
            self.q_snapshots[i-1][node_id] = norm_weight
            # Update graph for drawing
            self.nodes[node_id]["weight"] = norm_weight

        return beta_i

    def apply_q_i(self, i):
        q_i = self.q_snapshots[i-1]
        for node in self.nodes:
            self.nodes[node]["weight"] = q_i.get(node, 0)

    def iterate_qs(self):
        for i in range(1, self.q_N + 1):
            beta_i = self.calculate_q_i(i)
            self.betas[i-1] = beta_i

    def calculate_kappa(self):
        self.kappas = np.zeros((len(self.q_snapshots) // 2,))
        for i_pair in range(2, len(self.q_snapshots) + 1, 2):
            i = i_pair // 2

            product_ratios = 1.0
            for j in range(1, i):
                product_ratios *= (self.betas[2*j +
                                   1 - 1] / self.betas[2*j + 2 - 1])

            sign = (-1)**(i - 1)
            kappa_2i = sign * (self.iw / self.betas[1]) * product_ratios
            if i == 1:
                kappa_2i = self.iw / self.betas[1]  # k2*b2 = P
            self.kappas[i-1] = kappa_2i

    def calculate_psi_approx(self):
        self.psis = [{} for _ in range(len(self.q_snapshots) // 2)]
        psi_app = {node: 0 for node in self.nodes}

        self.calculate_kappa()
        for i_pair in range(2, len(self.q_snapshots) + 1, 2):
            i = i_pair // 2
            kappa_2i = self.kappas[i-1]
            for node, val in self.q_snapshots[i_pair-1].items():
                psi_app[node] += kappa_2i * val
            self.psis[i-1] = psi_app
        return psi_app

    def apply_psi_to_graph(self, i):
        psi_approx = self.psis[i-1]
        for node in self.nodes:
            self.nodes[node]["weight"] = psi_approx.get(node, 0)

    def psi_approx_squared(self):
        self.kappas_sum = np.cumsum((self.kappas)**2)
        self.psi_sqs = self.kappas_sum
        return self.psi_sqs

    def calculate_effective_resistances(self):
        self.R_eff = []
        for psi in self.psi_sqs:
            self.R_eff.append(1/psi)

        return self.R_eff

    def save_graph_json(self, filename="graph_data.json"):
        data = json_graph.cytoscape_data(self)

        for node in data['elements']['nodes']:
            pos = node["data"]['pos']
            node['position'] = {
                # On multiplie souvent car Cyto utilise une échelle pixel
                'x': float(pos[0] * 1000),
                'y': float(pos[1] * 1000)
            }

            node['data']['special'] = False
            if node["data"]["name"] == f"N_{self.ix}" or node["data"]["name"] == f"N_{self.ex}":
                node['data']['special'] = True

            del node['data']['pos']

        json.dump(data, open(filename, "w"))


class EuropeanGrid(nx.Graph):
    def __init__(self, pypsa_network, q_N, ix, iy, iw, ex, ey, ew):
        super().__init__()
        self.n = pypsa_network  # Store the PyPSA object
        self.q_N = q_N
        self.q_snapshots = {}
        self.betas = np.zeros(q_N)
        self._nodes = []
        self._lines = []

        # In real data, ix/iy/ex/ey will be Bus IDs (strings), not grid coordinates
        self.ix, self.iy = ix, iy
        self.ex, self.ey = ex, ey
        self.iw, self.ew = iw, ew

    def build_from_pypsa(self):
        """
        Converts PyPSA topology into the specific node-line-node 
        structure required by your algorithm.
        """
        # 1. Add Buses as Nodes
        for bus_id, row in self.n.buses.iterrows():
            self.add_node(f"N_{bus_id}",
                          type='node',
                          weight=0.0,
                          pos=(row['x'], row['y']),
                          country=row['country'])
            self._nodes.append(f"N_{bus_id}")

        # 2. Add Lines as Intermediate Nodes (to match your L_h/L_v logic)
        for line_id, row in self.n.lines.iterrows():
            u, v = row['bus0'], row['bus1']
            line_id = f"L_{line_id}"
            length = float(row.get('length', 1.0))
            # Calculate midpoint for the 'line node' position
            pos_u = self.nodes[f"N_{u}"]['pos']
            pos_v = self.nodes[f"N_{v}"]['pos']
            mid_pos = ((pos_u[0] + pos_v[0])/2, (pos_u[1] + pos_v[1])/2)
            sqrt_b = (1 / length)**0.5

            # Add the line as a node
            self.add_node(line_id, type='line', weight=0.0, pos=mid_pos)
            self._lines.append(line_id)

            # Connect with signs for your algorithm
            self.add_edge(f"N_{u}", line_id, sign=+sqrt_b)
            self.add_edge(f"N_{v}", line_id, sign=-sqrt_b)

        self.pos = nx.get_node_attributes(self, 'pos')
        return self

    # --- Keep your existing calculate_q_i, iterate_qs, etc. here ---
    # Just ensure you reference self.ix instead of f"N_{self.ix}_{self.iy}"
    def draw_network(self, with_labels=False, ax=None, node_size=600, figsize=(18, 10)):
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        weights = nx.get_node_attributes(self, 'weight').values()
        weights = list(map(lambda x: abs(x), weights))
        labels = {}
        for node in self.nodes():
            w = self.nodes[node]["weight"]

            if abs(w) > 0:

                labels[node] = f"{node}\n({w:.2f})"  # Affiche Nom et Poids
            else:
                labels[node] = "0"

            if node == f"N_{self.ix}":
                labels[node] = f"Ins: {labels[node]}"
            elif node == f"N_{self.ex}":
                labels[node] = f"Ext: {labels[node]}"

        nx.draw(self, pos=self.pos, ax=ax, node_color=weights, with_labels=False,
                cmap=plt.cm.viridis, node_size=node_size, font_size=9, font_weight="bold")
        if with_labels:
            nx.draw_networkx_labels(self, self.pos, labels=labels,
                                    font_size=8,
                                    font_family='sans-serif',
                                    font_weight="bold")

    def get_edge_sign(self, u, v):

        return self[u][v].get('sign', 1)

    def remove_element(self, type: str, index: int, country_code: str = ""):
        type = type.upper()
        if type == "N":
            self.remove_node(f"{country_code} {index}")
        elif type == "L":
            self.remove_node(f"L_{index}")

    def calculate_q_i(self, i):  # i is q_i
        temp_weights = {}
        next_beta_sq = 0

        if i == 1:
            for node in self.nodes:
                self.nodes[node]["weight"] = 0
            beta_1 = (self.iw**2+self.ew**2)**(1/2)

            insert_id = f"N_{self.ix}"

            self.nodes[insert_id]["weight"] = self.iw/beta_1

            extract_id = f"N_{self.ex}"
            self.nodes[extract_id]["weight"] = self.ew/beta_1
            self.q_snapshots[0] = {insert_id: self.iw /
                                   beta_1, extract_id: self.ew/beta_1}
            self.betas[0] = beta_1
            return beta_1

        nodes_to_check = set()
        for node_id in self.q_snapshots[i-2]:
            nodes_to_check.update(self.adj[node_id])

        for node_id in nodes_to_check:
            # H * q1: Sum weights of neighbors from the q1 snapshot
            h_qi = 0
            for neighbor in self.adj[node_id]:
                if neighbor in self.q_snapshots[i-2]:
                    # IMPORTANT: Le signe dépend de la direction neighbor -> node
                    sign = self.get_edge_sign(node_id, neighbor)
                    w = self.q_snapshots[i-2][neighbor]
                    h_qi += w * sign

            if i == 2:
                w_prime = h_qi
            else:

                w_prime = h_qi - self.betas[i - 1 - 1] * \
                    self.q_snapshots[i-2 - 1].get(node_id, 0)

            if w_prime != 0:
                temp_weights[node_id] = w_prime
                next_beta_sq += w_prime**2

        # Calculate normalization factor
        beta_i = next_beta_sq**(0.5)
        for node in self.nodes:
            # Ensure origin and all others are zero
            self.nodes[node]["weight"] = 0
        # Normalize and store ONLY nodes with values
        self.q_snapshots[i-1] = {}
        for node_id, weight in temp_weights.items():
            norm_weight = weight / beta_i
            self.q_snapshots[i-1][node_id] = norm_weight
            # Update graph for drawing
            self.nodes[node_id]["weight"] = norm_weight

        return beta_i

    def apply_q_i(self, i):
        q_i = self.q_snapshots[i-1]
        for node in self.nodes:
            self.nodes[node]["weight"] = q_i.get(node, 0)

    def iterate_qs(self):
        for i in range(1, self.q_N + 1):
            beta_i = self.calculate_q_i(i)
            self.betas[i-1] = beta_i

    def save_graph_json(self, filename="graph_data.json"):
        data = json_graph.cytoscape_data(self)

        for node in data['elements']['nodes']:
            pos = node["data"]['pos']
            node['position'] = {
                # On multiplie souvent car Cyto utilise une échelle pixel
                'x': float(pos[0] * 1000),
                'y': float(pos[1] * 1000)
            }

            node['data']['special'] = False
            if node["data"]["name"] == f"N_{self.ix}" or node["data"]["name"] == f"N_{self.ex}":
                node['data']['special'] = True

            del node['data']['pos']

        json.dump(data, open(filename, "w"))

    def calculate_kappa(self):
        self.kappas = np.zeros((len(self.q_snapshots) // 2,))
        for i_pair in range(2, len(self.q_snapshots) + 1, 2):
            i = i_pair // 2

            product_ratios = 1.0
            for j in range(1, i):
                product_ratios *= (self.betas[2*j +
                                   1 - 1] / self.betas[2*j + 2 - 1])

            sign = (-1)**(i - 1)
            kappa_2i = sign * (self.iw / self.betas[1]) * product_ratios
            if i == 1:
                kappa_2i = self.iw / self.betas[1]  # k2*b2 = P
            self.kappas[i-1] = kappa_2i

    def calculate_psi_approx(self):
        self.psis = [{} for _ in range(len(self.q_snapshots) // 2)]
        psi_app = {node: 0 for node in self.nodes}

        self.calculate_kappa()
        for i_pair in range(2, len(self.q_snapshots) + 1, 2):
            i = i_pair // 2
            kappa_2i = self.kappas[i-1]
            for node, val in self.q_snapshots[i_pair-1].items():
                psi_app[node] += kappa_2i * val
            self.psis[i-1] = psi_app
        return psi_app

    def apply_psi_to_graph(self, i):
        psi_approx = self.psis[i-1]
        for node in self.nodes:
            self.nodes[node]["weight"] = psi_approx.get(node, 0)

    def psi_approx_squared(self):
        self.kappas_sum = np.cumsum((self.kappas)**2)
        self.psi_sqs = self.kappas_sum
        return self.psi_sqs

    def calculate_effective_resistances(self):
        self.R_eff = []
        for psi in self.psi_sqs:
            self.R_eff.append(1/psi)

        return self.R_eff
