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

## Registro de execuções
Registre cada execução em `training/RESULTS.md`: data, dataset (contagens por split),
hiperparâmetros, mAP50 geral e por classe, matriz de confusão (`training/confusion_matrix.png`),
observações.
