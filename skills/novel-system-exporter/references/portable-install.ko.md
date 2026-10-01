# Novel OS 가져오기 및 배포

<!-- language-navigation --> [繁體中文](portable-install.md) | [English](portable-install.en.md) | [日本語](portable-install.ja.md) | **한국어** | [Español](portable-install.es.md) | [Français](portable-install.fr.md) | [Deutsch](portable-install.de.md) | [Português](portable-install.pt.md)

## 먼저 기능을 조사하고 배포 모드를 선택하세요

전달 전에 대상 환경에 다음을 확인하세요.

```text
1. 여러 Skill·명령을 설치할 수 있는가? 진입점 디렉터리나 설정은 어디인가?
2. 에이전트가 영속 파일 읽기·쓰기, 디렉터리 목록 조회, Python·shell 실행을 할 수 있는가?
3. Python 버전은 무엇이며 networkx, graphifyy, Git 설치가 허용되는가?
4. web·browser 도구, 두 번째 모델 또는 sub-agent가 있으며 도구로 어떻게 호출하는가?
5. 새 대화, 새 worker 또는 재시작 후 프로젝트 파일은 어디에 남는가?
```

답에 따라 **A: 전체 설치**(Skills+shell+storage), **B: 어댑터 연동**(맞춤 에이전트 도구), **C: 지식 파일 모드**, **D: 단일 프롬프트 수동 모드**를 선택하세요. 전체 판단, 패키지 및 프레임워크별 어댑터 요구 사항은 [platform-compatibility.ko.md](platform-compatibility.ko.md)를 참조하세요. A/B 전제 조건이 없으면 “자동 배포”를 완료했다고 주장하지 마세요.

## 맞춤 스킬 디렉터리가 있는 AI 플랫폼(A: 전체 모드)

1. ZIP을 풉니다.
2. 압축을 푼 루트에서 실행합니다.

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. 플랫폼의 스킬을 다시 검색하거나 스킬 인덱스를 재시작합니다.
4. “장편 소설 프로젝트를 만들어 줘”로 시험합니다. `novel-operating-system`이 시작되고 프로젝트 틀을 만들며 연구·세계 구축·행동·문체·그래프 작업 필요성을 판단하고 본문 작성 전에 계획과 게이트를 완료해야 합니다.

**업그레이드:** `--upgrade`를 추가하세요. 설치 도구는 같은 이름의 기존 스킬을 `<target>/backups/novel-os-<timestamp>-<unique>/`로 옮긴 뒤 교체하며 실패하면 원본 파일을 복원합니다.

### 라이선스와 제삼자 고지

전체 ZIP은 프로젝트 라이선스, 제삼자 안내, 상업적 조건의 8개 언어 버전(총 24개 루트 고지 문서)과 각 스킬의 원래 제삼자 라이선스 파일을 보존해야 합니다. 영어는 `LICENSE`, `THIRD_PARTY.md`, `docs/COMMERCIAL_TERMS.md`이며 다른 언어는 각각 `.zh-TW.md`, `.ja.md`, `.ko.md`, `.es.md`, `.fr.md`, `.de.md`, `.pt.md`를 사용합니다(라이선스는 `LICENSE.<언어>.md`). 설치 도구는 `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`에 원래 상대 경로를 유지해 문서 내 라이선스 링크가 작동하도록 합니다. 스킬 내 업스트림 고지도 원래 위치에 남습니다. 호스트 루트의 `LICENSE`나 `docs/`를 덮어쓰지 않습니다. 업그레이드 전 고지는 원래 스킬과 함께 해당 업그레이드 백업에 저장됩니다.

`novel-operating-system/INSTALLATION.json`은 각 고지의 원본·설치 경로, SHA-256 및 바이트 수를 기록합니다. 설치 후 압축을 푼 ZIP에서 읽기 전용 검사를 실행하세요.

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

파일이 없거나 변경되면 실패합니다. 이는 로컬 무결성 검사이며 신뢰할 수 있는 배포 출처를 대신하지 않습니다. 명시적 문서 목록은 [bundle-contract.ko.md](bundle-contract.ko.md)를 참조하세요. 논의용 초안은 유효한 라이선스가 아니며 공식 조건으로 내보내지 않습니다.

수동 이식 모드 B/C/D도 프로젝트 라이선스·상업적 조건과 모든 업스트림 고지를 함께 전달해야 합니다. `skills/`만 복사하고 라이선스 문서를 빼지 마세요.

