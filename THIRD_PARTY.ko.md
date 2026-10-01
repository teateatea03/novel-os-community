# 제삼자 구성 요소 및 참고 자료

<!-- language-navigation --> [繁體中文](THIRD_PARTY.zh-TW.md) | [English](THIRD_PARTY.md) | [日本語](THIRD_PARTY.ja.md) | **한국어** | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | [Deutsch](THIRD_PARTY.de.md) | [Português](THIRD_PARTY.pt.md)

Novel OS에는 제삼자 프로젝트와 연동하거나 이를 설명하는 프로젝트 자체 코드와 문서가 포함됩니다. 파일에 명시적으로 달리 적혀 있지 않다면 제삼자 프로젝트 소스 사본은 이 저장소에 **포함되지 않습니다**.

## 실행 환경 및 선택적 의존성

| 구성 요소 | 용도 | 라이선스 / 출처 |
|---|---|---|
| Python | 실행 환경(3.10+) | Python Software Foundation License |
| NetworkX | 그래프 알고리즘 및 GraphML 내보내기 | BSD-3-Clause; https://networkx.org/ |
| PyYAML | NPC 투영 유틸리티의 YAML 상태 입력 | MIT; https://pyyaml.org/ |
| MCP Python SDK | 선택적인 로컬 Instagram MCP 클라이언트 | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify(`graphifyy`) | 선택적 그래프 분석/내보내기 연동 | 업스트림은 Apache-2.0으로 표시하며 MIT 라이선스 자료도 포함; https://github.com/Graphify-Labs/graphify |

익명 Instagram MCP 서버와 Instaloader는 별도의 선택적 구성 요소이며 여기에 포함되지 않습니다. 운영자는 직접 설치하고 플랫폼 약관, 적용 법률, robots·접근 통제 및 프로젝트의 공개 자료 전용 제약을 준수할 책임이 있습니다.

## 연구 참고 자료

문서는 연구 인용으로 기사, 명세, 서적, 도구 및 공개 프로젝트를 연결합니다. 링크와 설명이 해당 작품의 코드나 문장을 Novel OS에 포함한다는 뜻은 아닙니다. 아이디어만 인용하는 것이 아니라 코드나 글을 각색한 자료를 기여한다면 정확한 출처, 라이선스, 변경 사항 및 필요한 저작자 표시를 명시해야 합니다.

## 이 배포에 포함된 각색 자료

- **Humanizer-zh**, copyright (c) 2026 歸藏, MIT: [업스트림 commit f4518a8eab97b8bfebc66a89d34320a89bef6930 소스](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - 각색: `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md`는 31개 편집 체크포인트를 번체 중국어로 번역·압축하고 소설 전용 보존 및 충돌 규칙을 추가합니다
  - [업스트림 MIT 고지](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt)를 보존했으며 해당 정확한 업스트림 commit과 대조했습니다
  - 이 고지는 소스, 휴대형 번들 및 설치된 런타임에서 스킬과 함께 유지됩니다. 업스트림 자료에 적용되며 Novel OS 전체에는 **적용되지 않습니다**. 프로젝트 자체 자료에는 별도로 [LICENSE](LICENSE.ko.md)가 적용됩니다

## 여기서 배포하지 않는 외부 호스트 연동

`lieflat-less-ai-tone`은 호스트가 제공하는 선택적 편집 단계이며 17개 런타임 스킬에 포함되지 않습니다. 연동 문서에는 외부 리비전이 기록되어 있으나 이 저장소에는 확인된 업스트림 URL·라이선스나 구현이 없습니다. 자동으로 가져오거나 소스 사본을 포함하거나 실행했다고 주장하지 마세요. 사용할 수 없으면 내장된 사람다운 문체 작업 흐름을 유지하고 이 추가 단계는 실행하지 않았다고 기록하세요. 설치 또는 배포 전에 출처와 라이선스를 별도로 확인하세요.

`minis-model-use` 독립 검토 어댑터에는 원래 호스트가 필요합니다. 다른 호스트는 명시적으로 구성한 대체 수단을 제공하거나 독립 모델 검토를 실행하지 않았다고 기록해야 합니다. 로컬 회귀 테스트는 실제 모델, Graphify, MCP 또는 Instagram 서비스를 시험하지 않습니다.

## 의존성 경계

위 선택적 패키지는 코어 배포에 포함되거나 자동 설치되지 않습니다. 라이선스 의무는 각 배포물의 조건을 따릅니다. 연동을 활성화하거나 결합 패키지를 재배포하기 전에 정확한 업스트림 버전을 검토하세요. 코어 테스트는 이 의존성 없이 실행됩니다. 이 목록은 검토 보조 자료이며 법률 자문이 아닙니다.
