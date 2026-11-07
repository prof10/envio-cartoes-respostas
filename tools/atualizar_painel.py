#!/usr/bin/env python3
"""Atualiza os dados agregados do painel com uma planilha XLSX da plataforma.
Não envia o Excel ao GitHub, não faz commit nem deploy.
Uso: python tools/atualizar_painel.py --excel "C:\caminho\monitoramento.xlsx"
"""
import argparse
import collections
import datetime
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "Painel_Avalia_Cartoes.html"
REQUIRED = {'C': 'escola', 'F': 'uf', 'G': 'atividade', 'H': 'aplicacao_tipo', 'I': 'enviada', 'K': 'situacao'}
CELL = re.compile(rb'<c r="([A-Z]+)[0-9]+"([^>]*)>(.*?)</c>', re.S)
INLINE = re.compile(rb'<t(?:\s[^>]*)?>(.*?)</t>', re.S)
VALUE = re.compile(rb'<v>(.*?)</v>', re.S)

def rows_from_xlsx(path):
    with zipfile.ZipFile(path) as z:
        if 'xl/sharedStrings.xml' in z.namelist():
            raise ValueError('Formato de Excel alterado (sharedStrings); requer validação manual.')
        with z.open('xl/worksheets/sheet1.xml') as stream:
            buf = b''
            while True:
                chunk = stream.read(4 * 1024 * 1024)
                chunks = (buf + chunk).split(b'</row>')
                buf = chunks.pop() if chunk else b''
                for raw in chunks:
                    if b'<row ' not in raw:
                        continue
                    raw = raw[raw.rfind(b'<row '):]
                    fields = {}
                    for m in CELL.finditer(raw):
                        col = m.group(1).decode()
                        if col not in REQUIRED and col != 'J':
                            continue
                        cm = INLINE.search(m.group(3)) or VALUE.search(m.group(3))
                        if cm:
                            fields[col] = html.unescape(cm.group(1).decode('utf8')).strip()
                    yield fields
                if not chunk:
                    break

def status(send, st):
    x = st.casefold().strip()
    if not x or x in ('null', 'none'):
        return 'Não enviada' if send.casefold() != 'sim' else 'Status ausente'
    if 'erro' in x:
        return 'Erro no processamento'
    if x.startswith('processada'):
        return 'Processada'
    if x.startswith('processando'):
        return 'Processando'
    if send.casefold() != 'sim':
        return 'Não enviada'
    return 'Outro: ' + st

def aggregate(path):
    it = rows_from_xlsx(path)
    headings = next(it)
    for col, expected in REQUIRED.items():
        if headings.get(col, '').casefold() != expected:
            raise ValueError(f'Cabeçalho inesperado em {col}: {headings.get(col)!r}')
    count = collections.Counter()
    totals = collections.Counter()
    schools, ufs = set(), set()
    warnings = collections.Counter()
    n = 0
    for f in it:
        uf, school, activity, kind, sent, state = (f.get(c, '') for c in ('F', 'C', 'G', 'H', 'I', 'K'))
        if not any((uf, school, activity, kind, sent, state)):
            continue
        if not uf or not school or not activity:
            raise ValueError(f'Registro sem UF, escola ou atividade, linha aproximada {n+2}')
        if sent.casefold() not in ('sim', 'não', 'nao'):
            raise ValueError(f'Enviada inesperado: {sent!r}')
        st = status(sent, state)
        if st not in ('Não enviada', 'Processada', 'Processando', 'Erro no processamento'):
            raise ValueError(f'Situação inesperada: {st!r}')
        if (sent.casefold() == 'sim') != (st != 'Não enviada'):
            warnings['Envio e situação divergentes'] += 1
        if sent.casefold() == 'sim' and not f.get('J'):
            warnings['Enviados sem data'] += 1
        count[(uf, school, activity, st, kind)] += 1
        totals[st] += 1
        schools.add((uf, school))
        ufs.add(uf)
        n += 1
    if n < 1000:
        raise ValueError(f'Exportação incompleta? Apenas {n} registros.')
    return [[*key, value] for key, value in sorted(count.items())], {
        'total': n, 'escolas': len(schools), 'regionais': len(ufs),
        'status': dict(totals), 'alertas': dict(warnings),
        'arquivo_origem': path.name, 'sha256_origem': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    }

def update(template, rows, stamp):
    marker = 'const DATA='
    if template.count(marker) != 1:
        raise ValueError('Marcador DATA incompatível. Não substituir HTML.')
    start = template.index(marker) + len(marker)
    previous, length = json.JSONDecoder().raw_decode(template[start:])
    if not isinstance(previous, dict) or not isinstance(previous.get('rows'), list):
        raise ValueError('Formato DATA incompatível')
    payload = json.dumps({'rows': rows}, ensure_ascii=False, separators=(',', ':'))
    new = template[:start] + payload + template[start + length:]
    dates = re.findall(r'\b\d{2}/\d{2}/2026 às \d{2}:\d{2}\b', new)
    if dates:
        new = new.replace(dates[0], stamp, 1)
    for element in ('id="schoolrows"', 'id="schedule"'):
        if template.count(element) != new.count(element):
            raise ValueError('Componente HTML alterado: ' + element)
    return new

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--excel', required=True, type=Path)
    p.add_argument('--snapshot', default=None, help='Ex.: 03/11/2026 às 13:40')
    p.add_argument('--dry-run', action='store_true', help='Valida e gera relatório, sem alterar o HTML')
    a = p.parse_args()
    if not a.excel.is_file():
        raise ValueError('Excel não encontrado: ' + str(a.excel))
    rows, info = aggregate(a.excel)
    snapshot = a.snapshot or datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')
    original = PANEL.read_text(encoding='utf8')
    updated = update(original, rows, snapshot)
    report_file = ROOT / 'validacao_atualizacao.json'
    report = {'status':'VALIDADO', 'publicado':False, 'data_extracao':snapshot, 'base':info,
              'grupos':len(rows), 'html_alterado':updated!=original}
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    if not a.dry_run:
        PANEL.write_text(updated, encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('Prévia local preparada. Não foi feito deploy nem commit.')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('ERRO:', e, file=sys.stderr)
        sys.exit(1)
