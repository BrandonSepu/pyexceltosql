"""Main application window built with Tkinter."""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import pandas as pd

from models.table_metadata import TableMetadata
from services.db_service import (
    DBConnectionError,
    DBQueryError,
    get_table_metadata,
    get_tables,
)
from services.excel_service import ExcelLoadError, load_excel
from services.insert_service import InsertError, insert_dataframe
from utils.validators import validate_columns


class MainWindow:
    """Top-level Tkinter window for the Excel → MySQL loader."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Excel → MySQL Loader")
        self.root.resizable(False, False)

        # Internal state
        self._df: Optional[pd.DataFrame] = None
        self._excel_columns: List[str] = []
        self._table_metadata: Optional[TableMetadata] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build and lay out all widgets."""
        pad = {"padx": 10, "pady": 6}

        # ── Section: Excel file ──────────────────────────────────────
        excel_frame = ttk.LabelFrame(self.root, text="1. Load Excel File")
        excel_frame.grid(row=0, column=0, sticky="ew", **pad)

        self._btn_load = ttk.Button(
            excel_frame, text="📂  Load Excel", command=self._on_load_excel
        )
        self._btn_load.grid(row=0, column=0, **pad)

        self._lbl_file = ttk.Label(
            excel_frame, text="No file loaded.", foreground="gray"
        )
        self._lbl_file.grid(row=0, column=1, sticky="w", **pad)

        self._lbl_info = ttk.Label(excel_frame, text="")
        self._lbl_info.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        # ── Section: Table selection ─────────────────────────────────
        table_frame = ttk.LabelFrame(self.root, text="2. Select Destination Table")
        table_frame.grid(row=1, column=0, sticky="ew", **pad)

        self._btn_refresh = ttk.Button(
            table_frame,
            text="🔄  Refresh Tables",
            command=self._on_refresh_tables,
        )
        self._btn_refresh.grid(row=0, column=0, **pad)

        self._combo_tables = ttk.Combobox(
            table_frame, state="readonly", width=35
        )
        self._combo_tables.grid(row=0, column=1, **pad)
        self._combo_tables.bind("<<ComboboxSelected>>", self._on_table_selected)

        self._lbl_columns = ttk.Label(table_frame, text="")
        self._lbl_columns.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        # ── Section: Validation ──────────────────────────────────────
        val_frame = ttk.LabelFrame(self.root, text="3. Column Validation")
        val_frame.grid(row=2, column=0, sticky="ew", **pad)

        self._lbl_validation = ttk.Label(
            val_frame, text="Load a file and select a table to validate.", wraplength=500
        )
        self._lbl_validation.grid(row=0, column=0, sticky="w", **pad)

        # ── Section: Insert ──────────────────────────────────────────
        insert_frame = ttk.LabelFrame(self.root, text="4. Insert Data")
        insert_frame.grid(row=3, column=0, sticky="ew", **pad)

        self._btn_insert = ttk.Button(
            insert_frame,
            text="▶  Start Insertion",
            command=self._on_insert,
            state="disabled",
        )
        self._btn_insert.grid(row=0, column=0, **pad)

        self._progress = ttk.Progressbar(
            insert_frame, orient="horizontal", length=400, mode="determinate"
        )
        self._progress.grid(row=0, column=1, **pad)

        self._lbl_result = ttk.Label(insert_frame, text="")
        self._lbl_result.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        # ── Status bar ───────────────────────────────────────────────
        self._status = ttk.Label(
            self.root,
            text="Ready.",
            relief="sunken",
            anchor="w",
            padding=(4, 2),
        )
        self._status.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))

        self.root.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_load_excel(self) -> None:
        """Open file dialog, load the selected Excel file."""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not file_path:
            return

        try:
            df, columns, row_count = load_excel(file_path)
        except ExcelLoadError as exc:
            messagebox.showerror("Excel Load Error", str(exc))
            return

        self._df = df
        self._excel_columns = columns
        self._table_metadata = None

        file_name = os.path.basename(file_path)
        self._lbl_file.configure(text=file_name, foreground="black")
        self._lbl_info.configure(
            text=f"Columns: {', '.join(columns)}  |  Rows: {row_count}"
        )
        self._lbl_validation.configure(
            text="File loaded. Select a table to validate columns."
        )
        self._btn_insert.configure(state="disabled")
        self._lbl_result.configure(text="")
        self._progress["value"] = 0
        self._set_status(f"Loaded '{file_name}' — {row_count} row(s).")
        self._run_validation()

    def _on_refresh_tables(self) -> None:
        """Fetch available tables from MySQL and populate the combobox."""
        self._set_status("Connecting to MySQL…")
        self._btn_refresh.configure(state="disabled")

        def fetch() -> None:
            try:
                tables = get_tables()
                self.root.after(0, lambda: self._update_tables(tables))
            except DBConnectionError as exc:
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Connection Error", str(exc)),
                )
            except DBQueryError as exc:
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Query Error", str(exc)),
                )
            finally:
                self.root.after(
                    0, lambda: self._btn_refresh.configure(state="normal")
                )

        threading.Thread(target=fetch, daemon=True).start()

    def _update_tables(self, tables: List[str]) -> None:
        """Populate the table combobox with *tables*."""
        if not tables:
            messagebox.showinfo(
                "No Tables",
                "No tables were found in the configured database.",
            )
            self._set_status("No tables found.")
            return

        self._combo_tables["values"] = tables
        self._combo_tables.set("")
        self._lbl_columns.configure(text="")
        self._set_status(f"{len(tables)} table(s) loaded from database.")

    def _on_table_selected(self, _event: object = None) -> None:
        """Load metadata for the selected table and trigger validation."""
        table_name = self._combo_tables.get()
        if not table_name:
            return

        self._set_status(f"Loading metadata for '{table_name}'…")

        def fetch() -> None:
            try:
                metadata = get_table_metadata(table_name)
                self.root.after(0, lambda: self._apply_table_metadata(metadata))
            except (DBConnectionError, DBQueryError) as exc:
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Metadata Error", str(exc)),
                )

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_table_metadata(self, metadata: TableMetadata) -> None:
        """Store metadata and refresh validation display."""
        self._table_metadata = metadata
        col_names = metadata.column_names
        self._lbl_columns.configure(
            text=f"DB columns: {', '.join(col_names)}"
        )
        self._run_validation()

    def _run_validation(self) -> None:
        """Compare Excel vs DB columns and update UI accordingly."""
        if self._df is None or self._table_metadata is None:
            return

        compatible, missing, extra = validate_columns(
            self._excel_columns, self._table_metadata.column_names
        )

        parts = []
        if compatible:
            parts.append("✅  Columns are compatible.")
        else:
            parts.append("❌  Incompatible columns – insertion blocked.")

        if extra:
            parts.append(f"⚠  Extra in Excel (not in DB): {', '.join(extra)}")
        if missing:
            parts.append(
                f"ℹ  DB columns absent in Excel (will use NULL/default): "
                f"{', '.join(missing)}"
            )

        self._lbl_validation.configure(text="\n".join(parts))
        self._btn_insert.configure(
            state="normal" if compatible else "disabled"
        )

    def _on_insert(self) -> None:
        """Confirm and start the data insertion in a background thread."""
        if self._df is None or self._table_metadata is None:
            return

        table_name = self._table_metadata.table_name
        row_count = len(self._df)

        answer = messagebox.askyesno(
            "Confirm Insertion",
            f"Insert {row_count} row(s) into table '{table_name}'?\n\n"
            "This action cannot be undone.",
        )
        if not answer:
            return

        # Only keep columns that exist in the target table
        db_cols = self._table_metadata.column_names
        df_to_insert = self._df[[c for c in self._df.columns if c in db_cols]]

        self._btn_insert.configure(state="disabled")
        self._btn_load.configure(state="disabled")
        self._btn_refresh.configure(state="disabled")
        self._progress["maximum"] = row_count
        self._progress["value"] = 0
        self._lbl_result.configure(text="Inserting…")
        self._set_status("Insertion in progress…")

        def do_insert() -> None:
            def on_progress(done: int, total: int) -> None:
                self.root.after(
                    0, lambda: self._progress.configure(value=done)
                )

            try:
                inserted, errors = insert_dataframe(
                    df_to_insert, table_name, progress_callback=on_progress
                )
                self.root.after(
                    0, lambda: self._finish_insert(inserted, row_count, errors)
                )
            except (DBConnectionError, InsertError) as exc:
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Insertion Error", str(exc)),
                )
                self.root.after(0, self._reset_buttons)

        threading.Thread(target=do_insert, daemon=True).start()

    def _finish_insert(
        self, inserted: int, total: int, errors: List[str]
    ) -> None:
        """Display results after insertion completes."""
        self._reset_buttons()
        self._progress["value"] = inserted

        if errors:
            error_detail = "\n".join(errors[:10])
            if len(errors) > 10:
                error_detail += f"\n… and {len(errors) - 10} more."
            messagebox.showwarning(
                "Insertion Completed With Errors",
                f"Inserted: {inserted}/{total}\n\nErrors:\n{error_detail}",
            )
            self._lbl_result.configure(
                text=f"Done: {inserted}/{total} rows inserted. {len(errors)} batch(es) failed."
            )
        else:
            messagebox.showinfo(
                "Insertion Successful",
                f"Successfully inserted {inserted} row(s) into "
                f"'{self._table_metadata.table_name}'.",
            )
            self._lbl_result.configure(
                text=f"✅  {inserted} row(s) inserted successfully."
            )

        self._set_status(f"Insertion complete: {inserted}/{total} rows.")

    def _reset_buttons(self) -> None:
        """Re-enable action buttons after an operation finishes."""
        self._btn_insert.configure(state="normal")
        self._btn_load.configure(state="normal")
        self._btn_refresh.configure(state="normal")

    def _set_status(self, message: str) -> None:
        """Update the status bar text."""
        self._status.configure(text=message)
