from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                               QHBoxLayout, QLabel, QSplitter)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont, QTextCursor
import sys
import traceback
from io import StringIO
from ..core.api import AphelionAPI

class ScriptConsole(QWidget):
    def __init__(self, api: AphelionAPI, parent=None):
        super().__init__(parent)
        self.api = api
        
        layout = QVBoxLayout()
        
        # Splitter for Output / Input
        splitter = QSplitter(Qt.Vertical)
        
        # Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Monospace", 10))
        self.output_area.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc;")
        splitter.addWidget(self.output_area)
        
        # Input Area
        self.input_area = QTextEdit()
        self.input_area.setFont(QFont("Monospace", 10))
        self.input_area.setStyleSheet("background-color: #252526; color: #dcdcdc;")
        self.input_area.setPlaceholderText("Enter Python code here... (Ctrl+Enter to Run)")
        splitter.addWidget(self.input_area)
        
        layout.addWidget(splitter)
        
        # Controls
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.run_script)
        
        self.btn_clear = QPushButton("Clear Output")
        self.btn_clear.clicked.connect(self.output_area.clear)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_run)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Shortcuts
        # Ctrl+Enter to run?
        # We need event filter or subclass QTextEdit. 
        # For simple MVP, just use button. 
        # Or simplistic key press check on input area.
        self.input_area.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.input_area and event.type() == QEvent.KeyPress:
             if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                 self.run_script()
                 return True
        return super().eventFilter(obj, event)

    def run_script(self):
        code = self.input_area.toPlainText()
        if not code.strip(): return
        
        self.output_area.append(f">>> Run Script")
        
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        
        try:
            # Execution Context
            # Expose 'api' and 'print' (via stdout redirect)
            local_scope = {"api": self.api}
            exec(code, {}, local_scope)
            
        except Exception:
            traceback.print_exc(file=redirected_output)
        finally:
            sys.stdout = old_stdout
            
        output = redirected_output.getvalue()
        if output:
            self.output_area.append(output)
        
        self.output_area.moveCursor(QTextCursor.End)
