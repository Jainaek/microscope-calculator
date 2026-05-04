# ============================================================
# CSC 442 — Project 1: Microscope Specimen Size Calculator
# app.py — Flask Web Application (Phase D & E)
# ============================================================
# This is the main entry point for the web-based version of
# the calculator. It handles:
#   - Serving the HTML frontend
#   - Receiving form submissions (image + inputs)
#   - Running calculations using Phase A logic
#   - Saving results to a database using SQLAlchemy
#   - Returning the full calculation history
#   - Supporting record deletion
# ============================================================

import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename  # Safely sanitises uploaded filenames
from datetime import datetime

# Import the shared database object and the record model
from models import shared_database_instance, SpecimenCalculationRecord

# Import core calculation logic from Phase A
from phase_a_core import (
    MICROSCOPE_MAGNIFICATION_LOOKUP,
    UNIT_CONVERSION_FACTORS,
    perform_specimen_size_calculation,
)

# ============================================================
# Flask App Initialisation & Configuration
# ============================================================

flask_application_instance = Flask(__name__)

# --- Database Configuration ---
# Use an environment variable for production (Render will set DATABASE_URL).
# Fall back to a local SQLite file for development.
raw_database_url_from_env = os.environ.get("DATABASE_URL", "sqlite:///microscope_records.db")

# Render provides PostgreSQL URLs starting with "postgres://" but SQLAlchemy
# requires "postgresql://", so we fix that here.
if raw_database_url_from_env.startswith("postgres://"):
    raw_database_url_from_env = raw_database_url_from_env.replace("postgres://", "postgresql://", 1)

flask_application_instance.config["SQLALCHEMY_DATABASE_URI"] = raw_database_url_from_env
flask_application_instance.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- File Upload Configuration ---
# Uploaded specimen images are stored in the 'static/uploads' folder.
UPLOAD_DESTINATION_FOLDER = os.path.join("static", "uploads")
flask_application_instance.config["UPLOAD_FOLDER"] = UPLOAD_DESTINATION_FOLDER

# Only these file extensions are accepted as valid image uploads
PERMITTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif"}

# Create the uploads folder if it doesn't exist yet
os.makedirs(UPLOAD_DESTINATION_FOLDER, exist_ok=True)

# --- Secret Key (needed for session handling if extended later) ---
flask_application_instance.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

# Bind the SQLAlchemy database instance to this Flask app
shared_database_instance.init_app(flask_application_instance)

# Create all database tables if they don't already exist
with flask_application_instance.app_context():
    shared_database_instance.create_all()


# ============================================================
# Helper Functions
# ============================================================

def is_file_extension_allowed(filename_string):
    """
    Checks whether the given filename has a permitted image extension.

    Parameters:
        filename_string (str): The original filename from the upload.

    Returns:
        bool: True if the extension is in PERMITTED_IMAGE_EXTENSIONS.
    """
    # Extract the part after the last dot, convert to lowercase, and check
    if "." not in filename_string:
        return False
    file_extension_part = filename_string.rsplit(".", 1)[1].lower()
    return file_extension_part in PERMITTED_IMAGE_EXTENSIONS


# ============================================================
# Routes
# ============================================================

@flask_application_instance.route("/")
def serve_main_page():
    """
    Serves the main web page (index.html).
    Passes the microscope types and units to the template
    so the dropdowns can be populated server-side.
    """
    microscope_type_names_list = list(MICROSCOPE_MAGNIFICATION_LOOKUP.keys())
    output_unit_names_list = list(UNIT_CONVERSION_FACTORS.keys())

    return render_template(
        "index.html",
        microscope_types=microscope_type_names_list,
        output_units=output_unit_names_list
    )


