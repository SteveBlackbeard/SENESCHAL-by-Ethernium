# Seneschal

[![PyPI](https://img.shields.io/badge/pypi-0.2.0-blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal ist eine local-first Kontrollschicht für günstigere und sicherere KI-gestützte Arbeit.

Sie entscheidet, welcher Kontext gesendet wird, was lokal bleibt, was blockiert wird und ob eine Aufgabe ein stärkeres Modell verdient. Ziel ist echte Token-Ökonomie: weniger Komplett-Dumps des Repositories, weniger Wiederholungen, kleinere Prompts, sicherere Werkzeug-Reichweite und klarere Aufgabenpakete.

> Ein Seneschall verwaltete die Ressourcen eines Hauses und autorisierte Handlungen im Namen des Herrn. Genau das tut dieses Werkzeug: es **rationiert Ausgaben** und **autorisiert Fähigkeiten**.

## Funktionen

- Schätzt Token-Budgets ohne Bindung an einen bestimmten Anbieter
- Packt Repository-Kontext unter einem expliziten Budget
- Empfiehlt den günstigsten ausreichenden Modellpfad für eine Aufgabe
- Erstellt Kontext-Snapshots, damit unveränderte Dateien nicht erneut gesendet werden
- Wählt den relevantesten benachbarten Kontext per BM25-Relevanz aus
- Prüft nicht vertrauenswürdige Texte und Dateien auf Prompt-Injection und Geheimnisse
- Verifiziert Least-Privilege-Berechtigungen, **mit Ed25519 signiert**

## Installation

```bash
pip install seneschal
seneschal --help
```

Optionale Extras:

```bash
pip install "seneschal[measure]"    # gemessener Tokenizer (tiktoken)
pip install "seneschal[security]"   # signierte Berechtigungen (cryptography)
```

## Signierte Berechtigungen

Eine unsignierte Berechtigung ist eine JSON-Datei, die jeder Prozess ändern kann: ein Agent könnte sich selbst Rechte fälschen. Mit Ed25519-Signatur weist der Broker fail-closed jede Berechtigung ab, die keine gültige Signatur hat, von einem nicht vertrauenswürdigen Schlüssel stammt, nach dem Signieren verändert wurde (Rechteausweitung) oder abgelaufen ist.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## Was es nicht ist

Es ist weder eine Sandbox noch eine Ausführungs-Engine für Agenten. Es entscheidet, **ob** ein Modell aufgerufen wird und **welchen** Kontext es erhält; es begrenzt nicht, was dieses Modell oder dieser Agent anschließend mit einer gewährten Fähigkeit tut.

## Status

Kern ohne Laufzeit-Abhängigkeiten. MIT-Lizenz. Keine Telemetrie.

Repository: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
