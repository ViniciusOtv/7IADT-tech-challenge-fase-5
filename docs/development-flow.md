# Fluxo de desenvolvimento da solução

Este documento descreve o processo de desenvolvimento do `strideai`, a
solução do grupo para o hackathon FIAP Pós Tech — Fase 5 ("Modelagem de
ameaças utilizando IA"). Ele complementa o `README.md` (o que o sistema faz e
como executá-lo) detalhando as decisões técnicas tomadas ao longo da
construção: entendimento do problema, arquitetura, dataset, treinamento,
motor de ameaças e testes.

## 1. Entendimento do problema

O enunciado do desafio (`doc/IADT - Fase 5 - Hackaton.pdf`) exige um MVP que
recebe **uma imagem de diagrama de arquitetura de software** e produz **um
relatório de modelagem de ameaças STRIDE**. Três requisitos são explícitos e
não-negociáveis:

1. Um **modelo supervisionado**, treinado pela própria equipe sobre um
   **dataset construído/coletado e anotado por ela**, capaz de detectar
   componentes de arquitetura na imagem (usuários, servidores, bancos de
   dados, APIs, etc.) — isto é, a tarefa de detecção de objetos não pode ser
   terceirizada a um serviço pronto ou a um LLM multimodal genérico.
2. Um sistema que associe cada componente detectado às suas
   **vulnerabilidades/ameaças e contramedidas específicas**.
3. Um **relatório de modelagem de ameaças STRIDE** gerado a partir dessa
   análise.

A avaliação usa diagramas de referência reais (uma arquitetura AWS
multi-AZ e uma arquitetura Azure API Management, ambas incluídas no PDF do
desafio) como as imagens de teste — ou seja, o sistema precisa generalizar
para diagramas de nuvem "de livro-texto", não apenas para as imagens
sintéticas de treino. Os entregáveis são: documentação do fluxo de
desenvolvimento (este arquivo), um vídeo de até 15 minutos e um repositório
público no GitHub.

Essas restrições moldaram a decisão de arquitetura central: o requisito 1
obriga a existência de um pipeline de treinamento supervisionado real e
auditável; os requisitos 2 e 3 podem, em princípio, ser resolvidos por um
LLM sozinho — mas isso enfraqueceria a exigência de um "sistema que busca
vulnerabilidades por componente" de forma determinística e explicável.

## 2. Decisões de arquitetura

A decisão de arquitetura está registrada em detalhe em
`docs/decisao-arquitetura.md`; esta
seção resume o raciocínio.

**Abordagem escolhida: detector YOLO + base de conhecimento STRIDE
determinística + LLM redator do relatório.**

Pipeline: imagem → YOLO (fine-tuned) detecta os componentes → o motor STRIDE
consulta cada tipo de componente numa base de conhecimento autoral (ameaças
por categoria STRIDE + contramedidas) → um LLM escreve o relatório final em
português, ancorado exclusivamente nesses dados estruturados, com um
*fallback* 100% baseado em template quando o LLM não está disponível.

Racional: o detector supervisionado atende ao requisito obrigatório de
treinamento e anotação; a base de conhecimento torna o mapeamento de ameaças
determinístico, rastreável e fácil de defender no vídeo de apresentação (dá
para apontar exatamente qual regra do YAML gerou qual ameaça); o LLM apenas
organiza e reformula texto, então o risco de alucinação é baixo e o sistema
continua funcionando mesmo sem chave de API.

**Alternativas consideradas e descartadas:**

- *LLM faz todo o raciocínio de ameaças* (envia a imagem ou os componentes
  direto para um LLM multimodal e deixa que ele "invente" as ameaças): mais
  rápido de implementar, porém não-determinístico e enfraquece exatamente o
  requisito explícito de "um sistema que busca vulnerabilidades por
  componente" — se o relatório muda a cada chamada, fica difícil defender a
  cobertura de ameaças no vídeo e nos testes automatizados.
- *Visão computacional clássica / classificação de imagem inteira*: não
  produz uma história de anotação/treinamento real (que é justamente o que é
  avaliado no requisito 1) e tende a ser frágil diante da diversidade visual
  de diagramas de nuvem reais (ícones, cores e layouts variam muito entre
  AWS/Azure/GCP).

