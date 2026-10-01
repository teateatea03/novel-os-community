# Novel OS 플랫폼 호환성 및 의존성 표

<!-- language-navigation -->

[繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | [日本語](platform-compatibility.ja.md) | **한국어** | [Español](platform-compatibility.es.md) | [Français](platform-compatibility.fr.md) | [Deutsch](platform-compatibility.de.md) | [Português](platform-compatibility.pt.md)

이 문서는 ZIP과 함께 전달해야 합니다. Novel OS는 **스킬 지침+로컬 템플릿·Python 검증기** 모음이며 독립 모델, 채팅 플랫폼, 벡터 데이터베이스 또는 클라우드 서비스가 아닙니다. “자동 배포” 가능 여부는 대상 AI 프레임워크가 다중 파일 스킬 읽기, 파일 쓰기, 명령 실행 및 선택적 모델 호출·네트워크 접근을 허용하는지에 달렸습니다.

```text
- 조정자 1+협업 스킬 16=런타임 Skill 17개(소스에는 내보내기 도구도 포함)
- 모델 능력 호환성: novel-model-capability-compatibility. 실제 엔드포인트 probe, L0–L5, adapter, fallback 및 전환 후 회귀 담당
- 현실 상태: novel-reality-state-engine. 이벤트→상태→능력→행동→본문 검증 사슬
- 세계 데이터베이스: novel-world-database-builder
- 특수 물체 데이터베이스: special-object-database-builder. 권위 있는 root는 SPECIAL_OBJECT_DATABASE_ROOT
- 중단 작품 완결: unfinished-novel-completion
```

## 1. 코어 구성 요소와 의존성

| 구성·기능 | 시스템·형식 | 최소 의존성 | 선택적 의존성 | 없을 때 대안 |
|---|---|---|---|---|
| 스킬 배정 | `SKILL.md` YAML frontmatter+Markdown; `novel-operating-system` | 여러 텍스트 파일을 로드하는 AI·agent | description에 따라 자동 실행하는 Skills runtime | 조정자를 system prompt·project instructions로 쓰고 나머지 스킬 수동 첨부 |
| 프로젝트 영속성 | Markdown, JSON, 일반 폴더 | UTF-8 파일 읽기·쓰기 | Git | chat·Canvas·클라우드 문서에 같은 이름의 파일을 관리하고 턴 간 영속성을 보장하지 않는다고 명시 |
| 장편 초기화·로컬 gate | Python CLI, 표준 라이브러리 | **Python 3.10+**, shell, 쓰기 가능한 디스크 | Git | 템플릿·체크리스트 수동 복사, gate·snapshot 실행 주장 금지 |
| 권위 있는 관계 그래프 | Graphify 호환 node-link JSON | Python 3.10+(초기화, JSON 검증) | `networkx`: path/affected; `graphifyy`+`networkx`: HTML, 커뮤니티, Cypher | graph.json 저장·읽기, 관계 수동 조회, 시각화·최단 경로 생성 주장 금지 |
| 세계 데이터베이스 | Graphify 호환 JSON; 세계·장소·세력·자원·규칙·이벤트·주장 node, 출처 증거 및 증분 배치 | Python 3.10+, 영속 UTF-8 파일 | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | graph.json 및 Markdown 대장 저장, 버전·지식 수동 검사, 시각화 내보내기 완료 주장 금지 |
| 특수 물체 데이터베이스 | Graphify 호환 JSON; 물체·버전·변형·module·능력·사양·에너지·제약·소유·운영·수명주기 node 및 출처 증거 | Python 3.10+, 영속 UTF-8 파일 | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | graph.json 및 물체 대장 저장, 버전·사양 충돌 수동 검사, 시각화 내보내기 완료 주장 금지 |
| 대화형 소설 | JSON 호환 state, Markdown turn log | 파일 읽기·쓰기; Python 3.10+로 검증·checkpoint | 장기 기억·데이터베이스 | 매 턴 chat에 붙인 state 검토, 대화 재개 후 보존 보장 불가 |
| 완결 출처 연구·검증 | 미완성 작품 | `unfinished-novel-completion`; 연구·첨부 도구 선택 사항 | `source_ingest.py`가 hash·버전·완전성·권리 상태 기록; `completion_gate.py`가 의도 과장 및 공개 경계 검사 | |
| 독립 모델 검토 | 호스트의 모델 호출 CLI/API | 없음, 필수 아님 | 두 번째 모델·sub-agent 호출 능력 | 수동·동일 모델 체크리스트 사용, “독립 모델 검토 완료” 주장 금지 |

### 출처 연구 및 미완성 작품 도구

`unfinished-novel-completion`의 기본 도구는 Python 표준 라이브러리만 사용합니다: `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py`, `run_regression.py`. 네트워크, OCR, PDF 도구, browser 및 두 번째 모델은 모두 선택 사항입니다. 없어도 사용자 제공 파일을 처리할 수 있지만 출처 범위와 미확인 사항을 밝혀야 하며 검증한 척하면 안 됩니다.

### 최소 “완전 자동” 환경

- **Python 3.10 이상:** 현재 코어 스크립트는 `X | None` 타입 합집합 문법을 사용하며 Python 3.11+를 권장합니다
- **POSIX shell 또는 동등한 프로세스 실행기:** Python CLI 실행용
- **쓰기 가능한 영속 파일 시스템:** 스킬 설치 및 소설 프로젝트 저장용. 쓰기 가능한 스킬 디렉터리 하나와 프로젝트 디렉터리 하나 이상 필요
- **UTF-8 파일 지원:** 이야기, 템플릿, JSON 및 번체 중국어 콘텐츠 모두 UTF-8 사용
- **ZIP 해제:** ZIP 배포에서만 필요하며 Git·폴더 업로드로 대체 가능
- **로컬 표준 라이브러리:** 코어 initializer, ledger, gate, state, bundle 스크립트는 Python 표준 라이브러리에만 의존하며 기본 스모크 테스트에 `pip install` 불필요

이 기능에 API 키, 데이터베이스, Node.js 또는 네트워크 접근은 필요하지 않습니다.

### 선택적 의존성(기본 작업 흐름이 아닌 확장)

```bash
# Graph paths, cascading queries, GraphML
python -m pip install networkx

# Graphify HTML/community/Cypher exports; the upstream package is named graphifyy
python -m pip install graphifyy networkx

# Git version snapshots and gate-protected commits
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot`은 Python 표준 라이브러리만으로 사용할 수 있으며 `path`·일부 cycle 검사에는 `networkx`가 필요합니다
- `relationship_graph.py export`에는 **`networkx`+`graphifyy`**가 필요합니다. 없으면 `graph.json`을 유지하고 HTML/GraphML/Cypher 출력을 생성했다고 허위 주장하지 마세요
- `independent_review.py`는 현재 `minis-model-use`를 호출하는 **Minis 전용 어댑터**입니다. 다른 프레임워크에서는 해당 두 번째 모델·sub-agent·API 어댑터로 교체하거나 이 선택적 검토를 끄세요
- `novel_git.py`는 선택적 버전 관리 계층입니다. Git이 없어도 `snapshot_project.py`로 파일 스냅샷을 만들 수 있습니다

## 3.2 호스트 결합 지점과 필수 교체

번들 코어 데이터 형식은 이식 가능하지만 통합 담당자는 다음 **호스트·프레임워크 결합 지점**을 처리해야 합니다.

| 결합 지점 | 현재 Minis 사용 | 다른 프레임워크가 할 일 |
|---|---|---|
| 기본 소설 root | `<NOVEL_PROJECTS_ROOT>` | `NOVEL_PROJECTS_ROOT` 설정 또는 각 초기화 도구에 `--root <persistent-projects-root>` 전달. `<MINIS_ROOT>` 존재 가정 금지 |
| 인물 DB root | `<CHARACTER_DATABASE_ROOT>` | `<CHARACTER_DATABASE_ROOT>`와 배치 `<CHARACTER_DATABASE_WORK_ROOT>`를 매핑하고 같은 project·agent에서 둘 다 접근 가능하게 함 |
| 특수 물체 DB root | `<SPECIAL_OBJECT_DATABASE_ROOT>` | `<SPECIAL_OBJECT_DATABASE_ROOT>`와 배치 `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>`를 매핑하고 같은 project·agent에서 둘 다 접근 가능하게 함 |
| 대화형 소설 state root | `<INTERACTIVE_PROJECTS_ROOT>` | 매핑하여 state/checkpoints/logs를 run 간 읽게 함 |
| 독립 검토 | `minis-model-use run` | `independent_review.py`의 명령 어댑터를 다시 쓰거나 동등 sub-agent 함수 작성. JSON schema, 오류 산출물, 정본 자동 승격 금지 규칙 유지 |
| 스킬 검색 | Minis skill registry+형제 디렉터리 | description **17개**(조정자+전문 16개) 등록 또는 의도 라우터 구축, 필요 시 형제 리소스 읽기 허용 |
| 장기 상태 | Minis 공유 디렉터리 | 영속 volume, DB, artifact store 또는 framework checkpointer 매핑, project ID로 state 조회 |
| 연구 도구 | Minis browser/shell | framework browser/search/file 도구 매핑, 없으면 사용자 제공 자료로 연구 제한 |

- `init_novel_project.py`는 이미 `NOVEL_PROJECTS_ROOT`를 지원하며 명시적 `--root`가 우선합니다. 인물·세계·특수 물체 DB 및 대화형 소설의 `<..._ROOT>`는 framework router·배포 설정으로 바꿔야 합니다. 원래 문서의 `<MINIS_ROOT>/...`는 Minis 외부에서 **기본 경로의 예**이지 필수 시스템 요구 사항이 아닙니다

## 4. AI 프레임워크 능력 수준

### A | 네이티브 Skills+shell+파일 시스템(전체 모드)

Skill runtime, agent tools, sandbox·terminal이 있는 프레임워크용입니다. 전체 패키지를 직접 설치합니다.

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**프레임워크 필수 사항:**

1. `<SKILLS_DIR>/novel-operating-system/SKILL.md`를 기본 트리거 가능 스킬로 등록합니다
2. **17개** 폴더(조정자+협업 16개)를 형제로 보존하며 진입점 파일만 업로드하지 않습니다
3. agent가 형제 스킬의 `SKILL.md`, 템플릿, 참고 자료 및 스크립트를 읽도록 허용합니다
4. `python3`용 안전한 명령 도구·프로세스 실행기를 제공합니다
5. skill registry 재색인·재시작 후 스모크 테스트 결과로 수락을 판단합니다

**권장 추가 기능:** 웹 연구 도구, 두 번째 모델 어댑터, Git, `networkx`, `graphifyy`.

### B | 맞춤 agent·tool-calling 프레임워크(어댑터 필요)

system prompt, function calling 및 파일 도구는 있으나 `SKILL.md`를 이해하지 못하는 프레임워크용입니다.

**통합 담당자 필수 사항:**

1. `novel-operating-system/SKILL.md`를 agent의 system/developer 지침에 넣고 YAML description을 라우팅 규칙으로 유지합니다
2. 나머지 **16개** 스킬을 검색 가능한 참고 문서로 만들거나 사용자 의도에 맞는 `SKILL.md`를 로드할 라우터를 구성합니다
3. 도구를 매핑합니다
   - shell → Python scripts
   - read/write/list files → project files와 state
   - web search/browser → 공개 출처 연구
   - second-model/sub-agent → `independent_review.py`의 대체 어댑터
4. Minis 전용 `minis-model-use` 호출을 프레임워크 자체 model client로 교체합니다. 원래 JSON review schema, 실패 산출물 및 “machine_suggestion은 정본으로 자동 승격하지 않는다” 원칙을 유지합니다
5. 영속 storage key·workspace를 지정해 같은 작품 파일을 대화·worker 간 유지합니다
6. 자동 스킬 트리거를 구현하거나 명시적으로 끕니다. **17개 Skill 문서**를 문맥에 넣는 것만으로 자동 협업을 주장할 수 없습니다

### C | 지식 파일 업로드·맞춤 지침만 지원하는 채팅 AI(문서 모드)

작문 규칙, 템플릿, 데이터 스키마 및 체크리스트는 이식할 수 있으나 실제 자동화는 불가능합니다.

**필수:** 전체 `skills/` 하위 트리를 업로드하고 조정자를 project instructions로 설정합니다. 매 턴 작품의 현재 state, story bible, timeline, 인물 파일, reader ledger 및 이전 장 요약을 첨부하거나 AI가 참조하게 합니다.

**약속하지 말 것:** 자동 폴더 생성, CLI gates, hash 검증, Git, Graphify export, 대화 간 기억, background tasks 또는 두 번째 모델 검토.

### D | 단일 system prompt만 있는 모델(수동 대안)

요약한 조정자를 system prompt에 붙이고 전문 스킬과 프로젝트 템플릿을 지식 기반으로 사용합니다. 사용자·통합 담당자가 매 턴 생성되는 상태 문서를 수동 저장해야 합니다. 추론 틀은 유지하지만 완전한 Novel OS와 동등하지 않습니다.

## 5. 일반 프레임워크 통합 점검표

| 유형 | 배치 위치 | 필수 설정 | 주요 주의점 |
|---|---|---|---|
| OpenAI Assistants/Responses형 | System instructions+vector/file search+code interpreter/맞춤 sandbox | router, 영속 file store, Python 실행 어댑터 구축 | run 간 자동 파일 동기화 가정 금지, project file 명시적 저장 |
| Claude Projects/MCP형 | Project instructions+knowledge files; MCP filesystem/shell server | skills를 resources로 노출, MCP로 read/write/runner/web | MCP가 없으면 C이며 스크립트 실행 불가 |
| Gemini Gems/Vertex Agent형 | System instruction+File Search/Code Execution/Cloud Storage | 영속 storage, function router, Python runner 연결 | Gem 지침만으로는 보통 대화 간 파일 작업 흐름을 제공하지 않음 |
| LangChain/LangGraph/CrewAI/AutoGen형 | Router node+file tools+subprocess tool+durable checkpointer | 의도별 skill load, project ID 보존, review-agent adapter 구축 | skill 검색 및 state checkpoint 구현 필요, 압축 해제만으로 활성화 안 됨 |
| Open WebUI/AnythingLLM/Dify/Flowise형 | Knowledge base+agent workflow/tool nodes | skill file 업로드, shell/Python tool 연결, persistent volume mount | 순수 RAG chat은 C이며 A/B에는 workflow 필요 |
| 세계 DB 호스트 | `WORLD_DATABASE_ROOT`+`WORLD_DATABASE_WORK_ROOT` | 영속 world graph와 batch workspace mount, snapshot/validate/affected/export 제공 | runner 없으면 JSON/Markdown만 저장, Graphify CLI 실행 주장 금지 |
| 특수 물체 DB 호스트 | `SPECIAL_OBJECT_DATABASE_ROOT`+`SPECIAL_OBJECT_DATABASE_WORK_ROOT` | 영속 special-object graph와 batch workspace mount, snapshot/validate/affected/export 제공 | runner 없으면 JSON/Markdown만 저장, 특수 물체 검증·export 실행 주장 금지 |
| Cursor/Claude Code/Codex CLI 등 coding agent | Skills/commands directory+workspace | **17개** 폴더 설치, Python 및 workspace root 설정 | 대화형 model-review adapter는 해당 CLI에 맞게 다시 작성 필요 |

이 명칭은 통합 유형의 예시일 뿐입니다. 제품 버전, 요금제 및 권한이 다르므로 배포 전에 최신 문서를 확인하세요.

## 6. 배포 수락 체크리스트

통합 후 호스트·통합 담당자는 각 항목을 확인해야 합니다.

- [ ] `novel-operating-system`과 이웃 전문 스킬 16개를 읽을 수 있습니다
- [ ] 테스트 파일 작성 후 새 agent run·대화에서 다시 읽을 수 있습니다
- [ ] `python3 --version`이 ≥ 3.10이며 graph exporter가 필요하면 `networkx`/`graphifyy`를 import할 수 있습니다
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test`가 통과하거나 실행 불가 항목을 명시했습니다
- [ ] 새 시험 소설 프로젝트에 story bible, state, timeline, reader ledger, graph.json이 생성되었습니다
- [ ] agent가 짧은 글 작성 후 state를 갱신하고 새 run에서 계속하여 연속성이 남은 문맥만에 의존하지 않음을 보입니다
- [ ] 연구를 켰다면 검색 snippet을 정본으로 취급하지 않고 URL·출처·confidence를 기록할 수 있습니다
- [ ] 두 번째 모델 검토를 켰다면 adapter 실패가 unavailable 산출물만 만들며 중단시키거나 결과를 조작하지 않습니다

## 7. 플랫폼 한계와 책임 경계

- 대상 모델의 콘텐츠 정책, 도구 권한, token 한도, 데이터 보존 및 네트워크 규칙은 Novel OS와 독립적이며 이 Skill로 재정의할 수 없습니다
- “자동 배포”는 **설치·파일·shell 권한이 있는 agent framework 내** 자동 설치, 틀 생성 및 router load를 뜻합니다. 아무 채팅 모델에 ZIP을 준다고 영구 설치된다는 뜻이 아닙니다
- 외부 모델, browser 및 Git은 모두 선택적 확장입니다. 없으면 대체 모드를 명시하고 완료 주장으로 능력 부족을 숨기지 마세요
