"""
Usage: python3 automata.py input_file (string: defaults to a prompt) (output_file: defaults to "graph.gif")

input should be a csv file in the form:

accept states...
rules
....

accept state 1, accept state 2, ...
from, input, pop, push, to
from, input, pop, push, to
from, input, pop, push, to
...

"""


import networkx as nx
import os
import pydot
from networkx.drawing.nx_agraph import to_agraph

import matplotlib
matplotlib.use("PDF")
from matplotlib import pyplot as plt

import csv
from sys import argv


EPS = "ε"

class State:
    """ A class for representing states within automata"""
    def __init__(self, name):
        self.name = name
        # (input string, top of stack) => [[what to push, next state], ...]
        self.connections = {}
        self.accept = False

    def connect(self, inpt, stack, push, state):
        """ Connects this state to another when the input and stack meet the desired critera"""
        args = (inpt, stack)
        self.connections.setdefault(args, [])
        self.connections[args].append([push, state])
        
    def next(self, inpt, stack):
        """ Returns the possible next states given an input and stack"""
        args = list(set([(inpt, stack[0]), (inpt, ""), ("", "")]))
        result = [{"arg": arg, "result": connection} for arg in args  if arg in self.connections for connection in self.connections[arg]]
        return result
class PushdownAutomata:
    """ A class for representing a Push Down Automata """
    def __init__(self, version = "_0"):
        self.stack = ["$"]
        self.states = {}
        self.start = None
        self.curState = None
        self.string = ""
        self.accept = []
        self.version = version
        
    def __copy__(self):
        m = PushdownAutomata()
        m.stack = self.stack.copy()
        m.states = self.states
        m.start = self.start
        m.curState = self.curState
        m.string = self.string
        m.accept = self.accept
        return m

    def __eq__(self, other):
        """ Returns if two machines are equivalent, used to avoid rechecking the same route. """
        return (self.stack == other.stack) and (self.string == other.string) and (self.curState == other.curState)
    def new_state(self, name):
        """ Creates a new state with the given name """
        state = State(name)
        self.states[name] = state
        return state
    
    def get_state(self, name):
        """ Return the state with a given name """
        return self.states[name]
        
    def fill(self, data):
        """ Given a list of tuples in the form (from, input, stack pop, stack push, to) populate the machine"""
        for state in data:
            fr, to = state[0], state[-1]
            if fr not in self.states:
                self.new_state(fr)
            if to not in self.states:
                self.new_state(to)
        for state in data:
            self.states[state[0]].connect(state[1], state[2], state[3], self.states[state[4]])
        self.start = self.states[data[0][0]]
        self.curState = self.start
    def set_start(self, start):
        """ Set the start node for the machine. """
        self.start = start
        
    def step(self):
        """ Given the machines current state and input, returns a list of machine/input/stack states that could result """
        print("Stepping:")
        print("Version: ", self.version)
        print("State: ", self.curState.name)
        print("Stack: ", self.stack)
        print("Input: Char:", self.string[0] if self.string else "", "| String:", self.string)
        inp = self.string[0] if self.string else ""
        next_states = self.curState.next(inp, self.stack)
        branches = []
        print("Next States:")
        i = 0
        child_v = 65
        for res in next_states:
            inpt, pop = res["arg"]
            push, state = res["result"]
            m = self.__copy__()
            # _0 -> _1a _1b _1c
            # _0a
            # _0b
            # _1
            m.version = (lambda k: "_".join(k[:-1] + [str(int(k[-1]) + 1)]))(self.version.split("_"))# + ("_" + str(i) if len(next_states) > 1 else "")
            if len(next_states) > 1:
                m.version += chr(child_v) + "_0"
                child_v += 1
                
            #(self.version + "_" + str(i)) if len(next_states) > 1 else (lambda k: "_".join(k[:-1] + [str(int(k[-1]) + 1)]))(self.version.split("_"))
            i += 1
            if pop:
                m.stack.pop(0)
            if push:
                m.stack.insert(0, push)
            m.curState = state
            if inpt:
                m.string = self.string[1::]
            print("Input:", inpt, "Pop:", pop if pop else EPS, "Push:", push if push else EPS, " ==> State:", m.curState.name, "Input:", m.string, "Stack:", m.stack)
            branches.append(m)
        return branches
    def get_label(self, f, t):
        """ Return the label for the connection from state f to state t  """
        return (f[0] if f[0] else EPS) + "," + (f[1] if f[1] else EPS) + "-->" +  (t[0] if t[0] else EPS)
    def snapshot(self, filename, initial=False):
        """ Saves a visual graph of the current machine as a png."""
        graph = nx.MultiDiGraph()
        graph.add_nodes_from([(m, {"height": 1, "width": 1, "color":
                                   "blue" if (self.curState.name == m and not initial) else
                                   "green" if m in self.accept else ""})
                              for m in self.states]
                             + [("start", {"height": 1, "width": 1, "color":"blue" if initial else ""}),
                                ("Version " + self.version + "\n State " + self.curState.name + "\n Stack " + "".join(self.stack) + "\n Input " + self.string, {"width": 4, "shape": "box"})])
        
        graph.add_edges_from([(m, c[1].name, {"length": 30, "label": self.get_label(n, c)})
                                   for m in self.states
                                   for n in self.states[m].connections
                                   for c in self.states[m].connections[n]] +
                                  [("start", self.start.name)])
        plt.rcParams["figure.autolayout"] = True

        pos = nx.planar_layout(graph)

        nx.draw_networkx(graph,
                         pos,
                         with_labels=True,
                         node_size=100,
                         linewidths=10,
                         arrowsize=20,
                         connectionstyle='arc3, rad = 0.5')
        #plt.savefig(filename + self.version + ".png")
        name = filename + self.version
        dotname = name + ".dot"

        nx.drawing.nx_pydot.write_dot(graph, dotname)#""graph.dot")
        os.system("dot -n -Tpng " + dotname + " > " + name + ".png")
        


