# ============================================================
# CSC 442 — Project 1: Microscope Specimen Size Calculator
# Phase B: Database Integration (Command-Line Interface)
# ============================================================
# This phase extends Phase A by:
#   - Asking the user for their username before any calculation
#   - Storing every calculation in an SQLite database
#   - Allowing the user to view and delete saved records
# ============================================================

import sqlite3          # Built-in Python library for SQLite database operations
import os               # For checking if the database file already exists
from datetime import datetime  # For timestamping each calculation record

# Re-use all calculation logic from Phase A
from phase_a_core import (
    MICROSCOPE_MAGNIFICATION_LOOKUP,
    UNIT_CONVERSION_FACTORS,
    display_numbered_menu,
    perform_specimen_size_calculation,
    display_calculation_breakdown,
)

# --- Database Configuration ---
# The SQLite database file will be created in the same folder as this script.
DATABASE_FILE_PATH = "microscope_records.db"

# The name of the table where all calculation records will be stored.
CALCULATIONS_TABLE_NAME = "specimen_calculations"


def initialise_database_connection():
    """
    Creates (or connects to) the SQLite database and ensures the
    calculations table exists with the required columns.

    Returns:
        sqlite3.Connection: An active connection to the database.
    """
    # sqlite3.connect() creates the .db file if it doesn't exist yet
    database_connection_object = sqlite3.connect(DATABASE_FILE_PATH)

    # Use a cursor to execute SQL commands
    database_cursor = database_connection_object.cursor()

    # Create the table only if it hasn't been created before
    database_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {CALCULATIONS_TABLE_NAME} (
            record_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            performer_username  TEXT NOT NULL,
            image_size_mm       REAL NOT NULL,
            real_size_mm        REAL NOT NULL,
            microscope_type     TEXT NOT NULL,
            output_unit         TEXT NOT NULL,
            final_result        REAL NOT NULL,
            timestamp_recorded  TEXT NOT NULL
        )
    """)

    # Commit the table creation to persist it
    database_connection_object.commit()

    return database_connection_object


def save_calculation_to_database(
    db_connection,
    performer_username_str,
    image_size_in_mm,
    real_size_in_mm,
    microscope_type_str,
    output_unit_str,
    final_result_value
):
    """
    Inserts a single calculation record into the database.

    Parameters:
        db_connection:           Active sqlite3.Connection object.
        performer_username_str:  The username of the person who ran the calculation.
        image_size_in_mm:        The measured image size entered (in mm).
        real_size_in_mm:         The calculated real-world size (in mm).
        microscope_type_str:     The microscope type used.
        output_unit_str:         The unit the result was displayed in.
        final_result_value:      The final converted result shown to the user.
    """
    current_timestamp_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        INSERT INTO {CALCULATIONS_TABLE_NAME}
            (performer_username, image_size_mm, real_size_mm,
             microscope_type, output_unit, final_result, timestamp_recorded)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        performer_username_str,
        image_size_in_mm,
        real_size_in_mm,
        microscope_type_str,
        output_unit_str,
        final_result_value,
        current_timestamp_string
    ))

    db_connection.commit()
    print(f"\n  ✅ Record saved to database at {current_timestamp_string}.")


def fetch_and_display_all_records(db_connection):
    """
    Retrieves all records from the database and prints them in a readable table.

    Parameters:
        db_connection: Active sqlite3.Connection object.
    """
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT * FROM {CALCULATIONS_TABLE_NAME} ORDER BY record_id ASC")
    all_records_list = db_cursor.fetchall()

    if not all_records_list:
        print("\n  📭 No records found in the database yet.")
        return

    print("\n" + "=" * 90)
    print(f"  {'ID':<5} {'Username':<15} {'Image Size (mm)':<18} {'Real Size (mm)':<20} {'Result':<20} {'Unit':<6} {'Timestamp'}")
    print("=" * 90)

    for single_record_row in all_records_list:
        record_id_val       = single_record_row[0]
        username_val        = single_record_row[1]
        image_size_val      = single_record_row[2]
        real_size_val       = single_record_row[3]
        result_val          = single_record_row[6]
        unit_val            = single_record_row[5]
        timestamp_val       = single_record_row[7]

        print(f"  {record_id_val:<5} {username_val:<15} {image_size_val:<18.6f} {real_size_val:<20.10f} {result_val:<20.6f} {unit_val:<6} {timestamp_val}")

    print("=" * 90)
    print(f"  Total records: {len(all_records_list)}")


def delete_record_by_id(db_connection):
    """
    Prompts the user for a record ID and deletes that record from the database.

    Parameters:
        db_connection: Active sqlite3.Connection object.
    """
    fetch_and_display_all_records(db_connection)

    try:
        target_record_id = int(input("\n  Enter the Record ID to delete (or 0 to cancel): "))
        if target_record_id == 0:
            print("  ↩ Deletion cancelled.")
            return
    except ValueError:
        print("  ⚠ Invalid input. Deletion cancelled.")
        return

    db_cursor = db_connection.cursor()
    db_cursor.execute(
        f"DELETE FROM {CALCULATIONS_TABLE_NAME} WHERE record_id = ?",
        (target_record_id,)
    )
    db_connection.commit()

    if db_cursor.rowcount > 0:
        print(f"  🗑 Record #{target_record_id} deleted successfully.")
    else:
        print(f"  ⚠ No record found with ID #{target_record_id}.")


def run_phase_b_cli():
    """
    Entry point for Phase B — the full command-line experience with database support.
    Allows the user to perform calculations, view records, and delete entries.
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║  Microscope Specimen Size Calculator     ║")
    print("║  Phase B — CLI with Database             ║")
    print("╚══════════════════════════════════════════╝")

    # Establish database connection (creates the DB file if needed)
    active_db_connection = initialise_database_connection()
    print(f"\n  📂 Database ready: '{DATABASE_FILE_PATH}'")

    # --- Input: Username ---
    # The user must provide their name before any calculation is recorded.
    while True:
        entered_username = input("\nEnter your username: ").strip()
        if entered_username:
            break
        print("  ⚠ Username cannot be empty.")

    print(f"\n  👋 Hello, {entered_username}! Let's begin.")

    # --- Main Menu Loop ---
    while True:
        print("\n┌─────────────────────────────────────┐")
        print("│           MAIN MENU                 │")
        print("├─────────────────────────────────────┤")
        print("│  1. Perform a New Calculation       │")
        print("│  2. View All Saved Records          │")
        print("│  3. Delete a Record                 │")
        print("│  4. Exit                            │")
        print("└─────────────────────────────────────┘")

        menu_choice_input = input("  Choose an option (1–4): ").strip()

        if menu_choice_input == "1":
            # --- Perform a calculation ---
            while True:
                try:
                    specimen_image_size_input = float(
                        input("\n  Enter specimen image size (in mm): ")
                    )
                    if specimen_image_size_input <= 0:
                        print("  ⚠ Must be greater than zero.")
                    else:
                        break
                except ValueError:
                    print("  ⚠ Please enter a valid number.")

            all_microscope_type_options = list(MICROSCOPE_MAGNIFICATION_LOOKUP.keys())
            chosen_microscope_type_str = display_numbered_menu(
                all_microscope_type_options, "Select Microscope Type"
            )

            all_output_unit_options = list(UNIT_CONVERSION_FACTORS.keys())
            chosen_output_unit_str = display_numbered_menu(
                all_output_unit_options, "Select Output Unit"
            )

            # Perform the actual calculation using Phase A logic
            result_data = perform_specimen_size_calculation(
                specimen_image_size_input,
                chosen_microscope_type_str,
                chosen_output_unit_str
            )

            # Display the calculation breakdown
            display_calculation_breakdown(result_data)

            # Save the result to the database
            save_calculation_to_database(
                db_connection=active_db_connection,
                performer_username_str=entered_username,
                image_size_in_mm=result_data["measured_image_size_mm"],
                real_size_in_mm=result_data["real_size_in_mm"],
                microscope_type_str=result_data["microscope_type"],
                output_unit_str=result_data["output_unit"],
                final_result_value=result_data["final_result"]
            )

        elif menu_choice_input == "2":
            fetch_and_display_all_records(active_db_connection)

        elif menu_choice_input == "3":
            delete_record_by_id(active_db_connection)

        elif menu_choice_input == "4":
            print("\n  👋 Goodbye! Database connection closed.")
            active_db_connection.close()
            break

        else:
            print("  ⚠ Invalid choice. Please enter 1, 2, 3, or 4.")


# Run this file directly to test Phase B
if __name__ == "__main__":
    run_phase_b_cli()