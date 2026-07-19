# Seneschal

[![PyPI](https://img.shields.io/pypi/v/seneschal?label=pypi&color=blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal은 더 저렴하고 더 안전한 AI 작업을 위한 로컬 우선 제어 계층입니다.

어떤 컨텍스트를 보낼지, 무엇을 로컬에 둘지, 무엇을 차단할지, 그리고 그 작업이 더 강력한 모델을 쓸 만한지 판단합니다. 목표는 실제 토큰 절약입니다. 저장소 전체를 붙여넣는 일을 줄이고, 재시도를 줄이며, 프롬프트를 작게 만들고, 도구 권한 범위를 좁히고, 작업 인계를 명확하게 합니다.

> 세네샬(seneschal)은 가문의 자원을 관리하고 주군을 대신해 행동을 승인하던 직책이었습니다. 이 도구가 하는 일도 정확히 같습니다. **비용을 배분하고**, **권한을 승인합니다**.

## 기능

- 특정 공급자에 종속되지 않는 토큰 예산 추정
- 명시적인 예산 안에서 저장소 컨텍스트 패키징
- 해당 작업에 충분한 범위에서 가장 저렴한 모델 경로 추천
- 컨텍스트 스냅샷 저장으로 변경되지 않은 파일의 재전송 방지
- BM25 어휘 관련도를 이용한 가장 관련성 높은 주변 컨텍스트 선택
- 신뢰할 수 없는 텍스트와 파일에서 프롬프트 인젝션 및 비밀 정보 검사
- **Ed25519로 서명된** 최소 권한 능력 부여 검증

## 설치

```bash
pip install seneschal
seneschal --help
```

선택적 추가 기능:

```bash
pip install "seneschal[measure]"    # 실측 토크나이저 (tiktoken)
pip install "seneschal[security]"   # 서명된 권한 부여 (cryptography)
```

## 서명된 능력 부여

서명되지 않은 부여는 어떤 프로세스든 편집할 수 있는 JSON 파일에 불과합니다. 에이전트가 자신의 권한을 위조할 수 있다는 뜻입니다. Ed25519 서명을 사용하면 브로커는 다음의 경우를 실패-차단(fail-closed) 방식으로 거부합니다. 유효한 서명이 없는 경우, 신뢰되지 않는 키로 서명된 경우, 서명 이후 변조된 경우(권한 상승), 또는 만료된 경우입니다.

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## 이것이 아닌 것

샌드박스도, 에이전트 실행 엔진도 아닙니다. 모델을 **호출할지 여부**와 **어떤 컨텍스트를 보낼지**만 결정하며, 그 모델이나 에이전트가 부여된 권한으로 이후에 무엇을 하는지는 제어하지 않습니다.

## 상태

핵심은 런타임 의존성 제로. MIT 라이선스. 텔레메트리 없음.

저장소: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
