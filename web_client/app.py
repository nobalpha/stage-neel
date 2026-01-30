"""
Flask backend for the European Grid Web Client
Provides REST API for grid simulation, node manipulation, and visualization
"""

from utils import EuropeanGrid
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import numpy as np
import pypsa
import sys
import os

# Add parent directory to path to import utils
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, static_folder='./static', static_url_path='')
CORS(app)

# Global grid state
grid_state = {
    'grid': None,
    'network': None,
    'bus_in': 'DE1 0',
    'bus_out': 'ES1 21',
    'removed_lines': [],
    'removed_nodes': []
}


def initialize_grid(network_path='../networks/elec_s_512.nc'):
    """Initialize or reinitialize the grid"""
    global grid_state

    # Load PyPSA Network
    n = pypsa.Network(network_path)
    grid_state['network'] = n

    # Initialize EuropeanGrid
    grid = EuropeanGrid(
        n,
        q_N=len(n.buses) * 2,
        ix=grid_state['bus_in'],
        iy=None,
        iw=1,
        ex=grid_state['bus_out'],
        ey=None,
        ew=-1,
        real_data=False
    )
    grid.build_from_pypsa()

    # Re-apply removed elements
    for line_id in grid_state['removed_lines']:
        try:
            grid.remove_element("L", line_id)
        except:
            pass

    for node_id in grid_state['removed_nodes']:
        try:
            grid.remove_element("N", node_id)
        except:
            pass

    grid_state['grid'] = grid
    return grid


def run_simulation():
    """Run the Lanczos simulation on the current grid"""
    grid = grid_state['grid']
    if grid is None:
        return None

    grid.iterate_qs()
    psi_approx = grid.calculate_psi_approx()
    grid.apply_psi_to_graph(0)

    return {
        'kappas': grid.kappas.tolist() if hasattr(grid, 'kappas') else [],
        'betas': grid.betas.tolist() if hasattr(grid, 'betas') else [],
        'psi_squared': grid.psi_approx_squared().tolist() if hasattr(grid, 'psi_approx_squared') else [],
        'effective_resistances': grid.calculate_effective_resistances() if hasattr(grid, 'calculate_effective_resistances') else []
    }


def get_graph_data():
    """Convert grid to JSON format for frontend visualization"""
    grid = grid_state['grid']
    if grid is None:
        return {'nodes': [], 'edges': []}

    nodes = []
    edges = []

    # Get max weight for normalization
    weights = [abs(data.get('weight', 0))
               for node, data in grid.nodes(data=True)]
    max_weight = max(weights) if weights and max(weights) > 0 else 1

    for node_id, data in grid.nodes(data=True):
        pos = data.get('pos', (0, 0))
        weight = data.get('weight', 0)
        node_type = data.get('type', 'node')
        country = data.get('country', 'N/A')

        # Determine if this is input/output node
        is_input = node_id == f"N_{grid_state['bus_in']}"
        is_output = node_id == f"N_{grid_state['bus_out']}"

        nodes.append({
            'id': node_id,
            'lat': pos[1],
            'lon': pos[0],
            'weight': weight,
            'normalized_weight': abs(weight) / max_weight if max_weight > 0 else 0,
            'type': node_type,
            'country': country,
            'is_input': is_input,
            'is_output': is_output
        })

    for u, v, data in grid.edges(data=True):
        edges.append({
            'source': u,
            'target': v,
            'sign': data.get('sign', 1)
        })

    return {'nodes': nodes, 'edges': edges, 'max_weight': max_weight}

# Routes


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/api/init', methods=['POST'])
def api_init():
    """Initialize the grid with optional parameters"""
    data = request.get_json() or {}

    network_path = data.get('network_path', '../networks/elec_s_512.nc')
    grid_state['bus_in'] = data.get('bus_in', 'DE1 0')
    grid_state['bus_out'] = data.get('bus_out', 'ES1 21')
    grid_state['removed_lines'] = []
    grid_state['removed_nodes'] = []

    try:
        initialize_grid(network_path)
        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results,
            'bus_in': grid_state['bus_in'],
            'bus_out': grid_state['bus_out']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """Run simulation with current grid state"""
    try:
        if grid_state['grid'] is None:
            initialize_grid()

        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/set_endpoints', methods=['POST'])
