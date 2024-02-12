import numpy as np
from enum import Enum

# enum specifying the different constraints
class Constraint(Enum):
    CELL = 0
    ROW = 1
    COLUMN = 2
    BOX = 3

# represents a node in the "torodical" linked list
class Node:
    def __init__(self, value, constraint = None):
        self.value = value

        # pointers to the nodes to the left, right, up and down of the current node
        self.left = self.right = self.up = self.down = self
        
        self.constraint = constraint # the constraint that this node satisfies
    
# represents the column headers of the torodical linked list
class ConstraintNode(Node):
    def __init__(self, value):
        super().__init__(value, self)

        # the number of nodes that currently satisfy this constraint
        # used to find the constraint that has the least number of nodes satisfying it
        self.num_of_nodes = 0 
    
    # adds a new node to the linked list that satisfies this constraint
    # parameters is the row, column and value of this new node and 
    # the node at the start of the row that the node will be inserted at
    def append_node(self, rcv, initial_node = None):
        new_node = Node(rcv, self) 

        # -- attach this new node to the constraint in the linked list --
        last_added_node = self.down
        last_added_node.up = new_node
        
        self.down = new_node

        new_node.down = last_added_node
        new_node.up = self
        
        self.num_of_nodes += 1

        # -- attach this new node to its row in the linked list --
        if initial_node: # does the row exist?
            last_added_node = initial_node.left
            last_added_node.right = new_node

            initial_node.left = new_node

            new_node.left = last_added_node
            new_node.right = initial_node
        else:
            initial_node = new_node # if the row doesn't exist, then this new node becomes the node at the start of the row 
        
        return initial_node

    # temporarily remove the constraint from the linked list
    def cover(self):
        # -- remove the nodes that satisfy this constraint --
        cur_row = self.up # get the first node that satisfies this constraint
        while cur_row != self: # keep looping until the constraint node is reached again
            # -- remove the rows that contain a node which satisfies this constraint --
            cur_node = cur_row.right
            while cur_node != cur_row:
                # remove the node
                cur_node.up.down = cur_node.down
                cur_node.down.up = cur_node.up

                cur_node.constraint.num_of_nodes -= 1

                cur_node = cur_node.right # go to the next node in the row

            cur_row = cur_row.up # go to the next row

        # -- remove the constraint from the linked list --
        self.left.right = self.right
        self.right.left = self.left
    
    # re-add the constraint to the linked list
    def uncover(self): 
        # -- re-add each row that satisfied this constraint --
        cur_row = self.up # go to the first node that satisfies the constraint
        while cur_row != self: # keep looping through the rows until the constraint node is reached again
            cur_node = cur_row.right
            while cur_node != cur_row:
                # re-add the node
                cur_node.up.down = cur_node
                cur_node.down.up = cur_node

                cur_node.constraint.num_of_nodes += 1

                cur_node = cur_node.right # go to the next node in the row
                
            cur_row = cur_row.up # go to the next row
        
        # -- re-add the constraint node to the linked list --
        self.right.left = self
        self.left.right = self

# the root node is the node that is the top most left node
# its right/left pointer points to the first/last constraint node respectively
# its up/down pointers point to None
class RootNode(Node):
    def __init__(self):
        super().__init__("root") # the value of the RootNode is "root" and it satisfies no constraints

    # returns the constraint node that has the least number of nodes that satisfy it
    def get_min_constraint(self):
        cur_node = self.right # go to the first constraint node
        min_constraint = cur_node 

        while cur_node != self: # keep going to the constraint node to the right until we reach the root node again
            if cur_node.num_of_nodes < min_constraint.num_of_nodes:
                min_constraint = cur_node
            cur_node = cur_node.right # go to the next constraint node

        return min_constraint