**Estrutura do repositório** (monorepo Python único): `dataset/` (geração e
fusão dos dados, em formato YOLO), `training/` (script de fine-tuning,
métricas, pesos), `src/strideai/{detection,stride,report,api,core}` (os
módulos do pipeline), `app/` (Streamlit) e `docs/` (esta documentação).
Contratos compartilhados (`DetectedComponent`, `Threat`, `ThreatModel`,
`AnalysisResponse`, todos em `src/strideai/core/models.py`, usando Pydantic)
permitem que cada módulo seja testado de forma independente: `detection`
contra imagens de fixture, `stride` como funções puras sobre o YAML, e
`report` com um cliente LLM mockado — foi exatamente assim que a suíte de
testes unitários foi construída (Seção 6).

## 3. Construção do dataset

**Taxonomia canônica de 15 classes:** `user`, `web_client`, `api_gateway`,
`load_balancer`, `app_server`, `database`, `cache`, `queue`, `storage`,
`function_serverless`, `firewall_waf`, `auth_service`, `cdn`, `monitoring`,
`external_service` (definida uma única vez em
`src/strideai/core/models.py::COMPONENT_CLASSES`, onde o índice da lista é o
próprio índice de classe usado pelo YOLO). Ícones específicos de provedor
(por exemplo, Amazon RDS e Azure SQL) são mapeados para a mesma classe
canônica (`database`), e a base de conhecimento STRIDE (Seção 5) usa essas
mesmas 15 chaves — ou seja, taxonomia de detecção e taxonomia de ameaças são
a mesma coisa, por construção.

**Três fontes de dados, pensadas para serem construídas em paralelo pela
equipe:**

1. **Geração sintética (`dataset/generate_synthetic.py`):** o script lê uma
   biblioteca de ícones oficiais AWS/Azure/GCP organizada por classe em
   `dataset/icons/<classe>/*.png` (ver `dataset/icons/README.md` para as
   fontes recomendadas e a convenção de pastas) e compõe diagramas
   plausíveis: escolhe uma grade de 3–4 colunas por 2–3 linhas com posições
   levemente aleatórias (*jitter*), cola de 3 até `cols × rows` ícones
   redimensionados, desenha linhas conectoras entre componentes consecutivos
   e escreve um rótulo textual sob cada ícone para dar realismo visual. Como
   o próprio script escolhe as coordenadas de colagem, as anotações YOLO
   (classe + bbox normalizado) são geradas junto, sem custo humano nenhum —
   por isso essa fonte pode produzir centenas de imagens em minutos. Optamos
   por composição direta com PIL em vez da biblioteca `diagrams` porque esta
   última renderiza via Graphviz e não expõe as coordenadas dos ícones
   depois de desenhados, o que inviabilizaria anotações automáticas.
2. **Datasets públicos (opcional):** conjuntos de diagramas de arquitetura e
   ícones de nuvem do Roboflow Universe, importados e remapeados para a
   taxonomia de 15 classes via o arquivo `mapping.yaml` que
   `dataset/build_dataset.py` espera em `dataset/external/`.
3. **Diagramas reais (opcional, ~50–100 imagens):** coletados de
   documentação de arquiteturas de referência AWS/Azure e anotados
   manualmente pela equipe no Roboflow (plano gratuito, exportação em
   formato YOLO), garantindo que o modelo veja o estilo visual real que será
   usado na avaliação.

**Fusão e política de split (`dataset/build_dataset.py`):** as imagens
sintéticas vão inteiramente para o split de treino; as imagens reais
anotadas manualmente (fontes 2 e 3, ambas opcionais — ver
`dataset/external/README.md`) são divididas 50/50 entre validação e teste.
Essa escolha é deliberada: como a avaliação do desafio usa diagramas reais
("de livro-texto"), as métricas de val/test precisam refletir esse estilo de
imagem, não o estilo sintético/gerado — caso contrário, o mAP reportado
mediria principalmente o quão bem o modelo reconhece os próprios diagramas
que ele foi treinado a produzir, não a generalização que o desafio exige.
Como diagramas reais anotados à mão são opcionais e dão trabalho, o script
não bloqueia sem eles: se `dataset/external/` estiver ausente ou vazia,
val/test são extraídos do próprio dataset sintético (10%/10%) para o
pipeline de treino/avaliação rodar de ponta a ponta desde já — só que,
nesse caso, as métricas reportadas são otimistas (o modelo é avaliado em
diagramas do mesmo estilo em que treinou) até que diagramas reais sejam
adicionados. O script também escreve o `data.yaml` consumido pelo Ultralytics (caminhos dos
três splits, número de classes e seus nomes, na ordem canônica).

