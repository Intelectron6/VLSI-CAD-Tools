import sys
from pathlib import Path
from prompt_toolkit import prompt
from rich.console import Console
from rich.table import Table

# Modules are in the same directory, no need for sys.path modification
import combinational_logic_simulator
import sequential_logic_simulator

console = Console()

def get_selection(title, items):
    if not items:
        return None
    console.print(f"\n[bold blue]{title}:[/bold blue]")
    for i, item in enumerate(items):
        console.print(f"{i}: {item.name}")
    
    choice = prompt("Enter the number: ")
    try:
        return items[int(choice)]
    except (ValueError, IndexError):
        console.print("[red]Invalid choice[/red]")
        return None

def run_simulation():
    # 1. Select Simulator
    console.print("[bold blue]Select Simulator:[/bold blue]")
    console.print("0: Combinational Logic Simulator")
    console.print("1: Sequential Logic Simulator")
    sim_choice = prompt("Enter the number: ")
    
    # 2. Select Netlist
    netlists = list(Path('Netlists').glob('*.txt'))
    netlist_path = get_selection("Select a netlist", netlists)
    if not netlist_path: return

    # 3. Select Stimulus
    stimuli = list(Path('Inputs').glob('*.csv'))
    stimulus_path = get_selection("Select a stimulus file", stimuli)
    if not stimulus_path: return
    
    # 4. Run
    console.print(f"\n[bold]Running simulation...[/bold]")
    output_dir = Path('Outputs')
    output_dir.mkdir(exist_ok=True)
    
    try:
        if sim_choice == '0':
            import circuit_modules
            input_nodes, output_nodes, ckt_nodes = combinational_logic_simulator.load_netlist(netlist_path)
            input_vectors = combinational_logic_simulator.load_input_vectors(stimulus_path, input_nodes)
            outputs = [tuple(circuit_modules.ckt(input_nodes, iv, ckt_nodes, output_nodes)) for iv in input_vectors]
            
            # Delegate saving
            report_path = output_dir / f"{netlist_path.stem}_results.csv"
            combinational_logic_simulator.write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs)
            
        elif sim_choice == '1':
            input_nodes, output_nodes, ckt_nodes = sequential_logic_simulator.load_netlist(netlist_path)
            input_vectors = sequential_logic_simulator.load_input_vectors(stimulus_path, input_nodes)
            outputs = sequential_logic_simulator.simulate_cycles(input_nodes, input_vectors, ckt_nodes, output_nodes)
            
            # Delegate saving
            report_path = output_dir / f"{netlist_path.stem}_results.csv"
            sequential_logic_simulator.write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs)
            
            # Delegate waveform
            signal_values = sequential_logic_simulator.build_signal_values(input_nodes, input_vectors, output_nodes, outputs)
            waveform_path = output_dir / f"{netlist_path.stem}_waveform.png"
            sequential_logic_simulator.plot_waveforms(signal_values, title=f"{netlist_path.stem} waveform", output_path=waveform_path)
        else:
            console.print("[red]Invalid simulator choice[/red]")
            return
        
        # Display results
        table = Table(title="Simulation Results")
        table.add_column("Step")
        for node in input_nodes: table.add_column(f"Input: {node}")
        for node in output_nodes: table.add_column(f"Output: {node}")
        for i, (iv, ov) in enumerate(zip(input_vectors, outputs)):
            table.add_row(*([str(i)] + list(iv) + list(ov)))
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error during simulation: {e}[/red]")

if __name__ == '__main__':
    run_simulation()
