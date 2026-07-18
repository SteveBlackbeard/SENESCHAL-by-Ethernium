# Seneschal

[![PyPI](https://img.shields.io/badge/pypi-0.2.0-blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal è uno strato di controllo local-first per un lavoro assistito dall'IA più economico e più sicuro.

Decide quale contesto inviare, cosa mantenere in locale, cosa bloccare e se un compito merita un modello più potente. L'obiettivo è una vera economia di token: meno dump dell'intero repository, meno tentativi ripetuti, prompt più piccoli, ambito degli strumenti più sicuro e pacchetti di attività più chiari.

> Un siniscalco amministrava le risorse di una casa e autorizzava le azioni per conto del signore. È esattamente ciò che fa questo strumento: **razionare la spesa** e **autorizzare le capacità**.

## Cosa fa

- Stima i budget di token senza vincolarsi a un fornitore specifico
- Impacchetta il contesto del repository entro un budget esplicito
- Raccomanda il percorso di modello più economico ma sufficiente per il compito
- Crea snapshot del contesto per non reinviare i file non modificati
- Seleziona il contesto vicino più rilevante tramite rilevanza lessicale BM25
- Analizza testi e file non attendibili in cerca di prompt injection e materiale segreto
- Verifica concessioni di capacità a privilegio minimo, **firmate con Ed25519**

## Installazione

```bash
pip install seneschal
seneschal --help
```

Extra opzionali:

```bash
pip install "seneschal[measure]"    # tokenizer misurato (tiktoken)
pip install "seneschal[security]"   # concessioni firmate (cryptography)
```

## Concessioni di capacità firmate

Una concessione non firmata è un file JSON che qualsiasi processo può modificare: un agente potrebbe falsificare i propri permessi. Con la firma Ed25519 il broker rifiuta in modo fail-closed ogni concessione priva di firma valida, firmata da una chiave non attendibile, modificata dopo la firma (escalation di privilegi) o scaduta.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## Cosa non è

Non è né una sandbox né un motore di esecuzione per agenti. Decide **se** chiamare un modello e **quale** contesto inviargli; non contiene ciò che quel modello o agente farà poi con una capacità concessa.

## Stato

Nucleo senza dipendenze di runtime. Licenza MIT. Nessuna telemetria.

Repository: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
