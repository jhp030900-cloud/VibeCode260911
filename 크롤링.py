import csv
import re
import sys
import time
from urllib.parse import quote

from openpyxl import Workbook
from bs4 import BeautifulSoup
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


SEARCH_URL = "https://search.naver.com/search.naver?ssc=tab.news.all&where=news&sm=tab_jum&query={query}"


def get_naver_news_url(query: str) -> str:
    return SEARCH_URL.format(query=quote(query))


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_article_text(driver: webdriver.Chrome) -> str:
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        selectors = [
            "#dic_area",
            ".article_view",
            ".newsct_article",
            "article",
            ".article_body",
            ".content_text",
            ".news_end",
            ".se_component",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                paragraphs = [p.get_text(" ", strip=True) for p in element.find_all("p")]
                text = "\n".join(p for p in paragraphs if p)
                if text:
                    return clean_text(text)

        text = soup.get_text("\n", strip=True)
        if text:
            return clean_text(text)[:5000]

        return ""
    except Exception:
        return ""


def extract_news_result(driver: webdriver.Chrome):
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href]")))
        time.sleep(1)
    except Exception:
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = []
    seen = set()

    selectors = [
        "a[data-nlog-area*='.tit']",
        "a[data-nlog-area*='nws_all.h.tit']",
        "a[data-nlog-area*='nws_all.i.tit']",
        "a.news_tit",
        "a[href][data-heatmap-target='.tit']",
        "a[href][class*='fSjI1YZLZceoACwh']",
    ]

    for selector in selectors:
        for a in soup.select(selector):
            href = a.get("href")
            if not href or href.startswith("#"):
                continue
            if not href.startswith("http"):
                continue

            title = a.get_text(" ", strip=True)
            title = title.replace("새 창 열림", "").replace("\u00a0", " ").strip()

            if not title:
                sub = a.select_one("span.sds-comps-text")
                if sub:
                    title = sub.get_text(" ", strip=True).replace("새 창 열림", "").strip()

            if title and href not in seen:
                seen.add(href)
                results.append({"title": title, "link": href})

    return results


def save_to_csv(rows, filename="naver_news.csv"):
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "content"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def save_to_excel(rows, filename="naverResult.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "NaverNews"

    ws.append(["title", "link", "content"])
    for row in rows:
        ws.append([row["title"], row["link"], row["content"]])

    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(length + 5, 80)

    wb.save(filename)


def crawl_naver_news(query: str, max_count: int = 10, progress_callback=None):
    url = get_naver_news_url(query)
    if progress_callback:
        progress_callback(f"검색 URL: {url}")

    driver = None
    rows = []

    try:
        driver = create_driver()
        driver.get(url)

        if progress_callback:
            progress_callback("검색 결과를 불러오는 중입니다...")

        news_items = extract_news_result(driver)
        if not news_items:
            raise ValueError("검색 결과를 찾지 못했습니다. 네이버 페이지 구조가 바뀌었거나 차단 상태일 수 있습니다.")

        seen_links = set()

        for idx, item in enumerate(news_items[:max_count], start=1):
            link = item["link"]
            if link in seen_links:
                continue
            seen_links.add(link)

            title = item["title"]
            if progress_callback:
                progress_callback(f"[{idx}] 기사 본문 수집 중: {title}")

            driver.get(link)
            content = extract_article_text(driver)

            rows.append({
                "title": title,
                "link": link,
                "content": content,
            })

        save_to_csv(rows)
        save_to_excel(rows, "naverResult.xlsx")

        if progress_callback:
            progress_callback(f"수집 완료: {len(rows)}건 저장됨")

        return rows
    except Exception as e:
        if progress_callback:
            progress_callback(f"오류: {str(e)}")
        raise
    finally:
        if driver is not None:
            driver.quit()


class CrawlWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, query: str, max_count: int):
        super().__init__()
        self.query = query
        self.max_count = max_count

    def run(self):
        try:
            rows = crawl_naver_news(self.query, self.max_count, progress_callback=self.progress.emit)
            self.finished.emit(rows)
        except Exception as e:
            self.error.emit(str(e))


class NaverNewsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤러")
        self.resize(700, 500)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("검색어 입력 (예: 반도체)")
        self.query_input.setText("반도체")

        self.count_input = QLineEdit("5")
        self.count_input.setPlaceholderText("개수")
        self.count_input.setMaximumWidth(100)

        self.run_button = QPushButton("크롤링 시작")
        self.run_button.clicked.connect(self.start_crawl)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("검색어:"))
        top_layout.addWidget(self.query_input)
        top_layout.addWidget(QLabel("개수:"))
        top_layout.addWidget(self.count_input)
        top_layout.addWidget(self.run_button)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("수집 로그가 여기에 표시됩니다.")

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(QLabel("실행 로그"))
        layout.addWidget(self.log_area)
        self.setLayout(layout)

        self.thread = None
        self.worker = None

    def start_crawl(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "오류", "검색어를 입력하세요.")
            return

        try:
            max_count = int(self.count_input.text().strip() or "5")
        except ValueError:
            QMessageBox.warning(self, "오류", "뉴스 개수는 숫자로 입력하세요.")
            return

        self.run_button.setEnabled(False)
        self.log_area.clear()
        self.log_area.append("크롤링을 시작합니다...\n")

        self.thread = QThread()
        self.worker = CrawlWorker(query, max_count)
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.thread.quit)
        self.worker.error.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def append_log(self, message: str):
        self.log_area.append(message)

    def on_finished(self, rows):
        self.run_button.setEnabled(True)
        self.log_area.append(f"\n완료: {len(rows)}건 수집됨")
        QMessageBox.information(self, "완료", f"뉴스 {len(rows)}건을 수집해 저장했습니다.\n파일: naverResult.xlsx")

    def on_error(self, message: str):
        self.run_button.setEnabled(True)
        self.log_area.append(f"\n오류: {message}")
        QMessageBox.critical(self, "오류", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NaverNewsWindow()
    window.show()
    sys.exit(app.exec())