class SudokuSolver:
    def __init__(self):
        self.root = RootNode()
        
        self.solvable = True # specifies if the sudoku is solvable
        self.solution = np.zeros((9, 9)) # initalise a 9x9 2d array with all zeros

        # -- initalise the torodical linked list --
        self.add_constraints()
        self.add_nodes()

    # calculates the box (3x3 grid) (0..8) that contains the cell for the specified row and column
    def calculate_box(self, row, column):
        return ((row // 3) * 3) + (column // 3)

    def start(self, sudoku):
        # -- cover the initial numbers (in the sudoku) in the linked list -- 
        for (row, column), value in np.ndenumerate(sudoku):
            if value == 0: # ignore all 0 values
                continue
            
            # cover all constraints that this row, column and value satisfy
            self.solvable = self.cover_constraints(row, column, value)
            if not self.solvable:
                break

            self.solution[row][column] = value

        if self.solvable:
            self.answer = None
            self.solve() # try to solve the sudoku
            
            if self.answer is None:
                self.solvable = False
            else:
                for (row, column, value) in self.answer:
                    self.solution[row][column] = value
            
        if not self.solvable:
            self.solution = np.array([[-1] * 9] * 9) # initalise a 9x9 array with all -1's

        return self.solution

    # adds to the constraint nodes to the linked list
    # it adds all the cell constraints then column then row then box
    def add_constraints(self):
        for column in range(9):
            for row in range(9):
                self.add_constraint((Constraint.CELL, row, column))

        for column in range(9):
            for value in range(1, 10):
                self.add_constraint((Constraint.COLUMN, column, value))

        for row in range(9):
            for value in range(1, 10):
                self.add_constraint((Constraint.ROW, row, value))

        for box in range(9):
            for value in range(1, 10):
                self.add_constraint((Constraint.BOX, box, value))

    # adds a constraint to the linked list
    def add_constraint(self, constraint):
        constraint_node = ConstraintNode(constraint)

        # -- attach the node to the linked list (left of the root node, right of the most recently added node) --
        last_added_constraint = self.root.left
        last_added_constraint.right = constraint_node

        constraint_node.right = self.root
        constraint_node.left = last_added_constraint

        self.root.left = constraint_node 

    # adds every combination of row, column and value to the linked list under their constraint
    def add_nodes(self):
        for row in range(9):
            for column in range(9):
                box = self.calculate_box(row, column)
                cell = ((row + 1) * 9) - (9 - column) # calculate the cell number 0..80

                for value in range(1, 10):
                    inital_node = None # node at the start of the current row
                    constraint = self.root.right
                    rcv = (row, column, value)

                    # c, r, b represents the distance between the column, row and block constraints respectively
                    c, r, b = (column * 9) + (value-1), (row * 9) + (value-1), (box * 9) + (value-1) 
                    for skip_amount in (cell, (81 - cell) + c, (81 - c) + r, (81 - r) + b):
                        # initally, the cell, row, column and box constraint are at a known distance apart
                        # therefore, i can use this distance to search for the constraint node i want
                        # by following the right pointer of each constraint node a fixed number of times until the node i want is reached
                        for _ in range(skip_amount):
                            constraint = constraint.right
                        
                        inital_node = constraint.append_node(rcv, inital_node)
    
    # cover the constraint nodes that this row, column and value combination satisfies 
    # returns a boolean representing if the sudoku is solvable
    def cover_constraints(self, row, column, value):
        constraint_node = self.root.right # go to the first constraint
        
        for constraint in [
            (Constraint.CELL, column, row), 
            (Constraint.COLUMN, column, value), 
            (Constraint.ROW, row, value), 
            (Constraint.BOX, self.calculate_box(row, column), value)
        ]:
            # keep going to the next constraint node until the desired constraint node is reached OR the root node is reached
            while constraint_node != self.root and constraint_node.value != constraint: 
                constraint_node = constraint_node.right

            # if the root node is reached it means that the constraint node doesn't exist
            # however, it should exist as this function is only called on the input sudoku 
            # therefore, each row, column and value combination should be valid
            if constraint_node == self.root: # sudoku is invalid / unsolvable
                return False

            constraint_node.cover() 
        
        return True

    # solution stores the (row, column, value) of the nodes currently in the solution
    def solve(self, solutions = []):       
        if self.root.right == self.root: # a solution is found if there are no more constraints to satisfy 
            self.answer = solutions[:]
            return 
        elif self.answer is not None: # stop backtracking if an answer is found
            return 
        
        # -- temporarily cover the constraint with the least number of nodes that satisfy it --
        constraint_node = self.root.get_min_constraint()
        constraint_node.cover()
        
        # -- add each node that satisfies this constraint to the solution and find which one leads to the correct answer --
        cur_node = constraint_node.down # get the first node connected to the constraint node
        while cur_node != constraint_node: # loop through all the nodes that satisfy this constraint
            # -- also cover every node in every row that contains a node that satisfies the current constraint --
            row_node = cur_node.right # go to the first node in the row
            while row_node != cur_node: # loop through all the nodes in the row
                row_node.constraint.cover()
                row_node = row_node.right # go to the next node in the row
            
            solutions.append(cur_node.value) # add this covered node to the solution
            
            self.solve(solutions) # see if this node being in the solution will lead to a correct answer

            # -- this node doesn't lead to an answer so uncover it and its row --
            solutions.pop() 
            
            row_node = cur_node.right
            while row_node != cur_node: # loop through all the nodes in the row
                row_node.constraint.uncover()
                row_node = row_node.right

            cur_node = cur_node.down # go to the next node that satisfies this constraint
        
        constraint_node.uncover()

def sudoku_solver(sudoku):
    solver = SudokuSolver()
    return solver.start(sudoku)