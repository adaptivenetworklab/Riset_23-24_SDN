"""
Debug manager for NetFlux5G Editor
Provides centralized debug logging control
"""

import sys
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import QObject, pyqtSignal

# Global debug state
_debug_enabled = False

def set_debug_enabled(enabled):
    """Set global debug state."""
    global _debug_enabled
    _debug_enabled = enabled

def is_debug_enabled():
    """Check if debug mode is enabled."""
    return _debug_enabled

def debug_print(message):
    """Print debug message if debug mode is enabled."""
    if _debug_enabled:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[DEBUG {timestamp}] {message}")

def error_print(message):
    """Print error message (always shown)."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[ERROR {timestamp}] {message}", file=sys.stderr)

def warning_print(message):
    """Print warning message (always shown)."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[WARN {timestamp}] {message}")

class DebugManager(QObject):
    """Manager for debug operations and console output."""
    
    message_logged = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.debug_console = None
        self.log_buffer = []
        self.max_buffer_size = 1000
        
    def log_message(self, message, level="INFO"):
        """Log a message with timestamp and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{level} {timestamp}] {message}"
        
        # Add to buffer
        self.log_buffer.append(formatted_message)
        
        # Trim buffer if too large
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_buffer_size:]
        
        # Emit signal
        self.message_logged.emit(formatted_message)
        
        # Print to console if debug enabled or if error/warning
        if level in ["ERROR", "WARN"] or is_debug_enabled():
            print(formatted_message)
    
    def show_debug_console(self):
        """Show debug console window."""
        if not self.debug_console:
            self.debug_console = DebugConsole(self)
        
        self.debug_console.show()
        self.debug_console.raise_()
        self.debug_console.activateWindow()
    
    def clear_output(self):
        """Clear debug output buffer."""
        self.log_buffer.clear()
        if self.debug_console:
            self.debug_console.clear_console()
    
    def get_log_contents(self):
        """Get current log contents as string."""
        return "\n".join(self.log_buffer)

class DebugConsole(QDialog):
    """Debug console window for viewing debug output."""
    
    def __init__(self, debug_manager):
        super().__init__()
        self.debug_manager = debug_manager
        self.setupUI()
        self.connectSignals()
        
    def setupUI(self):
        """Setup the debug console UI."""
        self.setWindowTitle("NetFlux5G Debug Console")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Text area for debug output
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(self.get_monospace_font())
        layout.addWidget(self.text_area)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_console)
        button_layout.addWidget(clear_button)
        
        # Save button
        save_button = QPushButton("Save Log")
        save_button.clicked.connect(self.save_log)
        button_layout.addWidget(save_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Load existing log contents
        self.text_area.setPlainText(self.debug_manager.get_log_contents())
        
    def get_monospace_font(self):
        """Get a monospace font for the console."""
        from PyQt5.QtGui import QFont
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Monaco")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setPointSize(9)
        return font
        
    def connectSignals(self):
        """Connect debug manager signals."""
        self.debug_manager.message_logged.connect(self.append_message)
        
    def append_message(self, message):
        """Append a new message to the console."""
        self.text_area.append(message)
        
        # Auto-scroll to bottom
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_console(self):
        """Clear the console display."""
        self.text_area.clear()
        
    def save_log(self):
        """Save log contents to file."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Debug Log",
            f"netflux5g_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.debug_manager.get_log_contents())
                QMessageBox.information(self, "Save Successful", f"Debug log saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save debug log:\n{str(e)}")

def log_exception(func):
    """Decorator to log exceptions from functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_print(f"Exception in {func.__name__}: {str(e)}")
            if is_debug_enabled():
                error_print(f"Traceback:\n{traceback.format_exc()}")
            raise
    return wrapper