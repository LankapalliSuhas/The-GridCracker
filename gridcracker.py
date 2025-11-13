# gridcracker.py
# By using OOP, File Handling (via file_io), Basic Programming, Functions/Modules, Data Structures

import random
from typing import List, Optional, Tuple
import os

# Optional AI model
try:
    from joblib import load as joblib_load
except:
    joblib_load = None


# -------------------------------------------------------------------
#  OOP CLASSES: Cell, Board, Puzzle
# -------------------------------------------------------------------

class Cell:
    def __init__(self, row: int, col: int, value: int = 0):
        self.row = row
        self.col = col
        self.value = value

    def is_empty(self) -> bool:
        return self.value == 0

    def set(self, v: int):
        self.value = int(v)

    def clear(self):
        self.value = 0

    def __repr__(self):
        return str(self.value)


class Board:
    SIZE = 9

    def __init__(self, grid: Optional[List[List[int]]] = None):
        if grid:
            self.grid = [[int(grid[r][c]) for c in range(self.SIZE)] for r in range(self.SIZE)]
        else:
            self.grid = [[0 for _ in range(self.SIZE)] for _ in range(self.SIZE)]

    def get(self, r: int, c: int) -> int:
        return self.grid[r][c]

    def set(self, r: int, c: int, v: int):
        self.grid[r][c] = int(v)

    def clear(self, r: int, c: int):
        self.grid[r][c] = 0

    def row_values(self, r: int) -> List[int]:
        return self.grid[r]

    def col_values(self, c: int) -> List[int]:
        return [self.grid[r][c] for r in range(self.SIZE)]

    def box_values(self, r: int, c: int) -> List[int]:
        br, bc = (r // 3) * 3, (c // 3) * 3
        vals = []
        for rr in range(br, br + 3):
            for cc in range(bc, bc + 3):
                vals.append(self.grid[rr][cc])
        return vals

    def is_valid(self, r: int, c: int, v: int) -> bool:
        if v in self.row_values(r):
            return False
        if v in self.col_values(c):
            return False
        if v in self.box_values(r, c):
            return False
        return True

    def find_empty(self) -> Optional[Tuple[int, int]]:
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self.grid[r][c] == 0:
                    return (r, c)
        return None

    def copy(self):
        return Board([row[:] for row in self.grid])

    def as_list(self):
        return [row[:] for row in self.grid]


class Puzzle:
    def __init__(self, grid: List[List[int]], name: str = ""):
        self.name = name
        self.board = Board(grid)

    def to_list(self):
        return self.board.as_list()

    def is_solved(self):
        return self.board.find_empty() is None

    def __repr__(self):
        return f"Puzzle(name={self.name})"


# -------------------------------------------------------------------
#  SOLVER (Backtracking)
# -------------------------------------------------------------------

class SudokuSolver:
    def __init__(self, grid: List[List[int]]):
        self.original = Board(grid)
        self.board = self.original.copy()

    def _solve(self) -> bool:
        empty = self.board.find_empty()
        if not empty:
            return True
        r, c = empty
        for num in range(1, 10):
            if self.board.is_valid(r, c, num):
                self.board.set(r, c, num)
                if self._solve():
                    return True
                self.board.clear(r, c)
        return False

    def solve(self) -> Optional[List[List[int]]]:
        self.board = self.original.copy()
        if self._solve():
            return self.board.as_list()
        return None


# Count the number of possible solutions — used to ensure unique generator
class CountingSolver(SudokuSolver):
    def __init__(self, grid):
        super().__init__(grid)
        self.count = 0
        self.limit = 2

    def _count(self):
        if self.count >= self.limit:
            return
        empty = self.board.find_empty()
        if not empty:
            self.count += 1
            return
        r, c = empty
        for num in range(1, 10):
            if self.board.is_valid(r, c, num):
                self.board.set(r, c, num)
                self._count()
                self.board.clear(r, c)
                if self.count >= self.limit:
                    return

    def count_solutions(self, limit=2):
        self.limit = limit
        self.count = 0
        self.board = self.original.copy()
        self._count()
        return self.count


# -------------------------------------------------------------------
#  AI Loader (optional)
# -------------------------------------------------------------------

def load_ai_model(path: str):
    if joblib_load is None:
        return None
    if not os.path.exists(path):
        return None
    try:
        return joblib_load(path)
    except:
        return None


# -------------------------------------------------------------------
#  GENERATOR
# -------------------------------------------------------------------

class SudokuGenerator:
    REMOVALS = {
        "Easy": 36,
        "Medium": 46,
        "Hard": 54
    }

    def __init__(self, difficulty="Medium", model_path="sudoku_ai.joblib"):
        self.difficulty = difficulty if difficulty in self.REMOVALS else "Medium"
        self.ai_model = load_ai_model(model_path)

    def _fill_board(self, board: Board) -> bool:
        empty = board.find_empty()
        if not empty:
            return True
        r, c = empty
        nums = list(range(1, 10))
        random.shuffle(nums)
        for num in nums:
            if board.is_valid(r, c, num):
                board.set(r, c, num)
                if self._fill_board(board):
                    return True
                board.clear(r, c)
        return False

    def _generate_full(self) -> Board:
        board = Board()
        # fill diagonal boxes quickly
        for box in range(0, 9, 3):
            vals = list(range(1, 10))
            random.shuffle(vals)
            idx = 0
            for r in range(box, box + 3):
                for c in range(box, box + 3):
                    board.set(r, c, vals[idx])
                    idx += 1
        self._fill_board(board)
        return board

    def _unique_remove(self, board: Board, removals: int) -> Board:
        while removals > 0:
            r, c = random.randrange(9), random.randrange(9)
            if board.get(r, c) == 0:
                continue
            backup = board.get(r, c)
            board.set(r, c, 0)
            # ensure unique solution
            solver = CountingSolver(board.as_list())
            if solver.count_solutions(limit=2) == 1:
                removals -= 1
            else:
                board.set(r, c, backup)
        return board

    def _estimate_difficulty(self, puzzle: List[List[int]]) -> str:
        if self.ai_model is None:
            clues = sum(1 for r in puzzle for v in r if v != 0)
            if clues >= 36: return "Easy"
            if clues >= 28: return "Medium"
            return "Hard"
        try:
            flat = [v for row in puzzle for v in row]
            pred = self.ai_model.predict([flat])
            return str(pred[0])
        except:
            return "Medium"

    def generate(self) -> List[List[int]]:
        full = self._generate_full()
        removals = self.REMOVALS[self.difficulty]
        puzzle = self._unique_remove(full.copy(), removals).as_list()
        # AI difficulty check (optional)
        _ = self._estimate_difficulty(puzzle)
        return puzzle
