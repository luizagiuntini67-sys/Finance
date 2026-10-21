# Vale Dashboard

Dashboard estático (um único `index.html`) com as cotações da **Vale** — VALE3 (B3) e VALE (ADR na NYSE) — usando dados do Yahoo Finance, publicado no GitHub Pages.

## O que tem no dashboard

- Preço atual, variação do dia, abertura, máxima/mínima, volume, faixa de 52 semanas
- Gráfico de preço com volume, períodos 1D · 5D · 1M · 6M · No ano · 1A · 5A · Máx e médias móveis de 20/50
- Desempenho vs. Ibovespa (base 100, retorno total)
- Tabela de rentabilidade (1M até 10A), volatilidade e queda máxima
- Proventos por ano + últimos proventos, dividend yield de 12 meses
- Histórico dos últimos 15 pregões
- Tema claro/escuro e layout responsivo

## Como funciona

O navegador não pode chamar a API do Yahoo Finance diretamente (bloqueio de CORS). Por isso:

1. `scripts/fetch_data.py` (só biblioteca padrão do Python) baixa os dados da API `v8/finance/chart` e grava JSON compactos em `data/`.
2. O workflow `.github/workflows/deploy.yml` roda esse script e publica `index.html` + `data/` no GitHub Pages:
   - a cada push na `main`;
   - a cada 30 min durante o pregão (seg–sex, 13h–21h UTC) e uma vez após o fechamento;
   - manualmente pela aba **Actions → Run workflow**.
3. Se `data/` não existir (ex.: abrindo o arquivo localmente sem rodar o script), a página tenta buscar ao vivo por um proxy CORS público (`corsproxy.io`) — útil para desenvolvimento, mas não confiável em produção.

## Publicando no GitHub Pages

1. Faça merge desta branch na `main`.
2. No repositório: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Vá em **Actions**, abra o workflow "Atualizar dados e publicar no GitHub Pages" e clique em **Run workflow** (ou faça um push na `main`).
4. O site fica em `https://<seu-usuario>.github.io/<repositorio>/`.

## Rodando localmente

```bash
python scripts/fetch_data.py      # gera data/*.json
python -m http.server 8000        # abra http://localhost:8000
```

## Personalizando

- Outros ativos: edite `SYMBOLS` em `scripts/fetch_data.py` e os botões `data-symbol` no `index.html`.
- Frequência de atualização: ajuste os `cron` em `.github/workflows/deploy.yml` (o GitHub pode atrasar execuções agendadas).

> Dados com atraso e apenas para fins informativos. Não é recomendação de investimento. A API do Yahoo Finance não é oficial e pode mudar sem aviso.
