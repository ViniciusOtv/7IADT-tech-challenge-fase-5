# Decisão de Arquitetura: Modelagem de Ameaças STRIDE com IA a partir de Diagramas de Arquitetura

**Data:** 2026-07-06
**Contexto:** FIAP Pós Tech — Hackathon da Fase 5 ("Modelagem de ameaças utilizando IA")
**Requisitos de origem:** `doc/IADT - Fase 5 - Hackaton.pdf`

## 1. Problema e Objetivo

Construir um MVP que recebe **um diagrama de arquitetura de software como imagem** e produz automaticamente um **relatório de modelagem de ameaças STRIDE**. O desafio exige explicitamente:

1. Um **modelo supervisionado**, treinado por nós em um dataset que construímos/coletamos **e anotamos**, que detecta componentes de arquitetura em imagens de diagramas (usuários, servidores, bancos de dados, APIs etc.).
2. Um sistema que mapeia cada componente detectado às suas **vulnerabilidades/ameaças e contramedidas específicas**.
3. Um **relatório de modelagem de ameaças STRIDE** gerado.

A avaliação usará diagramas de referência de nuvem reais, semelhantes às duas figuras do PDF (uma arquitetura AWS multi-AZ e uma arquitetura Azure API Management). Entregáveis: documentação do fluxo de desenvolvimento, um vídeo (≤15 min) e um repositório público no GitHub.

**Restrições estabelecidas:**
- 2–4 semanas, projeto em equipe (o trabalho pode ser paralelizado).
- Uso de API de LLM paga é aceitável.
- Interface: UI web em Streamlit apoiada por um serviço FastAPI.

## 2. Abordagem Escolhida

**Detector YOLO + base de conhecimento STRIDE determinística + gerador de relatório via LLM.**

Pipeline: imagem → YOLO ajustado detecta componentes → o motor STRIDE consulta cada tipo de componente em uma base de conhecimento redigida manualmente (ameaças por categoria STRIDE + contramedidas) → o LLM escreve o relatório narrativo final baseado exclusivamente nesses dados estruturados, com uma alternativa em template puro.

Racional: o detector supervisionado atende ao requisito obrigatório de treinamento/anotação; a base de conhecimento torna o mapeamento de ameaças determinístico, rastreável e defensável no vídeo; o LLM apenas organiza e reformula, então o risco de alucinação é mínimo e o sistema continua funcionando sem uma chave de API.

Alternativas rejeitadas:
- *O LLM faz todo o raciocínio de ameaças:* mais rápido, porém não determinístico e enfraquece o requisito explícito de "sistema que busca vulnerabilidades por componente".
- *Visão computacional clássica / classificação:* não atende de fato ao requisito de treinamento/anotação (que é o que é avaliado) e é frágil em diagramas de nuvem reais.

## 3. Arquitetura e Estrutura do Repositório

Monorepo único em Python:

```
tech-challenge-fase-5/
├── dataset/            # scripts de geração/download + anotações (formato YOLO)
├── training/           # scripts de fine-tuning, métricas de avaliação, RESULTS.md, pesos exportados
├── src/
│   ├── detection/      # carrega os pesos; imagem -> list[DetectedComponent]
│   ├── stride/         # knowledge_base.yaml + motor: componentes -> ThreatModel
│   ├── report/         # cliente LLM + alternativa Jinja2: ThreatModel -> Markdown
│   └── api/            # FastAPI: POST /analyze, GET /health
├── app/                # UI Streamlit
└── docs/               # documentação do fluxo de desenvolvimento (entregável avaliado)
```

**Fluxo de dados:** o Streamlit envia a imagem para `POST /analyze` → `detection` retorna componentes tipados com caixas delimitadoras e confiança → `stride` mapeia os tipos de componente para ameaças/contramedidas a partir do KB em YAML → `report` produz a narrativa (LLM, com fallback para template) → a resposta carrega a imagem anotada, o JSON estruturado do modelo de ameaças e o relatório em Markdown.

**Contratos:** modelos Pydantic compartilhados — `DetectedComponent` (classe, bbox, confiança), `Threat` (categoria, descrição, severidade, contramedidas), `ThreatModelReport`. Cada unidade é testável de forma independente: `detection` contra imagens de fixture, `stride` como funções puras sobre o YAML, `report` com um cliente LLM simulado (mock).

## 4. Dataset e Anotação

**Taxonomia canônica (~15 classes):** `user`, `web_client`, `api_gateway`, `load_balancer`, `app_server`, `database`, `cache`, `queue`, `storage`, `function_serverless`, `firewall_waf`, `auth_service`, `cdn`, `monitoring`, `external_service`. Ícones específicos de provedor (AWS, Azure, GCP, formas genéricas) são mapeados para essas classes — por exemplo, Amazon RDS e Azure SQL são ambos `database`. O KB do STRIDE usa essas mesmas classes como chave.

**Três fontes, construídas em paralelo:**

1. **Geração sintética (em massa):** um script compõe arquiteturas plausíveis e aleatórias posicionando ícones oficiais AWS/Azure/GCP em um canvas com PIL (desenhando linhas de conexão e rótulos). As posições dos ícones são escolhidas pelo script, então as anotações de bounding box saem gratuitamente. Aumentado com variedade de layout, ruído de fundo, compressão JPEG e escala. (A composição via PIL é usada em vez da biblioteca `diagrams` porque `diagrams` renderiza via Graphviz e não expõe as coordenadas dos ícones.)
2. **Datasets públicos:** datasets de diagramas de arquitetura e ícones de nuvem do Roboflow Universe, importados e remapeados para nossa taxonomia.
3. **Diagramas reais (~50–100):** coletados de documentações e blogs de arquiteturas de referência AWS/Azure, anotados manualmente pela equipe no Roboflow (tier gratuito, exportação YOLO).

