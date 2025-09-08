import random

"""
TODO: make sure that the board is fully solvable
"""





from enum import Enum
from typing import Optional, Tuple, Union

class ClueType(Enum):
    EXPLICIT = 1   # "Cell (r,c) is number 3"
    GENERAL  = 2   # "Row 2 contains two stars"
    CONDITIONAL = 3  # "If X then Y"

class Clue:
    def __init__(
        self,
        clue_type: ClueType,
        position: Optional[Tuple[int,int]] = None,  # for explicit facts
        attribute: Optional[str] = None,           # "number" or "shape"
        value: Optional[Union[int,str]] = None,    # e.g. 3, "circle"
        scope: Optional[str] = None,               # "row" or "col" (for general)
        scope_index: Optional[int] = None,         # which row/col
        count: Optional[int] = None,               # e.g. "2 stars"
        condition: Optional['Clue'] = None,        # for conditionals
        consequence: Optional['Clue'] = None
    ) -> None:
        self.clue_type = clue_type
        self.position = position
        self.attribute = attribute
        self.value = value
        self.scope = scope
        self.scope_index = scope_index
        self.count = count
        self.condition = condition
        self.consequence = consequence

    def __repr__(self):
        if self.clue_type == ClueType.EXPLICIT:
            return f"Cell{self.position} has {self.attribute}={self.value}"
        elif self.clue_type == ClueType.GENERAL:
            return f"{self.scope.capitalize()} {self.scope_index} has {self.count} {self.value}s"
        elif self.clue_type == ClueType.CONDITIONAL:
            return f"If ({self.condition}), then ({self.consequence})"
        return "Unknown clue"
    
    def to_dict(self):
        """Convert clue to dictionary for JSON serialization."""
        result = {
            'clue_type': self.clue_type.value,  # Convert enum to int
            'position': self.position,
            'attribute': self.attribute,
            'value': self.value,
            'scope': self.scope,
            'scope_index': self.scope_index,
            'count': self.count
        }
        
        # Handle nested clues for conditional types
        if self.condition:
            result['condition'] = self.condition.to_dict()
        if self.consequence:
            result['consequence'] = self.consequence.to_dict()
            
        return result















shape_map = {
    'circle': '🟢',
    'square': '🟦',
    'star': '⭐',
    'heart': '❤️',
}



class Cell:
    def __init__(self, shape, number) -> None:
        self.shape = shape
        self.number = number

    def __str__(self) -> str:
        return f"{self.number} ({self.shape})"


