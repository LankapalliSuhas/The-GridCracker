import streamlit as st
import json
import time
import numpy as np
from gridcracker import SudokuSolver, SudokuGenerator
from file_io import FileHandler


st.set_page_config(page_title="GridCracker", page_icon="🧩", layout="wide")

def parse_text_grid(text):
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) != 9:
        return None
    grid = []
    for ln in lines:
        parts = ln.split()
        if len(parts) == 9:
            try:
                row = [int(x) for x in parts]
            except:
                return None
        elif len(ln) == 9 and ln.isdigit():
            row = [int(ch) for ch in ln]
        else:
            return None
        if any(v < 0 or v > 9 for v in row):
            return None
        grid.append(row)
    return grid


def pretty_json(data):
    return json.dumps(data, indent=2)


st.title("🧩 GridCracker")
st.subheader("Minimal, robust Sudoku Solver & Generator")
st.write("---")

if "current_puzzle" not in st.session_state:
    st.session_state.current_puzzle = None
if "solved_puzzle" not in st.session_state:
    st.session_state.solved_puzzle = None


tab_solve, tab_generate, tab_data = st.tabs(["Solve", "Generate", "Load & Save"])

# ---------------- SOLVE ----------------
with tab_solve:
    st.header("Solve a Sudoku")

    uploaded = st.file_uploader("Upload puzzle (.txt or .json)", type=["txt", "json"])
    manual = st.text_area("Or paste puzzle (9 rows, use 0 for blanks)", height=220)

    if uploaded:
        try:
            puzzle = FileHandler.load(uploaded)
            st.session_state.current_puzzle = puzzle
            st.success("Puzzle loaded from file.")
        except Exception as e:
            st.error(f"Error: {e}")

    if manual and st.button("Load manual puzzle"):
        parsed = parse_text_grid(manual)
        if parsed is None:
            st.error("Invalid puzzle format.")
        else:
            st.session_state.current_puzzle = parsed
            st.success("Manual puzzle loaded.")

    if st.session_state.current_puzzle:
        st.write("### Current Puzzle")
        st.table(st.session_state.current_puzzle)

    if st.button("Solve Puzzle"):
        if not st.session_state.current_puzzle:
            st.warning("No puzzle loaded.")
        else:
            with st.spinner("Solving..."):
                solver = SudokuSolver(st.session_state.current_puzzle)
                solved = solver.solve()
                time.sleep(0.3)
                if solved:
                    st.session_state.solved_puzzle = solved
                    st.success("Solved!")
                    st.table(solved)
                    st.download_button("Download Solved (JSON)", pretty_json(solved), "solved.json")
                else:
                    st.error("Could not solve puzzle.")


# ---------------- GENERATE ----------------
with tab_generate:
    st.header("Generate Sudoku")

    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    count = st.number_input("How many puzzles?", 1, 5, 1)

    if st.button("Generate"):
        with st.spinner("Generating..."):
            generator = SudokuGenerator(difficulty=difficulty)
            puzzles = [generator.generate() for _ in range(count)]
            st.success("Generated!")

        for i, p in enumerate(puzzles, start=1):
            st.write(f"### Puzzle {i}")
            st.table(np.array(p))
            st.download_button(
                f"Download Puzzle {i}",
                pretty_json(p),
                file_name=f"{difficulty.lower()}_{i}.json"
            )


# ---------------- LOAD & SAVE ----------------
with tab_data:
    st.header("Load & Save")

    save_name = st.text_input("Save name", "my_puzzle")
    save_path = st.text_input("Save file path", "data/saved_puzzles.json")

    if st.button("Save current puzzle"):
        if not st.session_state.current_puzzle:
            st.warning("Nothing to save.")
        else:
            FileHandler.save_json(st.session_state.current_puzzle, save_path, save_name)
            st.success(f"Saved as '{save_name}'")

    load_path = st.text_input("Load saved puzzles from", "data/saved_puzzles.json")

    if st.button("Load saved file"):
        try:
            saved = FileHandler.load_json(load_path)
            if saved:
                st.json(saved)
            else:
                st.info("No puzzles found.")
        except Exception as e:
            st.error(f"Error: {e}")
