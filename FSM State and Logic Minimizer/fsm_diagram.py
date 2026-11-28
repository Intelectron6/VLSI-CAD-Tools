"""
State Transition Diagram Generator for FSM Minimizer.

Generates visual state transition diagrams (state graphs) for both the
initial and post-state-minimization FSM tables.

The FSM is a Mealy machine: output z depends on both present state PS
and input x. Edge labels are in "x/z" format (input/output).

Uses matplotlib + networkx for rendering (no external binaries required).
Graphviz is used as an optional alternative if available.

Usage:
    python fsm_diagram.py <csv_or_json_file> [output_prefix] [format]

Examples:
    python fsm_diagram.py fsm.csv fsm_diagrams png
    python fsm_diagram.py examples/fsm.json fsm_diagrams pdf

Generates:
    - <output_prefix>_initial.<format>  (initial state diagram)
    - <output_prefix>_reduced.<format>  (reduced state diagram)
"""

import sys
import os
from pathlib import Path

# Add the FSM directory to path
FSM_DIR = os.path.dirname(os.path.abspath(__file__))
if FSM_DIR not in sys.path:
    sys.path.insert(0, FSM_DIR)

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx


def build_initial_graph(stt_df, diagram_name="Initial FSM"):
    """Build a networkx DiGraph from the original transition table.

    Parameters
    ----------
    stt_df : pandas.DataFrame
        DataFrame with columns 'x', 'PS', 'NS', 'z'.
    diagram_name : str
        Title for the diagram.

    Returns
    -------
    nx.DiGraph
        The generated graph with node and edge attributes.
    """
    G = nx.DiGraph()
    G.graph['name'] = diagram_name

    # Get unique states and inputs
    states = sorted(stt_df['PS'].unique())

    # Add all states as nodes
    for state in states:
        G.add_node(str(state), label=str(state))

    # Mark initial state (first state in sorted order)
    initial_state = str(states[0])

    # Add transitions as edges (Mealy machine: label = "x/z")
    transitions = {}
    for _, row in stt_df.iterrows():
        key = (str(row['PS']), str(row['x']))
        value = (str(row['NS']), str(row['z']))
        transitions[key] = value

    for (ps, x), (ns, z) in sorted(transitions.items()):
        label = f"{x}/{z}"
        G.add_edge(str(ps), str(ns), label=label)

    return G, initial_state


def build_reduced_graph(result, stt_df, diagram_name="Reduced FSM"):
    """Build a networkx DiGraph from minimization results.

    Uses the state_mapping from result to map old states to new states
    (S0, S1, ...) and reconstructs the reduced transition table.

    Parameters
    ----------
    result : dict
        Result dict from fsm_minimizer.run_minimization() containing
        'state_mapping' and 'final_states'.
    stt_df : pandas.DataFrame
        Original transition table (needed to reconstruct transitions).
    diagram_name : str
        Title for the diagram.

    Returns
    -------
    tuple
        (nx.DiGraph, initial_state_name)
    """
    G = nx.DiGraph()
    G.graph['name'] = diagram_name

    state_mapping = result['state_mapping']
    final_states = result['final_states']

    # Add all new states as nodes
    for state in final_states:
        G.add_node(str(state), label=str(state))

    # Mark initial state (S0)
    initial_state = 'S0'

    # Reconstruct reduced transitions from original stt_df using state_mapping
    transitions = {}
    for _, row in stt_df.iterrows():
        old_ps = str(row['PS'])
        old_ns = str(row['NS'])
        x = str(row['x'])
        z = str(row['z'])

        new_ps = state_mapping.get(old_ps, old_ps)
        new_ns = state_mapping.get(old_ns, old_ns)

        key = (new_ps, x)
        value = (new_ns, z)
        transitions[key] = value  # Should be unique after minimization

    for (ps, x), (ns, z) in sorted(transitions.items()):
        label = f"{x}/{z}"
        G.add_edge(str(ps), str(ns), label=label)

    return G, initial_state


