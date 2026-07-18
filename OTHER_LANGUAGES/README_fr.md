# Seneschal

[![PyPI](https://img.shields.io/badge/pypi-0.2.0-blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal est une couche de contrôle local-first pour un travail assisté par IA moins coûteux et plus sûr.

Elle décide quel contexte envoyer, quoi garder en local, quoi bloquer, et si une tâche mérite un modèle plus puissant. L'objectif est une véritable économie de jetons : moins de dumps du dépôt entier, moins de reprises, des prompts plus courts, une portée d'outils plus sûre et des paquets de tâche plus clairs.

> Un sénéchal administrait les ressources d'une maison et autorisait les actions au nom du seigneur. C'est exactement ce que fait cet outil : **rationner la dépense** et **autoriser les capacités**.

## Ce qu'il fait

- Estime les budgets de jetons sans dépendre d'un fournisseur précis
- Assemble le contexte du dépôt sous un budget explicite
- Recommande le chemin de modèle le moins cher qui soit suffisant
- Enregistre des instantanés du contexte pour ne pas renvoyer les fichiers inchangés
- Sélectionne le contexte voisin le plus pertinent via la pertinence lexicale BM25
- Analyse textes et fichiers non fiables à la recherche d'injections de prompt et de secrets
- Vérifie des octrois de capacités à moindre privilège, **signés en Ed25519**

## Installation

```bash
pip install seneschal
seneschal --help
```

Extras optionnels :

```bash
pip install "seneschal[measure]"    # tokenizer mesuré (tiktoken)
pip install "seneschal[security]"   # octrois signés (cryptography)
```

## Octrois de capacités signés

Un octroi non signé est un fichier JSON que n'importe quel processus peut modifier : un agent pourrait falsifier ses propres permissions. Avec une signature Ed25519, le broker refuse (fail-closed) tout octroi sans signature valide, signé par une clé non fiable, modifié après signature (élévation de privilèges) ou expiré.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## Ce qu'il n'est pas

Ce n'est ni un bac à sable ni un moteur d'exécution d'agents. Il décide **s'il faut** appeler un modèle et **quel** contexte lui transmettre ; il ne confine pas ce que ce modèle ou cet agent fera ensuite d'une capacité accordée.

## Statut

Cœur sans dépendances d'exécution. Licence MIT. Aucune télémétrie.

Dépôt : https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
