#!/usr/bin/env python3
"""
Clue dependency tree visualizer using NetworkX and Pyvis.
Creates both static and interactive visualizations of the clue dependency tree.
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pyvis.network import Network
import random
from typing import List, Dict, Tuple, Set
from game import Board, Clue, ClueType

class ClueTreeVisualizer:
    def __init__(self, board: Board, clues: List[Clue], root_cells: List[Tuple[int, int]]):
        self.board = board
        self.clues = clues
        self.root_cells = root_cells
        self.G = nx.DiGraph()
        self.clue_map = {}  # cell -> list of clues about that cell
        self.dependencies = {}  # cell -> list of cells that depend on it
        
        self._build_graph()
    
    def _build_graph(self):
        """Build the NetworkX graph from clues."""
        # Add nodes for all cells
        for r in range(self.board.size):
            for c in range(self.board.size):
                cell = (r, c)
                self.G.add_node(cell, pos=(c, -r))  # Invert y for proper display
                
                # Get actual cell data
                actual_cell = self.board.board[r][c]
                self.G.nodes[cell]['shape'] = actual_cell.shape
                self.G.nodes[cell]['number'] = actual_cell.number
                self.G.nodes[cell]['is_root'] = cell in self.root_cells
        
        # Process clues to build edges and clue mapping
        for i, clue in enumerate(self.clues):
            if clue.clue_type.value == 1:  # EXPLICIT
                cell = clue.position
                if cell not in self.clue_map:
                    self.clue_map[cell] = []
                self.clue_map[cell].append((i, clue))
                
            elif clue.clue_type.value == 3:  # CONDITIONAL
                condition_cell = clue.condition.position
                consequence_cell = clue.consequence.position
                
                # Add edge from condition to consequence
                self.G.add_edge(condition_cell, consequence_cell, 
                              clue_type="conditional", clue_idx=i)
                
                if condition_cell not in self.dependencies:
                    self.dependencies[condition_cell] = []
                self.dependencies[condition_cell].append(consequence_cell)
                
                if consequence_cell not in self.clue_map:
                    self.clue_map[consequence_cell] = []
                self.clue_map[consequence_cell].append((i, clue))
    
    def create_static_visualization(self, filename: str = "clue_tree.png"):
        """Create a static matplotlib visualization."""
        plt.figure(figsize=(12, 10))
        
        # Define colors for different node types
        node_colors = []
        node_sizes = []
        
        for node in self.G.nodes():
            if self.G.nodes[node]['is_root']:
                node_colors.append('#ff6b6b')  # Red for roots
                node_sizes.append(1000)
            else:
                node_colors.append('#4ecdc4')  # Teal for derived nodes
                node_sizes.append(600)
        
        # Define edge colors
        edge_colors = []
        for edge in self.G.edges():
            edge_colors.append('#95a5a6')  # Gray for edges
        
        # Draw the graph
        pos = nx.spring_layout(self.G, k=3, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.G, pos, 
                              node_color=node_colors, 
                              node_size=node_sizes,
                              alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(self.G, pos, 
                              edge_color=edge_colors,
                              arrows=True, 
                              arrowsize=20,
                              arrowstyle='->',
                              alpha=0.6)
        
        # Draw labels
        labels = {}
        for node in self.G.nodes():
            cell_data = self.G.nodes[node]
            labels[node] = f"{node}\n{cell_data['number']}({cell_data['shape'][0]})"
        
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, font_weight='bold')
        
        # Add title and legend
        plt.title("Clue Dependency Tree\nRed = Root Nodes, Teal = Derived Nodes", 
                 fontsize=16, fontweight='bold')
        
        # Create legend
        root_patch = mpatches.Patch(color='#ff6b6b', label='Root Nodes (Explicit Clues)')
        derived_patch = mpatches.Patch(color='#4ecdc4', label='Derived Nodes (Conditional Clues)')
        plt.legend(handles=[root_patch, derived_patch], loc='upper right')
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Static visualization saved as {filename}")
    
    def create_interactive_visualization(self, filename: str = "clue_tree.html"):
        """Create an interactive Pyvis visualization."""
        net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")
        net.barnes_hut()
        
        # Add nodes
        for node in self.G.nodes():
            cell_data = self.G.nodes[node]
            is_root = cell_data['is_root']
            
            # Node properties
            color = "#ff6b6b" if is_root else "#4ecdc4"
            size = 30 if is_root else 20
            
            # Create tooltip with cell info and clues
            tooltip = f"Cell {node}<br>"
            tooltip += f"Number: {cell_data['number']}<br>"
            tooltip += f"Shape: {cell_data['shape']}<br>"
            
            if node in self.clue_map:
                tooltip += "<br>Clues:<br>"
                for clue_idx, clue in self.clue_map[node]:
                    clue_desc = self._clue_to_string(clue)
                    tooltip += f"• {clue_desc}<br>"
            
            net.add_node(str(node), 
                        label=f"{node}\n{cell_data['number']}({cell_data['shape'][0]})",
                        color=color,
                        size=size,
                        title=tooltip)
        
        # Add edges
        for edge in self.G.edges():
            source, target = edge
            edge_data = self.G.edges[edge]
            
            # Get clue description for edge tooltip
            clue_idx = edge_data.get('clue_idx', -1)
            if clue_idx >= 0 and clue_idx < len(self.clues):
                clue = self.clues[clue_idx]
                clue_desc = self._clue_to_string(clue)
            else:
                clue_desc = "Dependency"
            
            net.add_edge(str(source), str(target), 
                        title=clue_desc,
                        color="#95a5a6")
        
        # Add physics and options
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200
          }
        }
        """)
        
        net.save_graph(filename)
        print(f"Interactive visualization saved as {filename}")
        print(f"Open {filename} in your browser to explore the tree interactively!")
    
    def _clue_to_string(self, clue: Clue) -> str:
        """Convert a clue to a readable string."""
        if clue.clue_type.value == 1:  # EXPLICIT
            return f"Cell {clue.position} has {clue.attribute} = {clue.value}"
        elif clue.clue_type.value == 2:  # GENERAL
            return f"{clue.scope.capitalize()} {clue.scope_index} has {clue.count} {clue.value}s"
        elif clue.clue_type.value == 3:  # CONDITIONAL
            cond = f"Cell {clue.condition.position} has {clue.condition.attribute} = {clue.condition.value}"
            cons = f"Cell {clue.consequence.position} has {clue.consequence.attribute} = {clue.consequence.value}"
            return f"If {cond}, then {cons}"
        return "Unknown clue"
    
    def print_tree_analysis(self):
        """Print analysis of the dependency tree."""
        print("\n" + "="*60)
        print("TREE ANALYSIS")
        print("="*60)
        
        # Basic stats
        print(f"Total nodes: {self.G.number_of_nodes()}")
        print(f"Total edges: {self.G.number_of_edges()}")
        print(f"Root nodes: {len(self.root_cells)}")
        
        # Tree depth analysis
        depths = {}
        for root in self.root_cells:
            depths[root] = 0
            self._calculate_depths(root, depths, 0)
        
        max_depth = max(depths.values()) if depths else 0
        print(f"Maximum tree depth: {max_depth}")
        
        # Node degrees
        in_degrees = dict(self.G.in_degree())
        out_degrees = dict(self.G.out_degree())
        
        print(f"Nodes with no dependencies: {sum(1 for d in in_degrees.values() if d == 0)}")
        print(f"Leaf nodes (no children): {sum(1 for d in out_degrees.values() if d == 0)}")
        
        # Clue type distribution
        clue_types = {"explicit": 0, "conditional": 0, "general": 0}
        for clue in self.clues:
            if clue.clue_type.value == 1:
                clue_types["explicit"] += 1
            elif clue.clue_type.value == 2:
                clue_types["general"] += 1
            elif clue.clue_type.value == 3:
                clue_types["conditional"] += 1
        
        print(f"\nClue distribution:")
        for clue_type, count in clue_types.items():
            print(f"  {clue_type.capitalize()}: {count}")
        
        print("="*60)
    
    def _calculate_depths(self, node, depths, current_depth):
        """Calculate depths of all nodes reachable from a given node."""
        if node in self.dependencies:
            for child in self.dependencies[node]:
                if child not in depths or depths[child] < current_depth + 1:
                    depths[child] = current_depth + 1
                    self._calculate_depths(child, depths, current_depth + 1)

def visualize_clue_tree(board: Board, clues: List[Clue], root_cells: List[Tuple[int, int]], 
                       create_static: bool = True, create_interactive: bool = True):
    """Main function to create visualizations of the clue dependency tree."""
    visualizer = ClueTreeVisualizer(board, clues, root_cells)
    
    # Print analysis
    visualizer.print_tree_analysis()
    
    # Create visualizations
    if create_static:
        visualizer.create_static_visualization()
    
    if create_interactive:
        visualizer.create_interactive_visualization()
    
    return visualizer

if __name__ == "__main__":
    # Test the visualizer
    print("Creating test board and generating clues...")
    board = Board(size=3)
    clues = board.generate_all_clues()
    
    # Extract root cells from the generation process
    # (This would normally be passed from the generation function)
    root_cells = [(0, 0), (1, 1)]  # Example root cells
    
    print("Creating visualizations...")
    visualizer = visualize_clue_tree(board, clues, root_cells)
