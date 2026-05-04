# ============================================================
# CSC 442 — Project 1: Microscope Specimen Size Calculator
# Phase A: Core Calculation Program (Command-Line Interface)
# ============================================================
# This module handles the fundamental scientific calculation:
#   Real Size = Measured Size (mm) ÷ Magnification Factor
# The user picks a microscope type and an output unit.
# ============================================================


# --- Microscope Types and Their Magnification Factors ---
# Each microscope type is mapped to its standard magnification value.
# This dictionary ensures the magnification is always selected from
# a predefined list — never entered as free text.
MICROSCOPE_MAGNIFICATION_LOOKUP = {
    "Light Microscope (40x)":         40,
    "Light Microscope (100x)":        100,
    "Light Microscope (400x)":        400,
    "Light Microscope (1000x)":       1000,
    "Stereo Microscope (10x)":        10,
    "Stereo Microscope (45x)":        45,
    "Scanning Electron Microscope":   100000,
    "Transmission Electron Microscope": 500000,
    "Fluorescence Microscope (40x)":  40,
    "Fluorescence Microscope (100x)": 100,
}

# --- Unit Conversion Factors ---
# All conversions are relative to millimetres (mm),
# since the measured input size is always in mm.
# Formula: real_size_in_mm × conversion_factor = result in chosen unit
UNIT_CONVERSION_FACTORS = {
    "nm":  1_000_000,      # 1 mm = 1,000,000 nm
    "µm":  1_000,          # 1 mm = 1,000 µm
    "mm":  1,              # 1 mm = 1 mm (no conversion)
    "cm":  0.1,            # 1 mm = 0.1 cm
    "m":   0.001,          # 1 mm = 0.001 m
}


def display_numbered_menu(menu_options_list, menu_title):
    """
    Displays a numbered list of options for the user to choose from.
    Returns the selected item from the list.

    Parameters:
        menu_options_list (list): The list of option strings to display.
        menu_title (str): A heading label shown above the numbered choices.

    Returns:
        str: The selected option string.
    """
    print(f"\n--- {menu_title} ---")
    for option_index, option_label in enumerate(menu_options_list, start=1):
        print(f"  {option_index}. {option_label}")

    while True:
        try:
            user_choice_number = int(input(f"Enter number (1–{len(menu_options_list)}): "))
            if 1 <= user_choice_number <= len(menu_options_list):
                # Valid selection — return the corresponding item
                return menu_options_list[user_choice_number - 1]
            else:
                print(f"  ⚠ Please enter a number between 1 and {len(menu_options_list)}.")
        except ValueError:
            # User typed something that isn't a number
            print("  ⚠ Invalid input. Please enter a whole number.")


def perform_specimen_size_calculation(
    measured_image_size_in_mm,
    selected_microscope_type,
    selected_output_unit
):
    """
    Performs the core microscopy calculation and returns a results dictionary.

    Scientific Formula:
        Real Size (mm) = Measured Image Size (mm) ÷ Magnification Factor
        Result = Real Size (mm) × Unit Conversion Factor

    Parameters:
        measured_image_size_in_mm (float): Size of the specimen as seen in the image (in mm).
        selected_microscope_type (str): The microscope type key from MICROSCOPE_MAGNIFICATION_LOOKUP.
        selected_output_unit (str): The desired output unit key from UNIT_CONVERSION_FACTORS.

    Returns:
        dict: A dictionary containing all calculated values and display information.
    """
    # Step 1: Retrieve the magnification factor for the chosen microscope
    magnification_factor_value = MICROSCOPE_MAGNIFICATION_LOOKUP[selected_microscope_type]

    # Step 2: Apply the core formula — divide measured size by magnification
    real_specimen_size_in_mm = measured_image_size_in_mm / magnification_factor_value

    # Step 3: Convert the result from mm into the user's preferred unit
    unit_multiplier_value = UNIT_CONVERSION_FACTORS[selected_output_unit]
    final_converted_result = real_specimen_size_in_mm * unit_multiplier_value

    # Step 4: Package all values into a dictionary for display and storage
    calculation_result_package = {
        "measured_image_size_mm":   measured_image_size_in_mm,
        "microscope_type":          selected_microscope_type,
        "magnification_factor":     magnification_factor_value,
        "real_size_in_mm":          real_specimen_size_in_mm,
        "output_unit":              selected_output_unit,
        "final_result":             final_converted_result,
    }

    return calculation_result_package


def display_calculation_breakdown(result_data_dict):
    """
    Prints a clear, human-readable breakdown of how the result was computed.

    Parameters:
        result_data_dict (dict): The result dictionary from perform_specimen_size_calculation().
    """
    print("\n" + "=" * 55)
    print("         CALCULATION BREAKDOWN")
    print("=" * 55)
    print(f"  Measured image size    : {result_data_dict['measured_image_size_mm']} mm")
    print(f"  Microscope type        : {result_data_dict['microscope_type']}")
    print(f"  Magnification factor   : ×{result_data_dict['magnification_factor']}")
    print(f"  Formula applied        : {result_data_dict['measured_image_size_mm']} ÷ {result_data_dict['magnification_factor']}")
    print(f"  Real size (mm)         : {result_data_dict['real_size_in_mm']:.10f} mm")
    print(f"  Converted to           : {result_data_dict['output_unit']}")
    print(f"  ✅ REAL SIZE           : {result_data_dict['final_result']:.6f} {result_data_dict['output_unit']}")
    print("=" * 55)


def run_phase_a_cli():
    """
    Entry point for Phase A — runs the command-line interface.
    Prompts the user for all inputs and displays the result breakdown.
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║  Microscope Specimen Size Calculator     ║")
    print("║  Phase A — Command-Line Interface        ║")
    print("╚══════════════════════════════════════════╝")

    # --- Input: Measured specimen size ---
    while True:
        try:
            measured_specimen_image_size = float(
                input("\nEnter the specimen size as measured from the microscope image (in mm): ")
            )
            if measured_specimen_image_size <= 0:
                print("  ⚠ Size must be greater than zero.")
            else:
                break
        except ValueError:
            print("  ⚠ Please enter a valid decimal number (e.g. 0.25).")

    # --- Input: Microscope type (chosen from list, not typed) ---
    all_microscope_types = list(MICROSCOPE_MAGNIFICATION_LOOKUP.keys())
    chosen_microscope_type = display_numbered_menu(all_microscope_types, "Select Microscope Type")

    # --- Input: Output unit (chosen from list) ---
    all_output_units = list(UNIT_CONVERSION_FACTORS.keys())
    chosen_output_unit = display_numbered_menu(all_output_units, "Select Output Unit")

    # --- Perform the calculation ---
    result_package = perform_specimen_size_calculation(
        measured_specimen_image_size,
        chosen_microscope_type,
        chosen_output_unit
    )

    # --- Display the result breakdown ---
    display_calculation_breakdown(result_package)


# Run this file directly to test Phase A
if __name__ == "__main__":
    run_phase_a_cli()