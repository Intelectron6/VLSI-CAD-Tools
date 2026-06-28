import os

import circuit_modules
from matplotlib import pyplot as plt


def load_netlist(netlist_path):
    with open(netlist_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        raise ValueError('Netlist must contain at least input and output lines')

    input_nodes = lines[0].split()[1:]
    output_nodes = lines[1].split()[1:]
    ckt_nodes = [line.split() for line in lines[2:]]
    return input_nodes, output_nodes, ckt_nodes


def seed_flipflop_values(node_vals, ckt_nodes):
    for node in ckt_nodes:
        if node[0] == 'DFF':
            ff_name = node[4]
            if ff_name in circuit_modules._flipflop_state:
                node_vals[ff_name] = circuit_modules._flipflop_state[ff_name]['q']


def get_node_value(node_vals, name):
    return node_vals.get(name, 'x')


def is_clock_signal(name):
    return name.lower() in {'clk', 'clock', 'clkin', 'clock_in'}


def build_input_vectors(input_nodes, cycles, clock_nodes=None, fixed_values=None):
    if clock_nodes is None:
        clock_nodes = []
    if fixed_values is None:
        fixed_values = {}

    vectors = []
    for cycle_index in range(cycles):
        vector = []
        for name in input_nodes:
            if name in clock_nodes or is_clock_signal(name):
                vector.append('0' if cycle_index % 2 == 0 else '1')
            elif name in fixed_values:
                seq = fixed_values[name]
                vector.append(seq[cycle_index % len(seq)])
            else:
                vector.append('0')
        vectors.append(tuple(vector))
    return vectors


def evaluate_cycle(input_nodes, input_vector, ckt_nodes, output_nodes):
    node_vals = {}
    for name, value in zip(input_nodes, input_vector):
        node_vals[name] = value

    seed_flipflop_values(node_vals, ckt_nodes)

    for node in ckt_nodes:
        if node[0] == 'DFF':
            continue

        if node[0] == 'NOT':
            node_vals[node[2]] = circuit_modules.not_gate(get_node_value(node_vals, node[1]))
        elif node[0] == 'BUFF':
            node_vals[node[2]] = circuit_modules.buffer(get_node_value(node_vals, node[1]))
        elif node[0] == 'AND':
            node_vals[node[3]] = circuit_modules.and_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'OR':
            node_vals[node[3]] = circuit_modules.or_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'NAND':
            node_vals[node[3]] = circuit_modules.nand_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'NOR':
            node_vals[node[3]] = circuit_modules.nor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'XOR':
            node_vals[node[3]] = circuit_modules.xor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'XNOR':
            node_vals[node[3]] = circuit_modules.xnor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'MUX2x1':
            node_vals[node[4]] = circuit_modules.mux_2x1(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]), get_node_value(node_vals, node[3]))

    for node in ckt_nodes:
        if node[0] == 'DFF':
            node_vals[node[4]] = circuit_modules.d_flipflop(node[4], get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]), get_node_value(node_vals, node[3]))

    return [node_vals[name] for name in output_nodes]


def simulate_cycles(input_nodes, input_vectors, ckt_nodes, output_nodes):
    if not input_vectors:
        raise ValueError('At least one input vector is required')

    circuit_modules.reset_flipflop_states()
    results = []
    for input_vector in input_vectors:
        results.append(evaluate_cycle(input_nodes, input_vector, ckt_nodes, output_nodes))
    return results


def plot_waveforms(signal_values, title='Waveform', output_path=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), 'waveform.png')

    signals = list(signal_values.keys())
    series = [signal_values[name] for name in signals]

    fig, axes = plt.subplots(len(signals), 1, figsize=(10, 2 * len(signals)), sharex=True)
    if len(signals) == 1:
        axes = [axes]

    for ax, name, values in zip(axes, signals, series):

        numeric_values = []
        for value in values:
            if value in ['1', 1, True]:
                numeric_values.append(1)
            elif value in ['0', 0, False]:
                numeric_values.append(0)
            else:
                numeric_values.append(0.5)

        # Draw each horizontal segment separately
        for i in range(len(values) - 1):

            color = 'red' if values[i] not in ['0', 0, False, '1', 1, True] else 'C0'
            linestyle = ':' if color == 'red' else '-'
            linewidth = 2.5 if color == 'red' else 1.8

            # Horizontal segment
            ax.plot(
                [i, i + 1],
                [numeric_values[i], numeric_values[i]],
                color=color,
                linestyle=linestyle,
                linewidth=linewidth
            )

            # Vertical transition
            ax.plot(
                [i + 1, i + 1],
                [numeric_values[i], numeric_values[i + 1]],
                color='C0',
                linewidth=1.8
            )

        # Draw the final sample
        final_color = 'red' if values[-1] not in ['0', 0, False, '1', 1, True] else 'C0'
        ax.scatter(
            len(values) - 1,
            numeric_values[-1],
            color=final_color,
            s=40,
            zorder=5
        )

        ax.set_ylabel(name)
        ax.set_ylim(-0.1, 1.1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_yticklabels(['0', 'X', '1'])
        ax.set_xlim(0, len(values) - 1)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel('Cycle')
    fig.suptitle(title)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f'Waveform saved to {output_path}')


def main():
    base_dir = os.path.dirname(__file__)
    netlist_path = os.path.join(base_dir, 'dff_only.txt')
    input_nodes, output_nodes, ckt_nodes = load_netlist(netlist_path)

    input_vectors = build_input_vectors(
        input_nodes,
        cycles=7,
        fixed_values={'d': ['1', '1', '0', '0', '1', '1', '1']},
    )

    outputs = simulate_cycles(input_nodes, input_vectors, ckt_nodes, output_nodes)
    print('Cycle-based simulation results:')
    for i, out in enumerate(outputs):
        print(f'cycle {i}: d={input_vectors[i][0]} clk={input_vectors[i][1]} rst={input_vectors[i][2]} q={out[0]}')

    signal_values = {
        'd': [value[0] for value in input_vectors],
        'clk': [value[1] for value in input_vectors],
        'rst': [value[2] for value in input_vectors],
        'q': [value[0] for value in outputs],
    }
    plot_waveforms(signal_values, title='D Flip-Flop Waveform')


if __name__ == '__main__':
    main()
