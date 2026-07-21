# Treinamento do detector

## Local (GPU) 
    pip install -e .
    python dataset/generate_synthetic.py --count 800
    python dataset/build_dataset.py
    python training/train.py

## Google Colab (GPU gratuita)

Pré-requisito: o repositório precisa estar publicado no GitHub (o nosso é público em
`https://github.com/ViniciusOtv/7IADT-tech-challenge-fase-5`). Não é preciso zipar e
subir o dataset manualmente — a biblioteca de ícones (`dataset/icons/`) já está
versionada no repositório, então o dataset sintético pode ser gerado direto dentro do
Colab.

1. Abra https://colab.research.google.com, crie um notebook novo e ative a GPU em
   `Ambiente de execução > Alterar tipo de ambiente de execução > GPU`.

2. Clone o repositório:

       !git clone https://github.com/ViniciusOtv/7IADT-tech-challenge-fase-5.git
       %cd 7IADT-tech-challenge-fase-5

3. Instale o projeto:

       !pip install -q -e .

4. Gere o dataset sintético a partir dos ícones já versionados no repositório:

       !python dataset/generate_synthetic.py --count 800

5. Funda os dados sintéticos (e os reais anotados, se `dataset/external/` estiver
   populado) no dataset final, e confira se ele foi criado:

       !python dataset/build_dataset.py
       !ls dataset/final

   (esse passo é fácil de esquecer — sem ele, `dataset/final/data.yaml` não existe e
   o treino falha com `FileNotFoundError`)

6. Confirme que a GPU está disponível:

       import torch
       print(torch.cuda.is_available(), torch.cuda.get_device_name(0))

7. Treine:

       !python training/train.py --data dataset/final/data.yaml --batch 32

   Como o `data.yaml` foi gerado dentro do próprio Colab (passo 5), o caminho `path:`
   já sai correto — não precisa editar nada manualmente. O treino roda até
   `epochs=100` ou até o early stopping (`patience=20`) interromper antes disso; ao
   final, o script imprime `test mAP50: 0.XXXX`.

8. Salve os artefatos no Drive antes de encerrar a sessão — tudo em `/content` é
   apagado quando o runtime desconecta:

       from google.colab import drive
       drive.mount('/content/drive')
       !cp runs/detect/strideai/weights/best.pt /content/drive/MyDrive/best.pt
       !cp runs/detect/val/confusion_matrix.png /content/drive/MyDrive/confusion_matrix.png

9. Baixe os dois arquivos do Drive (ou pelo painel de arquivos à esquerda no Colab) e
   coloque, no projeto local:
   - `best.pt` em `models/best.pt`
   - `confusion_matrix.png` em `training/confusion_matrix.png`

   Alternativa para distribuir `best.pt` sem depender do Drive: anexá-lo a uma
   *release* do GitHub e usar
   `python scripts/download_weights.py --url <url-da-release>`.

10. Preencha `training/RESULTS.md` com data, contagem do dataset por split (aparece
    no log de treino como `train: ... N images`, idem para `val`/`test`), número de
    épocas efetivamente rodadas (log `EarlyStopping` ou `N epochs completed`),
    `mAP50 (test)` e a tabela por classe — ambos aparecem perto do fim do log, no
    bloco `Validating .../weights/best.pt...` referente ao split de teste. Veja
    `## Registro de execuções` abaixo.

## Diagramas reais (dataset/external/)

Sem diagramas reais anotados, `dataset/build_dataset.py` tira val/test de uma fatia
do próprio dataset sintético — as métricas resultantes são otimistas, pois o modelo é
avaliado em imagens parecidas com as de treino. Popular `dataset/external/` substitui
essa fatia por diagramas reais no estilo usado pela avaliação do desafio.

1. Colecione entre 50 e 100 imagens de diagramas de arquitetura reais (não gerados
   pelo projeto), no mesmo estilo das figuras de avaliação do PDF do desafio —
   AWS Architecture Center, Azure Architecture Center ou documentação técnica
   equivalente. Salve como `.png`/`.jpg`.