class Board:
    def __init__(self, size: int = 3) -> None:
        self.size = size
        self.generate_random_board()
    


    def generate_random_board(self) -> None:
        shapes, numbers = list(shape_map.keys()), [1,2,3,4]

        # total unique cards = size × number of shapes
        perms = [Cell(shape, num) for num in numbers for shape in shapes]

        random.shuffle(perms)

        # only take size*size cells
        perms = perms[: self.size * self.size]

        # reshape into board rows
        self.board = [perms[i:i+self.size] for i in range(0, self.size * self.size, self.size)]








    def generate_all_clues(self, num_roots=2, vacuous_ratio=0.15) -> list[Clue]:
        """
        Generate clues using a tree-based approach:
        1. Start with explicit clues as roots
        2. Build dependency tree where each clue depends on previous ones
        3. Ensure every cell is reachable through logical deduction
        """
        clues = []
        covered = set()  # Cells that have at least one clue
        fully_covered = set()  # Cells that have both shape and number clues
        
        # 1) Create root explicit clues
        root_cells = random.sample(
            [(r, c) for r in range(self.size) for c in range(self.size)], num_roots
        )
        
        for pos in root_cells:
            # Generate one explicit clue per root cell
            clues.append(self.generate_order1_clue(pos))
            covered.add(pos)
        
        print(f"DEBUG: Created {len(root_cells)} root explicit clues")
        
        # 2) Build dependency tree level by level
        current_level = set(root_cells)
        level = 0
        
        while len(covered) < self.size * self.size and level < 10:  # Prevent infinite loops
            level += 1
            next_level = set()
            
            print(f"DEBUG: Building level {level}, current covered: {len(covered)}/{self.size * self.size}")
            
            # For each cell in current level, try to create clues that help deduce other cells
            for known_cell in list(current_level):
                # Find uncovered cells that could be deduced from this known cell
                uncovered = [(r, c) for r in range(self.size) for c in range(self.size) 
                           if (r, c) not in covered]
                
                if not uncovered:
                    break
                
                # Try to create different types of clues from this known cell
                clue_created = False
                
                # 2a) Try conditional clues (if-then relationships) - prioritize these
                if random.random() < 0.7 and len(uncovered) > 0:
                    target = random.choice(uncovered)
                    vacuous = (random.random() < vacuous_ratio)
                    try:
                        clue = self.generate_order3_clue_known(known_cell, target, vacuous=vacuous)
                        clues.append(clue)
                        covered.add(target)
                        next_level.add(target)
                        clue_created = True
                        print(f"DEBUG: Created conditional clue from {known_cell} to {target}")
                    except Exception as e:
                        print(f"DEBUG: Failed to create conditional clue: {e}")
                
                # 2b) Try general clues (row/col constraints) if no conditional clue was created
                if not clue_created and len(uncovered) > 0:
                    # Find cells in same row or column
                    same_row_col = [cell for cell in uncovered 
                                  if cell[0] == known_cell[0] or cell[1] == known_cell[1]]
                    
                    if same_row_col:
                        target = random.choice(same_row_col)
                        try:
                            clue = self.generate_order2_clue_known(known_cell, target)
                            clues.append(clue)
                            covered.add(target)
                            next_level.add(target)
                            clue_created = True
                            print(f"DEBUG: Created general clue from {known_cell} to {target}")
                        except Exception as e:
                            print(f"DEBUG: Failed to create general clue: {e}")
                
                # 2c) If still no clue created, try any conditional clue
                if not clue_created and len(uncovered) > 0:
                    target = random.choice(uncovered)
                    vacuous = (random.random() < vacuous_ratio)
                    try:
                        clue = self.generate_order3_clue_known(known_cell, target, vacuous=vacuous)
                        clues.append(clue)
                        covered.add(target)
                        next_level.add(target)
                        print(f"DEBUG: Created fallback conditional clue from {known_cell} to {target}")
                    except Exception as e:
                        print(f"DEBUG: Failed to create fallback clue: {e}")
                        # If all else fails, add a simple explicit clue for the target
                        clues.append(self.generate_order1_clue(target))
                        covered.add(target)
                        next_level.add(target)
                        print(f"DEBUG: Added explicit clue for {target} as fallback")
            
            current_level = next_level
            
            # If no progress was made, break to prevent infinite loops
            if not current_level:
                print(f"DEBUG: No progress made at level {level}, breaking")
                break
        
        # 3) Add cross-constraint clues to create interesting deduction chains
        # These clues help players deduce cells through multiple constraints
        print("DEBUG: Adding cross-constraint clues")
        
        # Add row/column constraint clues
        for i in range(self.size):
            # Row constraints
            row_cells = [(i, c) for c in range(self.size)]
            if len([cell for cell in row_cells if cell in covered]) >= 2:
                # Create a general clue about this row
                clue = self.generate_row_constraint_clue(i)
                if clue:
                    clues.append(clue)
                    print(f"DEBUG: Added row constraint for row {i}")
            
            # Column constraints
            col_cells = [(r, i) for r in range(self.size)]
            if len([cell for cell in col_cells if cell in covered]) >= 2:
                # Create a general clue about this column
                clue = self.generate_col_constraint_clue(i)
                if clue:
                    clues.append(clue)
                    print(f"DEBUG: Added column constraint for column {i}")
        
        # 3b) Add number-based constraint clues (e.g., "Row 0 has numbers 1,2,3")
        for i in range(self.size):
            # Row number constraints
            clue = self.generate_row_number_constraint_clue(i)
            if clue:
                clues.append(clue)
                print(f"DEBUG: Added row number constraint for row {i}")
            
            # Column number constraints
            clue = self.generate_col_number_constraint_clue(i)
            if clue:
                clues.append(clue)
                print(f"DEBUG: Added column number constraint for column {i}")
        
        # 4) Ensure every cell has at least one clue
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) not in covered:
                    # Add a simple explicit clue for uncovered cells
                    clues.append(self.generate_order1_clue((r, c)))
                    print(f"DEBUG: Added explicit clue for uncovered cell ({r}, {c})")
        
        print(f"DEBUG: Generated {len(clues)} total clues")
        
        # Generate and print the dependency tree visualization
        self.print_dependency_tree(clues, root_cells)
        
        # Create graphical visualizations if requested
        try:
            from clue_visualizer import visualize_clue_tree
            print("\nCreating graphical visualizations...")
            visualize_clue_tree(self, clues, root_cells, 
                              create_static=True, create_interactive=True)
        except ImportError:
            print("Note: Install networkx, matplotlib, and pyvis for graphical visualizations")
        except Exception as e:
            print(f"Visualization error: {e}")
        
        return clues
    
    def print_dependency_tree(self, clues: list[Clue], root_cells: list[tuple]):
        """Print a visual representation of the clue dependency tree."""
        print("\n" + "="*60)
        print("CLUE DEPENDENCY TREE")
        print("="*60)
        
        # Build dependency graph
        dependencies = {}  # cell -> list of cells that depend on it
        clue_map = {}      # cell -> list of clues about that cell
        
        for i, clue in enumerate(clues):
            if clue.clue_type.value == 1:  # EXPLICIT
                cell = clue.position
                if cell not in clue_map:
                    clue_map[cell] = []
                clue_map[cell].append((i, clue))
                
            elif clue.clue_type.value == 3:  # CONDITIONAL
                condition_cell = clue.condition.position
                consequence_cell = clue.consequence.position
                
                if condition_cell not in dependencies:
                    dependencies[condition_cell] = []
                dependencies[condition_cell].append(consequence_cell)
                
                if consequence_cell not in clue_map:
                    clue_map[consequence_cell] = []
                clue_map[consequence_cell].append((i, clue))
        
        # Print tree starting from roots
        visited = set()
        
        def print_node(cell, level=0, prefix=""):
            if cell in visited:
                return
            visited.add(cell)
            
            indent = "  " * level
            cell_display = f"({cell[0]},{cell[1]})"
            
            # Print this cell's clues
            if cell in clue_map:
                for clue_idx, clue in clue_map[cell]:
                    clue_desc = self.clue_to_string(clue)
                    print(f"{indent}{prefix}├─ {cell_display}: {clue_desc}")
                    prefix = "│  " if level > 0 else "   "
            
            # Print dependent cells
            if cell in dependencies:
                for i, dep_cell in enumerate(dependencies[cell]):
                    is_last = (i == len(dependencies[cell]) - 1)
                    new_prefix = "└─ " if is_last else "├─ "
                    print_node(dep_cell, level + 1, new_prefix)
        
        # Start from root cells
        print("ROOT NODES (Explicit Clues):")
        for root_cell in root_cells:
            print_node(root_cell)
        
        # Print any cells not reached by the tree (shouldn't happen in good generation)
        unreached = set()
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) not in visited and (r, c) in clue_map:
                    unreached.add((r, c))
        
        if unreached:
            print("\nUNREACHED CELLS (Generation Issue):")
            for cell in unreached:
                print_node(cell)
        
        # Print cross-constraint clues separately
        print("\nCROSS-CONSTRAINT CLUES:")
        for i, clue in enumerate(clues):
            if clue.clue_type.value == 2:  # GENERAL
                clue_desc = self.clue_to_string(clue)
                print(f"  • {clue_desc}")
        
        print("="*60)
    
    def clue_to_string(self, clue: Clue) -> str:
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
    
    def generate_row_constraint_clue(self, row: int) -> Optional[Clue]:
        """Generate a general clue about a row (e.g., 'Row 0 has 2 stars')."""
        row_cells = [self.board[row][c] for c in range(self.size)]
        
        # Count shapes in this row
        shape_counts = {}
        for cell in row_cells:
            shape_counts[cell.shape] = shape_counts.get(cell.shape, 0) + 1
        
        # Find a shape that appears more than once
        for shape, count in shape_counts.items():
            if count > 1:
                return Clue(ClueType.GENERAL, scope="row", scope_index=row, 
                           count=count, value=shape)
        
        return None
    
    def generate_col_constraint_clue(self, col: int) -> Optional[Clue]:
        """Generate a general clue about a column (e.g., 'Column 0 has 3 hearts')."""
        col_cells = [self.board[r][col] for r in range(self.size)]
        
        # Count shapes in this column
        shape_counts = {}
        for cell in col_cells:
            shape_counts[cell.shape] = shape_counts.get(cell.shape, 0) + 1
        
        # Find a shape that appears more than once
        for shape, count in shape_counts.items():
            if count > 1:
                return Clue(ClueType.GENERAL, scope="col", scope_index=col, 
                           count=count, value=shape)
        
        return None
    
    def generate_row_number_constraint_clue(self, row: int) -> Optional[Clue]:
        """Generate a general clue about numbers in a row (e.g., 'Row 0 has numbers 1,2,3')."""
        row_cells = [self.board[row][c] for c in range(self.size)]
        
        # Count numbers in this row
        number_counts = {}
        for cell in row_cells:
            number_counts[cell.number] = number_counts.get(cell.number, 0) + 1
        
        # Find a number that appears more than once
        for number, count in number_counts.items():
            if count > 1:
                return Clue(ClueType.GENERAL, scope="row", scope_index=row, 
                           count=count, value=number)
        
        return None
    
    def generate_col_number_constraint_clue(self, col: int) -> Optional[Clue]:
        """Generate a general clue about numbers in a column (e.g., 'Column 0 has numbers 1,2,3')."""
        col_cells = [self.board[r][col] for r in range(self.size)]
        
        # Count numbers in this column
        number_counts = {}
        for cell in col_cells:
            number_counts[cell.number] = number_counts.get(cell.number, 0) + 1
        
        # Find a number that appears more than once
        for number, count in number_counts.items():
            if count > 1:
                return Clue(ClueType.GENERAL, scope="col", scope_index=col, 
                           count=count, value=number)
        
        return None






    def generate_order1_clue(self, position, attribute=None) -> Clue:
        r, c = position
        cell = self.board[r][c]
        if attribute is None:
            attribute = random.choice(["number", "shape"])
        
        if attribute == "number":
            return Clue(ClueType.EXPLICIT, position=position, attribute="number", value=cell.number)
        else:
            return Clue(ClueType.EXPLICIT, position=position, attribute="shape", value=cell.shape)














    def generate_order2_clue_random(self, position) -> Clue:
        r, c = position
        use_row = random.choice([True, False])
        if use_row:
            scope, scope_index = "row", r
            items = self.board[r]
        else:
            scope, scope_index = "col", c
            items = [self.board[i][c] for i in range(self.size)]

        # pick a random cell from the scope and build a count clue
        chosen = random.choice(items)
        count = sum(1 for x in items if x.shape == chosen.shape)
        return Clue(
            ClueType.GENERAL,
            scope=scope,
            scope_index=scope_index,
            count=count,
            value=chosen.shape
        )
    






    def generate_order2_clue_known(self, known: tuple[int,int], target: tuple[int,int]) -> Clue:
        r_known, c_known = known
        r_target, c_target = target

        # if they share a row, build a row clue
        if r_known == r_target:
            scope, scope_index = "row", r_known
            items = self.board[r_known]
            chosen_shape = self.board[r_known][c_target].shape
            count = sum(1 for cell in items if cell.shape == chosen_shape)

        # else if they share a column, build a column clue
        elif c_known == c_target:
            scope, scope_index = "col", c_known
            items = [self.board[r][c_known] for r in range(self.size)]
            chosen_shape = self.board[r_target][c_target].shape
            count = sum(1 for cell in items if cell.shape == chosen_shape)

        else:
            raise ValueError(
                f"Order 2 clue requires known and target to share row or column. "
                f"Got known={known}, target={target}"
            )

        return Clue(
            ClueType.GENERAL,
            scope=scope,
            scope_index=scope_index,
            count=count,
            value=chosen_shape
        )













    def generate_order3_clue_random(self, position, vacuous: bool = False) -> Clue:
        r, c = position

        r2, c2 = r, c
        while (r2, c2) == (r, c):
            r2, c2 = random.randint(0, self.size-1), random.randint(0, self.size-1)

        cell1, cell2 = self.board[r][c], self.board[r2][c2]

        if vacuous:
            # condition that is false for cell2
            cond_attr = random.choice(["number", "shape"])
            cond_value = random.choice([1,2,3,4]) if cond_attr == "number" else random.choice(["circle","square","star","heart"])
            while getattr(cell2, cond_attr) == cond_value:
                cond_value = random.choice([1,2,3,4]) if cond_attr == "number" else random.choice(["circle","square","star","heart"])
            condition = Clue(ClueType.EXPLICIT, position=(r2,c2), attribute=cond_attr, value=cond_value)
            
            #gnerate consequence that is false for cell1
            cons_attr = random.choice(["number", "shape"])
            cons_value = random.choice([1,2,3,4]) if cons_attr == "number" else random.choice(["circle","square","star","heart"])
            while getattr(cell1, cons_attr) == cons_value:
                cons_value = random.choice([1,2,3,4]) if cons_attr == "number" else random.choice(["circle","square","star","heart"])
            consequence = Clue(ClueType.EXPLICIT, position=(r,c), attribute=cons_attr, value=cons_value)

        else:
            # normal clue both sides are true
            cond_attr = random.choice(["number", "shape"])
            cond_value = getattr(cell2, cond_attr)
            condition = Clue(ClueType.EXPLICIT, position=(r2,c2), attribute=cond_attr, value=cond_value)

            cons_attr = random.choice(["number", "shape"])
            cons_value = getattr(cell1, cons_attr)
            consequence = Clue(ClueType.EXPLICIT, position=(r,c), attribute=cons_attr, value=cons_value)

        return Clue(ClueType.CONDITIONAL, condition=condition, consequence=consequence)











    def generate_order3_clue_known(self, known: tuple[int,int], target: tuple[int,int], vacuous: bool = False) -> Clue:
        r_known, c_known = known
        r_target, c_target = target

        cell_known = self.board[r_known][c_known]
        cell_target = self.board[r_target][c_target]

        if vacuous:
            # false condition, false consequence
            cond_attr = random.choice(["number", "shape"])
            cond_value = random.choice([1,2,3,4]) if cond_attr == "number" else random.choice(["circle","square","star","heart"])
            while getattr(cell_known, cond_attr) == cond_value:
                cond_value = random.choice([1,2,3,4]) if cond_attr == "number" else random.choice(["circle","square","star","heart"])
            condition = Clue(ClueType.EXPLICIT, position=known, attribute=cond_attr, value=cond_value)

            cons_attr = random.choice(["number", "shape"])
            cons_value = random.choice([1,2,3,4]) if cons_attr == "number" else random.choice(["circle","square","star","heart"])
            while getattr(cell_target, cons_attr) == cons_value:
                cons_value = random.choice([1,2,3,4]) if cons_attr == "number" else random.choice(["circle","square","star","heart"])
            consequence = Clue(ClueType.EXPLICIT, position=target, attribute=cons_attr, value=cons_value)

        else:
            # true condition, true consequence
            cond_attr = random.choice(["number", "shape"])
            cond_value = getattr(cell_known, cond_attr)
            condition = Clue(ClueType.EXPLICIT, position=known, attribute=cond_attr, value=cond_value)

            cons_attr = random.choice(["number", "shape"])
            cons_value = getattr(cell_target, cons_attr)
            consequence = Clue(ClueType.EXPLICIT, position=target, attribute=cons_attr, value=cons_value)

        return Clue(ClueType.CONDITIONAL, condition=condition, consequence=consequence)












if __name__ == "__main__":
    b = Board()


