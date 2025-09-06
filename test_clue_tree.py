#!/usr/bin/env python3
"""
Test script to demonstrate the clue dependency tree visualization.
Run this to see how the tree-based clue generation works.
"""

from game import Board

def main():
    print("Generating a 3x3 board with tree-based clues...")
    print("=" * 60)
    
    # Create a board and generate clues
    board = Board(size=3)
    
    print("\nACTUAL BOARD:")
    print("-" * 20)
    for r in range(board.size):
        row_str = ""
        for c in range(board.size):
            cell = board.board[r][c]
            row_str += f"{cell.number}({cell.shape[0]}) "  # Show number and first letter of shape
        print(f"Row {r}: {row_str}")
    
    print("\nGenerating clues with dependency tree...")
    clues = board.generate_all_clues()
    
    print(f"\nTotal clues generated: {len(clues)}")
    
    # Show all clues in order
    print("\nALL CLUES (in generation order):")
    print("-" * 40)
    for i, clue in enumerate(clues):
        clue_desc = board.clue_to_string(clue)
        print(f"{i+1:2d}. {clue_desc}")

if __name__ == "__main__":
    main()
