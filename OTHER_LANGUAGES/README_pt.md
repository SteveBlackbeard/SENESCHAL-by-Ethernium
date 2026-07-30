# Seneschal

[![PyPI](https://img.shields.io/badge/pypi-0.2.0-blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal é uma camada de controlo local-first para trabalho assistido por IA mais barato e mais seguro.

Decide que contexto enviar, o que manter local, o que bloquear e se uma tarefa merece um modelo mais forte. O objetivo é economia real de tokens: menos despejos do repositório inteiro, menos repetições, prompts mais pequenos, âmbito de ferramentas mais seguro e pacotes de tarefa mais claros.

> Um senescal administrava os recursos de uma casa e autorizava ações em nome do senhor. É exatamente o que esta ferramenta faz: **raciona o gasto** e **autoriza capacidades**.

## O que faz

- Estima orçamentos de tokens sem prender-se a um fornecedor específico
- Empacota o contexto do repositório dentro de um orçamento explícito
- Recomenda o caminho de modelo mais barato que seja suficiente para a tarefa
- Guarda instantâneos do contexto para não reenviar ficheiros inalterados
- Seleciona o contexto vizinho mais relevante através de relevância lexical BM25
- Analisa textos e ficheiros não confiáveis à procura de prompt injection e segredos
- Verifica concessões de capacidades de privilégio mínimo, **assinadas com Ed25519**

## Instalação

```bash
pip install seneschal
seneschal --help
```

Extras opcionais:

```bash
pip install "seneschal[measure]"    # tokenizador medido (tiktoken)
pip install "seneschal[security]"   # concessões assinadas (cryptography)
```

## Concessões de capacidade assinadas

Uma concessão não assinada é um ficheiro JSON que qualquer processo pode editar: um agente poderia forjar as suas próprias permissões. Com assinatura Ed25519, o broker rejeita em fail-closed qualquer concessão sem assinatura válida, assinada por uma chave não confiável, modificada após a assinatura (escalada de privilégios) ou expirada.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## O que não é

Não é uma sandbox nem um motor de execução de agentes. Decide **se** deve chamar um modelo e **que** contexto lhe enviar; não contém o que esse modelo ou agente fará depois com uma capacidade concedida.

## Estado

Núcleo sem dependências de execução. Licença MIT. Sem telemetria.

Repositório: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
