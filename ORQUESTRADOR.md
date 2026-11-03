# Orquestrador — fluxo operacional de atualização do painel

## Objetivo
Uma solicitação única deve produzir: validação da nova base, HTML atualizado, relatório de conferência, Pull Request para revisão, prévia quando disponível e solicitação de aprovação antes de publicar.

## Contrato de entrada
- Arquivo Excel exportado da plataforma, enviado **na conversa do Orquestrador**, e indicação de que é a base oficial.
- Repositório: `prof10/envio-cartoes-respostas`.
- HTML de produção: `Painel_Avalia_Cartoes.html`, branch `main`.
- Nunca pedir ao usuário para reenviar algo já anexado, salvo se o arquivo realmente não estiver acessível.

## Execução pelo Orquestrador (com ferramentas conectadas)

1. **Dados & Inteligência:** carregar o XLSX em ambiente temporário, validar cabeçalhos, consistência de status, totalização, cobertura por escola/UF e diferenças relevantes contra o painel atual. Se houver mudança de universo, registrar a diferença; só bloquear quando a integridade dos dados estiver comprometida. Observar decisão explícita do usuário sobre base oficial.
2. **Dashboards & Sistemas:** obter a versão **atual** do HTML do GitHub, nunca substituí-la cegamente por um arquivo histórico. Atualizar apenas o bloco estruturado de dados e a referência temporal pertinente, sem reescrever layout e lógica. Gerar prévia e relatório de diferenças.
3. **Automações:** executar verificações automáticas, com sumário do resultado; criar **branch separada** a partir da `main` atual e enviar apenas HTML agregado e documentação de revisão. Nunca incluir XLSX, dados pessoais, identificadores ou credenciais no GitHub.
4. **Revisão do Orquestrador:** conferir os resultados com a planilha (totais e percentuais), testar sintaxe, componentes, filtros e responsividade; indicar explicitamente verificações que não puderam ser executadas.
5. **GitHub/Vercel:** criar ou atualizar PR, coletar resultado do GitHub Actions e link de prévia Vercel, quando disponível. A existência de uma prévia não comprova a validação visual.
6. **Aprovação:** apresentar os dados-chave, mudanças, riscos, links de prévia e PR. **Somente publicar/mesclar após aprovação expressa** do usuário para essa versão.

## Limites da integração
- Os Projetos do ChatGPT são ambientes distintos. O Orquestrador **não aciona automaticamente** outros Projetos como processos independentes.
- A coordenação ocorre na própria conversa, usando as ferramentas realmente acessíveis e as regras das competências.
- Não afirmar que executou um teste, criou uma branch, fez deploy ou acionou um especialista sem evidência da execução.
- Se ferramenta faltar ou a transferência do arquivo não for possível, fornecer artefatos e explicar o bloqueio real.
- O repositório é público: revisar o nível de agregação e a autorização institucional para publicação dos dados por escola.

## Entrega final obrigatória
- Base usada, data/hora e total de registros.
- Distribuição por status, enviados e percentual.
- Diferenças relevantes em relação ao painel anterior.
- Verificações feitas e pendentes.
- PR e prévia, se criados.
- Status claro: preparado / em revisão / aprovado / publicado.

## Reutilização
Este é um caso operacional de referência, **não** uma regra universal para todos os dashboards. Outros projetos devem ter seus próprios esquemas e verificações.
