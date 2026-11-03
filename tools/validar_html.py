#!/usr/bin/env python3
"""Verificação sem dependências: estrutura HTML e consistência de contagens."""
import collections
import json
import re
from pathlib import Path

path = Path('Painel_Avalia_Cartoes.html')
s = path.read_text(encoding='utf-8')
assert s.count('const DATA=') == 1, 'Marcador DATA deve existir exatamente uma vez'
start = s.index('const DATA=') + len('const DATA=')
data, _ = json.JSONDecoder().raw_decode(s[start:])
rows = data['rows']
assert rows and all(len(row)==6 for row in rows), 'Registros inválidos'
totals = collections.Counter()
for uf, school, activity, state, kind, amount in rows:
    assert uf and school and activity, 'Identificação de grupo ausente'
    assert state in ('Não enviada','Processada','Processando','Erro no processamento'), state
    assert isinstance(amount,int) and amount>0, 'Contagem inválida'
    totals[state] += amount
assert sum(totals.values()) > 1000, 'Base vazia/incompleta'
for element in ('id="schoolrows"', 'id="schedule"'):
    assert s.count(element) == 1, f'Componente ausente ou duplicado: {element}'
# Não exibir nem enviar dados de grupos individuais nos logs.
print('Validação concluída. Total:',sum(totals.values()),' | Status:',dict(totals))
