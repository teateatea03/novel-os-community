# 로컬 설정 및 휴대형 설치

<!-- language-navigation -->

[繁體中文](../zh-TW/GETTING_STARTED.md) | [English](../../GETTING_STARTED.md) | [日本語](../ja/GETTING_STARTED.md) | **한국어** | [Español](../es/GETTING_STARTED.md) | [Français](../fr/GETTING_STARTED.md) | [Deutsch](../de/GETTING_STARTED.md) | [Português](../pt/GETTING_STARTED.md)

이 안내는 로컬 런타임과 휴대형 번들을 다룹니다. 사용 및 재배포는 [LICENSE](LICENSE.md)를 따르며 상업적 신고와 지급 상세는 [COMMERCIAL_TERMS.md](COMMERCIAL_TERMS.md)에 있습니다.

## 언어 지원 범위

공개 문서는 8개 언어로 제공됩니다. 런타임 스킬, 템플릿 및 해당 기술 참고 자료는 현재 원래 언어를 유지합니다. 이번 다국어 문서 배포는 런타임을 번역하지 않습니다.

## 모드 선택

- **로컬 도구:** Python 3.10+ 및 영속 UTF-8 파일. 코어 검증, 프로젝트 틀 생성 및 테스트는 표준 라이브러리를 사용합니다
- **에이전트 런타임:** 위 조건과 함께 같은 계층의 `SKILL.md` 패키지를 로드하고 프로젝트 파일을 읽고 쓰며 Python을 실행할 호스트가 필요합니다. `novel-operating-system`을 진입점으로 등록하세요
- **문서·수동 모드:** 셸이나 영속 파일이 없는 호스트도 템플릿을 따를 수 있지만 CLI 게이트, 설치 또는 영속 상태 처리가 실행되었다고 주장할 수 없습니다

Novel OS는 모델, API 계정, 웹 서비스 또는 비공개 원고를 포함하지 않습니다. 소스 스킬 디렉터리는 18개로, 설치 가능한 런타임 스킬 17개(조정자 1개와 협업 스킬 16개) 및 내보내기 도구입니다.

## 새 체크아웃 확인

저장소 루트에서 POSIX 셸로 다음 명령을 실행하세요.

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

실제 작업에는 별도 비공개 프로젝트 디렉터리를 사용하세요. 기존 원고나 데이터베이스를 이 체크아웃에 복사하지 마세요. 첫 합성 프로젝트에는 [README](README.md)의 `mktemp` 예제를 사용하세요. 명시적 `--root`가 `NOVEL_PROJECTS_ROOT`보다 우선하며 둘 다 없으면 초기화 도구는 `~/.novel-os/novels`를 사용합니다.

## 로컬 번들 빌드 및 테스트

다음 명령은 저장소 파일과 임시 디렉터리만 사용합니다. 업로드, 실제 모델, API 키 또는 외부 연구는 관여하지 않습니다. 생성된 페이로드가 실수로 커밋되지 않도록 빌드 결과는 소스 체크아웃 외부에 두세요.

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

전체 검증 프로필은 로컬 회귀 스위트와 함께 10만 자 이상의 합성 장편 파일럿을 실행합니다. 이는 로컬 정확성 검사이며 실제 모델 품질이나 여러 플랫폼의 인증이 아닙니다. 설치 도구는 `--upgrade`를 명시하지 않으면 기존 스킬 덮어쓰기를 거부하며 업그레이드 시 로컬 백업을 만듭니다. 첫 테스트는 운영 중인 스킬 디렉터리를 대상으로 하지 마세요.

검사를 통과한 뒤 압축 파일을 만드세요.

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

매니페스트는 모든 패키징 파일과 해시를 기록합니다. 프로젝트 라이선스, 상업적 조건 및 제삼자 안내의 8개 언어 버전과 각색 스킬 안의 변경되지 않은 Humanizer-zh 고지도 포함됩니다. 압축 파일과 설치본에 고지를 유지하세요. 설치 도구는 호스트 루트 라이선스를 덮어쓰지 않고 프로젝트 고지를 `novel-operating-system/DISTRIBUTION_NOTICES/`에 보존합니다.

## 선택적 기능

호스트에 필요한 것만 격리 환경에 설치하세요.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

이 파일은 호환 버전 범위를 나열하며 재현 가능한 잠금 파일이 아닙니다. 선택적 연동을 사용한다면 정확한 버전을 선택·시험하고 업스트림 조건을 검토하세요. 위 코어 안내에는 선택적 의존성이 필요하지 않습니다.

- NetworkX는 선택적 그래프 알고리즘·GraphML을 활성화하며 Graphify의 추가 내보내기 기능은 별도로 설치합니다
- PyYAML은 YAML NPC 투영 입력을 지원합니다. MCP 및 외부 Instagram 서버는 선택적 연동입니다
- 원래 호스트 외부에서 독립 모델 검토를 하려면 호스트별 `minis-model-use` 대체 수단이 필요합니다. 없으면 실행하지 않았다고 기록하세요
- `lieflat-less-ai-tone`은 포함되지 않습니다. 출처와 라이선스를 별도로 확인해야 합니다. 없으면 내장된 사람다운 문체 작업 흐름을 사용하고 추가 단계는 미실행으로 기록하세요

[THIRD_PARTY.md](THIRD_PARTY.md), [플랫폼 호환성](../../../skills/novel-system-exporter/references/platform-compatibility.ko.md) 및 [호스트 어댑터 계약](../../../skills/novel-system-exporter/references/host-adapter-contract.ko.md)을 참조하세요. Windows·네이티브 호스트 및 선택적 서비스 시험은 별도의 수락 작업이며 Linux 스모크 테스트가 이를 검증하지 않습니다.
