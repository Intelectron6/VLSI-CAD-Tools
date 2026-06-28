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
Example: AND 1 2 5

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

The name of the netlist to be simulated must be changed in the code. No other change is necessary.
The tool will ask to provide input values and will display output values. 
Enter 0 or 1 only for accurate results, any other entry will be treated as X.
