# ============================================================
# CSC 442 — Project 1: Microscope Specimen Size Calculator
# Phase C: Python-Based GUI (Tkinter)
# ============================================================
# This phase replaces the command-line with a full graphical
# user interface built using Python's built-in Tkinter library.
# All Phase A and Phase B functionality is preserved here.
# ============================================================
# NOTE FOR MARKERS: These files are retained as required even
# though the live application runs on Flask (Phase D/E).
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sqlite3
import os
from datetime import datetime
from PIL import Image, ImageTk  # Pillow is needed for image preview

# Import core logic and data from Phase A and B
from phase_a_core import (
    MICROSCOPE_MAGNIFICATION_LOOKUP,
    UNIT_CONVERSION_FACTORS,
    perform_specimen_size_calculation,
)
from phase_b_database import (
    DATABASE_FILE_PATH,
    CALCULATIONS_TABLE_NAME,
    initialise_database_connection,
    save_calculation_to_database,
    fetch_and_display_all_records,
)

# ============================================================
# Main Application Window Class
# ============================================================

class MicroscopeCalculatorGUIApp:
    """
    The main GUI application class for the Microscope Specimen Size Calculator.
    All widgets, layout logic, and event handlers live here.
    """

    def __init__(self, root_window):
        """
        Initialises the application: sets up the window, connects to the
        database, and builds all the interface widgets.

        Parameters:
            root_window (tk.Tk): The root Tkinter window object.
        """
        self.root_window_ref = root_window
        self.root_window_ref.title("Microscope Specimen Size Calculator — Phase C")
        self.root_window_ref.geometry("780x750")
        self.root_window_ref.resizable(False, False)
        self.root_window_ref.configure(bg="#f0f4f8")

        # Connect to the SQLite database (creates it if it doesn't exist)
        self.active_db_connection = initialise_database_connection()

        # This will hold the path of the currently uploaded image file
        self.uploaded_image_filepath = None

        # Build the entire interface
        self._build_all_interface_sections()

    # ----------------------------------------------------------
    # Interface Builder Methods
    # ----------------------------------------------------------

    def _build_all_interface_sections(self):
        """Constructs every section of the GUI layout from top to bottom."""
        self._build_header_section()
        self._build_username_section()
        self._build_image_upload_section()
        self._build_calculation_inputs_section()
        self._build_action_buttons_section()
        self._build_result_display_section()
        self._build_history_section()

    def _build_header_section(self):
        """Creates the top title/header banner."""
        header_frame_container = tk.Frame(
            self.root_window_ref, bg="#1a3a5c", pady=12
        )
        header_frame_container.pack(fill="x")

        tk.Label(
            header_frame_container,
            text="🔬  Microscope Specimen Size Calculator",
            font=("Helvetica", 17, "bold"),
            fg="white",
            bg="#1a3a5c"
        ).pack()

        tk.Label(
            header_frame_container,
            text="CSC 442 — Computational Biology  |  Phase C: Python GUI",
            font=("Helvetica", 9),
            fg="#a0c4e8",
            bg="#1a3a5c"
        ).pack()

    def _build_username_section(self):
        """Creates the username input field."""
        username_frame = tk.LabelFrame(
            self.root_window_ref,
            text=" 👤 User Identity ",
            font=("Helvetica", 10, "bold"),
            bg="#f0f4f8", fg="#1a3a5c", padx=10, pady=8
        )
        username_frame.pack(fill="x", padx=20, pady=(14, 4))

        tk.Label(
            username_frame, text="Username:", bg="#f0f4f8", font=("Helvetica", 10)
        ).pack(side="left", padx=(0, 8))

        # StringVar lets us read the username value easily
        self.username_entry_var = tk.StringVar()
        tk.Entry(
            username_frame,
            textvariable=self.username_entry_var,
            font=("Helvetica", 11),
            width=30, relief="solid", bd=1
        ).pack(side="left")

    def _build_image_upload_section(self):
        """Creates the specimen image upload button and preview area."""
        image_upload_frame = tk.LabelFrame(
            self.root_window_ref,
            text=" 🖼 Specimen Image ",
            font=("Helvetica", 10, "bold"),
            bg="#f0f4f8", fg="#1a3a5c", padx=10, pady=8
        )
        image_upload_frame.pack(fill="x", padx=20, pady=4)

        # Row: upload button + filename label
        upload_row_frame = tk.Frame(image_upload_frame, bg="#f0f4f8")
        upload_row_frame.pack(fill="x")

        tk.Button(
            upload_row_frame,
            text="📂  Browse & Upload Image",
            command=self._handle_image_upload_button,
            bg="#1a3a5c", fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat", padx=12, pady=5, cursor="hand2"
        ).pack(side="left")

        # Label to show the selected filename
        self.image_filename_display_var = tk.StringVar(value="No image selected")
        tk.Label(
            upload_row_frame,
            textvariable=self.image_filename_display_var,
            bg="#f0f4f8",
            font=("Helvetica", 9),
            fg="#555", wraplength=430
        ).pack(side="left", padx=12)

        # Image preview label (hidden until an image is loaded)
        self.image_preview_label_widget = tk.Label(
            image_upload_frame, bg="#f0f4f8"
        )
        self.image_preview_label_widget.pack(pady=6)

    def _build_calculation_inputs_section(self):
        """Creates the measurement size input, microscope type dropdown, and unit dropdown."""
        inputs_frame = tk.LabelFrame(
            self.root_window_ref,
            text=" ⚗ Calculation Inputs ",
            font=("Helvetica", 10, "bold"),
            bg="#f0f4f8", fg="#1a3a5c", padx=10, pady=10
        )
        inputs_frame.pack(fill="x", padx=20, pady=4)

        # -- Measured Size Input --
        size_row_frame = tk.Frame(inputs_frame, bg="#f0f4f8")
        size_row_frame.pack(fill="x", pady=3)

        tk.Label(
            size_row_frame,
            text="Measured Image Size (mm):",
            bg="#f0f4f8", font=("Helvetica", 10), width=28, anchor="w"
        ).pack(side="left")

        self.measured_size_entry_var = tk.StringVar()
        tk.Entry(
            size_row_frame,
            textvariable=self.measured_size_entry_var,
            font=("Helvetica", 11), width=20, relief="solid", bd=1
        ).pack(side="left")

        # -- Microscope Type Dropdown --
        microscope_row_frame = tk.Frame(inputs_frame, bg="#f0f4f8")
        microscope_row_frame.pack(fill="x", pady=3)

        tk.Label(
            microscope_row_frame,
            text="Microscope Type:",
            bg="#f0f4f8", font=("Helvetica", 10), width=28, anchor="w"
        ).pack(side="left")

        self.microscope_type_combobox_var = tk.StringVar()
        all_microscope_type_names = list(MICROSCOPE_MAGNIFICATION_LOOKUP.keys())
        microscope_type_combobox_widget = ttk.Combobox(
            microscope_row_frame,
            textvariable=self.microscope_type_combobox_var,
            values=all_microscope_type_names,
            state="readonly",  # Prevents free-text entry
            font=("Helvetica", 10), width=35
        )
        microscope_type_combobox_widget.pack(side="left")
        microscope_type_combobox_widget.current(0)  # Default to first option

        # -- Output Unit Dropdown --
        unit_row_frame = tk.Frame(inputs_frame, bg="#f0f4f8")
        unit_row_frame.pack(fill="x", pady=3)

        tk.Label(
            unit_row_frame,
            text="Output Unit:",
            bg="#f0f4f8", font=("Helvetica", 10), width=28, anchor="w"
        ).pack(side="left")

        self.output_unit_combobox_var = tk.StringVar()
        all_output_unit_names = list(UNIT_CONVERSION_FACTORS.keys())
        output_unit_combobox_widget = ttk.Combobox(
            unit_row_frame,
            textvariable=self.output_unit_combobox_var,
            values=all_output_unit_names,
            state="readonly",
            font=("Helvetica", 10), width=15
        )
        output_unit_combobox_widget.pack(side="left")
        output_unit_combobox_widget.current(1)  # Default to µm

    def _build_action_buttons_section(self):
        """Creates the Calculate and View History action buttons."""
        buttons_frame = tk.Frame(self.root_window_ref, bg="#f0f4f8")
        buttons_frame.pack(pady=10)

        tk.Button(
            buttons_frame,
            text="🔬  Calculate Real Size",
            command=self._handle_calculate_button_click,
            bg="#2e7d32", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2"
        ).pack(side="left", padx=8)

        tk.Button(
            buttons_frame,
            text="📋  View / Manage Records",
            command=self._handle_view_records_button_click,
            bg="#1565c0", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2"
        ).pack(side="left", padx=8)

    def _build_result_display_section(self):
        """Creates the result display text area."""
        result_frame = tk.LabelFrame(
            self.root_window_ref,
            text=" 📊 Result & Calculation Breakdown ",
            font=("Helvetica", 10, "bold"),
            bg="#f0f4f8", fg="#1a3a5c", padx=10, pady=8
        )
        result_frame.pack(fill="x", padx=20, pady=4)

        # ScrolledText allows vertical scrolling for long results
        self.result_text_display_widget = scrolledtext.ScrolledText(
            result_frame,
            font=("Courier", 10),
            height=8, width=85,
            state="disabled",   # Read-only by default
            bg="#e8f5e9", fg="#1b5e20",
            relief="solid", bd=1
        )
        self.result_text_display_widget.pack()

    def _build_history_section(self):
        """Placeholder footer for the history panel (launched in a popup window)."""
        tk.Label(
            self.root_window_ref,
            text="Use 'View / Manage Records' to see the full database history.",
            font=("Helvetica", 8), fg="#888", bg="#f0f4f8"
        ).pack(pady=(0, 10))

    # ----------------------------------------------------------
    # Event Handlers
    # ----------------------------------------------------------

    def _handle_image_upload_button(self):
        """
        Opens a file browser dialog for the user to select a specimen image.
        Displays the filename and a thumbnail preview after selection.
        """
        selected_file_path = filedialog.askopenfilename(
            title="Select Specimen Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All Files", "*.*")
            ]
        )

        if not selected_file_path:
            # User closed the dialog without selecting a file
            return

        self.uploaded_image_filepath = selected_file_path
        filename_only = os.path.basename(selected_file_path)
        self.image_filename_display_var.set(f"✅  {filename_only}")

        # Display a thumbnail preview (max 200×150 pixels)
        try:
            raw_image_object = Image.open(selected_file_path)
            raw_image_object.thumbnail((200, 150))
            # Keep a reference to prevent garbage collection
            self.preview_image_ref = ImageTk.PhotoImage(raw_image_object)
            self.image_preview_label_widget.config(image=self.preview_image_ref)
        except Exception as image_load_error:
            self.image_preview_label_widget.config(
                text=f"⚠ Preview unavailable: {image_load_error}"
            )

    def _handle_calculate_button_click(self):
        """
        Validates all inputs, performs the calculation, displays the breakdown,
        and saves the result to the database.
        """
        # Retrieve and validate username
        entered_username_value = self.username_entry_var.get().strip()
        if not entered_username_value:
            messagebox.showwarning("Missing Username", "Please enter your username before calculating.")
            return

        # Retrieve and validate measured size
        raw_size_input_text = self.measured_size_entry_var.get().strip()
        try:
            parsed_measured_size_value = float(raw_size_input_text)
            if parsed_measured_size_value <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            messagebox.showerror("Invalid Size", "Measured image size must be a positive number (e.g. 0.5).")
            return

        # Retrieve dropdown selections
        selected_microscope_type_value = self.microscope_type_combobox_var.get()
        selected_output_unit_value = self.output_unit_combobox_var.get()

        # Perform the calculation using Phase A logic
        calculation_results = perform_specimen_size_calculation(
            parsed_measured_size_value,
            selected_microscope_type_value,
            selected_output_unit_value
        )

        # Build the result text to display
        image_note = ""
        if self.uploaded_image_filepath:
            image_note = f"  Uploaded Image     : {os.path.basename(self.uploaded_image_filepath)}\n"

        result_display_text = (
            f"\n"
            f"  =================== RESULT ===================\n"
            f"{image_note}"
            f"  Username           : {entered_username_value}\n"
            f"  Measured Size      : {calculation_results['measured_image_size_mm']} mm\n"
            f"  Microscope Type    : {calculation_results['microscope_type']}\n"
            f"  Magnification      : ×{calculation_results['magnification_factor']}\n"
            f"  Formula            : {calculation_results['measured_image_size_mm']} ÷ {calculation_results['magnification_factor']}\n"
            f"  Real Size (mm)     : {calculation_results['real_size_in_mm']:.10f} mm\n"
            f"  ✅ Final Result    : {calculation_results['final_result']:.6f} {calculation_results['output_unit']}\n"
            f"  ==============================================\n"
        )

        # Update the read-only display widget
        self.result_text_display_widget.config(state="normal")
        self.result_text_display_widget.delete("1.0", tk.END)
        self.result_text_display_widget.insert(tk.END, result_display_text)
        self.result_text_display_widget.config(state="disabled")

        # Save to database
        save_calculation_to_database(
            db_connection=self.active_db_connection,
            performer_username_str=entered_username_value,
            image_size_in_mm=calculation_results["measured_image_size_mm"],
            real_size_in_mm=calculation_results["real_size_in_mm"],
            microscope_type_str=calculation_results["microscope_type"],
            output_unit_str=calculation_results["output_unit"],
            final_result_value=calculation_results["final_result"]
        )

        messagebox.showinfo("Saved", "Calculation saved to database successfully!")

    def _handle_view_records_button_click(self):
        """
        Opens a popup window showing all saved calculation records,
        with an option to delete individual entries.
        """
        # Create a new popup (Toplevel) window
        records_popup_window = tk.Toplevel(self.root_window_ref)
        records_popup_window.title("Saved Calculation Records")
        records_popup_window.geometry("900x500")
        records_popup_window.configure(bg="#f0f4f8")

        tk.Label(
            records_popup_window,
            text="📋 Calculation History",
            font=("Helvetica", 14, "bold"),
            bg="#1a3a5c", fg="white", pady=8
        ).pack(fill="x")

        # Use a Treeview widget to display records as a table
        tree_columns_tuple = ("ID", "Username", "Image Size (mm)", "Real Size (mm)", "Result", "Unit", "Timestamp")
        records_treeview_widget = ttk.Treeview(
            records_popup_window,
            columns=tree_columns_tuple,
            show="headings",
            height=18
        )

        # Define column headings and widths
        column_width_map = {
            "ID": 40, "Username": 100, "Image Size (mm)": 130,
            "Real Size (mm)": 155, "Result": 130, "Unit": 50, "Timestamp": 145
        }
        for column_name in tree_columns_tuple:
            records_treeview_widget.heading(column_name, text=column_name)
            records_treeview_widget.column(column_name, width=column_width_map[column_name], anchor="center")

        records_treeview_widget.pack(fill="both", expand=True, padx=10, pady=8)

        # Load all records from the database
        db_cursor = self.active_db_connection.cursor()
        db_cursor.execute(
            f"SELECT record_id, performer_username, image_size_mm, real_size_mm, "
            f"final_result, output_unit, timestamp_recorded "
            f"FROM {CALCULATIONS_TABLE_NAME} ORDER BY record_id ASC"
        )
        all_database_records = db_cursor.fetchall()

        for single_record_row in all_database_records:
            records_treeview_widget.insert("", tk.END, values=single_record_row)

        # --- Delete Selected Record Button ---
        def handle_delete_selected_record():
            """Deletes the record currently highlighted in the Treeview."""
            selected_treeview_items = records_treeview_widget.selection()
            if not selected_treeview_items:
                messagebox.showwarning("No Selection", "Please click a record to select it first.", parent=records_popup_window)
                return

            selected_item_values = records_treeview_widget.item(selected_treeview_items[0], "values")
            target_delete_id = int(selected_item_values[0])

            confirm_deletion = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete Record #{target_delete_id}?",
                parent=records_popup_window
            )
            if confirm_deletion:
                inner_cursor = self.active_db_connection.cursor()
                inner_cursor.execute(
                    f"DELETE FROM {CALCULATIONS_TABLE_NAME} WHERE record_id = ?",
                    (target_delete_id,)
                )
                self.active_db_connection.commit()
                records_treeview_widget.delete(selected_treeview_items[0])
                messagebox.showinfo("Deleted", f"Record #{target_delete_id} removed.", parent=records_popup_window)

        tk.Button(
            records_popup_window,
            text="🗑  Delete Selected Record",
            command=handle_delete_selected_record,
            bg="#c62828", fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat", padx=14, pady=6, cursor="hand2"
        ).pack(pady=6)


# ============================================================
# Launch the GUI Application
# ============================================================

def run_phase_c_gui():
    """Creates the root Tkinter window and starts the GUI event loop."""
    root_tk_window = tk.Tk()
    app_instance = MicroscopeCalculatorGUIApp(root_tk_window)
    root_tk_window.mainloop()


if __name__ == "__main__":
    run_phase_c_gui()