**Contagens finais do dataset:** _(preencher após o treinamento — número de
imagens e instâncias por classe em cada split de `dataset/final/`)_. Até o
momento deste commit, a biblioteca de ícones (`dataset/icons/`) e os
diagramas reais anotados (`dataset/external/`) ainda não foram populados
pela equipe; esse é o próximo passo humano antes de rodar `training/train.py`
(ver checklist em `training/README.md`).

## 4. Treinamento e avaliação do modelo

**Modelo:** Ultralytics YOLO11s, partindo dos pesos pré-treinados em COCO
(`yolo11s.pt`), ajustado (*fine-tuned*) sobre `dataset/final/data.yaml`
(`training/train.py`). A escolha de um modelo "small" em vez de um maior
prioriza tempo de treino em GPU gratuita (Colab/Kaggle, ~30–60 min por
execução) e velocidade de inferência aceitável para a demo do Streamlit —
como os ícones em diagramas de arquitetura ocupam uma fração pequena da
imagem, a resolução de entrada importa mais do que a capacidade do modelo
para a acurácia final.

**Hiperparâmetros e por quê:**
- `imgsz=1024` (configurável até 1280): diagramas de arquitetura têm muitos
  ícones pequenos lado a lado; aumentar a resolução de entrada ajuda mais a
  detectar esses ícones do que trocar para um modelo maior com imagens
  menores.
- `flipud=0.0` (sem espelhamento vertical): ícones de arquitetura carregam
  significado por orientação (uma seta de banco de dados, um símbolo de
  cadeado) — invertê-los verticalmente criaria exemplos de treino
  visualmente incoerentes.
- `hsv_h=0.005` e `hsv_s=0.2` (variação de matiz mínima, saturação moderada):
  a cor de um ícone frequentemente identifica o provedor/serviço (laranja
  para muitos serviços AWS, azul para Azure); deslocamentos agressivos de
  matiz destruiriam esse sinal.
- `patience=20` (parada antecipada) e `close_mosaic=10` (desliga mosaico nas
  últimas 10 épocas) para estabilizar a convergência final, seguindo prática
  padrão do Ultralytics para datasets pequenos/médios.
- `epochs=100` como teto, com a expectativa de que a parada antecipada
  interrompa antes disso na maioria das execuções.

**Avaliação:** mAP@50 geral e por classe, além da matriz de confusão gerada
pelo Ultralytics, calculados sobre o split de **teste** (diagramas reais,
nunca vistos em treino ou validação) — ver `metrics.box.map50` em
`training/train.py`. A matriz de confusão serve especificamente para
detectar confusões sistemáticas esperadas entre classes visualmente
parecidas (por exemplo, `cache` vs. `database`). Cada execução de
treinamento deve ser registrada em `training/RESULTS.md` (data, contagens do
dataset, hiperparâmetros, mAP50 geral e por classe, observações).

**Critério de aceite:** o pipeline completo deve identificar corretamente os
componentes principais nas duas figuras de avaliação do PDF do desafio — a
arquitetura AWS multi-AZ deve produzir ao menos `user`, `load_balancer`,
`database` e `firewall_waf`; a arquitetura Azure API Management deve
produzir ao menos `user`, `api_gateway` e `external_service`. Essas duas
imagens são mantidas como fixtures de teste (`tests/fixtures/eval_arch{1,2}.png`,
extraídas do PDF por `scripts/extract_eval_figures.py`) e verificadas
automaticamente pelo smoke test de integração (Seção 6).

