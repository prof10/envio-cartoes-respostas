# Automação do painel — piloto

Este repositório tem um painel HTML e um atualizador local de dados. O objetivo é receber um Excel exportado da plataforma, validar, atualizar **somente os dados agregados** do HTML e levar a alteração à revisão antes da publicação.

## Como usar no computador (Python 3)

1. Baixe/clone o repositório. Execute com a branch principal atualizada.
2. Guarde o Excel em uma pasta **fora do repositório**: ele pode conter informações pessoais.
3. Valide sem alterar o painel:
   \`python tools/atualizar_painel.py --excel "C:\caminho\monitoramento.xlsx" --dry-run\`
4. Confira o resumo de validação. Em seguida, execute sem \`--dry-run\` para atualizar o HTML.
5. Abra o HTML localmente e confira indicadores, filtros, escola, prazos e apresentação mobile.
6. Use uma branch de revisão e um Pull Request. **Não faça commit do XLSX nem publique diretamente na main.**
7. A Vercel pode gerar uma prévia a partir do PR se a integração Git estiver habilitada. A produção só deve ser atualizada após aprovação.

## Conferência automatizada

O workflow \`Validar painel HTML\` valida a estrutura e contagens quando um Pull Request altera o painel. Isso **não substitui** o teste visual e funcional no navegador.

## Limites

- A exportação deve preservar a estrutura de colunas e células \`inlineStr\` atual. Alterações de formato bloqueiam a atualização.
- O painel atualmente mostra dados agregados por escola, atividade e situação. O Excel bruto não deve ser publicado.
- O repositório é público: antes de qualquer PR, verificar a divulgação permitida de informações por escola.
- Este fluxo é uma **automação de processamento e validação**, não uma comunicação autônoma entre Projetos do ChatGPT.
