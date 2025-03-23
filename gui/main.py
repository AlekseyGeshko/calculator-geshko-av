import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal


SERVER_URL = "http://localhost:8000/calc"


class CalcWorker(QThread):
    result_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, expression: str, use_float: bool):
        super().__init__()
        self.expression = expression
        self.use_float = use_float

    def run(self):
        try:
            url = SERVER_URL
            if self.use_float:
                url += "?float=true"

            response = requests.post(
                url,
                json=self.expression,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                self.result_ready.emit(str(result))
            else:
                try:
                    error_msg = response.json().get("error", "Неизвестная ошибка")
                except Exception:
                    error_msg = "Не удалось обработать ответ от сервера"
                self.error_occurred.emit(f"Ошибка вычисления")

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Сервер недоступен. Попробуйте позже.")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Сервер не отвечает. Превышено время ожидания.")
        except Exception as e:
            self.error_occurred.emit(f"Неизвестная ошибка: {e}")


class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор")
        self.setMinimumWidth(500)

        self.create_ui()
        self.apply_styles()

    def create_ui(self):
        layout = QVBoxLayout()

        # Ввод
        input_layout = QVBoxLayout()
        self.input_label = QLabel("Введите выражение:")
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("3 + 2 * (5 - 1)")
        self.input_edit.returnPressed.connect(self.calculate)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_edit)

        # Чекбокс + Кнопки
        controls_layout = QHBoxLayout()
        self.float_checkbox = QCheckBox("Режим с плавающей точкой")
        self.calc_button = QPushButton("Посчитать")
        self.clear_button = QPushButton("Очистить")

        self.calc_button.clicked.connect(self.calculate)
        self.clear_button.clicked.connect(self.clear_all)

        controls_layout.addWidget(self.float_checkbox)
        controls_layout.addStretch()
        controls_layout.addWidget(self.calc_button)
        controls_layout.addWidget(self.clear_button)

        # Результат
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)

        # История
        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setPlaceholderText("История вычислений будет тут...")

        # Сборка
        layout.addLayout(input_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(self.result_label)
        layout.addWidget(QLabel("История:"))
        layout.addWidget(self.history_box)

        self.setLayout(layout)
        self.input_edit.setFocus()

    def apply_styles(self):
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                font-size: 16px;
                padding: 6px;
            }
            QPushButton {
                font-size: 14px;
                padding: 6px 12px;
            }
            QTextEdit {
                font-family: monospace;
                font-size: 13px;
                background-color: #f7f7f7;
            }
        """)
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold;")

    def calculate(self):
        expr = self.input_edit.text().strip()
        if not expr:
            self.show_error("Введите выражение")
            return

        self.calc_button.setEnabled(False)
        self.result_label.setStyleSheet("color: gray; font-size: 16px;")
        self.result_label.setText("⏳ Считаю...")

        use_float = self.float_checkbox.isChecked()
        self.worker = CalcWorker(expression=expr, use_float=use_float)
        self.worker.result_ready.connect(self.show_result)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def show_result(self, result):
        expr = self.input_edit.text().strip()
        self.result_label.setStyleSheet("color: green; font-size: 16px;")
        self.result_label.setText(f"✅ Результат: {result}")
        self.history_box.append(f"{expr} = {result}")
        self.calc_button.setEnabled(True)

    def show_error(self, error_message):
        self.result_label.setStyleSheet("color: red; font-size: 16px;")
        self.result_label.setText(f"❌ {error_message}")
        self.calc_button.setEnabled(True)

    def clear_all(self):
        self.input_edit.clear()
        self.result_label.setText("")
        self.input_edit.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec())
