import random

"""
TODO: create an object for a clue
TODO: make sure that the board is fully solvable
"""


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
    def __init__(self) -> None:
        self.generate_random_board()
    

    def generate_random_board(self) -> None:

        shapes, numbers = shape_map.values(), [1,2,3,4]

        perms = [Cell(shapes[j],numbers[i]) for i in range(len(numbers)) for j in range(len(shapes))]


        perms = random.sample(perms, 9)
        
        self.board = [
            perms[:3],
            perms[3:6],
            perms[6:9],
        ]

        
    def generate_all_clues(self) -> None:
        """
        1. generate 3 explicit clues (first order)
        2. generate 3 generalized clues (second order)
        3. generate 3 deductive if/then clues (third order)
        """

    def generate_order1_clue(self, position) -> str:
        """
        return a clue that explicitly reveals either the shape or the number of one position
        """

    def generate_order2_clue(self, position) -> str:
        """
        for either the row or column (randomly chosen) of that position, reveal something more general than an explicit (order 1) clue but
        more specific than a deductive (order 3) clue. 
        
        we need to do this systematically, perhaps choosing randomly between a couple of 
        different hint types. (like reveal oddness/evenness of numbers, explicitly state a number or shape in that row/col, etc)
        """

    def generate_order3_clue(self, position) -> str:
        """
        1. generate 3 clues like:
            - pick a true statement from the board that is at a different position
            - make an if then statement saying if the above expression is true, then (another true expression revealing this position)

            example:
                position (0,0) is passed in as an arg and make a true expression (e.g. the shape is square)

                pick another position at random (0,2) (and )

                for each position:
                    - make a random true explicit expression (e.g. the shape is square, or the number is 5)

                create an if/then statement saying if (expression 1) then (expression 2)
        """
            




if __name__ == "__main__":
    b = Board()


