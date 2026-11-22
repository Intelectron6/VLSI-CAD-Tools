import sys
from pathlib import Path
from prompt_toolkit import prompt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import espresso

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

def run_interactive_minimizer():
    console.print(Panel.fit(
        "[bold cyan]ESPRESSO Combinational Logic Minimizer - Interactive TUI[/bold cyan]",
        border_style="cyan"
    ))

    # 1. Select Input Type
    console.print("\n[bold blue]Select Input Type:[/bold blue]")
    console.print("0: Boolean Expression (Symbolic, e.g. 'A & B | ~C')")
    console.print("1: Truth Table CSV File")
    input_choice = prompt("Enter the number: ")

    onset = None
    width = 0
    input_desc = ""

    if input_choice == '0':
        expr_str = prompt("Enter boolean expression (e.g. A & B | ~C): ")
        try:
            onset_expr, offset_expr, var_list = espresso.expression_to_cubes(expr_str)
            espresso.offset = offset_expr
            onset = onset_expr
            width = len(var_list)
            input_desc = f"expression: {expr_str}"
        except Exception as e:
            console.print(f"[red]Error parsing expression: {e}[/red]")
            return
    elif input_choice == '1':
        csv_files = list(Path('.').glob('*.csv'))
        csv_path = get_selection("Select a truth table CSV file", csv_files)
        if not csv_path:
            return
        try:
            onset, width = espresso.load_data(str(csv_path))
            input_desc = f"CSV: {csv_path.name}"
        except Exception as e:
            console.print(f"[red]Error loading CSV: {e}[/red]")
            return
    else:
        console.print("[red]Invalid selection[/red]")
        return

    # 2. Target Cost (tau)
    tau_str = prompt("Enter target cost tau (integer, e.g. 5): ")
    try:
        tau = int(tau_str)
    except ValueError:
        console.print("[red]Invalid tau value, defaulting to 5[/red]")
        tau = 5

    # 3. Netlist Generation
    gen_netlist = prompt("Generate SPICE-style netlist? (y/n): ").strip().lower()
    netlist_path = None
    if gen_netlist == 'y':
        netlist_filename = prompt("Enter output netlist filename (default: netlist.txt): ").strip()
        if not netlist_filename:
            netlist_filename = "netlist.txt"
        netlist_path = Path(netlist_filename)

    # 4. Run Minimization
    console.print(f"\n[bold]Running ESPRESSO minimization...[/bold]")
    try:
        sol_str, final_cost = espresso.run_minimization(onset, width, tau)
    except Exception as e:
        console.print(f"[red]Error during minimization: {e}[/red]")
        return

    # 5. Display Results
    table = Table(title="Minimization Result")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="green")

    table.add_row("Input Source", input_desc)
    table.add_row("Target Cost (tau)", str(tau))
    table.add_row("Minimized Expression", f"f = {sol_str}")
    table.add_row("Final Cost", str(final_cost))

    if netlist_path:
        try:
            netlist_text, net_inputs, net_outputs = espresso.generate_netlist(sol_str)
            with open(netlist_path, 'w', encoding='utf-8') as f:
                f.write(netlist_text)
            table.add_row("Generated Netlist", str(netlist_path))
            console.print(table)
            console.print(f"\n[bold blue]Netlist Content ({netlist_path}):[/bold blue]")
            console.print(netlist_text)
        except Exception as e:
            console.print(f"[red]Error generating netlist: {e}[/red]")
            console.print(table)
    else:
        console.print(table)

if __name__ == '__main__':
    run_interactive_minimizer()