@flask_application_instance.route("/calculate", methods=["POST"])
def handle_calculation_request():
    """
    Receives the form data (username, image size, microscope type, unit, image file),
    performs the calculation, saves the result to the database, and returns
    a JSON response with the breakdown.

    Expected form fields:
        - username         : str
        - measured_size_mm : float (the image measurement)
        - microscope_type  : str (must match a key in MICROSCOPE_MAGNIFICATION_LOOKUP)
        - output_unit      : str (must match a key in UNIT_CONVERSION_FACTORS)
        - specimen_image   : file (optional but strongly recommended)
    """

    # --- Extract and validate username ---
    submitted_username = request.form.get("username", "").strip()
    if not submitted_username:
        return jsonify({"error": "Username is required."}), 400

    # --- Extract and validate measured size ---
    raw_size_text_value = request.form.get("measured_size_mm", "").strip()
    try:
        parsed_measured_size = float(raw_size_text_value)
        if parsed_measured_size <= 0:
            raise ValueError("Size must be positive")
    except ValueError:
        return jsonify({"error": "Measured size must be a valid positive number."}), 400

    # --- Extract and validate microscope type ---
    submitted_microscope_type = request.form.get("microscope_type", "").strip()
    if submitted_microscope_type not in MICROSCOPE_MAGNIFICATION_LOOKUP:
        return jsonify({"error": "Invalid microscope type selected."}), 400

    # --- Extract and validate output unit ---
    submitted_output_unit = request.form.get("output_unit", "").strip()
    if submitted_output_unit not in UNIT_CONVERSION_FACTORS:
        return jsonify({"error": "Invalid output unit selected."}), 400

    # --- Handle the uploaded image file (if provided) ---
    saved_image_filename_string = ""
    uploaded_file_object = request.files.get("specimen_image")

    if uploaded_file_object and uploaded_file_object.filename:
        if not is_file_extension_allowed(uploaded_file_object.filename):
            return jsonify({"error": "Invalid image type. Allowed: PNG, JPG, BMP, TIF, GIF."}), 400

        # Sanitise the filename to prevent directory traversal attacks
        sanitised_filename = secure_filename(uploaded_file_object.filename)

        # Prepend a timestamp to avoid filename collisions
        timestamp_prefix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        final_saved_filename = f"{timestamp_prefix}_{sanitised_filename}"

        # Save the file to the uploads folder
        full_save_path = os.path.join(
            flask_application_instance.config["UPLOAD_FOLDER"],
            final_saved_filename
        )
        uploaded_file_object.save(full_save_path)
        saved_image_filename_string = final_saved_filename

    # --- Perform the core scientific calculation ---
    calculation_result_dict = perform_specimen_size_calculation(
        parsed_measured_size,
        submitted_microscope_type,
        submitted_output_unit
    )

    # --- Save the calculation record to the database ---
    new_record_object = SpecimenCalculationRecord(
        performer_username=submitted_username,
        image_size_in_mm=calculation_result_dict["measured_image_size_mm"],
        real_size_in_mm=calculation_result_dict["real_size_in_mm"],
        microscope_type_label=calculation_result_dict["microscope_type"],
        output_unit_label=calculation_result_dict["output_unit"],
        final_converted_result=calculation_result_dict["final_result"],
        uploaded_image_filename=saved_image_filename_string
    )
    shared_database_instance.session.add(new_record_object)
    shared_database_instance.session.commit()

    # --- Build the JSON response payload ---
    response_payload = {
        "success": True,
        "username": submitted_username,
        "measured_size_mm": calculation_result_dict["measured_image_size_mm"],
        "microscope_type": calculation_result_dict["microscope_type"],
        "magnification_factor": calculation_result_dict["magnification_factor"],
        "real_size_mm": calculation_result_dict["real_size_in_mm"],
        "output_unit": calculation_result_dict["output_unit"],
        "final_result": calculation_result_dict["final_result"],
        "image_filename": saved_image_filename_string,
        "record_id": new_record_object.record_primary_key_id,
        # Human-readable formula string for the breakdown panel
        "formula_string": (
            f"{calculation_result_dict['measured_image_size_mm']} mm ÷ "
            f"{calculation_result_dict['magnification_factor']} = "
            f"{calculation_result_dict['real_size_in_mm']:.10f} mm → "
            f"{calculation_result_dict['final_result']:.6f} {calculation_result_dict['output_unit']}"
        )
    }

    return jsonify(response_payload), 200


@flask_application_instance.route("/records", methods=["GET"])
def fetch_all_calculation_records():
    """
    Returns all saved calculation records from the database as a JSON array,
    ordered from most recent to oldest.
    """
    all_saved_records = SpecimenCalculationRecord.query.order_by(
        SpecimenCalculationRecord.record_primary_key_id.desc()
    ).all()

    # Serialise each record to a dictionary using the model's helper method
    serialised_records_list = [record.to_dictionary() for record in all_saved_records]

    return jsonify({"records": serialised_records_list}), 200


@flask_application_instance.route("/records/<int:target_record_id>", methods=["DELETE"])
def delete_single_record(target_record_id):
    """
    Deletes a single record from the database by its integer ID.

    Parameters (in URL):
        target_record_id (int): The primary key of the record to delete.
    """
    # Fetch the record or return a 404 if it doesn't exist
    record_to_delete = SpecimenCalculationRecord.query.get_or_404(target_record_id)

    # Also delete the associated image file from disk if it exists
    if record_to_delete.uploaded_image_filename:
        image_disk_path = os.path.join(
            flask_application_instance.config["UPLOAD_FOLDER"],
            record_to_delete.uploaded_image_filename
        )
        if os.path.exists(image_disk_path):
            os.remove(image_disk_path)

    shared_database_instance.session.delete(record_to_delete)
    shared_database_instance.session.commit()

    return jsonify({"success": True, "deleted_id": target_record_id}), 200


@flask_application_instance.route("/uploads/<path:image_filename>")
def serve_uploaded_image(image_filename):
    """
    Serves an uploaded image file so it can be displayed in the browser.

    Parameters (in URL):
        image_filename (str): The filename of the image to serve.
    """
    return send_from_directory(
        flask_application_instance.config["UPLOAD_FOLDER"],
        image_filename
    )


# ============================================================
# Run the Application
# ============================================================

if __name__ == "__main__":
    # debug=True enables hot-reloading during development.
    # In production (Render), Gunicorn takes over — this block won't run.
    flask_application_instance.run(debug=True, host="0.0.0.0", port=5000)