import csv
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = 'https://finance.naver.com/sise/sise_index.naver?code=KPI200'
ENTRY_URL = 'https://finance.naver.com/sise/entryJongmok.naver?type=KPI200'
CSV_FILE = 'kospi200_top_stocks.csv'
XLSX_FILE = 'kospi200_top_stocks.xlsx'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}
FIELDNAMES = ['종목명', '현재가', '전일비', '등락률', '거래량', '거래대금(백만)', '시가총액(억)']


def request_html(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def clean_text(element):
    if element is None:
        return ''
    return re.sub(r'\s+', ' ', element.get_text(' ', strip=True)).strip()


def find_entry_url(soup):
    """메인 페이지에서 편입종목 iframe의 실제 URL을 찾는다."""
    iframe = soup.select_one("iframe[title='편입종목상위 영역']")
    if iframe and iframe.get('src'):
        return urljoin('https://finance.naver.com', iframe['src'])
    return ENTRY_URL


def find_entry_table(soup):
    """편입종목상위 표를 찾는 함수"""
    for div in soup.select('div.box_type_m'):
        h4 = div.select_one('h4.top_tlt')
        if h4:
            text = h4.get_text(' ', strip=True)
            if '편입종목' in text and '상위' in text:
                table = div.select_one('table.type_1')
                if table:
                    return table

    for table in soup.select('table.type_1'):
        headers = [clean_text(th) for th in table.select('th')]
        if '종목별' in headers and '현재가' in headers and '등락률' in headers:
            return table

    raise ValueError('편입종목상위 테이블을 찾지 못했습니다.')


def extract_max_page(soup):
    """페이지 네비게이션에서 마지막 페이지 번호를 추출한다."""
    pages = []
    for a in soup.select('table.Nnavi a[href*="page="]'):
        href = a.get('href', '')
        match = re.search(r'page=(\d+)', href)
        if match:
            pages.append(int(match.group(1)))
    if pages:
        return max(pages)
    return 1


def parse_entry_table(table):
    """테이블에서 종목별 데이터를 추출한다."""
    rows = []

    for row in table.select('tr'):
        stock_link = row.select_one('td.ctg a')
        if not stock_link:
            continue

        cells = row.select('td')
        if len(cells) < 7:
            continue

        name = stock_link.get_text(' ', strip=True)
        current_price = clean_text(cells[1])
        change_value = clean_text(cells[2].select_one('span.tah') or cells[2])
        change_rate = clean_text(cells[3].select_one('span.tah') or cells[3])
        trade_volume = clean_text(cells[4])
        trade_amount = clean_text(cells[5])
        market_cap = clean_text(cells[6])

        rows.append({
            '종목명': name,
            '현재가': current_price,
            '전일비': change_value,
            '등락률': change_rate,
            '거래량': trade_volume,
            '거래대금(백만)': trade_amount,
            '시가총액(억)': market_cap,
        })

    return rows


def save_to_csv(rows, filename=CSV_FILE):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return filename


def save_to_excel(rows, filename=XLSX_FILE):
    df = pd.DataFrame(rows, columns=FIELDNAMES)
    df.to_excel(filename, index=False, engine='openpyxl')
    return filename


def get_kospi200_top_stocks():
    main_soup = request_html(URL)
    entry_url = find_entry_url(main_soup)
    entry_soup = request_html(entry_url)
    total_pages = extract_max_page(entry_soup)

    all_rows = []
    for page in range(1, total_pages + 1):
        page_url = f'{ENTRY_URL}&page={page}' if 'page=' not in ENTRY_URL else f"{ENTRY_URL.split('page=')[0]}page={page}"
        page_soup = request_html(page_url)
        page_rows = parse_entry_table(find_entry_table(page_soup))
        all_rows.extend(page_rows)

    return all_rows


if __name__ == '__main__':
    try:
        stocks = get_kospi200_top_stocks()
        csv_filename = save_to_csv(stocks)
        xlsx_filename = save_to_excel(stocks)
        print(f'편입종목상위 전체 페이지 결과 수: {len(stocks)}')
        print(f'CSV 저장 완료: {csv_filename}')
        print(f'XLSX 저장 완료: {xlsx_filename}')
        for stock in stocks[:10]:
            print(stock)
    except Exception as e:
        print(f'오류 발생: {e}')
