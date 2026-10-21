"""Baixa cotações do Yahoo Finance e salva em data/*.json.

O navegador não consegue chamar a API do Yahoo diretamente (bloqueio de CORS),
então este script roda no GitHub Actions e publica os JSON junto com o site.

Uso: python scripts/fetch_data.py
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SYMBOLS = {
    "VALE3.SA": "Vale ON (B3)",
    "VALE": "Vale ADR (NYSE)",
    "^BVSP": "Ibovespa",
}

# (nome do arquivo, parâmetros da API de chart)
SERIES = [
    ("intraday", {"range": "1d", "interval": "5m"}),
    ("week", {"range": "5d", "interval": "15m"}),
    ("daily", {"range": "max", "interval": "1d", "events": "div,split"}),
]

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; finance-dashboard/1.0)"}
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_chart(symbol, params, retries=3):
    url = BASE_URL + urllib.parse.quote(symbol) + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)["chart"]["result"][0]
        except Exception as exc:  # noqa: BLE001
            print(f"  tentativa {attempt + 1} falhou: {exc}", file=sys.stderr)
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Falha ao baixar {symbol} {params}")


def simplify(result):
    """Reduz a resposta do Yahoo a colunas compactas, sem pontos nulos."""
    meta = result.get("meta", {})
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    adj = result.get("indicators", {}).get("adjclose", [{}])
    adjclose = adj[0].get("adjclose") if adj else None
    ts = result.get("timestamp") or []

    rows = []
    for i, t in enumerate(ts):
        close = quote.get("close", [None] * len(ts))[i]
        if close is None:
            continue
        rows.append([
            t,
            quote["open"][i],
            quote["high"][i],
            quote["low"][i],
            close,
            quote["volume"][i] or 0,
            adjclose[i] if adjclose else close,
        ])

    events = result.get("events", {})
    dividends = sorted(
        ([d["date"], d["amount"]] for d in events.get("dividends", {}).values()),
        key=lambda d: d[0],
    )
    splits = sorted(
        ([s["date"], s["numerator"], s["denominator"]] for s in events.get("splits", {}).values()),
        key=lambda s: s[0],
    )

    keep = [
        "currency", "symbol", "exchangeName", "fullExchangeName", "instrumentType",
        "regularMarketPrice", "regularMarketTime", "regularMarketDayHigh",
        "regularMarketDayLow", "regularMarketVolume", "chartPreviousClose",
        "previousClose", "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "longName",
        "shortName", "exchangeTimezoneName", "gmtoffset",
    ]
    return {
        "meta": {k: meta.get(k) for k in keep if k in meta},
        "columns": ["t", "open", "high", "low", "close", "volume", "adjclose"],
        "rows": rows,
        "dividends": dividends,
        "splits": splits,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = {"updatedAt": datetime.now(timezone.utc).isoformat(), "symbols": {}}
    errors = 0
    for symbol, label in SYMBOLS.items():
        manifest["symbols"][symbol] = {"label": label, "files": {}}
        for name, params in SERIES:
            print(f"Baixando {symbol} [{name}]...")
            try:
                data = simplify(fetch_chart(symbol, params))
            except RuntimeError as exc:
                print(f"  ERRO: {exc}", file=sys.stderr)
                errors += 1
                continue
            fname = f"{symbol.replace('^', '')}_{name}.json"
            with open(os.path.join(OUT_DIR, fname), "w") as fh:
                json.dump(data, fh, separators=(",", ":"))
            manifest["symbols"][symbol]["files"][name] = fname
            print(f"  {len(data['rows'])} pontos -> data/{fname}")

    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    if errors == len(SYMBOLS) * len(SERIES):
        sys.exit("Nenhum dado foi baixado.")


if __name__ == "__main__":
    main()
