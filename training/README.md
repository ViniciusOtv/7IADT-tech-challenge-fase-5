# Treinamento do detector

## Local (GPU) 
    pip install -e .
    python dataset/generate_synthetic.py --count 800
    python dataset/build_dataset.py
    python training/train.py

## Google Colab (GPU gratuita)
1. Zipe `dataset/final/` e envie ao Drive (ou clone o repositório no Colab).
2. Em um notebook com runtime GPU:

       !pip install ultralytics
       !python training/train.py --data /content/dataset/final/data.yaml --batch 32

3. Baixe `runs/detect/strideai/weights/best.pt` e coloque em `models/best.pt`
   OU anexe a uma release do GitHub e use:

       python scripts/download_weights.py --url <url-da-release>

## Registro de execuções
Registre cada execução em `training/RESULTS.md`: data, dataset (contagens por split),
hiperparâmetros, mAP50 geral e por classe, matriz de confusão, observações.
