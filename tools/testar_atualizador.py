#!/usr/bin/env python3
"""Teste de ponta a ponta sem dados pessoais: gera um XLSX fictício e roda o atualizador real."""
import collections
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "atualizar_painel.py"

HEADER = {
    "C": "escola", "F": "uf", "G": "atividade",
    "H": "aplicacao_tipo", "I": "enviada",
    "J": "data_envio", "K": "situacao"
}

def make_row(index, fields):
    cells = "".join(
        f'<c r="{column}{index}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
        for column, value in fields.items()
    )
    return f'<row r="{index}">{cells}</row>'

def write_test_xlsx(path):
    records = [make_row(1, HEADER)]
    for i in range(1, 1009):
        statuses = ("Processada", "Processando", "Erro no processamento", "Não enviada")
        status = statuses[(i - 1) % 4]
        uf = "DF" if i <= 504 else "GO"
        fields = {
            "C": "ESCOLA TESTE A" if uf == "DF" else "ESCOLA TESTE B",
            "F": uf, "G": "Avaliação sintética", "H": "Impressa",
            "I": "Não" if status == "Não enviada" else "Sim",
            "J": "" if status == "Não enviada" else "03/11/2026, 13:40:00",
            "K": status
        }
        records.append(make_row(i + 1, fields))
    sheet = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData>' + ''.join(records) + '</sheetData></worksheet>')
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        excel = tmp / "DADOS_FICTICIOS.xlsx"
        write_test_xlsx(excel)
        # Copia o HTML do próprio PR para não testar um modelo diferente do painel real.
        html_path = tmp / "Painel_Avalia_Cartoes.html"
        original = (ROOT / "Painel_Avalia_Cartoes.html").read_bytes()
        html_path.write_bytes(original)
        before = original.decode("utf8")
        marker = "const DATA="
        assert before.count(marker) == 1, "Estrutura original incompatível"
        start = before.index(marker) + len(marker)
        old_data, length = json.JSONDecoder().raw_decode(before[start:])
        assert len(old_data["rows"]) > 0

        (tmp / "tools").mkdir()
        temp_script = tmp / "tools" / "atualizar_painel.py"
        shutil.copy2(SCRIPT, temp_script)
        cmd = [sys.executable, str(temp_script), "--excel", str(excel),
               "--snapshot", "03/11/2026 às 13:40"]
        result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError("Atualizador falhou: " + result.stderr[:1200])

        after = html_path.read_text(encoding="utf8")
        new_data, _ = json.JSONDecoder().raw_decode(after[start:])
        rows = new_data["rows"]
        counts = collections.Counter()
        for uf, school, activity, status, kind, amount in rows:
            counts[status] += amount
        assert sum(counts.values()) == 1008, counts
        assert counts == {"Processada": 252, "Processando": 252,
                          "Erro no processamento": 252, "Não enviada": 252}, counts
        assert len(rows) == 8, f"Grupos incorretos: {len(rows)}"
        # Não permite reescrever HTML/CSS/JS fora do JSON e data da fotografia.
        assert after.count('id="schoolrows"') == before.count('id="schoolrows"')
        assert after.count('id="schedule"') == before.count('id="schedule"')
        report = json.loads((tmp / "validacao_atualizacao.json").read_text(encoding="utf8"))
        assert report["base"]["total"] == 1008, report
        assert report["publicado"] is False
        print("Teste end-to-end aprovado: 1008 registros fictícios, todos os status e relatório consistentes.")

if __name__ == "__main__":
    main()
