# 휴대형 Novel OS 번들 계약

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | **한국어** | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

`novel-os-portable-v<version>/` 패키지 구조의 `skills/`에는 조정자 1개와 전문 스킬 16개가 있습니다. `public-web-research/`는 안전하고 재개 가능한 공개 HTTP(S) 수집 및 Evidence Run 후보 스테이징을 제공합니다. `novel-model-capability-compatibility/`는 모델 능력 probe·L0–L5·fallback 계약을 유지합니다. `novel-reality-state-engine/`은 이벤트 → 상태 → 능력 → 행동 → 본문 검증 도구를 유지합니다. `novel-world-database-builder/`는 세계 데이터베이스 스키마, 배치 템플릿, 인계 패키지 및 질의 명세를 유지합니다. `special-object-database-builder/`는 소품·갑옷·기체·장치의 버전, 능력, 사양 및 수명주기 스키마를 유지합니다.

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── LICENSE.{zh-TW,ja,ko,es,fr,de,pt}.md
├── THIRD_PARTY.md
├── THIRD_PARTY.{zh-TW,ja,ko,es,fr,de,pt}.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   └── COMMERCIAL_TERMS.{zh-TW,ja,ko,es,fr,de,pt}.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.{en,ja,ko,es,fr,de,pt}.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.{en,ja,ko,es,fr,de,pt}.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.{en,ja,ko,es,fr,de,pt}.md
│   ├── bundle-contract.md
│   └── bundle-contract.{en,ja,ko,es,fr,de,pt}.md
├── skills/
│   ├── novel-operating-system/      # mandatory single entry point
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

구조의 중괄호는 나열된 각 언어의 별도 파일을 줄여 쓴 것입니다.

`MANIFEST.json`에는 번들 스키마·버전, 패키지 목록, 소스 스킬 버전, 각 페이로드 파일의 SHA-256 및 바이트 수, 별도 `distribution_notices` 목록, 빌드 시간, 제외 항목 및 런타임 의존성 선언이 들어갑니다. 페이로드에는 **플랫폼 호환성 안내**의 휴대형 사본도 포함됩니다. 비밀, 로컬 절대 경로, 이야기 프로젝트, 계정 설정 또는 세계 데이터베이스는 포함하지 않습니다.

## 라이선스와 고지 보존

- `--source-root`는 소스 `skills/` 디렉터리를 가리킵니다. 그 부모 저장소에는 필수 고지 24개 모두가 있어야 합니다. 영어 `LICENSE`, `THIRD_PARTY.md`, `docs/COMMERCIAL_TERMS.md` 및 `zh-TW`, `ja`, `ko`, `es`, `fr`, `de`, `pt` 각각의 `LICENSE.<language>.md`, `THIRD_PARTY.<language>.md`, `docs/COMMERCIAL_TERMS.<language>.md`입니다. refresh는 필수 문서가 없거나 일반 파일이 아니거나 심볼릭 링크이면 페이로드 변경 전에 거부합니다. 이는 소유자가 선택한 프로젝트 조건이며 업스트림 고지는 원래 적용 범위를 유지합니다
- 추가 명시적 허용 목록은 `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `docs/COMMERCIAL_LICENSE.md`입니다. 있으면 바이트 단위로 그대로 복사합니다. 그 외 루트 `docs/` 파일은 내보내지 않습니다. 특히 `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md`는 효력이 없는 논의용 초안으로 라이선스나 상업적 조건으로 내보내지 않습니다
- 스킬 내부의 `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md` 및 `THIRD_PARTY_LICENSES/`의 모든 파일은 스킬과 함께 보존하며 `distribution_notices`에 선언합니다. refresh는 소스와 바이트를 대조하고 build·install은 선언 누락, 파일 누락, 바이트 변경, 위험한 경로 또는 해시 항목 누락을 거부합니다
- 기존 Humanizer-zh 각색 자료에는 `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`가 특별히 필요합니다. 해당 자료를 배포하는 동안 소스나 매니페스트에서 제거할 수 없습니다
- 새로운 법적 필수 파일명은 배포 전에 이 명시적 계약에 추가해야 합니다. 포함되지 않은 문서 링크에 의존하지 마세요. refresh는 기존 페이로드에서 더 이상 필요 없는 선택적 루트 고지 사본을 제거합니다
- ZIP은 같은 루트 상대 구조를 유지합니다. 설치 시 모든 고지를 `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`에 저장하면서 `docs/COMMERCIAL_TERMS.md`, `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt` 같은 경로를 유지하여 상대 라이선스 링크가 작동하게 합니다. 스킬 내부 업스트림 고지도 원래 스킬 디렉터리에 남습니다. 설치 도구는 `<target>/LICENSE`, `<target>/THIRD_PARTY.md`, `<target>/docs/`에 쓰지 않습니다
- `novel-operating-system/INSTALLATION.json`은 설치한 각 고지의 원본 경로, 설치 경로, 문서 사본 경로, SHA-256 및 바이트 수를 기록합니다. 해당하는 경우 스테이징과 최종 설치에서 두 사본 모두를 검증합니다. 업그레이드는 이전 조정자와 고지를 일반 스킬 백업에 저장하고 실패하면 복원합니다. 조정자 내부의 `DISTRIBUTION_NOTICES/`는 설치 도구가 관리하는 문서용 예약 영역입니다
- 설치 재검사는 압축을 푼 번들에서 `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices`를 실행합니다. 이 읽기 전용 모드는 루트·업스트림 고지를 설치 기록과 대조합니다. 해시는 로컬 무결성을 확인할 뿐 파일과 기록을 모두 바꿀 수 있는 공격자에 대한 진위를 보장하지 않습니다. 신뢰할 수 있는 배포본을 별도로 보관하세요

## 런타임 의존성 선언

모든 배포에는 명시적 허용 목록의 휴대형 참고 문서 32개가 포함되어야 합니다. `references/` 아래 `portable-install`, `platform-compatibility`, `host-adapter-contract`, `bundle-contract` 각각에 번체 중국어 `.md` 및 `en`, `ja`, `ko`, `es`, `fr`, `de`, `pt`의 `.<language>.md`가 필요합니다. 다음 수준을 사실대로 선언하세요.

- **기본 문서 작업 흐름:** Skill 파일을 읽을 수 있는 LLM이며 코드 실행은 필요하지 않습니다
- **자동화된 로컬 작업 흐름(v2.7):** Python 3.10+(3.11+ 권장), shell·프로세스 실행기, 영속 UTF-8 파일, 다중 스킬 검색 또는 동등한 라우터, branch lock, 단일 `ProjectRuntimeAdapter.commit()` production authority, 7개 Gate, 형식화된 의미 이벤트, project readiness·projection freshness, 작가 피드백 Quality Eval 및 ZIP 배포 시 압축 해제 기능. 세계 데이터베이스에는 쓰기 가능한 `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, 특수 물체 데이터베이스에는 `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT`도 필요합니다
- **그래프 확장:** 그래프 탐색에 `networkx`, Graphify HTML·커뮤니티·Cypher 내보내기에 `graphifyy`와 `networkx`. 두 패키지가 없어도 그래프 JSON 자체는 사용할 수 있습니다
- **선택적 연동:** 커밋용 Git, 출처 연구용 web·browser 및 독립 검토용 호스트별 두 번째 모델·sub-agent 어댑터. 교체하기 전까지 `independent_review.py`는 Minis 전용입니다

