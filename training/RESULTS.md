# Registro de treinamentos

| Data | Dataset (train/val/test) | Modelo | Épocas | imgsz | mAP50 (test) | Observações |
|------|--------------------------|--------|--------|-------|--------------|-------------|
| 2026-07-08 | 896 / 164 / 164 | YOLO11s (COCO pré-treinado, fine-tuned) | 96 (early stopping, patience=20; melhor peso salvo na época 76) | 1024 | 0.9950 | Treinado no Google Colab (GPU Tesla T4, ~1h13min). Batch solicitado de 32 caiu automaticamente para 16 por falta de memória da GPU (CUDA OOM) logo na 1ª época. mAP50 muito próximo de 1.0 em quase todas as classes — vale rodar `pytest -m integration` sobre as duas figuras de avaliação do PDF do desafio para confirmar que a generalização para diagramas reais "de livro-texto" acompanha essas métricas. |

## Por classe (última execução, split de teste)

| Classe | Imagens | Instâncias | P | R | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| all | 164 | 1060 | 0.999 | 0.999 | 0.995 | 0.994 |
| user | 56 | 67 | 0.999 | 1.000 | 0.995 | 0.994 |
| web_client | 62 | 85 | 1.000 | 0.990 | 0.995 | 0.995 |
| api_gateway | 66 | 82 | 1.000 | 1.000 | 0.995 | 0.995 |
| load_balancer | 64 | 75 | 1.000 | 1.000 | 0.995 | 0.995 |
| app_server | 60 | 72 | 0.999 | 1.000 | 0.995 | 0.993 |
| database | 50 | 61 | 1.000 | 1.000 | 0.995 | 0.995 |
| cache | 59 | 72 | 1.000 | 1.000 | 0.995 | 0.995 |
| queue | 58 | 70 | 0.999 | 1.000 | 0.995 | 0.995 |
| storage | 59 | 75 | 1.000 | 1.000 | 0.995 | 0.995 |
| function_serverless | 58 | 71 | 0.999 | 1.000 | 0.995 | 0.995 |
| firewall_waf | 55 | 65 | 0.999 | 1.000 | 0.995 | 0.995 |
| auth_service | 55 | 68 | 0.999 | 1.000 | 0.995 | 0.995 |
| cdn | 55 | 71 | 1.000 | 1.000 | 0.995 | 0.995 |
| monitoring | 52 | 60 | 0.999 | 1.000 | 0.995 | 0.995 |
| external_service | 56 | 66 | 0.998 | 1.000 | 0.995 | 0.988 |

_Matriz de confusão: pendente — copiar `runs/detect/val/confusion_matrix.png` (gerada pela validação no split de teste) do Colab para este repositório e referenciar aqui, ex.: `![matriz de confusão](confusion_matrix.png)`._
