"""Entry point for the Excel → MySQL desktop application."""

import sys
import tkinter as tk

# Ensure the project root is on sys.path so that relative imports work
# when the script is invoked directly (python main.py).
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    """Initialise and run the Tkinter application."""
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