**Inferência:** limiar de confiança padrão de 0.4, ajustável pelo usuário no
slider da interface Streamlit; detecções abaixo do limiar são simplesmente
descartadas — o sistema nunca "adivinha" um componente com baixa confiança.

**Métricas da execução mais recente:** _(preencher após o treinamento —
mAP50 geral, tabela por classe e matriz de confusão; ver
`training/RESULTS.md`)_. Nenhum treinamento foi executado ainda: `models/`
contém apenas um `.gitkeep`, e os testes de integração que dependem de
`models/best.pt` são pulados automaticamente (`pytest.mark.skipif`) até que
os pesos existam.

## 5. Motor STRIDE e geração do relatório

**Base de conhecimento (`src/strideai/stride/knowledge_base.yaml`):** um
documento YAML com uma entrada por classe canônica (as mesmas 15 da Seção
3), cada uma listando as categorias STRIDE aplicáveis com descrição da
ameaça, severidade (`high`/`medium`/`low`) e uma lista de contramedidas
concretas (ex.: MFA, expiração de sessão, CSP, rate limiting, mTLS,
deny-by-default) inspiradas em fontes reconhecidas de segurança (boas
práticas OWASP e dos próprios provedores de nuvem). O carregador
(`src/strideai/stride/kb.py`) lê o YAML embutido no pacote (via
`importlib.resources`, não um caminho de arquivo absoluto) e o converte em
objetos Pydantic tipados (`Threat`), com cache (`lru_cache`) para evitar
reparsing a cada requisição.

**Motor (`src/strideai/stride/engine.py`):** uma função pura,
`analyze(detections) -> ThreatModel`. Ela primeiro deduplica componentes
repetidos (três load balancers detectados viram uma única seção
`load_balancer` com `instance_count=3`), depois monta a lista de componentes
na ordem canônica das 15 classes (não na ordem de detecção, para o relatório
sair sempre na mesma sequência) e, por fim, aplica um pequeno conjunto de
**regras de composição** extensíveis — cada regra é uma tripla (conjunto que
precisa estar presente, conjunto que precisa estar ausente, mensagem de
aviso em português): por exemplo, "há um `database` mas nenhum
`firewall_waf`" gera um aviso sobre proteção de perímetro ausente; "há
`user` mas nenhum `auth_service`" gera um aviso sobre gerência de
identidade; e a simples presença de `external_service` sempre gera um aviso
sobre a fronteira de confiança sendo cruzada. Cada classe da base de
conhecimento e cada regra têm teste unitário dedicado (`tests/test_kb.py`,
`tests/test_engine.py`).

**Geração do relatório (`src/strideai/report/`):**
- `llm_writer.py` — envia o `ThreatModel` inteiro, serializado como JSON
  (`model_dump_json`), para a API da Anthropic (modelo padrão configurável
  por `STRIDEAI_LLM_MODEL`, `claude-haiku-4-5` por padrão — suficiente e
  barato para uma tarefa de reformulação/organização de texto, não de
  raciocínio aberto). O *system prompt* restringe explicitamente o modelo a
  usar **apenas** os componentes, ameaças e contramedidas presentes no JSON
  recebido — ele pode reformular e organizar, mas a instrução é explícita
  em proibir invenção de componentes, ameaças ou contramedidas novas. Isso
  mantém o relatório final rastreável até a base de conhecimento
  determinística, mesmo passando por um LLM.
- `template_writer.py` — renderiza a mesma estrutura (sumário, avisos de
  arquitetura, ameaças por componente, contramedidas) como Markdown puro via
  Jinja2, sem depender de rede ou chave de API.
- `generator.py` — decide qual caminho usar: sem `ANTHROPIC_API_KEY`
  configurada, ou sem componentes detectados, vai direto para o template;
  com a chave configurada, tenta o LLM e cai para o template
  automaticamente se a chamada falhar por qualquer motivo (`LLMError`). O
  sistema **sempre** produz um relatório, e a origem (`"llm"` ou
  `"template"`) é exposta na resposta da API e mostrada na interface.

## 6. Testes e qualidade