class GraphicProgram:
    """ A class for building a PDA, running an input on it, and generating a gif of the result. """
    def __init__(self, machine="npda", data=None, accept=[], out_file="graph.gif"):
        self.machine = PushdownAutomata()
        self.machine.fill(data)
        self.machine.accept = accept
        self.out_file = out_file
        
        
    def run(self, inpt):
        """ Runs the input on the selected machine and generate a gif of each state of the execution process. """
        os.system("mkdir build")
        generation = 1
        self.machine.string = inpt
        seen_machines = []
        machines = [self.machine]
        new_machines = []
        divider = "".join(["="] * 20)
        while machines:
            print (divider, "GENERATION", generation, divider)
            for num, machine in enumerate(machines):
                machine.snapshot("build/graph", machine.version == "_0")
                print ("================ PushdownAutomata", num, "=================")
                if not machine.string and machine.curState.name in machine.accept:
                    return self.generate_gif(True, machine, inpt)
                new_machines += machine.step()
            # Organize results by shortest input first
            new_machines.sort(key = lambda k: len(k.string))

            # Store global machine "states" that have been seen (stack, input, state) 
            seen_machines += [m for m in machines if m not in seen_machines]
            # Remove machines from the next gen we've already seen
            machines = [m for m in new_machines if m not in seen_machines]
            new_machines = []
            generation += 1
        return self.generate_gif(False, machine, inpt)

    def generate_gif(self, recognized, machine, inpt):
        """ Generates the gif. """
        print("String" + ("" if recognized else " not") + " recognized:", inpt, machine.curState.name)
        print("Generating graph", self.out_file)
        os.system("convert -delay 100 " + "build/graph*.png " + self.out_file)
        os.system("rm -rf build")
        return recognized
        
        
def get_data_from_file(filename):
    """ Given a csv file, parses the data into the correct form. """
    accept = []
    data = []
    with open(filename, newline="") as f:
        reader = csv.reader(f, delimiter=",")
        first = True
        for row in reader:
            if first:
                first = False
                accept = row
            else:
                data.append(tuple([str(i) if i else "" for i in row]))
    return accept, data
def main():
    if len(argv) == 2:
        argv.append(input("Please input a string-->"))
    if len(argv) == 3:
        argv.append("graph.gif")
        
    input_file, string, out_file= argv[1::]
    accept, data = get_data_from_file(input_file)
    
    p = GraphicProgram(None, data, accept, out_file)
    p.run(string)

if __name__ == "__main__":
    main()