**Disciplina de divisão (split):** diagramas reais predominam em validação/teste; os dados sintéticos ficam principalmente no treino, de forma que as métricas reportadas reflitam o desempenho em imagens no estilo dos avaliadores. Meta: ~1.000+ imagens de treino, ~100 de val/teste.

## 5. Treinamento e Avaliação do Modelo

- **Modelo:** Ultralytics YOLO11s (ou YOLOv8s), ajustado a partir de pesos pré-treinados no COCO, no Google Colab/Kaggle com GPU gratuita (~30–60 min/execução). Os pesos (`best.pt`, ~20 MB) são versionados no repositório ou anexados como release do GitHub — o avaliador nunca precisa retreinar.
- **Configuração:** ~100 épocas com early stopping; imgsz 960–1280 (muitos ícones pequenos — resolução vence tamanho do modelo); augmentation padrão sem flips verticais e sem grandes variações de matiz/HSV (ícones têm significado de orientação e cor); mosaico ligado, desativado nas épocas finais.
- **Avaliação:** mAP@50 e precisão/recall por classe no conjunto de teste com diagramas reais; matriz de confusão para identificar confusões sistemáticas (ex.: `cache` vs `database`). Execuções, métricas e versões de dataset registradas em `training/RESULTS.md`.
- **Critério de aceite:** o pipeline identifica corretamente os principais componentes nas duas figuras de avaliação do PDF, mantidas como fixtures nomeadas de smoke test com verificação automatizada.
- **Inferência:** limiar de confiança ~0.4 (ajustável pelo usuário na UI); detecções abaixo do limiar são descartadas, nunca "chutadas".

## 6. Motor STRIDE

`src/stride/knowledge_base.yaml`: uma entrada por classe canônica listando as categorias STRIDE aplicáveis, cada uma com descrição da ameaça, severidade (alta/média/baixa) e contramedidas concretas citando fontes reconhecidas (OWASP ASVS/cheat sheets, boas práticas de segurança dos provedores de nuvem).

Motor: função pura em Python `analyze(components) -> ThreatModel`.
- Deduplica tipos de componente repetidos (três load balancers → uma seção `load_balancer` indicando 3 instâncias).
- **Regras de composição** (conjunto pequeno e extensível): ex.: banco de dados presente mas sem `firewall_waf` → sinaliza ausência de defesa de perímetro; `user` presente → ameaças de spoofing/autenticação sempre incluídas.
- Determinístico e testado unitariamente: toda classe do KB deve produzir ameaças; toda regra tem um teste.

## 7. Geração do Relatório

- **Caminho via LLM:** a API da Anthropic (um modelo econômico, classe Haiku, é suficiente) recebe o JSON estruturado do ThreatModel e escreve o relatório **em português**: sumário executivo, tabela de componentes detectados, seções STRIDE por componente, contramedidas priorizadas. O prompt restringe o modelo a apenas organizar/reformular as ameaças fornecidas — ele não pode inventar componentes ou ameaças.
- **Caminho alternativo (fallback):** se a chave de API estiver ausente ou a chamada falhar, um template Jinja2 renderiza a mesma estrutura como Markdown puro. O sistema sempre produz um relatório.
- **Saída:** Markdown sempre; exportação em PDF é uma meta secundária (stretch goal).

## 8. API e UI

**FastAPI:**
- `POST /analyze` (imagem multipart) → JSON: `components` (classe, bbox, confiança), `threat_model` (dados STRIDE estruturados), `report_markdown`, imagem anotada em base64.
- `GET /health`.
- Documentação Swagger embutida. `docker-compose.yml` sobe API + Streamlit com um único comando.

**Streamlit (página única):** upload → imagem original vs. anotada lado a lado → tabela de componentes → relatório STRIDE renderizado com download em `.md`. Barra lateral: slider de limiar de confiança e as duas figuras de avaliação do PDF como exemplos prontos para testar.

## 9. Tratamento de Erros

- Upload que não é imagem/corrompido → 422 com mensagem clara.
- Zero componentes detectados → 200 com um relatório honesto de "nenhum componente reconhecido", nunca uma análise fabricada.
- Falha do LLM → alternativa em template (Seção 7).
- Imagens muito grandes são reduzidas antes da inferência.

## 10. Testes

- **Unitários:** motor STRIDE (cobertura do KB por classe, regras de composição), renderização da alternativa de relatório, pós-processamento da detecção.
- **Teste de integração (smoke test):** pipeline completo nas duas figuras de avaliação do PDF, verificando que os componentes-chave esperados são encontrados (ex.: a Figura 1 deve produzir `load_balancer`, `database`, `firewall_waf`, `user`).
- **CI:** GitHub Actions rodando lint + testes; pesos do modelo obtidos de uma release do GitHub para o smoke test.

## 11. Mapeamento dos Entregáveis

| Entregável do desafio | Artefato |
|---|---|
| Documentação do fluxo de desenvolvimento | `docs/` — construção do dataset, anotação, execuções de treinamento, métricas, decisões de arquitetura (escrito ao longo do projeto) |
| Vídeo de até 15 min | Roteiro de demonstração no README; demo do Streamlit nas figuras do PDF |
| Link do GitHub | Repositório público com pesos/release versionados, execução com um comando via docker-compose |

## 12. Fora de Escopo (YAGNI)

- Detectar setas de fluxo de dados/fronteiras de confiança como classes do modelo (as regras de composição aproximam o valor com custo de anotação muito menor).
- Relatórios em múltiplos idiomas (apenas português).
- Contas de usuário, persistência, histórico de relatórios.
- Exportação em PDF (apenas meta secundária).
