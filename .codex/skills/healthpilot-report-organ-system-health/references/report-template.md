# Relatório de saúde dos órgãos e sistemas — {nome_do_perfil}

**Relatório gerado:** {AAAA-MM-DD HH:MM FUSO}
**Perfil:** {nome_do_perfil}
**Data-limite dos registos:** {data mais recente da evidência analisada}
**Instantâneo de evidência:** {id_do_instantâneo} às {data_hora_do_instantâneo}
**Relatório comparável anterior:** {nome do ficheiro ou nenhum}
**Gravidade das lacunas nas fontes:** {nenhuma | ligeira | material | crítica}

> As pontuações usam uma grelha de priorização Healthpilot não validada. Não são diagnósticos, probabilidades, classificações clínicas nem comparações com outras pessoas.

## Sistemas com pontuação mais baixa

| Posição | Sistema | Pontuação | Intervalo plausível | Enquadramento de confiança | Confiança na evidência | Fator principal | Urgência | Próximo dado útil |
|---:|---|---:|---:|---|---|---|---|---|
| 1 | {sistema} | {N.N}/10 | {L–H} | {enquadramento} | {alta/moderada/baixa} | {compromisso/incerteza/misto} | {urgência} | {teste ou reconciliação} |

## Alterações desde o relatório anterior

{No primeiro relatório, use a frase de referência exata. Caso contrário, classifique as alterações de pontuação como Adicionadas, Alteradas, Resolvidas ou Inalteradas e cite os IDs de evidência atuais.}

## Significado das pontuações

- `10` = saúde excecional diretamente sustentada por evidência da estrutura, função, sintomas, controlo da doença e evolução.
- `5` = ponto médio neutro/indeterminado quando a evidência é insuficiente ou mista; não significa 50% de saúde.
- `0` = falência crítica aguda diretamente sustentada por evidência.
- Interpretar cada pontuação juntamente com o intervalo plausível e a confiança na evidência.

## Contexto do estado atual

### Condições ativas

{Condições ativas ou em monitorização, com enquadramentos de confiança.}

### Medicação e tratamentos atuais considerados

{Regime atual reconciliado ou evidência que precisa de reconciliação.}

## Pontuações dos sistemas por ordem

| Posição | Órgão/sistema | Pontuação de saúde | Intervalo plausível | Confiança na evidência | Fator principal | Evidência ou lacuna principal |
|---:|---|---:|---:|---|---|---|
| 1 | {sistema canónico com pontuação mais baixa} | {N.N}/10 | {L–H} | {confiança} | {fator} | {citação segura ou lacuna} |
| … | {os 16 sistemas canónicos por ordem crescente de pontuação} | {N.N}/10 | {L–H} | {confiança} | {fator} | {evidência} |
| 16 | {sistema canónico com pontuação mais alta} | {N.N}/10 | {L–H} | {confiança} | {fator} | {evidência} |

## Pontuações detalhadas dos órgãos e subsistemas

| Sistema principal | Órgão ou subsistema | Pontuação de saúde | Intervalo plausível | Confiança na evidência | Fator principal | Evidência ou lacuna principal |
|---|---|---:|---:|---|---|---|
| {sistema principal} | {órgão/subsistema obrigatório} | {N.N}/10 | {L–H} | {confiança} | {fator} | {evidência} |

## Cinco sistemas com pontuação mais baixa

### 1. {Sistema} — {N.N}/10 ({L–H})

- **Conclusão de trabalho:** {conclusão}
- **Enquadramento de confiança:** {conclusão clara | diagnóstico provável | diagnóstico diferencial | questão em aberto}
- **Confiança na evidência:** {alta | moderada | baixa}
- **Urgência:** {imediata | breve | rotina | monitorização}
- **Fator principal:** {compromisso | incerteza | misto | saúde sustentada por evidência}
- **Pontuações por dimensão:** estrutura {N}/2; função {N}/2; sintomas/impacto {N}/2; doença/controlo {N}/2; evolução/reserva {N}/2
- **Evidência observada a favor:** {IDs de evidência datados}
- **Evidência tranquilizadora ou contraditória:** {IDs de evidência datados}
- **Dados em falta que alterariam a pontuação:** {dados}
- **Passo seguinte:** {teste, monitorização ou discussão com especialista}
- **Resultado que mais alteraria a pontuação:** {resultado}

{Repetir para as posições 2–5.}

## Achados transversais aos sistemas

- {Sinal sistémico, local principal da pontuação, relevância noutros sistemas e controlo de dupla contagem.}

## Lacunas de evidência

1. {Lacuna com maior impacto e sistemas afetados.}

## Apêndice de evidência

### Cobertura das fontes

| Fonte | Estado | Atualidade / período | Sistemas informados | Limitação ou impacto na incerteza |
|---|---|---|---|---|
| {fonte} | {disponível/em falta/ilegível/não configurada} | {data ou período} | {sistemas} | {limitação} |

**Fontes indisponíveis:** {lista ou `Nenhuma`}

### Notas de segurança

- {Sinal de alarme urgente ou `Não foi identificado qualquer sinal de falência aguda de órgão nos registos disponíveis.`}

### Limitações

- {Evidência em falta, pontuação da incerteza, horizonte de saúde atual e impossibilidade de comparação entre pessoas.}

### Referências de evidência

- {ID de evidência seguro}: {descrição datada; nunca um caminho absoluto}
