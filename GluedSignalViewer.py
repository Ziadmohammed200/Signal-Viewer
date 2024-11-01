import os


from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox, QGroupBox, QFormLayout, QWidget, QPushButton, QMessageBox,
    QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from statistics import mean, stdev
from reportlab.platypus import PageBreak


class GluedSignalViewer(QWidget):
    gap_changed = pyqtSignal(int)
    interpolation_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GluedSignalViewer")
        self.setWindowIcon(QIcon("path_to_icon.png"))  # Add a valid path for the icon
        self.figure = plt.Figure(facecolor='black')
        self.resize(1000, 600)
        self.axis = self.figure.add_subplot(111)

        # Set up plot appearance
        self.axis.set_facecolor('black')
        self.axis.set_xlabel('Time (s)', color='white')
        self.axis.set_ylabel('Amplitude', color='white')
        self.axis.tick_params(axis='x', colors='white')
        self.axis.tick_params(axis='y', colors='white')
        self.axis.grid(True, which='both', linestyle='-', linewidth=0.5, color='white')

        # Create layout
        vertical_layout = QVBoxLayout()

        # Create a canvas for the plot
        self.canvas = FigureCanvas(self.figure)
        vertical_layout.addWidget(self.canvas)

        # Slider section with label
        self.group = QGroupBox("Adjustments")
        self.form = QFormLayout()

        self.slider_label = QLabel("Gap Adjustment: 0")
        self.moving_slider = QSlider(Qt.Horizontal)
        self.moving_slider.setRange(-50, 50)
        self.moving_slider.setTickInterval(1)
        self.moving_slider.setTickPosition(QSlider.TicksBelow)
        self.moving_slider.sliderMoved.connect(self.update_slider_value)
        self.moving_slider.valueChanged.connect(self.slider_value)

        self.form.addRow(self.slider_label, self.moving_slider)

        # Dropdown list for interpolation method selection
        self.interpolation_dropdown = QComboBox()
        self.interpolation_dropdown.addItems(["Linear", "Quadratic", "Cubic"])
        self.interpolation_dropdown.currentTextChanged.connect(self.update_interpolation_method)
        self.interpolation_dropdown.setFixedWidth(150)
        self.form.addRow(QLabel("Interpolation Method:"), self.interpolation_dropdown)

        self.group.setLayout(self.form)
        vertical_layout.addWidget(self.group)

        # "Generate Report" button
        self.report_button = QPushButton("Generate Report")
        self.report_button.clicked.connect(self.generate_report)
        vertical_layout.addWidget(self.report_button)

        self.setLayout(vertical_layout)

        self.glued_signal = []
        self.interpolation_method = "Linear"  # Default interpolation method

    def assign_glued_signal(self, glued_signal):
        self.glued_signal = glued_signal




    def plot(self):
        """Plot the glued signal with proper axis settings."""
        self.axis.clear()

        # Reapply axis settings
        self.axis.set_facecolor('black')
        self.axis.set_xlabel('Time (s)', color='white')
        self.axis.set_ylabel('Amplitude', color='white')
        self.axis.tick_params(axis='x', colors='white')
        self.axis.tick_params(axis='y', colors='white')
        self.axis.grid(True, which='both', linestyle='-', linewidth=0.5, color='white')

        # Create time array and plot the glued signal
        time_array = np.arange(len(self.glued_signal)) / 100
        self.axis.plot(time_array, self.glued_signal, color='white')
        self.canvas.draw()

    def update_slider_value(self, value):
        """Update the slider label dynamically."""
        self.slider_label.setText(f"Gap Adjustment: {value}")

    def slider_value(self, value):
        """Emit gap_changed signal with slider value."""
        self.gap_changed.emit(value)

    def update_interpolation_method(self, method):
        """Update interpolation method and emit signal when changed."""
        self.interpolation_method = method
        self.interpolation_changed.emit(method)

    def assign_segments(self, segment1, segment2):
        """Assigns segments to be used for concatenation and plotting."""
        self.segment1 = segment1
        self.segment2 = segment2
        print(f"after {self.segment1, self.segment2}")

    def generate_report(self):
        """Generate a beautifully organized PDF report with statistics and snapshots for signal segments."""
        try:
            snapshots = []

            # Capture snapshots
            snapshots.append(self.save_signal_plot(self.segment1, "segment1_snapshot.png", "Segment 1"))
            snapshots.append(self.save_signal_plot(self.segment2, "segment2_snapshot.png", "Segment 2"))

            # Snapshot of combined segment1 and segment2 before gluing
            combined_segments = np.concatenate((self.segment1, self.segment2))
            snapshots.append(self.save_signal_plot(combined_segments, "signal_before_gap_snapshot.png", "Signal Before Updating Gap"))

            # Snapshot of the glued signal
            snapshots.append(self.save_signal_plot(self.glued_signal, "glued_signal_snapshot.png", "Glued Signal"))

            # Create PDF report
            pdf_filename = "glued_signal_report.pdf"
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Add logos to the report
            logo_left = ReportLabImage("icons/logo_left.png", width=1 * inch, height=1 * inch)
            logo_right = ReportLabImage("icons/logo_right.png", width=1 * inch, height=1 * inch)
            logo_table = Table([[logo_left, None, logo_right]], colWidths=[1 * inch, 4 * inch, 1 * inch])
            elements.append(logo_table)
            elements.append(Spacer(1, 0.5 * inch))

            # Title
            title = Paragraph("Glued Signal Report", styles["Title"])
            elements.append(title)
            elements.append(Spacer(1, 0.2 * inch))

            # Subtitle
            subtitle = Paragraph("This report includes comprehensive statistics and signal snapshots.", styles["BodyText"])
            elements.append(subtitle)
            elements.append(Spacer(1, 0.5 * inch))

            # Statistics Table
            def calculate_statistics(signal):
                """Calculate and return statistics of the given signal."""
                max_value = round(max(signal), 7)
                min_value = round(min(signal), 7)
                mean_value = round(np.mean(signal), 7)
                std_dev_value = round(np.std(signal), 7)
                duration = round(len(signal) / 100, 7)  # Assuming sample rate is 100 Hz

                return [max_value, min_value, mean_value, std_dev_value, duration]

            stats_data = [
                ["Signal", "Max", "Min", "Mean", "Std Dev", "Duration (s)"],
                ["Segment 1", *calculate_statistics(self.segment1)],
                ["Segment 2", *calculate_statistics(self.segment2)],
                ["Combined Segments", *calculate_statistics(combined_segments)],
                ["Glued Signal", *calculate_statistics(self.glued_signal)],
            ]

            table = Table(stats_data, colWidths=[100, 100, 100, 100, 100, 100])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.beige),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5 * inch))

            # Add  snapshot
            for image_path, title_text in snapshots:
                elements.append(Paragraph(title_text, styles["Heading2"]))
                img = ReportLabImage(image_path, width=5 * inch, height=3 * inch)
                img.hAlign = "CENTER"
                elements.append(img)
                elements.append(Spacer(1, 0.7 * inch))




            doc.build(elements)
            QMessageBox.information(self, "Report Generated", f"Report saved as {pdf_filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating the report: {str(e)}")


    def save_signal_plot(self, signal_data, filename, title):
        """Save a plot of the given signal data and return filename and title for the report."""
        plt.figure(figsize=(8, 4))
        time_array = np.arange(len(signal_data)) / 100
        plt.plot(time_array, signal_data, color='blue')
        plt.title(title)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        return filename, title

