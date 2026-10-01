# Novel OS

<!-- language-navigation --> [繁體中文](README.zh-TW.md) | [English](README.md) | [日本語](README.ja.md) | **한국어** | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

Novel OS는 장편 소설, 대화형 소설, 연속성, 인물·세계 연구, 행동 일관성, 출처를 추적하는 그래프 및 서사 검증을 위한 재사용 가능한 AI 에이전트 스킬과 로컬 Python 도구 모음입니다.

> **라이선스:** teateatea03 저작권의 [Novel OS 상업적 이익 배분 라이선스](LICENSE.ko.md)에 따라 소스를 공개합니다. 비상업적 사용은 무료이며 상업적 사용은 연간 관련 양의 순이익의 0.5%를 지급해야 합니다. 수정 및 재배포 시 동일한 조건과 고지를 유지합니다. MIT, GPL 또는 OSI 오픈 소스 라이선스가 아닙니다.

상업적 사용과 두 토큰 지급 정보는 [상업적 이익 배분 및 지급 안내](docs/COMMERCIAL_TERMS.ko.md)를 참조하세요. 사용자 소설과 기타 결과물의 권리는 시스템 소유자에게 이전되지 않습니다.

## 언어 지원 범위

공개 문서는 8개 언어로 제공됩니다. 런타임 스킬, 템플릿 및 해당 기술 참고 자료는 현재 원래 언어를 유지합니다. 이번 다국어 문서 배포는 런타임 번역이 아닙니다.

## 개인정보 경계

이 소스 저장소는 의도적으로 다음을 제외합니다.

- 원고, 장 초안, 대화형 플레이 세션, 이야기 상태 및 작가 피드백 데이터셋
- 등장인물, 세계, 특수 물체 및 실존 인물 연구 데이터베이스
- 채팅 기억, 기기 로컬 상태, 백업, 내보낸 파일, 인증 정보, 비공개 엔드포인트 및 환경 파일

공개 예제와 테스트 자료는 합성이어야 합니다. push 또는 배포 전마다 개인정보 스캐너를 실행하고 스테이징 목록을 검토하세요.

## 저장소 구조

- `skills/`: 재사용 가능한 스킬 패키지, 스크립트, 템플릿 및 합성 테스트 자료
- `scripts/`: 개인정보, 검증 및 테스트 유틸리티
- `docs/`: 프로젝트 운영 및 공개 범위 문서

소스 트리에는 18개 스킬 디렉터리가 있습니다. 설치 가능한 런타임 스킬 17개(조정자 1개와 협업 스킬 16개)와 번들 내보내기 도구입니다. 내보내기 도구는 패키징 도구이며 런타임 스킬로 설치되지 않습니다.

## 요구 사항

- Python 3.10+
- 영속적인 UTF-8 저장소
- 코어 경로는 표준 라이브러리만 사용
- 선택적 기능: `requirements-optional.txt` 및 [THIRD_PARTY.ko.md](THIRD_PARTY.ko.md) 참조

선택적 Python 의존성은 격리된 환경에 설치하세요.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Graphify 연동은 선택 사항이며 업스트림 문서에 따라 별도로 설치합니다.

## 첫 로컬 실행(모델이나 네트워크 불필요)

저장소 루트에서 Python 3.10+와 Git을 사용하세요. 코어 검사와 합성 데모에는 선택적 패키지, API 키 또는 비공개 원고가 필요하지 않습니다.

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Keep generated project state outside the source repository.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

초기화 도구는 빈 계획·상태 틀을 만들며 소설을 생성하거나 모델을 호출하지 않습니다. 자신의 이야기는 별도 비공개 디렉터리에 보관하세요. 초기화 도구는 기존 프로젝트 덮어쓰기를 거부합니다.

에이전트 호스트에서는 런타임 스킬을 같은 계층의 디렉터리로 보존하고 `novel-operating-system`을 진입점으로 등록하세요. 영속 파일이나 Python 프로세스 실행기가 없는 호스트는 문서·수동 모드만 지원합니다. 번들 명령, 스모크 테스트, 선택적 연동 및 플랫폼 한계는 [검증된 로컬 빌드·설치 안내](docs/GETTING_STARTED.ko.md)를 참조하세요.

## 검증

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Novel Judge 스위트는 `scripts/run_tests.py`로 실행해야 합니다. 패키지 상대 경로 테스트 파일을 하나씩 호출하는 방식은 지원하지 않습니다.

개인정보 및 JSON 검사는 추적되지 않거나 gitignore로 무시된 파일을 포함한 소스 파일을 검사합니다. Git 메타데이터, 생성된 Python·테스트 캐시 및 확인된 루트 가상 환경은 제외하며 추적 파일은 계속 검사합니다. 심볼릭 링크, 읽을 수 없는 파일, UTF-8이 아닌 텍스트는 차단합니다. 생성된 번들과 이야기 상태는 체크아웃 외부에 두세요. 스캐너는 파일명과 발견 범주만 보고하고 일치한 내용은 표시하지 않습니다. 이는 휴리스틱 검사이며 개인정보 안전의 증명이나 기록 스캔이 아닙니다.

## 플랫폼 경로

문서는 `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>`, `<NOVEL_PROJECTS_ROOT>` 같은 자리표시자를 사용합니다. 호스트 플랫폼에 맞게 설정하세요. 실행 가능한 초기화 도구는 `NOVEL_PROJECTS_ROOT` 또는 명시적 `--root`가 없으면 `~/.novel-os/novels`를 기본값으로 사용합니다.

## 안전 및 연구 범위

연구 스킬은 적법하고 공개 접근 가능한 자료를 대상으로 하며 로그인 장벽, CAPTCHA, 유료 접근 장벽, robots·접근 통제 또는 플랫폼 제한을 우회해서는 안 됩니다. 실존 인물 연구는 출처 기록이 필요하며 미확인 자료나 민감한 자료를 사실 주장으로 바꾸어서는 안 됩니다.

## 운영

다음을 읽어 주세요.

- [CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)
- [CODE_OF_CONDUCT.ko.md](CODE_OF_CONDUCT.ko.md)
- [SECURITY.ko.md](SECURITY.ko.md)
- [THIRD_PARTY.ko.md](THIRD_PARTY.ko.md)

## 라이선스 및 기여

상업적 사용 전에 [LICENSE](LICENSE.ko.md)와 [상업적 지급 상세](docs/COMMERCIAL_TERMS.ko.md)를 읽으세요. 관련 제품, 서비스 및 소설의 연간 양의 순이익만 포함하며 무관한 사업은 제외합니다. 자진 신고 방식이며 숨겨진 원격 측정이나 자동 징수는 없습니다. 제삼자 구성 요소는 각자의 라이선스와 고지를 유지합니다.

상업적 사용자는 사용 전에 라이선스 버전에 명시적으로 동의합니다. 비공개 신고 경로를 마련하려면 사적·재무 상세가 없는 GitHub issue로 시작하고 재무제표나 지급 기록을 공개 게시하지 마세요. 기여 및 재배포 규칙은 [CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)에 있습니다.

## 검증 한계

코어 Linux 테스트와 합성 설치 검사를 제공합니다. 선택적 Graphify·MCP·Instagram 서비스, 실제 모델, 네이티브 에이전트 연동, 여러 플랫폼·Python 버전 조합은 인증하지 않습니다. 모델 보고서 예시는 합성 설명 자료이며 공급자나 모델의 실측 성능을 보여 주는 증거가 아닙니다.
