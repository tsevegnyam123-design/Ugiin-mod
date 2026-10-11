#!/usr/bin/env python3
"""Fetch a PUBLISHED Google Sheets CSV, map 15 columns to public JSON."""
import csv, io, json, os, urllib.request, pathlib
URL = os.environ.get('SHEETS_CSV_URL', '').strip()
if not URL.startswith('https://'):
    raise SystemExit('Set SHEETS_CSV_URL to the published CSV URL (https://...)')
req = urllib.request.Request(URL, headers={'User-Agent':'family-tree-builder/1.0'})
with urllib.request.urlopen(req, timeout=25) as response:
    raw = response.read(8_000_001)
if len(raw) > 8_000_000:
    raise SystemExit('CSV too large')
content = raw.decode('utf-8-sig')
reader = csv.DictReader(io.StringIO(content))
required = ['ID','Овог, нэр','Хүйс','Төрсөн он','Нас барсан он','Төрсөн нутаг','Ихэр мөн эсэх','Эцгийн ID','Эхийн ID','Гэрлэсэн эсэх','Гэрлэлтийн тоо','Хань / ID-1','Хань / ID-2','Нэмэлт мэдээлэл','Нийтлэх']
reader.fieldnames = [str(x or '').strip() for x in (reader.fieldnames or [])]
missing = [x for x in required if x not in reader.fieldnames]
if missing:
    raise SystemExit('Missing Google Sheets columns: '+', '.join(missing))
fields = {'ID':'id','Овог, нэр':'name','Хүйс':'gender','Төрсөн он':'birth','Нас барсан он':'death','Төрсөн нутаг':'birthplace','Ихэр мөн эсэх':'twin','Эцгийн ID':'father','Эхийн ID':'mother','Гэрлэсэн эсэх':'married','Гэрлэлтийн тоо':'marriages','Хань / ID-1':'spouse1','Хань / ID-2':'spouse2','Нэмэлт мэдээлэл':'notes'}
people=[]; ids=set()
for row_no,row in enumerate(reader,start=2):
    p={v:(row.get(k) or '').strip() for k,v in fields.items()}
    if not p['id'] and not p['name']:
        continue
    if not p['id'] or not p['name']:
        raise SystemExit(f'Row {row_no}: ID and name required')
    if p['id'] in ids:
        raise SystemExit(f'Row {row_no}: duplicate ID {p["id"]}')
    ids.add(p['id']); people.append(p)
# All rows, including Нийтлэх = Үгүй, per requested configuration.
pathlib.Path('data').mkdir(exist_ok=True)
pathlib.Path('data/people.json').write_text(json.dumps(people,ensure_ascii=False,indent=2), encoding='utf-8')
print(f'Wrote {len(people)} records. WARNING: published publicly on GitHub Pages.')