기본 로컬 기능에는 Node.js, 데이터베이스 서버, API 키 또는 인터넷 연결이 필요하지 않습니다. 파일·프로세스 접근이 없는 프레임워크는 완전 자동 설치가 아닌 문서·수동 모드로 설명해야 합니다.

## 빌드 정책

- 페이로드에는 허용 목록의 스킬 디렉터리 **17개**(조정자 1+전문 스킬 16), 휴대형 참고 자료, 설치·빌드 스크립트 및 일반 텍스트·소스·테스트 자료·템플릿 파일이 있어야 합니다
- `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, 모든 소설 프로젝트, 데이터베이스, 압축 파일 및 시스템별 파일을 제외합니다
- 페이로드 변경 전에 소스 스킬 경로나 패키징 스킬의 심볼릭 링크를 거부하며 무관한 호스트 파일을 따라가지 않습니다. 기존 미승인 페이로드 문서도 새 매니페스트에 몰래 포함하지 않고 refresh를 실패시킵니다
- 소스의 `scripts/*.py`에 실행 비트가 있으면 보존합니다
- 로컬 소스 스킬 트리와 명시적 저장소 수준 고지 허용 목록만 읽습니다. 빌드는 `built_at` 외에는 결정적입니다
- 번들은 독립적입니다. 런타임 보조 도구는 Python 표준 라이브러리를 사용하고 설치 위치를 기준으로 상대적으로 의존성을 찾습니다

## 검증 정책

`verify`는 누락·변경·예상 외·해시 불일치 페이로드 파일을 거부한 뒤 모든 Python 파일을 컴파일해야 합니다. 설치 스모크 테스트는 추가로 다음을 수행합니다.

1. 활성 production authority 아래 임시 소설 프로젝트를 초기화합니다
2. FileStore를 통한 직접 정본 변경이 차단되는지 확인합니다
3. Gate authority, readiness, command executor, Quality Eval v2, 형식화된 의미 이벤트 및 일반 장편 제작을 포함한 전체 Novel Judge 스위트를 실행합니다
4. 그래프 검증기와 장편·Reality·능력 회귀를 실행합니다
5. 번들 스킬 집합과 소스 집합의 차이를 검증합니다
6. 전체 배포에서는 격리된 두 번째 프로젝트 계약 probe와 10만 자 이상 일반 장편·지식 반전·연쇄 수정 파일럿을 실행합니다

Python을 실행할 수 없는 플랫폼은 작업 흐름·문서 수준으로만 지원합니다. 인계 시 해당 한계를 명시하세요.
