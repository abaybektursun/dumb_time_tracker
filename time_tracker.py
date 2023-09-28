from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QFormLayout, QCalendarWidget,
    QTableWidget, QTableWidgetItem, QMainWindow,
    QStyleFactory,
    QHBoxLayout, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QPainter, QColor, QPalette
import dbm
import time
import json
from datetime import datetime

class CustomCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dates_with_data = set()

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        date_str = date.toString('yyyy-MM-dd')
        if date_str in self.dates_with_data:
            painter.save()
            painter.fillRect(rect, QColor(152, 251, 152))
            painter.restore()

class TimeTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.current_project = None
        self.timer = QTimer()  # Timer to update elapsed time
        self.timer.timeout.connect(self.update_elapsed_time)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Time Tracker')

        # Use Fusion style to get a more modern and flat appearance
        self.setStyle(QStyleFactory.create('Fusion'))

		# Set a light palette for a MacOS/iOS-like look
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.Text, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(60, 140, 220))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

        # Create a layout with consistent margins and spacing
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        #self.layout = QVBoxLayout(self)
        #self.layout.setSpacing(20)

        self.form_layout = QFormLayout()
        self.project_input = QLineEdit()
        self.form_layout.addRow('Project Name:', self.project_input)

        self.button_layout = QHBoxLayout()
        self.start_button = QPushButton('Start Timer')
        self.start_button.clicked.connect(self.start_timer)
        self.stop_button = QPushButton('Stop Timer')
        self.stop_button.clicked.connect(self.stop_timer)
        self.show_button = QPushButton('Show Times')
        self.show_button.clicked.connect(self.show_times)
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.show_button)

        # Style the buttons to be flat with rounded corners
        button_style = """
        QPushButton {
            font-size: 14px;
            color: #fff;
            background-color: #3498db;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            outline: none;
        }
        QPushButton:disabled {
            background-color: #bbb;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #1c598f;
        }
        """
        self.start_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        self.show_button.setStyleSheet(button_style)

        self.time_label = QLabel('Current Project Time: 0 seconds')

        self.calendar = CustomCalendar()
        self.calendar.hide()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Project Name', 'Times', 'Duration'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.hide()

        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.calendar)
        self.layout.addWidget(self.table)

    def start_timer(self):
        self.current_project = self.project_input.text()
        if self.current_project:
            self.start_time = time.time()
            self.timer.start(1000)  # Update every 1 second
            self.start_button.setStyleSheet(
                "background-color: qradialgradient(cx:0.5, cy:0.5, radius: 1.5, fx:0.5, fy:0.5, stop:0 #ff0000, stop:1 #ffffff);"
            )
            self.start_button.setEnabled(False)
        else:
            self.time_label.setText('Please enter a project name')

    def stop_timer(self):
        if self.start_time is not None and self.current_project:
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            with dbm.open('times.db', 'c') as db:
                project_data_bytes = db.get(self.current_project, b'{}')
                try:
                    project_data = json.loads(project_data_bytes.decode())
                except json.JSONDecodeError:
                    project_data = {}  # Reset to an empty dictionary if decode fails

                # Check if project_data is a dictionary before proceeding
                if not isinstance(project_data, dict):
                    project_data = {}  # Reset to an empty dictionary if it's not a dict

                date_str = datetime.utcfromtimestamp(self.start_time).strftime('%Y-%m-%d')
                interval = (self.start_time, end_time)
                project_data[date_str] = project_data.get(date_str, []) + [interval]
                db[self.current_project] = json.dumps(project_data).encode()
            
            self.time_label.setText(f'Current Project Time: {elapsed_time:.2f} seconds')
            self.start_time = None
        else:
            self.time_label.setText('No timer running')

        self.timer.stop()
        self.start_button.setStyleSheet("")


    def update_elapsed_time(self):
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            self.time_label.setText(f'Current Project Time: {elapsed_time:.2f} seconds')

    def show_times(self):
        if self.show_button.text() == "Show Times":
            self.show_button.setText("Hide Times")
            self.calendar.show()
            self.table.show()
            self.update_table()
        else:
            self.show_button.setText("Show Times")
            self.calendar.hide()
            self.table.hide()

    def update_table(self):
        self.calendar.dates_with_data.clear()
        self.table.setRowCount(0)  # Clear previous entries

        
        if Path("times.db").exists():
            with dbm.open('times.db', 'r') as db:
                for key in db.keys():
                    project_data_bytes = db.get(key)
                    try:
                        project_data = json.loads(project_data_bytes.decode())
                        if isinstance(project_data, dict):
                            self.calendar.dates_with_data.update(project_data.keys())
                    except json.JSONDecodeError:
                        pass  # Handle unexpected data format
        self.calendar.updateCells()

    def show_time_intervals(self, date):
        date_str = date.toString('yyyy-MM-dd')
        aggregated_intervals = []

        if Path('times.db').exists():
            with dbm.open('times.db', 'r') as db:
                for key in db.keys():
                    project_data_bytes = db.get(key)
                    try:
                        project_data = json.loads(project_data_bytes.decode())
                        if isinstance(project_data, dict):
                            intervals = project_data.get(date_str, [])
                            for interval in intervals:
                                aggregated_intervals.append((key.decode(), interval))
                    except json.JSONDecodeError:
                        pass  # Handle unexpected data format

        # Sort intervals by start time
        aggregated_intervals.sort(key=lambda x: x[1][0])

        self.table.setRowCount(len(aggregated_intervals))
        for i, (project_name, interval) in enumerate(aggregated_intervals):
            start_utc = datetime.utcfromtimestamp(interval[0])
            end_utc = datetime.utcfromtimestamp(interval[1])

            # Convert to local time using the original method
            start_local = start_utc.astimezone(datetime.now().astimezone().tzinfo)
            end_local = end_utc.astimezone(datetime.now().astimezone().tzinfo)

            start_str = start_local.strftime('%I:%M %p')
            end_str = end_local.strftime('%I:%M %p')

            duration = end_utc - start_utc
            duration_str = f'{duration.seconds // 3600}h {duration.seconds % 3600 // 60}m'

            self.table.setItem(i, 0, QTableWidgetItem(project_name))
            self.table.setItem(i, 1, QTableWidgetItem(f'{start_str} - {end_str}'))
            self.table.setItem(i, 2, QTableWidgetItem(duration_str))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
    """)
    tracker = TimeTracker()
    main_window.setCentralWidget(tracker)
    main_window.show()
    tracker.calendar.selectionChanged.connect(lambda: tracker.show_time_intervals(tracker.calendar.selectedDate()))
    sys.exit(app.exec())
