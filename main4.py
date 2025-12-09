import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QLabel, QComboBox, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


BASE_URL = "http://localhost/asd/odata/standard.odata/"


class HotelApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Система бронирования отеля")
        self.setFixedSize(520, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title = QLabel("Система работы с гостиницей")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        btn_employees = QPushButton("📌 Получить сотрудников")
        btn_employees.clicked.connect(self.load_employees)
        layout.addWidget(btn_employees)

        btn_guests = QPushButton("👤 Получить гостей")
        btn_guests.clicked.connect(self.load_guests)
        layout.addWidget(btn_guests)

        btn_bookings = QPushButton("📝 Получить бронирования")
        btn_bookings.clicked.connect(self.load_bookings)
        layout.addWidget(btn_bookings)

        self.type_label = QLabel("Выберите престиж номера:")
        layout.addWidget(self.type_label)

        self.room_type_select = QComboBox()
        self.room_type_select.addItems(["Базовый", "Комфорт", "Люкс", "Президентский"])
        layout.addWidget(self.room_type_select)

        btn_rooms = QPushButton("🏨 Показать номера по престижу")
        btn_rooms.clicked.connect(self.load_rooms)
        layout.addWidget(btn_rooms)

    def get_data(self, endpoint):
        try:
            url = BASE_URL + endpoint + "?$format=json"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return f"Ошибка запроса: {response.status_code}"

            return response.json()

        except Exception as e:
            return f"Ошибка соединения: {str(e)}"

    def display(self, title, items, mapping=None):
        if isinstance(items, str):
            self.output.setText(items)
            return

        if "value" not in items:
            self.output.setText("⚠ Нет данных")
            return

        lines = [f"=== {title} ==="]

        for row in items["value"]:
            text = row.get("Description", "(без названия)")
            if mapping:
                mapped = [f"{key}: {row.get(field, '')}" for key, field in mapping.items()]
                text += " | " + ", ".join(mapped)
            lines.append(text)

        self.output.setText("\n".join(lines))
    
    def resolve_name(self, dataset, key_field, key_value, name_field="Description"):

        for item in dataset.get("value", []):
            if item.get(key_field) == key_value:
                return item.get(name_field)

        return "Не найдено"

    def load_employees(self):
        data = self.get_data("Catalog_Сотрудники")
        self.display("Сотрудники", data, {"Должность": "Должность"})

    def load_guests(self):
        data = self.get_data("Catalog_Гость")
        self.display("Гости", data)

    def load_bookings(self):
        data = self.get_data("Document_Бронирование")

        if isinstance(data, str):
            self.output.setText(data)
            return

        bookings = data.get("value", [])

        rooms = self.get_data("Catalog_НомерКомнаты")
        guests = self.get_data("Catalog_Гость")

        result_text = ""

        for b in bookings:
            room_name = self.resolve_name(
                rooms, "Ref_Key", b.get("НомерКомнаты_Key"), "Description"
            )

            entry_date = b.get("ДатаЗаезда", "")[:10]
            exit_date = b.get("ДатаВыезда", "")[:10]

            # Для гостей
            guest_list = []
            for g in b.get("Гость", []):
                guest_name = self.resolve_name(
                    guests, "Ref_Key", g.get("Гость_Key"), "Description"
                )
                guest_list.append(guest_name)

            guests_formatted = ", ".join(guest_list) if guest_list else "Нет данных"

            result_text += f"""
            Номер: {room_name}
            Заезд: {entry_date}
            Выезд: {exit_date}
            Гости: {guests_formatted}
            ------------------------------
            """

        self.output.setText(result_text.strip())


    def load_rooms(self):
        selected_type = self.room_type_select.currentText()

        data = self.get_data("Catalog_НомерКомнаты")

        if isinstance(data, str):
            self.output.setText(data)
            return

        rooms = data.get("value", [])

        prestige_field = None
        if rooms:
            keys = rooms[0].keys()
            for field in ["Престиж", "Категория", "Тип"]:
                if field in keys:
                    prestige_field = field
                    break

        if prestige_field:
            filtered = [r for r in rooms if r.get(prestige_field) == selected_type]

            if filtered:
                out = {"value": filtered}
                self.display(f"Номера — {selected_type}", out, {prestige_field: prestige_field})
            else:
                self.output.setText(f"⚠ Нет номеров с престижем: {selected_type}")
        else:
            self.display("Все номера", data)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QMainWindow { background-color: #e8eef5; }
        QPushButton {
            background-color: #4682B4;
            color: white;
            padding: 8px;
            font-size: 14px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #5A9BD6;
        }
        QTextEdit { background: white; border: 1px solid gray; }
    """)

    window = HotelApp()
    window.show()

    sys.exit(app.exec())
