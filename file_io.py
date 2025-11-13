# file_io.py
# By using basic Python + file operations

import json
import os
from typing import List, Dict, Any


class FileHandler:

    # -------------------------------------------------------------
    # Load puzzle from uploaded file (.txt or .json)
    # -------------------------------------------------------------
    @staticmethod
    def load(file_obj) -> List[List[int]]:
        """
        Accepts a file-like object from Streamlit.
        Supports:
            - .txt   -> 9 lines of 9 digits or space-separated numbers
            - .json  -> nested list or dict containing the puzzle
        Returns: 9×9 integer grid.
        Raises: ValueError on invalid format.
        """
        raw = file_obj.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        raw = raw.strip()

        name = getattr(file_obj, "name", "").lower()

        # ---------- JSON ----------
        if name.endswith(".json") or raw.startswith("[") or raw.startswith("{"):
            try:
                data = json.loads(raw)

                # if directly array of arrays
                if isinstance(data, list):
                    return FileHandler._validate_grid(data)

                # if dict → try common keys
                if isinstance(data, dict):
                    for key in ("grid", "puzzle", "board", "data"):
                        if key in data:
                            return FileHandler._validate_grid(data[key])

                    # fallback: first valid list
                    for v in data.values():
                        if isinstance(v, list) and len(v) == 9:
                            return FileHandler._validate_grid(v)

                raise ValueError("JSON doesn't contain a valid 9×9 puzzle.")

            except Exception as e:
                raise ValueError(f"Invalid JSON puzzle: {e}")

        # ---------- TEXT ----------
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if len(lines) != 9:
            raise ValueError("Text puzzle must contain exactly 9 lines.")

        grid = []
        for ln in lines:
            parts = ln.split()

            if len(parts) == 9:
                # Format: "0 3 0 4 ..."
                try:
                    row = [int(x) for x in parts]
                except:
                    raise ValueError("Text puzzle contains non-numeric values.")
            else:
                # Format: "030400100"
                if len(ln) == 9 and all(ch.isdigit() for ch in ln):
                    row = [int(ch) for ch in ln]
                else:
                    raise ValueError("Invalid text line — must be 9 digits or 9 space-separated numbers.")

            if any(not (0 <= v <= 9) for v in row):
                raise ValueError("Values must be digits 0–9.")

            grid.append(row)

        return grid

    # -------------------------------------------------------------
    # Validate puzzle format
    # -------------------------------------------------------------
    @staticmethod
    def _validate_grid(grid: Any) -> List[List[int]]:
        if not isinstance(grid, list) or len(grid) != 9:
            raise ValueError("Puzzle must be a 9×9 list.")

        result = []
        for row in grid:
            if not isinstance(row, list) or len(row) != 9:
                raise ValueError("Puzzle must be 9 rows of 9 values each.")
            try:
                r = [int(v) for v in row]
            except:
                raise ValueError("Puzzle contains non-numeric values.")
            if any(not (0 <= v <= 9) for v in r):
                raise ValueError("Values must be digits 0–9.")
            result.append(r)

        return result

    # -------------------------------------------------------------
    # Save puzzle to JSON
    # -------------------------------------------------------------
    @staticmethod
    def save_json(puzzle: List[List[int]], path: str, name: str = "puzzle") -> None:
        """
        Saves puzzle to JSON file under a given key.
        Creates file if missing.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except:
                data = {}

        data[name] = puzzle

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # -------------------------------------------------------------
    # Load JSON file safely
    # -------------------------------------------------------------
    @staticmethod
    def load_json(path: str) -> Dict[str, Any]:
        """
        Loads JSON safely.
        If file missing or corrupted → returns {} instead of crashing Streamlit.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                return obj if isinstance(obj, dict) else {"data": obj}
        except json.JSONDecodeError:
            return {}
        except:
            return {}

    # -------------------------------------------------------------
    # Save puzzle to .txt
    # -------------------------------------------------------------
    @staticmethod
    def save_text(puzzle: List[List[int]], path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for row in puzzle:
                f.write(" ".join(str(v) for v in row) + "\n")
