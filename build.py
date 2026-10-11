#!/usr/bin/env python3
"""Build a public GitHub Pages data file from a published Google Sheets CSV."""
import csv
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

HEADERS = {
    'id': 'ID', 'name': 'Овог, нэр', 'gender': 'Хүйс',
    'birth_year': 'Төрсөн он', 'death_year': 'Нас барсан он',
    'birth_place': 'Төрсөн нутаг', 'twin': 'Ихэр мөн эсэх',
    'father_id': 'Эцгийн ID', 'mother_id': 'Эхийн ID',
    'married': 'Гэрлэсэн эсэх', 'marriage_count': 'Гэрлэлтийн тоо',
    'spouse_id': 'Хань / ID-1', 'spouse_id_2': 'Хань / ID-2',
    'notes': 'Нэмэлт мэдээлэл', 'publish': 'Нийтлэх',
}

def norm(value):
    return re.sub(r'\s+', ' ', (value or '').replace('\ufeff', '').strip()).casefold()

def build(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError('CSV файл хоосон байна.')
    columns = {norm(k): k for k in reader.fieldnames if k is not None}
    required = ['id', 'name', 'gender', 'father_id', 'mother_id', 'spouse_id', 'spouse_id_2']
    absent = [HEADERS[k] for k in required if norm(HEADERS[k]) not in columns]
    if absent:
        raise ValueError('Багана олдсонгүй: ' + ', '.join(absent))

    people = []
    seen = set()
    for line, row in enumerate(reader, start=2):
        if not any(str(v or '').strip() for v in row.values()):
            continue
        get = lambda key: str(row.get(columns.get(norm(HEADERS[key]), ''), '') or '').strip()
        pid, name = get('id'), get('name')
        if not pid or not name:
            raise ValueError(f'{line}-р мөр: ID болон Овог, нэр заавал байх ёстой.')
        if pid in seen:
            raise ValueError(f'{line}-р мөр: Давхардсан ID: {pid}')
        seen.add(pid)
        person = {key: get(key) for key in HEADERS if key != 'publish'}
        people.append(person)
    if not people:
        raise ValueError('Нэг ч хүн олдсонгүй.')
    return people

def main():
    url = os.getenv('SHEETS_CSV_URL', '').strip()
    if not url.startswith('https://docs.google.com/spreadsheets/'):
        sys.exit('SHEETS_CSV_URL нь нийтэлсэн Google Sheets CSV-ийн https холбоос байх ёстой.')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FamilyTreeBuilder/2.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            csv_text = resp.read(8_000_001)
        if len(csv_text) > 8_000_000:
            raise ValueError('CSV 8MB-аас том байна.')
        people = build(csv_text.decode('utf-8-sig'))
        destination = Path('data/people.json')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(people, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Бэлэн: {len(people)} хүн. Нийтийн сайтад нийтлэгдэх JSON үүсгэлээ.')
    except Exception as exc:
        sys.exit(f'Өгөгдөл боловсруулахад алдаа: {exc}')

if __name__ == '__main__':
    main()
