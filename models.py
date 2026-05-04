# ============================================================
# CSC 442 — Project 1: Microscope Specimen Size Calculator
# models.py — SQLAlchemy Database Model for Flask (Phase D/E)
# ============================================================
# This module defines the database table structure used by the
# Flask web application. SQLAlchemy maps Python classes directly
# to database tables, so we don't write raw SQL here.
# ============================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create a shared SQLAlchemy instance.
# This object is imported into app.py and bound to the Flask app there.
shared_database_instance = SQLAlchemy()


class SpecimenCalculationRecord(shared_database_instance.Model):
    """
    Represents a single calculation record stored in the database.

    Each instance of this class corresponds to one row in the
    'specimen_calculation_records' table.

    Columns:
        record_primary_key_id  : Auto-incrementing unique integer ID.
        performer_username     : The username of the person who ran the calculation.
        image_size_in_mm       : The measured specimen size from the microscope image (in mm).
        real_size_in_mm        : The calculated true real-world size (in mm).
        microscope_type_label  : The descriptive name of the microscope used.
        output_unit_label      : The unit selected for displaying the result.
        final_converted_result : The result value in the user's chosen unit.
        uploaded_image_filename: The filename of the uploaded specimen image.
        created_at_timestamp   : The date and time when this record was created.
    """

    # Explicitly name the database table
    __tablename__ = "specimen_calculation_records"

    # -- Primary Key --
    record_primary_key_id = shared_database_instance.Column(
        shared_database_instance.Integer,
        primary_key=True,
        autoincrement=True
    )

    # -- Username of the person who performed the calculation --
    performer_username = shared_database_instance.Column(
        shared_database_instance.String(120),
        nullable=False
    )

    # -- The size the user measured from the microscope image (in mm) --
    image_size_in_mm = shared_database_instance.Column(
        shared_database_instance.Float,
        nullable=False
    )

    # -- The calculated real-world size (in mm, before unit conversion) --
    real_size_in_mm = shared_database_instance.Column(
        shared_database_instance.Float,
        nullable=False
    )

    # -- The microscope type selected from the dropdown --
    microscope_type_label = shared_database_instance.Column(
        shared_database_instance.String(200),
        nullable=False
    )

    # -- The output unit selected (nm, µm, mm, cm, m) --
    output_unit_label = shared_database_instance.Column(
        shared_database_instance.String(20),
        nullable=False
    )

    # -- The final result after unit conversion --
    final_converted_result = shared_database_instance.Column(
        shared_database_instance.Float,
        nullable=False
    )

    # -- Filename of the uploaded image (or empty string if none) --
    uploaded_image_filename = shared_database_instance.Column(
        shared_database_instance.String(260),
        nullable=False,
        default=""
    )

    # -- Auto-recorded timestamp of when the record was saved --
    created_at_timestamp = shared_database_instance.Column(
        shared_database_instance.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def to_dictionary(self):
        """
        Converts this model instance into a plain Python dictionary.
        Useful for serialising records to JSON in API responses.

        Returns:
            dict: A dictionary representation of this record.
        """
        return {
            "id":               self.record_primary_key_id,
            "username":         self.performer_username,
            "image_size_mm":    self.image_size_in_mm,
            "real_size_mm":     self.real_size_in_mm,
            "microscope_type":  self.microscope_type_label,
            "unit":             self.output_unit_label,
            "result":           self.final_converted_result,
            "image_filename":   self.uploaded_image_filename,
            "timestamp":        self.created_at_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }