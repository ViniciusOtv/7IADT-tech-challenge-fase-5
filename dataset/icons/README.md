# Biblioteca de ícones

Coloque ícones oficiais (PNG com fundo transparente) em subpastas nomeadas com as
15 classes canônicas, por exemplo:

    dataset/icons/database/aws_rds.png
    dataset/icons/database/azure_sql.png
    dataset/icons/load_balancer/aws_elb.png

Fontes oficiais (uso permitido para arquiteturas):
- AWS Architecture Icons: https://aws.amazon.com/architecture/icons/
- Azure Architecture Icons: https://learn.microsoft.com/azure/architecture/icons/
- GCP Icons: https://cloud.google.com/icons

Classes: user, web_client, api_gateway, load_balancer, app_server, database, cache,
queue, storage, function_serverless, firewall_waf, auth_service, cdn, monitoring,
external_service.

Recomendação: 3-8 ícones por classe misturando provedores. Depois rode:

    python dataset/generate_synthetic.py --count 800
