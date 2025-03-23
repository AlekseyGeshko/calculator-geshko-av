# gui/main.py

import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

SERVER_URL = "http://localhost:8000/calc"


class CalcWorker(QThread):
    result_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, expression):
        super().__init__()
        self.expression = expression

    def run(self):
        try:
            response = requests.post(
                SERVER_URL,
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
                self.error_occurred.emit(f"Ошибка вычисления: {error_msg}")

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Сервер недоступен. Попробуйте позже.")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Сервер не отвечает. Превышено время ожидания.")
        except Exception as e:
            self.error_occurred.emit(f"Неизвестная ошибка: {e}")


class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор (с FastAPI сервером)")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout()

        self.input_label = QLabel("Введите выражение:")
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("3 + 2 * (5 - 1)")

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)

        self.calc_button = QPushButton("Посчитать")
        self.calc_button.clicked.connect(self.calculate)

        self.layout.addWidget(self.input_label)
        self.layout.addWidget(self.input_edit)
        self.layout.addWidget(self.calc_button)
        self.layout.addWidget(self.result_label)

        self.setLayout(self.layout)

    def calculate(self):
        expr = self.input_edit.text().strip()
        if not expr:
            QMessageBox.warning(self, "Ошибка", "Выражение не может быть пустым.")
            return

        self.result_label.setText("Считаю...")

        self.worker = CalcWorker(expression=expr)
        self.worker.result_ready.connect(self.show_result)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def show_result(self, result):
        self.result_label.setStyleSheet("color: green;")
        self.result_label.setText(f"Результат: {result}")

    def show_error(self, error_message):
        self.result_label.setStyleSheet("color: red;")
        self.result_label.setText(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec())