## 맞춤 에이전트·도구 호출 프레임워크(B: 어댑터 필요)

네이티브 `SKILL.md` 런타임은 없지만 system prompt, function calling 및 파일·명령 도구가 있는 프레임워크에서는 ZIP 해제만으로 배포가 완료되지 않습니다. 통합 담당자는 다음을 해야 합니다.

1. `novel-operating-system/SKILL.md`를 system/developer 지침에 넣고 description으로 의도 라우터를 구성합니다
2. 전문 스킬 16개를 라우터가 필요할 때 읽는 리소스로 제공하고 폴더 상대 관계를 유지합니다
3. 중단되거나 미완성인 작품은 먼저 `unfinished-novel-completion`에서 출처·정본·증거·의도·실현 가능성·분기·권리·출처 기록을 인계한 뒤 선택한 분기를 장편 작가에게 넘깁니다
4. 파일 읽기·쓰기, 디렉터리 목록, Python 프로세스, 영속 작업 공간, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` 및 웹 연구를 프레임워크 도구 API에 매핑합니다
5. `independent_review.py`의 `minis-model-use` 호출을 플랫폼의 두 번째 모델·sub-agent·API 연동으로 교체합니다. 없으면 이 단계를 끄고 미실행으로 기록합니다
6. 문서의 배포 수락 체크리스트로 run 간 파일 지속성과 장 완료 후 상태 갱신을 시험합니다

LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini 및 Dify/Flowise/Open WebUI의 일반적 통합 지점은 [platform-compatibility.ko.md](platform-compatibility.ko.md)에 있습니다. 모두 통합 담당자가 라우터·도구 어댑터를 만들어야 하며 이 ZIP이 낯선 클라우드 계정에 자동으로 구성할 수는 없습니다.

## Skill 가져오기 필드가 하나뿐인 플랫폼(C: 지식 파일 모드)

참고 자료를 포함한 `skills/novel-operating-system/` 전체를 업로드하거나 붙여 넣고 다른 스킬 폴더 16개를 같은 계층의 첨부·지식 파일로 유지하세요. AI에는 다음과 같이 지시하세요.

> 먼저 novel-operating-system/SKILL.md를 읽으세요. 모든 형제 스킬은 이 시스템의 필수 협업 요소입니다. shell이 없으면 동등한 Markdown/JSON 프로젝트 파일을 만들고 실행할 수 없는 게이트를 표시하세요. Git 스냅샷 생성, 검증기 실행 또는 그래프 내보내기를 완료했다고 허위로 주장하지 마세요.

## 채팅·맞춤 지침 전용 플랫폼(D: 수동 대안)

`novel-operating-system/SKILL.md`를 주 지침으로, `skills/` 전체를 검색 문서로 사용하세요. 이 모드는 작업 흐름, 템플릿, 스키마, 출력 형식, 규칙 및 체크리스트를 이식할 수 있습니다. 자동 파일 생성, 턴 간 영속성, CLI 검증, ZIP 설치 또는 트리거 감지를 보장하지는 못합니다.

### 미완성 작품 완결을 위한 배포 검사

중단 작품을 인계할 때 일반 소설 프로젝트 파일과 함께 `completion-brief.md`, `source-manifest.json`, 증거·의도·버전·분기 대장, `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json` 및 completion Gate를 유지하세요. 권리가 불분명하거나 허가받지 않은 작품은 기본적으로 `private-only`/`research` 모드이며 본문을 바로 공개하지 마세요.

프로젝트를 스킬 ZIP에 직접 넣지 말고 별도 프로젝트 폴더 또는 정리된 ZIP으로 전달하세요.

1. 먼저 실존 인물의 민감 정보, 비공개 출처, 인증 정보, 무허가 원문 또는 공유하면 안 되는 초안을 확인합니다
2. 기존 시스템의 `snapshot_project.py`, `deep_consistency.py`, `chapter_gate.py`를 실행하고 결과를 인계 메모에 포함합니다
3. `project-brief.md`에 정본 확정 마지막 장, 미완성 초안 장, 작가의 재정의 권한 및 알려진 위험을 명확히 표시합니다
4. 가져온 뒤 수령자는 story bible, 현재 상태, 연표, 독자 대장, 줄거리 실마리, 개체 등록부 및 최신 요약을 읽고 이야기를 이어가야 합니다
