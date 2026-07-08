# Diagramas reais anotados (opcional)

Esta pasta é **opcional**. Se não existir ou estiver vazia,
`dataset/build_dataset.py` roda normalmente usando só o dataset sintético —
nesse caso val/test são uma fatia (10%/10%) do próprio dataset sintético, e
as métricas de avaliação ficam otimistas até diagramas reais serem
adicionados aqui.

Quando quiser popular esta pasta, `dataset/build_dataset.py` espera uma
exportação em formato YOLO (Roboflow ou equivalente), com esta estrutura:

    dataset/external/images/*.jpg   (ou .png)
    dataset/external/labels/*.txt   (um .txt por imagem, mesmo stem)
    dataset/external/mapping.yaml   (opcional)

Cada imagem precisa de um `.txt` correspondente (mesmo nome, sem extensão) —
mesmo que vazio, para imagens de fundo/negativas sem componente nenhum.

## Origem das imagens

Duas fontes, ambas descritas em `docs/development-flow.md`:

1. **Datasets públicos do Roboflow Universe** com diagramas de arquitetura,
   remapeados para a taxonomia de 15 classes deste projeto.
2. **Diagramas reais (~50-100 imagens)** de documentação de arquiteturas de
   referência AWS/Azure, anotados manualmente pela equipe no Roboflow (plano
   gratuito, exportação em formato YOLO).

## `mapping.yaml`

Se as classes exportadas pelo Roboflow não usarem os mesmos índices/nomes da
taxonomia canônica deste projeto, forneça `mapping.yaml` traduzindo o índice
de classe original do Roboflow para o nome de classe canônico, por exemplo:

    0: database
    1: load_balancer
    2: api_gateway

Classes canônicas: user, web_client, api_gateway, load_balancer, app_server,
database, cache, queue, storage, function_serverless, firewall_waf,
auth_service, cdn, monitoring, external_service.

Qualquer índice original não presente no mapeamento é descartado (a anotação
daquele componente é ignorada, não vira uma classe nova). Depois de popular
esta pasta, rode:

    python dataset/build_dataset.py
