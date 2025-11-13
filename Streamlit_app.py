```python
# app.py

import streamlit as st
import json
import time
import numpy as np
from typing import List, Optional

# Import core logic (single-file module)
# gridcracker.py should define: SudokuSolver, SudokuGenerator, load_ai_model (optional)
from gridcracker import SudokuSolver, SudokuGenerator  # type: ignore
from file_io import FileHandler  # type: ignore


st.set_page_config(page_title="GridCracker", page_icon="🧩", layout="wide")

# --- Helpers ---
def parse_text_grid(text: str) -> Optional[List[List[int]]]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) != 9:
        return None
    grid = []
    for ln in lines:
        parts = ln.split()
        if len(parts) == 9:
            try:
                row = [int(x) for x in parts]
            except ValueError:
                return None
        elif len(ln) == 9 and all(ch.isdigit() for ch in ln):
            row = [int(ch) for ch in ln]
        else:
            return None
        if any(not (0 <= v <= 9) for v in row):
            return None
        grid.append(row)
    return grid

def pretty_json(data):
    return json.dumps(data, indent=2)

# --- UI Layout ---
st.markdown("<h1 style='text-align:center'>🧩 GridCracker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray'>Minimal, robust Sudoku Solver & Generator</p>", unsafe_allow_html=True)
st.write("---")

if "current_puzzle" not in st.session_state:
    st.session_state.current_puzzle = None
if "solved_puzzle" not in st.session_state:
    st.session_state.solved_puzzle = None

tab_solve, tab_generate, tab_data = st.tabs(["🧠 Solve", "🎲 Generate", "📁 Load & Save"])

# ---------------- Solve Tab ----------------
with tab_solve:
    st.header("Solve a Sudoku Puzzle")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded = st.file_uploader("Upload puzzle (.txt or .json)", type=["txt", "json"])
        manual = st.text_area(
            "Or paste puzzle (9 rows, space-separated or continuous digits, use 0 for blanks)",
            height=240,
            placeholder="0 3 0 0 7 0 0 0 1\n6 0 0 0 0 0 4 0 0\n..."
        )
        if uploaded:
            try:
                puzzle = FileHandler.load(uploaded)
                st.session_state.current_puzzle = puzzle
                st.success("Puzzle loaded from file.")
            except Exception as e:
                st.error(f"Failed to load file: {e}")

        elif manual and st.button("Load manual puzzle"):
            parsed = parse_text_grid(manual)
            if parsed is None:
                st.error("Invalid puzzle format — ensure 9 rows of 9 digits/numbers (0-9).")
            else:
                st.session_state.current_puzzle = parsed
                st.success("Manual puzzle loaded.")

    with col2:
        st.write("Tips")
        st.write("- Upload `.txt` or `.json` puzzle, or paste 9 lines of numbers.")
        st.write("- Use `0` for blanks.")
        if st.session_state.current_puzzle:
            st.json({"status": "puzzle_loaded", "clues": sum(1 for r in st.session_state.current_puzzle for v in r if v != 0)})

    st.write("---")

    if st.session_state.current_puzzle:
        st.subheader("Current Puzzle")
        st.table(st.session_state.current_puzzle)

    if st.button("Solve Puzzle"):
        if not st.session_state.current_puzzle:
            st.warning("No puzzle loaded — upload or paste one first.")
        else:
            with st.spinner("Solving..."):
                try:
                    solver = SudokuSolver(st.session_state.current_puzzle)
                    solved = solver.solve()
                    time.sleep(0.5)
                    if solved:
                        st.session_state.solved_puzzle = solved
                        st.success("Puzzle solved ✅")
                        st.table(solved)
                        st.download_button(
                            "Download solved (JSON)",
                            data=pretty_json(solved),
                            file_name="solved_sudoku.json",
                            mime="application/json"
                        )
                    else:
                        st.session_state.solved_puzzle = None
                        st.error("Could not solve the puzzle (may be invalid or have multiple contradictions).")
                except Exception as e:
                    st.error(f"Solver error: {e}")

    if st.session_state.solved_puzzle and st.button("Replace current with solved"):
        st.session_state.current_puzzle = st.session_state.solved_puzzle
        st.success("Current puzzle replaced with solved puzzle.")

# ---------------- Generate Tab ----------------
with tab_generate:
    st.header("Generate Sudoku Puzzles")

    gen_col1, gen_col2 = st.columns([1, 2])
    with gen_col1:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
        count = st.number_input("How many?", min_value=1, max_value=5, value=1)
        ai_toggle = st.checkbox("Use local AI estimator (if available)", value=True)
    with gen_col2:
        st.write("Generator will produce puzzles with unique solutions (uses CountingSolver checks).")

    if st.button("Generate"):
        with st.spinner("Generating..."):
            try:
                generator = SudokuGenerator(difficulty=difficulty)
                puzzles = [generator.generate() for _ in range(count)]
                st.success(f"Generated {len(puzzles)} puzzle(s).")
                for idx, p in enumerate(puzzles, start=1):
                    st.subheader(f"{difficulty} Puzzle #{idx}")
                    st.table(np.array(p))
                    st.download_button(
                        f"Download Puzzle #{idx} (JSON)",
                        data=pretty_json(p),
                        file_name=f"{difficulty.lower()}_puzzle_{idx}.json",
                        mime="application/json"
                    )
                    if st.button(f"Load Puzzle #{idx} into current", key=f"load_{idx}"):
                        st.session_state.current_puzzle = p
                        st.success(f"Puzzle #{idx} loaded as current puzzle.")
            except Exception as e:
                st.error(f"Generator error: {e}")

# ---------------- Load & Save Tab ----------------
with tab_data:
    st.header("Load & Save Puzzles")

    st.subheader("Save current puzzle")
    save_name = st.text_input("Name to save as", value="my_puzzle")
    save_path = st.text_input("Storage JSON path", value="data/saved_puzzles.json")

    if st.button("Save current puzzle"):
        if not st.session_state.current_puzzle:
            st.warning("No current puzzle to save. Generate or load one first.")
        else:
            try:
                FileHandler.save_json(st.session_state.current_puzzle, save_path, save_name)
                st.success(f"Saved as '{save_name}' in {save_path}.")
            except Exception as e:
                st.error(f"Failed to save: {e}")

    st.write("---")
    st.subheader("Load saved puzzles")
    list_path = st.text_input("Saved JSON path to load", value="data/saved_puzzles.json", key="list_path")

    try:
        saved = FileHandler.load_json(list_path)
        if not saved:
            st.info("No saved puzzles found (file missing, empty, or invalid).")
        else:
            keys = list(saved.keys())
            sel = st.selectbox("Select saved puzzle", keys) if keys else None
            if sel and st.button("Load selected"):
                candidate = saved.get(sel)
                if isinstance(candidate, list) and len(candidate) == 9:
                    st.session_state.current_puzzle = candidate
                    st.success(f"Loaded '{sel}'.")
                else:
                    st.error("Selected entry is not a valid 9x9 puzzle.")
            if keys:
                if st.button("Show saved JSON"):
                    st.code(pretty_json(saved), language="json")
    except FileNotFoundError:
        st.info("Saved file not found. Save a puzzle to create it.")
    except Exception as e:
        st.error(f"Error loading saved puzzles: {e}")

st.write("---")
st.caption("GridCracker — built with OOP, classic algorithms, and a small optional AI helper. No pandas required.")
```
