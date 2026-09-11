import re

import requests
from bs4 import BeautifulSoup

URL = 'https://finance.naver.com/sise/sise_index.naver?code=KPI200'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}


def get_entry_table(soup):
    """h4 제목 '편입종목상위'를 기준으로 정확한 표를 찾는다."""
    title_pattern = re.compile(r'편입종목.*상위', re.IGNORECASE)

    for h4 in soup.find_all('h4', class_='top_tlt'):
        if title_pattern.search(h4.get_text(' ', strip=True)):
            parent = h4.parent
            table = parent.select_one('table.type_1')
            if table:
                return table

    for div in soup.select('div.box_type_m'):
        h4 = div.find('h4', class_='top_tlt')
        if h4 and title_pattern.search(h4.get_text(' ', strip=True)):
            table = div.select_one('table.type_1')
            if table:
                return table

    for table in soup.select('table.type_1'):
        header = [th.get_text(' ', strip=True) for th in table.select('th')]
        if '종목별' in header and '현재가' in header and '등락률' in header:
            return table

    raise ValueError('편입종목상위 테이블을 찾지 못했습니다.')


def clean_text(cell):
    if cell is None:
        return ''
    return cell.get_text(' ', strip=True)


def parse_rows(table):
    """표에서 종목 데이터 추출"""
    data = []

    for row in table.select('tr'):
        if not row.select('td.ctg a'):
            continue

        cells = row.select('td')
        if len(cells) < 7:
            continue

        name = cells[0].select_one('a').get_text(' ', strip=True)
        current_price = clean_text(cells[1])

        change_text = clean_text(cells[2].select_one('span.tah'))
        if not change_text:
            change_text = clean_text(cells[2])

        rate_text = clean_text(cells[3].select_one('span.tah'))
        if not rate_text:
            rate_text = clean_text(cells[3])

        volume = clean_text(cells[4])
        trading_value = clean_text(cells[5])
        market_cap = clean_text(cells[6])

        data.append({
            '종목명': name,
            '현재가': current_price,
            '전일비': change_text,
            '등락률': rate_text,
            '거래량': volume,
            '거래대금(백만)': trading_value,
            '시가총액(억)': market_cap,
        })

    return data


def get_kospi200_top_stocks():
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    table = get_entry_table(soup)
    if table is None:
        raise ValueError('편입종목상위 테이블을 찾지 못했습니다.')

    return parse_rows(table)


if __name__ == '__main__':
    try:
        stocks = get_kospi200_top_stocks()
        print(f'편입종목상위 결과 수: {len(stocks)}')
        for item in stocks[:10]:
            print(item)
    except Exception as e:
        print('오류 발생:', e)