**Unitário (TDD por módulo, `tests/*.py`):** cada módulo do pipeline tem sua
própria suíte, testando os contratos Pydantic (`test_models.py`), a base de
conhecimento (`test_kb.py` — toda classe canônica precisa ter entrada válida
na KB), o motor de regras (`test_engine.py` — deduplicação, ordenação
canônica e cada regra de composição individualmente), o gerador de imagem
sintética (`test_generate_synthetic.py` — biblioteca de ícones só usa
classes conhecidas, labels YOLO válidos, determinismo com seed fixa), a
fusão do dataset (`test_build_dataset.py`), o wrapper de detecção
(`test_detector.py`, com um modelo YOLO mockado), o desenho de anotações
(`test_annotate.py`), os dois caminhos de geração de relatório
(`test_llm_writer.py` com o cliente Anthropic mockado, `test_template_writer.py`,
`test_generator.py` cobrindo a lógica de fallback) e o serviço FastAPI
(`test_api.py` — caminho feliz, upload inválido, zero detecções, proteção
contra imagem "bomba de descompressão"). No total, a suíte tem 43 testes,
sendo 40 unitários (rodam sempre, sem depender de pesos treinados) e 3 de
integração.

**Integração / smoke test (`tests/integration/test_eval_figures.py`):**
sobe a aplicação FastAPI completa com um `ComponentDetector` real apontando
para `models/best.pt` e roda `/analyze` sobre as duas figuras de avaliação
extraídas do PDF do desafio (`scripts/extract_eval_figures.py`), verificando
exatamente o critério de aceite descrito na Seção 4 (componentes-chave
esperados em cada figura, e que um relatório com o título correto é gerado
para ambas). Esses três testes são marcados com `pytest.mark.integration` e
automaticamente pulados (`skipif`) enquanto `models/best.pt` ou as imagens
de fixture não existirem — por isso a suíte "padrão" (`python -m pytest`,
sem marcador) roda limpa em qualquer máquina, mesmo sem GPU ou pesos
treinados, mas o smoke test real só é considerado satisfeito quando rodado
explicitamente com `python -m pytest -m integration -v` após o treinamento.

**CI (`.github/workflows/ci.yml`):** um job `test` roda em todo push/PR —
instala o projeto com `pip install -e .[dev]`, roda `ruff check` sobre
`src`, `tests`, `dataset`, `training`, `scripts` e `app`, e então
`python -m pytest -v` (que exclui os testes de integração via
`addopts = "-m 'not integration'"` em `pyproject.toml`, então esse job nunca
precisa de pesos treinados ou GPU). Um segundo job, `smoke`, só roda quando a
variável de repositório `WEIGHTS_URL` está configurada (isto é, depois que a
equipe treinar o modelo e publicar uma release no GitHub): ele baixa os
pesos com `scripts/download_weights.py`, extrai as figuras de avaliação e
roda a suíte de integração completa — assim o smoke test real também vira
verificação contínua assim que os pesos existirem, sem exigir hardware
específico no runner do GitHub Actions.

## 7. Limitações e próximos passos

- **Fluxos de dados/setas não são detectados como objetos.** O YOLO
  reconhece componentes (ícones), não as conexões entre eles; a análise de
  fronteiras de confiança é aproximada pelas regras de composição do motor
  STRIDE (Seção 5), não por detecção real de arestas/fluxos no diagrama.
  Modelar arrows/fluxos como classes do detector foi conscientemente deixado
  de fora do escopo (custo de anotação alto para o ganho esperado).
- **Cobertura de classes é fixa em 15 tipos canônicos.** Componentes de
  nicho ou ícones de provedores menos comuns que não se encaixem em nenhuma
  das 15 classes (ou no mapeamento manual de `dataset/build_dataset.py`)
  simplesmente não são reconhecidos; a base de conhecimento STRIDE também só
  cobre essas 15 chaves.
- **Exportação em PDF do relatório é um objetivo "stretch", não implementado
  no MVP** — o relatório é entregue e baixável apenas como Markdown.
- **Relatório é gerado apenas em português.** Suporte multi-idioma, contas
  de usuário, persistência e histórico de relatórios ficaram fora do escopo
  do MVP por decisão deliberada (ver Seção 12 — "Out of Scope" — da spec de
  design).
