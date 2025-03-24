import sys
import json
import requests

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox
)

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtNetwork import QAbstractSocket

SERVER_URL = "http://localhost:8000/calc"
WS_URL = "ws://localhost:8000/ws"


class CalcWorker(QThread):
    """
    Работник, который делает POST запрос на /calc в отдельном потоке,
    чтобы не блокировать UI.
    """
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
                result = response.json()  # ожидаем строку
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


class WebSocketClient:
    def __init__(self, url: str, reconnect_interval=2000):
        self.url = url
        self.reconnect_interval = reconnect_interval  # мс
        self.keep_reconnecting = True  # пока True, мы пытаемся переподключаться

        self.ws = QWebSocket()
        self.ws.connected.connect(self.on_connected)
        self.ws.disconnected.connect(self.on_disconnected)
        self.ws.errorOccurred.connect(self.on_error)
        self.ws.textMessageReceived.connect(self.on_text_message)

        self.on_history = None
        self.on_new_record = None

        self.ws.open(self.url)  # Первая попытка

    def close(self):
        self.keep_reconnecting = False
        self.ws.close()

    @Slot()
    def on_connected(self):
        print("[WebSocket] Connected")

    @Slot()
    def on_disconnected(self):
        print("[WebSocket] Disconnected")
        if self.keep_reconnecting:
            # Запланировать переподключение через 2 сек
            QTimer.singleShot(self.reconnect_interval, self.try_reconnect)

    @Slot(QAbstractSocket.SocketError)
    def on_error(self, error):
        print("[WebSocket] Error:", self.ws.errorString())
        # Если ошибка - тоже пробуем переподключиться
        # (Иногда on_disconnected может не вызываться)
        if self.keep_reconnecting:
            QTimer.singleShot(self.reconnect_interval, self.try_reconnect)

    def try_reconnect(self):
        if self.ws.state() in (QAbstractSocket.ConnectingState, QAbstractSocket.ConnectedState):
            # Может, уже подключились
            return
        print("[WebSocket] Trying to reconnect...")
        self.ws.open(self.url)

    @Slot(str)
    def on_text_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print("[WebSocket] Invalid JSON:", message)
            return

        if "history" in data:
            if self.on_history:
                self.on_history(data["history"])
        else:
            if self.on_new_record:
                self.on_new_record(data)


class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор")
        self.setMinimumWidth(500)

        # Подключим WebSocket
        self.ws_client = WebSocketClient(url=WS_URL, reconnect_interval=2000)
        # Подписываемся на события
        self.ws_client.on_history = self.handle_history
        self.ws_client.on_new_record = self.handle_new_record

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
        self.history_box.setPlaceholderText("История вычислений...")

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
        self.result_label.setText("Считаю...")

        use_float = self.float_checkbox.isChecked()
        self.worker = CalcWorker(expression=expr, use_float=use_float)
        self.worker.result_ready.connect(self.show_result)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def show_result(self, result):
        expr = self.input_edit.text().strip()
        self.result_label.setStyleSheet("color: green; font-size: 16px;")
        self.result_label.setText(f"✅ Результат: {result}")
        self.calc_button.setEnabled(True)


    def show_error(self, error_message):
        self.result_label.setStyleSheet("color: red; font-size: 16px;")
        self.result_label.setText(f"❌ {error_message}")
        self.calc_button.setEnabled(True)

    def clear_all(self):
        self.input_edit.clear()
        self.result_label.setText("")
        self.input_edit.setFocus()

    # ========== WebSocket callbacks ==========

    def handle_history(self, history_list):
        """
        Вызывается один раз при подключении к WebSocket.
        history_list – это весь список вычислений (от самого первого),
        каждый элемент: {"expression": "...", "result": "...", "float_mode": bool, "timestamp": "..."}
        """
        self.history_box.clear()
        for record in history_list:
            expr = record["expression"]
            res = record["result"]
            # Можем при желании показать timestamp
            self.history_box.append(f"{expr} = {res}")

    def handle_new_record(self, record):
        """
        Вызывается при новом выражении. Формат: {"expression": ..., "result": ..., "float_mode": ..., "timestamp": ...}
        """
        expr = record["expression"]
        res = record["result"]
        self.history_box.append(f"{expr} = {res}")

    def closeEvent(self, event):
        """
        Когда окно закрывается, рвём WS-подключение, чтобы корректно освободить ресурсы.
        """
        self.ws_client.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec())