2. Crie uma conta gratuita em https://roboflow.com e um novo projeto do tipo
   **Object Detection**. Cadastre as 15 classes com os mesmos nomes da taxonomia
   canônica (evita a necessidade de `mapping.yaml` mais adiante):

       user, web_client, api_gateway, load_balancer, app_server, database, cache,
       queue, storage, function_serverless, firewall_waf, auth_service, cdn,
       monitoring, external_service

3. Envie as imagens coletadas (`Upload Data`).

4. Anote cada imagem na fila `Unannotated`: ferramenta de caixa (tecla `B`), arraste
   uma caixa justa ao redor de cada ícone reconhecível como uma das 15 classes,
   selecione a classe no `Class Selector` e confirme com `Enter`. Ícones que não se
   encaixam em nenhuma das 15 classes ficam sem caixa — mas todo ícone que se encaixa
   deve ser anotado; anotação parcial de uma imagem introduz ruído no treino (melhor
   excluir a imagem inteira do que deixá-la parcialmente anotada).

5. Gere e exporte uma versão do dataset (`Generate` → `Export Dataset`) no formato
   **YOLOv11** (ou equivalente, com rótulos `.txt`).

6. Descompacte a exportação e una as subpastas do Roboflow em uma única pasta
   plana, no formato esperado por `dataset/build_dataset.py`
   (`dataset/external/images/*.jpg` e `dataset/external/labels/*.txt`). O
   Roboflow só cria as subpastas `train/`, `valid/` e `test/` que efetivamente
   receberam imagens na divisão configurada no passo `Generate` — com poucas
   imagens ou split 100% treino, a exportação pode conter apenas `train/`.
   Verifique antes com `dir <zip_extraido>` e copie apenas as pastas que
   existirem:

       mkdir dataset\external\images
       mkdir dataset\external\labels
       copy <zip_extraido>\train\images\* dataset\external\images\
       copy <zip_extraido>\valid\images\* dataset\external\images\
       copy <zip_extraido>\test\images\*  dataset\external\images\
       copy <zip_extraido>\train\labels\* dataset\external\labels\
       copy <zip_extraido>\valid\labels\* dataset\external\labels\
       copy <zip_extraido>\test\labels\*  dataset\external\labels\

   `dataset/build_dataset.py` não depende da divisão feita pelo Roboflow: trata
   tudo em `dataset/external/images` como um único conjunto e faz sua própria
   divisão 50/50 entre val/test — não há problema em exportar só com `train/`.

   Se os nomes/índices de classe exportados não coincidirem com a taxonomia
   canônica, adicione `dataset/external/mapping.yaml` (ver exemplo nesse mesmo
   arquivo README).

7. Reconstrua o dataset final e confirme que val/test passaram a usar as imagens
   reais:

       python dataset/build_dataset.py
       ls dataset/final/val/images

   O aviso `warning: no real diagrams found` não deve mais aparecer.

8. Para treinar no Colab, `dataset/external/` não é versionado no Git (está no
   `.gitignore`) e não vem junto do `git clone`. Compacte a pasta localmente e
   suba para o Google Drive:

       Compress-Archive -Path dataset\external -DestinationPath external.zip

   No notebook, após clonar o repositório e instalar o projeto (passos 2-3 da
   seção "Google Colab" acima), monte o Drive e descompacte antes de gerar o
   dataset:

       from google.colab import drive
       drive.mount('/content/drive')
       !unzip -q "/content/drive/MyDrive/external.zip" -d /content/7IADT-tech-challenge-fase-5/dataset

9. Prossiga com os passos 4 a 9 da seção "Google Colab" (gerar sintético, fundir,
   conferir GPU, treinar, salvar `best.pt` e `confusion_matrix.png`).

10. Registre a nova execução em `training/RESULTS.md` como uma linha adicional (sem
    sobrescrever o histórico anterior), anotando na observação que essa execução usa
    diagramas reais anotados manualmente. Um `mAP50 (test)` mais baixo que o obtido
    apenas com dataset sintético é esperado e reflete uma medição mais honesta de
    generalização. Em seguida, confirme o critério de aceite do desafio:

        python scripts/extract_eval_figures.py
        python -m pytest -m integration -v

## Registro de execuções
Registre cada execução em `training/RESULTS.md`: data, dataset (contagens por split),
hiperparâmetros, mAP50 geral e por classe, matriz de confusão (`training/confusion_matrix.png`),
observações.
