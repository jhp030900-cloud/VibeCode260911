import sqlite3
from openpyxl import Workbook
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFormLayout,
)

DB_NAME = "products.db"

STYLESHEET = """
QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f5f7ff, stop:1 #eef9f7);
    color: #1f2937;
    font-family: "Malgun Gothic";
    font-size: 11pt;
}

QLabel {
    color: #1f2937;
    font-weight: 600;
}

QLineEdit {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #c7d2fe;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 36px;
    selection-background-color: #7c3aed;
}

QLineEdit:focus {
    border: 2px solid #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

QPushButton {
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    color: white;
    font-weight: 700;
    min-width: 90px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #2563eb);
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #3b82f6);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6d28d9, stop:1 #1d4ed8);
}

#add_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #22c55e, stop:1 #16a34a);
}

#update_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f59e0b, stop:1 #f97316);
}

#delete_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ef4444, stop:1 #dc2626);
}

#search_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06b6d4, stop:1 #0891b2);
}

#export_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ec4899, stop:1 #db2777);
}

QTableWidget {
    background: rgba(255, 255, 255, 0.8);
    alternate-background-color: #f8fafc;
    gridline-color: #dbeafe;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    selection-background-color: #c4b5fd;
    selection-color: #111827;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #7c3aed, stop:1 #4f46e5);
    color: white;
    padding: 8px;
    border: none;
    font-weight: 700;
}

QMessageBox {
    background: #f8fafc;
}
"""


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Products (
                productID INTEGER PRIMARY KEY AUTOINCREMENT,
                productName TEXT NOT NULL,
                productPrice INTEGER NOT NULL,
                productCategory TEXT,
                productStock INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def insert_product(product_name, product_price, product_category=None, product_stock=0):
    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO Products (productName, productPrice, productCategory, productStock)
            VALUES (?, ?, ?, ?)
            """,
            (product_name, product_price, product_category, product_stock),
        )
        conn.commit()
        return cursor.lastrowid


def update_product(product_id, product_name=None, product_price=None, product_category=None, product_stock=None):
    with connect_db() as conn:
        updates = []
        values = []

        if product_name is not None:
            updates.append("productName = ?")
            values.append(product_name)
        if product_price is not None:
            updates.append("productPrice = ?")
            values.append(product_price)
        if product_category is not None:
            updates.append("productCategory = ?")
            values.append(product_category)
        if product_stock is not None:
            updates.append("productStock = ?")
            values.append(product_stock)

        if not updates:
            return 0

        values.append(product_id)
        sql = f"UPDATE Products SET {', '.join(updates)} WHERE productID = ?"
        cursor = conn.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount


def delete_product(product_id):
    with connect_db() as conn:
        cursor = conn.execute("DELETE FROM Products WHERE productID = ?", (product_id,))
        conn.commit()
        return cursor.rowcount


def search_products(keyword):
    with connect_db() as conn:
        cursor = conn.execute(
            """
            SELECT productID, productName, productPrice, productCategory, productStock
            FROM Products
            WHERE productName LIKE ? OR productCategory LIKE ?
            ORDER BY productID
            """,
            (f"%{keyword}%", f"%{keyword}%"),
        )
        return cursor.fetchall()


def get_all_products():
    with connect_db() as conn:
        cursor = conn.execute(
            """
            SELECT productID, productName, productPrice, productCategory, productStock
            FROM Products
            ORDER BY productID
            """
        )
        return cursor.fetchall()


def export_to_excel(filename="products.xlsx"):
    rows = get_all_products()
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = ["productID", "productName", "productPrice", "productCategory", "productStock"]
    ws.append(headers)

    for row in rows:
        ws.append([row["productID"], row["productName"], row["productPrice"], row["productCategory"], row["productStock"]])

    wb.save(filename)
    return filename


class ProductWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("제품 관리 프로그램")
        self.resize(980, 620)
        self.setStyleSheet(STYLESHEET)

        self.create_table()
        self.init_ui()
        self.load_products()

    def create_table(self):
        create_table()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        title = QLabel("제품 관리 시스템")
        title.setStyleSheet(
            "font-size: 24px; font-weight: 800; color: #312e81; margin-bottom: 4px;"
        )
        main_layout.addWidget(title)

        form_frame = QWidget()
        form_frame.setStyleSheet(
            "QWidget { background: rgba(255,255,255,0.35); border: 1px solid rgba(167,139,250,0.5); border-radius: 16px; }"
        )
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.category_input = QLineEdit()
        self.stock_input = QLineEdit()

        form_layout.addRow("상품명:", self.name_input)
        form_layout.addRow("가격:", self.price_input)
        form_layout.addRow("분류:", self.category_input)
        form_layout.addRow("재고:", self.stock_input)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.add_btn = QPushButton("추가")
        self.update_btn = QPushButton("수정")
        self.delete_btn = QPushButton("삭제")
        self.search_btn = QPushButton("검색")
        self.export_btn = QPushButton("엑셀 저장")

        self.add_btn.setObjectName("add_btn")
        self.update_btn.setObjectName("update_btn")
        self.delete_btn.setObjectName("delete_btn")
        self.search_btn.setObjectName("search_btn")
        self.export_btn.setObjectName("export_btn")

        self.add_btn.clicked.connect(self.add_product)
        self.update_btn.clicked.connect(self.update_product)
        self.delete_btn.clicked.connect(self.delete_product)
        self.search_btn.clicked.connect(self.search_product)
        self.export_btn.clicked.connect(self.export_product_excel)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.search_btn)
        button_layout.addWidget(self.export_btn)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["상품ID", "상품명", "가격", "분류", "재고"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            "QTableWidget { border-radius: 12px; }"
        )
        self.table.cellClicked.connect(self.fill_form_from_table)

        main_layout.addWidget(form_frame)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def get_selected_product_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return int(item.text())

    def clear_form(self):
        self.name_input.clear()
        self.price_input.clear()
        self.category_input.clear()
        self.stock_input.clear()

    def add_product(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        category = self.category_input.text().strip()
        stock_text = self.stock_input.text().strip()

        if not name or not price_text:
            QMessageBox.warning(self, "입력 오류", "상품명과 가격은 필수입니다.")
            return

        try:
            price = int(price_text)
            stock = int(stock_text) if stock_text else 0
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "가격과 재고는 정수로 입력해주세요.")
            return

        insert_product(name, price, category, stock)
        QMessageBox.information(self, "성공", "상품이 추가되었습니다.")
        self.clear_form()
        self.load_products()

    def update_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "선택 오류", "수정할 상품을 선택해주세요.")
            return

        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        category = self.category_input.text().strip()
        stock_text = self.stock_input.text().strip()

        if not name and not price_text and not category and not stock_text:
            QMessageBox.warning(self, "입력 오류", "수정할 값을 입력해주세요.")
            return

        update_data = {}
        if name:
            update_data["product_name"] = name
        if price_text:
            update_data["product_price"] = int(price_text)
        if category:
            update_data["product_category"] = category
        if stock_text:
            update_data["product_stock"] = int(stock_text)

        with connect_db() as conn:
            sql = "UPDATE Products SET "
            values = []
            for key, value in update_data.items():
                if key == "product_name":
                    sql += "productName = ?, "
                elif key == "product_price":
                    sql += "productPrice = ?, "
                elif key == "product_category":
                    sql += "productCategory = ?, "
                elif key == "product_stock":
                    sql += "productStock = ?, "
                values.append(value)
            sql = sql.rstrip(", ") + " WHERE productID = ?"
            values.append(product_id)
            conn.execute(sql, tuple(values))
            conn.commit()

        QMessageBox.information(self, "성공", "상품이 수정되었습니다.")
        self.clear_form()
        self.load_products()

    def delete_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "선택 오류", "삭제할 상품을 선택해주세요.")
            return

        reply = QMessageBox.question(self, "삭제 확인", "선택한 상품을 삭제하시겠습니까?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_product(product_id)
            QMessageBox.information(self, "성공", "상품이 삭제되었습니다.")
            self.clear_form()
            self.load_products()

    def search_product(self):
        keyword = self.name_input.text().strip()
        if not keyword:
            self.load_products()
            return

        rows = search_products(keyword)
        self.show_rows(rows)

    def export_product_excel(self):
        try:
            filename = export_to_excel("products.xlsx")
            QMessageBox.information(self, "엑셀 저장 완료", f"엑셀 파일이 저장되었습니다: {filename}")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"엑셀 저장 중 오류가 발생했습니다: {e}")

    def fill_form_from_table(self, row, column):
        product_id = self.table.item(row, 0).text()
        product_name = self.table.item(row, 1).text()
        product_price = self.table.item(row, 2).text()
        product_category = self.table.item(row, 3).text()
        product_stock = self.table.item(row, 4).text()

        self.name_input.setText(product_name)
        self.price_input.setText(product_price)
        self.category_input.setText(product_category)
        self.stock_input.setText(product_stock)

        self.table.selectRow(row)

    def show_rows(self, rows):
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["상품ID", "상품명", "가격", "분류", "재고"])

        for row_index, row in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row["productID"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(row["productName"])))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(row["productPrice"])))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(row["productCategory"])))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(row["productStock"])))

    def load_products(self):
        rows = get_all_products()
        self.show_rows(rows)


if __name__ == "__main__":
    app = QApplication([])
    window = ProductWindow()
    window.show()
    app.exec()