def api_set_endpoints():
    """Set new input/output bus endpoints"""
    data = request.get_json()

    if 'bus_in' in data:
        grid_state['bus_in'] = data['bus_in']
    if 'bus_out' in data:
        grid_state['bus_out'] = data['bus_out']

    try:
        # Reinitialize with new endpoints
        initialize_grid()
        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results,
            'bus_in': grid_state['bus_in'],
            'bus_out': grid_state['bus_out']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/remove_line', methods=['POST'])
def api_remove_line():
    """Remove a line from the grid"""
    data = request.get_json()
    line_id = data.get('line_id')

    if not line_id:
        return jsonify({'success': False, 'error': 'line_id required'}), 400

    try:
        grid = grid_state['grid']
        if grid is None:
            initialize_grid()
            grid = grid_state['grid']

        # Extract the numeric part if full ID provided
        if line_id.startswith('L_'):
            line_id = line_id[2:]

        grid.remove_element("L", line_id)
        grid_state['removed_lines'].append(line_id)

        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results,
            'removed_line': line_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/remove_node', methods=['POST'])
def api_remove_node():
    """Remove a node from the grid"""
    data = request.get_json()
    node_id = data.get('node_id')

    if not node_id:
        return jsonify({'success': False, 'error': 'node_id required'}), 400

    try:
        grid = grid_state['grid']
        if grid is None:
            initialize_grid()
            grid = grid_state['grid']

        # Extract parts if full ID provided (e.g., "N_DE1 0" -> "DE1", "0")
        if node_id.startswith('N_'):
            node_id = node_id[2:]

        parts = node_id.split(' ')
        if len(parts) == 2:
            country_code = parts[0]
            index = parts[1]
            grid.remove_element("N", index, country_code)
        else:
            grid.remove_element("N", node_id)

        grid_state['removed_nodes'].append(node_id)

        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results,
            'removed_node': node_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset the grid to initial state"""
    grid_state['removed_lines'] = []
    grid_state['removed_nodes'] = []

    try:
        initialize_grid()
        simulation_results = run_simulation()
        graph_data = get_graph_data()

        return jsonify({
            'success': True,
            'graph': graph_data,
            'simulation': simulation_results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get_buses', methods=['GET'])
def api_get_buses():
    """Get list of all available buses"""
    try:
        if grid_state['network'] is None:
            n = pypsa.Network('../networks/elec_s_512.nc')
        else:
            n = grid_state['network']

        buses = []
        for bus_id, row in n.buses.iterrows():
            buses.append({
                'id': bus_id,
                'country': row['country'],
                'x': row['x'],
                'y': row['y']
            })

        return jsonify({'success': True, 'buses': buses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get_lines', methods=['GET'])
def api_get_lines():
    """Get list of all available lines"""
    try:
        grid = grid_state['grid']
        if grid is None:
            return jsonify({'success': True, 'lines': []})

        lines = []
        for line_id in grid._lines:
            lines.append({
                'id': line_id,
                'weight': grid.nodes[line_id].get('weight', 0)
            })

        return jsonify({'success': True, 'lines': lines})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulation_stats', methods=['GET'])
def api_simulation_stats():
    """Get current simulation statistics"""
    try:
        grid = grid_state['grid']
        if grid is None:
            return jsonify({'success': False, 'error': 'Grid not initialized'})

        return jsonify({
            'success': True,
            'stats': {
                'num_nodes': len(grid._nodes),
                'num_lines': len(grid._lines),
                'bus_in': grid_state['bus_in'],
                'bus_out': grid_state['bus_out'],
                'removed_lines': grid_state['removed_lines'],
                'removed_nodes': grid_state['removed_nodes'],
                'avg_beta': float(np.mean(grid.betas)) if hasattr(grid, 'betas') else 0,
                'avg_resistance': float(np.mean(grid.R_eff)) if hasattr(grid, 'R_eff') and grid.R_eff else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("Initializing European Grid Web Client...")
    print("Loading network data...")

    # Change to parent directory to access networks folder
    # os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    initialize_grid('../networks/elec_s_512.nc')
    run_simulation()

    print("Grid initialized successfully!")
    print("Starting web server on http://localhost:5000")

    app.run(debug=True, port=5000, threaded=True)