def draw_graph(G, initial_state, output_path, diagram_name, format='png'):
    """Draw a networkx DiGraph to file using matplotlib.

    Parameters
    ----------
    G : nx.DiGraph
        The graph to draw.
    initial_state : str
        Name of the initial state node.
    output_path : str
        Output file path (without extension).
    diagram_name : str
        Title for the diagram.
    format : str
        Output format ('png', 'pdf', 'svg', etc.).
    """
    plt.figure(figsize=(10, 6))
    plt.title(diagram_name, fontsize=16, fontweight='bold', pad=20)

    # Use spring layout for good node placement
    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)

    # Draw nodes with colors
    node_colors = []
    for node in G.nodes():
        if node == initial_state:
            node_colors.append('#90EE90')  # light green for initial
        else:
            node_colors.append('#ADD8E6')  # light blue for others

    # Draw everything with nx.draw() so arrows are rendered on DiGraph edges
    nx.draw(G, pos,
            node_color=node_colors,
            node_size=2000,
            edgecolors='black',
            linewidths=2,
            font_size=12,
            font_weight='bold',
            edge_color='#333333',
            width=2,
            arrows=True,
            arrowsize=25,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.15')

    # Draw node labels (overrides nx.draw default labels)
    labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=12, font_weight='bold')

    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=10,
                                 font_color='#333333',
                                 label_pos=0.5)

    # Add legend for initial state
    import matplotlib.patches as mpatches
    initial_patch = mpatches.Patch(color='#90EE90', label='Initial State')
    other_patch = mpatches.Patch(color='#ADD8E6', label='State')
    plt.legend(handles=[initial_patch, other_patch], loc='lower left',
               fontsize=10)

    plt.axis('off')
    plt.tight_layout()
    output_path_with_ext = f"{output_path}.{format}"
    plt.savefig(output_path_with_ext, format=format, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Diagram saved to {output_path_with_ext}")


def generate_initial_diagram(stt_df, output_path, diagram_name="Initial FSM",
                             format='png'):
    """Generate state transition diagram for the initial (unminimized) FSM.

    Parameters
    ----------
    stt_df : pandas.DataFrame
        Original transition table with columns 'x', 'PS', 'NS', 'z'.
    output_path : str
        Output file path (without extension).
    diagram_name : str
        Title for the diagram.
    format : str
        Output format ('png', 'pdf', 'svg', etc.).
    """
    G, initial_state = build_initial_graph(stt_df, diagram_name)
    draw_graph(G, initial_state, output_path, diagram_name, format)
    return G


def generate_reduced_diagram(result, stt_df, output_path,
                             diagram_name="Reduced FSM", format='png'):
    """Generate state transition diagram for the reduced (minimized) FSM.

    Parameters
    ----------
    result : dict
        Result dict from fsm_minimizer.run_minimization() containing
        'state_mapping' and 'final_states'.
    stt_df : pandas.DataFrame
        Original transition table (needed to reconstruct transitions).
    output_path : str
        Output file path (without extension).
    diagram_name : str
        Title for the diagram.
    format : str
        Output format ('png', 'pdf', 'svg', etc.).
    """
    G, initial_state = build_reduced_graph(result, stt_df, diagram_name)
    draw_graph(G, initial_state, output_path, diagram_name, format)
    return G


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fsm_diagram.py <csv_or_json_file> "
              "[output_prefix] [format]")
        print("\nExamples:")
        print("  python fsm_diagram.py fsm.csv fsm_diagrams")
        print("  python fsm_diagram.py examples/fsm.json fsm_diagrams pdf")
        sys.exit(1)

    input_path = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else 'fsm_diagrams'
    output_format = sys.argv[3] if len(sys.argv) > 3 else 'png'

    # Load input
    if input_path.endswith('.json'):
        from fsm_parser import json_to_dataframe
        stt_df = json_to_dataframe(input_path)
    else:
        stt_df = pd.read_csv(input_path)

    from fsm_minimizer import run_minimization

    # Run minimization to get result with state_mapping
    result = run_minimization(stt_df, target_cost=float('inf'))

    # Generate initial diagram
    initial_path = f"{output_prefix}_initial"
    print(f"Generating initial state diagram: {initial_path}.{output_format}")
    generate_initial_diagram(stt_df, initial_path, "Initial FSM",
                             format=output_format)

    # Generate reduced diagram
    reduced_path = f"{output_prefix}_reduced"
    print(f"Generating reduced state diagram: {reduced_path}.{output_format}")
    generate_reduced_diagram(result, stt_df, reduced_path, "Reduced FSM",
                             format=output_format)

    print("\nDiagrams generated successfully.")
