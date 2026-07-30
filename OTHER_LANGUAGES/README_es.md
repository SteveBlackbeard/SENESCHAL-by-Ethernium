# Seneschal

[![PyPI](https://img.shields.io/badge/pypi-0.2.0-blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal es una capa de control local-first para trabajo con IA más barato y más seguro.

Decide qué contexto enviar, qué mantener en local, qué bloquear y si una tarea merece un modelo más potente. El objetivo es economía real de tokens: menos volcados del repositorio entero, menos reintentos, prompts más pequeños, alcance de herramientas más seguro y paquetes de tarea más claros.

> Un senescal administraba los recursos de una casa y autorizaba acciones en nombre del señor. Eso es exactamente lo que hace esta herramienta: **raciona el gasto** y **autoriza capacidades**.

## Qué hace

- Estima presupuestos de tokens sin atarte a un proveedor concreto
- Empaqueta contexto del repositorio bajo un presupuesto explícito
- Recomienda la ruta de modelo más barata que sea suficiente para la tarea
- Guarda instantáneas del contexto para no reenviar archivos sin cambios
- Selecciona el contexto vecino más relevante con relevancia léxica BM25
- Analiza texto y archivos no confiables buscando inyección de prompts y material secreto
- Verifica concesiones de capacidades de mínimo privilegio, **firmadas con Ed25519**

## Instalación

```bash
pip install seneschal
seneschal --help
```

Extras opcionales:

```bash
pip install "seneschal[measure]"    # tokenizador medido (tiktoken)
pip install "seneschal[security]"   # concesiones firmadas (cryptography)
```

## Concesiones de capacidad firmadas

Una concesión sin firmar es un fichero JSON que cualquier proceso puede editar: un agente podría falsificarse sus propios permisos. Con firma Ed25519, el broker rechaza en cerrado cualquier concesión sin firma válida, firmada por una clave no confiable, modificada después de firmar (escalada de privilegios) o caducada.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## Qué NO es

No es un sandbox ni un motor de ejecución de agentes. Decide **si** llamar a un modelo y **qué** contexto enviarle; no contiene lo que ese modelo o agente haga después con una capacidad concedida.

## Estado

Núcleo sin dependencias de ejecución. Licencia MIT. Sin telemetría.

Repositorio: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
