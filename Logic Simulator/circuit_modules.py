# Global state storage for flip-flops to maintain state across simulation cycles
_flipflop_state = {}

def reset_flipflop_states():
    global _flipflop_state
    _flipflop_state = {}

def d_flipflop(ff_id, d, clk, rst):
    if ff_id not in _flipflop_state:
        _flipflop_state[ff_id] = {'q': 'x', 'prev_clk': '0', 'prev_d': '0'}
    state = _flipflop_state[ff_id]

    if rst == '1':
        state['q'] = '0'
        state['prev_clk'] = clk
        state['prev_d'] = '0'
        return '0'
    
    if rst not in ['0', '1', 'x'] or clk not in ['0', '1', 'x'] or d not in ['0', '1', 'x']:
        return 'x'

    prev_clk = state['prev_clk']
    if prev_clk == '0' and clk == '1' and rst == '0':
        if state['prev_d'] in ['0', '1']:
            state['q'] = state['prev_d']
        else:
            state['q'] = 'x'

    state['prev_clk'] = clk
    state['prev_d'] = d

    return state['q']

def not_gate(a):
    if (a == '0'):
        return '1'
    elif (a == '1'):
        return '0'
    elif (a == 'x'):
        return 'x'
    else:
        return 'x'

def buffer(a):
    return a

def and_gate(a, b):
    if (a == '1' and b == '1'):
        return '1'
    elif (a == '0'):
        return '0'
    elif (b == '0'):
        return '0'
    else:
        return 'x'

def or_gate(a, b):
    if (a == '0' and b == '0'):
        return '0'
    elif (a == '1'):
        return '1'
    elif (b == '1'):
        return '1'
    else:
        return 'x'

def xor_gate(a, b):
    if (a == '0' and b == '0'):
        return '0'
    elif (a == '1' and b == '1'):
        return '0'
    elif (a == '1' and b == '0'):
        return '1'
    elif (a == '0' and b == '1'):
        return '1'
    else:
        return 'x'

def nand_gate(a, b):
    if (a == '1' and b == '1'):
        return '0'
    elif (a == '0'):
        return '1'
    elif (b == '0'):
        return '1'
    else:
        return 'x'

def nor_gate(a, b):
    if (a == '0' and b == '0'):
        return '1'
    elif (a == '1'):
        return '0'
    elif (b == '1'):
        return '0'
    else:
        return 'x'

def xnor_gate(a, b):
    if (a == '0' and b == '0'):
        return '1'
    elif (a == '1' and b == '1'):
        return '1'
    elif (a == '1' and b == '0'):
        return '0'
    elif (a == '0' and b == '1'):
        return '0'
    else:
        return 'x'

def mux_2x1(a, b, s):
    if (s == '1'):
        return b
    elif (s == '0'):
        return a
    else:
        return 'x'

def ckt (input_nodes, input_vector, ckt_nodes, output_nodes):
	node_vals = {}
	for i in range(len(input_vector)):
		node_vals[input_nodes[i]] = input_vector[i]
	
	for i in ckt_nodes:
		if i[0] == 'NOT':
			inp = node_vals[i[1]]
			outp = not_gate(inp)
			node_vals[i[2]] = outp

		if i[0] == 'BUFF':
			inp = node_vals[i[1]]
			outp = buffer(inp)
			node_vals[i[2]] = outp
		
		if i[0] == 'AND':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = and_gate(inp1, inp2)
			node_vals[i[3]] = outp	
	
		if i[0] == 'OR':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = or_gate(inp1, inp2)
			node_vals[i[3]] = outp
			
		if i[0] == 'NAND':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = nand_gate(inp1, inp2)
			node_vals[i[3]] = outp	
	
		if i[0] == 'NOR':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = nor_gate(inp1, inp2)
			node_vals[i[3]] = outp
		
		if i[0] == 'XOR':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = xor_gate(inp1, inp2)
			node_vals[i[3]] = outp	
	
		if i[0] == 'XNOR':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			outp = xnor_gate(inp1, inp2)
			node_vals[i[3]] = outp
			
		if i[0] == 'MUX2x1':
			inp1 = node_vals[i[1]]
			inp2 = node_vals[i[2]]
			sel0 = node_vals[i[3]]
			outp = mux_2x1(inp1, inp2, sel0)
			node_vals[i[4]] = outp	
	
		if i[0] == 'DFF':
			d_inp = node_vals[i[1]]
			clk_inp = node_vals[i[2]]
			rst_inp = node_vals[i[3]]
			ff_id = i[4]
			outp = d_flipflop(ff_id, d_inp, clk_inp, rst_inp)
			node_vals[i[4]] = outp	
	
	outputs = ''
	for i in output_nodes:
		outputs = outputs + node_vals[i]

	return outputs
        
