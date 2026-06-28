This is a simple compiled code simulator capable of simulating combinational and sequential circuits.
A netlist (txt file) of a specific format is required. Some sample netlists have been provided.

The netlist can contain the following components-
* Inverter
* Buffer
* 2 input OR Gate
* 2 input AND Gate
* 2 input NOR Gate
* 2 input NAND Gate
* 2 input XOR Gate
* 2 input XNOR Gate
* 2x1 Multiplexer
* D Flip-Flop (DFF)

COMBINATIONAL COMPONENTS:
Gate format: GATETYPE input1 input2 output
Example: AND i1 i2 o1

SEQUENTIAL COMPONENTS:
D Flip-Flop format: DFF d clk rst q
  - d: Data input
  - clk: Clock signal
  - rst: Asynchronous reset (active high, rst=1 sets q=0)
  - q: Output

Example: DFF n1 clk reset q1

For sequential circuits, the simulator maintains flip-flop states across multiple simulation cycles.
Enter 0 or 1 for each cycle. Use multiple cycles to observe state transitions.
Use internal signal names for both intermediate nodes and flip-flop outputs.

INTERACTIVE INTERFACE:
To run simulations interactively, use the provided TUI script from the Logic Simulator directory:
  python3 run_sim.py

This interface allows you to:
- Select between Combinational and Sequential simulators.
- Choose a netlist from the /Netlists directory.
- Select a stimulus file from the /Inputs directory.
- View results in a table and have reports/waveforms saved automatically to the /Outputs directory.
