# Novel OS 호스트 어댑터 계약

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | [日本語](host-adapter-contract.ja.md) | **한국어** | [Español](host-adapter-contract.es.md) | [Français](host-adapter-contract.fr.md) | [Deutsch](host-adapter-contract.de.md) | [Português](host-adapter-contract.pt.md)

이 계약은 Minis 외 AI 프레임워크 통합 담당자를 위한 것입니다. Novel OS는 ZIP 업로드만으로 파일 접근, 모델 접근 또는 대화 간 기억을 얻는 플러그인이 아닙니다. 자동 배포라고 하려면 호스트가 다음 기능을 제공해야 합니다.

## A. 호스트가 제공해야 할 최소 인터페이스

| 기능 | 최소 작업 | Novel OS 용도 | 없을 때 |
|---|---|---|---|
| Skill router | `load_skill(name)`/리소스 파일 읽기 | 조정자가 의도에 따라 전문 스킬 16개를 로드 | 해당 Skill을 프롬프트에 수동 포함 |
| 영속 저장소 | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | 프로젝트 성경, 장, 대장, state, 그래프, 스냅샷 | 문서 전용 모드이며 run 간 연속성 보장 불가 |
| Process runner | `run(argv, cwd)` | Python 초기화·gate·state·graph 도구 실행 | 템플릿·체크리스트 수동 사용, 검증 실행 주장 금지 |
| Project identity | 안정적인 `project_id` → storage root | 새 대화·worker에서 동일 소설 상태 읽기 | 매번 사용자가 파일·요약을 수동 제공 |
| Branch writer lock | `lock(project,session,branch)`/트랜잭션 잠금 | recovery, stale-hash, event, state, manifest commit 직렬화 | single-writer만 허용하며 다중 worker 안전성 주장 금지 |
| Model task adapter | `minis.model-task.v1` 수신, schedule 먼저 영속화, worker가 lease로 claim, 고정 schema 반환 | L1/L2 모델을 개별 extract/plan/render/repair 작업으로 제한, retry/cancel/stale/restart recovery 지원 | 문서 모드·수동 양식이며 모델에 state 권한 없음 |
| Runtime/event versioning | Runtime build, event schema, transition contract, golden replay fixture | 업그레이드 후 과거 기록 재생도 동일 state hash, 미지 계약 차단 | 기존 런타임 고정, 수동 이관 후에만 업그레이드 |
| Story solver | 상한이 있는 storylet 상태 탐색 | unreachable, broken target, soft lock을 찾고 탐색 한계 공개 | 수동 경로 검토, 모든 경로 검증 주장 금지 |
| Random-event suggestion control | branch별 `off`/`on-suggestion`, semantic window, seeded pool, non-canonical audit | 적합한 창에서만 선택적 방향 카드 제안, no-event와 재현 가능한 출처 보존 | `off` 고정, 프롬프트로 몰래 추첨하거나 제안을 정본 취급하지 않음 |
| Memory/Graph projector | event → episodic memory; events → Graphify projection | 추적 가능한 기억과 재구축 가능한 그래프 | events 보존, 파생 인덱스를 미갱신으로 표시 |
| Graphify completion index | `sync_graph.py`가 출처·주장·분기를 기존 `graph.json`에 동기화 | 출처, 증거, 버전, 완결 가설 조회 | 그래프는 파생 인덱스이며 본문·정본을 역방향 덮어쓰기 금지 |

프로세스 실행기는 **결합된 shell 문자열보다 argv 배열**을 우선하고 프로젝트·스킬 작업 공간 안에서만 실행하며 stdout, stderr, exit code를 gate 산출물로 보존해야 합니다.

## B. 경로 매핑

배포 설정은 다음 값을 제공해야 하며 다른 환경에 Minis 경로를 하드코딩하지 마세요.

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py`는 `NOVEL_PROJECTS_ROOT`를 읽거나 명시적 `--root`를 받습니다
- `SPECIAL_OBJECT_DATABASE_ROOT`는 특수 물체 데이터베이스의 권위 있는 원본 `graphify-out/graph.json`을 저장합니다. `SPECIAL_OBJECT_DATABASE_WORK_ROOT`는 배치 JSON·인계 패키지이며 원본을 대체할 수 없습니다
- `WORLD_DATABASE_ROOT`는 세계 데이터베이스의 권위 있는 원본 `graphify-out/graph.json`을 저장합니다. `WORLD_DATABASE_WORK_ROOT`는 세계 배치 JSON·인계 패키지이며 원본을 대체할 수 없습니다
- 다른 root는 라우터·프레임워크 어댑터 설정입니다. 관련 Skill의 `<..._ROOT>` 자리표시자를 실제 영속 경로로 바꿉니다
- 한 소설의 모든 파일은 다시 읽을 수 있는 같은 프로젝트 루트에 있어야 합니다. 최신 장만 임시 채팅 문맥에 보관하지 마세요

## C. 필수 배포 절차

1. 번들을 풀고 먼저 실행합니다.

   ```bash
   # First confirm Python, hashes, and the complete smoke test are available:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. **17개** Skill(조정자+전문 16개)을 등록합니다. `novel-reality-state-engine`은 event/state JSON, Reality Card, 실행 가능한 Reality Gate를 제공해야 합니다. `novel-model-capability-compatibility`는 실제 엔드포인트의 text/JSON/tool/state probe, 능력 수준 및 fallback을 제공해야 합니다. `novel-sensory-sound-prose`는 소리·오감 본문 계약을 유지해야 합니다. 형제 상대 경로를 보존합니다
3. `project_id`를 위 영속 root에 매핑하고 에이전트에 해당 프로젝트 파일 읽기·쓰기를 허가합니다
4. 새 프로젝트 초기화 도구를 실행하여 Markdown/JSON/`graphify-out/graph.json`이 모두 생성되는지 확인합니다
5. 에이전트 run을 종료하고 새 run을 시작하여 계속 쓰기 전에 상태를 읽게 하여 임시 문맥에 의존하지 않는지 확인합니다
6. 같은 소스 state hash에 두 worker가 동시 commit하게 합니다. 정확히 하나만 성공하고 다른 하나는 stale-hash/conflict여야 합니다. 그 뒤 event replay로 현재 state hash를 확인합니다
7. episodic memory 2개를 만들고 reflection이 기존 evidence ID를 최소 2개 인용하는지 확인합니다. L1 render task를 컴파일하여 패키지에 hidden truth가 없고 `may_commit_state=false`인지 확인합니다
8. events에서 대화형 Graphify projection을 재구축합니다. 삭제하고 다시 구축해도 source hash가 같아야 합니다
9. golden-history fixture를 최소 하나 보존합니다. 새 런타임으로 재생하면 기대 state hash가 나와야 하며 알 수 없는 transition contract는 거부해야 합니다
10. model activity를 만들어 lease 만료 후 복구, state 전진 후 이전 결과 stale 표시, activity pending 중 author console 차단을 검증합니다
11. unreachable state, broken target, soft lock이 있는 storylet fixture를 만들고 solver가 모두 감지하며 max depth/max states를 명시하는지 확인합니다
12. events를 compact한 후 인덱스를 지우고 archive를 변조합니다. manifest integrity gate는 인덱스 재구축 전에 거부해야 합니다
13. 새 branch가 기본 `off`이며 추첨이나 audit 쓰기가 없는지 확인합니다. 사용자가 `on-suggestion`을 켠 뒤 scene 경계에서 고정 seed로 같은 suggestion/no-event를 얻고 정본 event log, State, Graph, Knowledge 및 본문이 변하지 않는지 확인합니다
14. meta input, 보류 중인 직접 결과, 자연스러운 휴지가 없는 고압 상황, 기존 결정적 결과, 복선 없는 위협에 대한 요청을 보냅니다. 모두 억제되어야 합니다. 제안 채택은 계획 인계만 만들 수 있으며 Reality/Knowledge/Agency/Behavior/World/Canon Gates를 나열해야 합니다
15. active segment의 manifest hash/bytes/count를 검증합니다. event index를 지운 뒤 active log를 변조하면 차단되어야 합니다. activity claim은 fencing token을 반환하며 이전 token, token 누락, lease 만료 시 완료를 거부해야 합니다. 파일 기반 ID는 모두 path traversal을 거부해야 합니다. 같은 random-event `request_id` 재시도는 재추첨이나 두 번째 audit 항목을 만들면 안 됩니다. 변조된 audit hash chain은 재생하지 않고 만료된 제안은 adoption handoff를 만들면 안 됩니다

## D. 선택적 도구 어댑터

### 웹 연구

호스트가 browser/search 도구를 제공하면 라우터는 검색 결과, URL, 발행자, 날짜 및 짧은 인용을 research/graph 증거 필드에 기록해야 합니다. browser가 없으면 사용자 제공 자료만 처리하고 `【待定】`(미정)/`【提案】`(제안)을 사용하며 출처를 확인한 척하지 마세요.

### 두 번째 모델·sub-agent 검토

`long-form-novel-writer/scripts/independent_review.py`는 현재 Minis의 `minis-model-use`를 호출합니다. 다른 프레임워크는 다음 중 하나를 수행해야 합니다.

1. `role`, `prompt`, `max_tokens`를 받아 다른 모델·sub-agent를 호출하고 원문 및 파싱한 JSON을 `reviews/`에 저장하는 어댑터 작성
2. 독립 검토를 끄고 로컬 gate·수동 체크리스트를 사용하며 인계에 “두 번째 모델 미실행” 표시

어느 경우에도 출력 규칙을 보존합니다. `machine_suggestion`을 `[CANON]`으로 바로 승격할 수 없습니다. 뒷받침 증거 2개가 없는 이슈는 `questions`에만 넣습니다. 실패는 `unavailable` 산출물을 만들어야 하며 몰래 통과로 계산하면 안 됩니다.

### 그래프와 버전 관리

- `networkx`: path, affected, GraphML 및 관련 기능 활성화
- `graphifyy`+`networkx`: Graphify HTML, 커뮤니티 분석 및 Cypher 내보내기 활성화
- Git: commit·branch 전용이며 없어도 파일 스냅샷 사용 가능

이들은 확장 기능이며 소설 시작의 전제 조건이 아닙니다.

## E. 최소 라우터 논리

```text
if request is to create/update/query/compare/export a special-object database:
    load special-object-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add character-db + behavior when operator/autonomous-machine/personality matters
    add long-form when linked to a novel project or chapter state
elif request is to create/update/query/export a world database:
    load novel-world-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add long-form when linked to a novel project or chapter state
elif request is cross-chapter writing/continuation/outline revision:
    load long-form + behavior
    add world/style/graph only when the story state needs them
elif request is character research:
    load character-deep-digger
    add behavior + character-db/graph when evidence or persistence is needed
elif request is a human-voice/Taiwan Traditional Chinese/character-voice revision:
    load human-voice-editor after content/continuity/style checks
elif request is completion of an abandoned/unfinished novel, original-author intent, or an alternative ending:
    load unfinished-novel-completion
    add long-form + evidence/source tools + world/behavior/style/graph as needed
elif request is free-input interactive fiction:
    load immersive-interactive-fiction
    add world/behavior/style/graph by scene complexity
```

조정자가 먼저 이 라우터를 처리해야 합니다. 매 턴 모든 Skill을 무작정 모델 문맥에 넣지 마세요.

## F. 번들이 자동으로 할 수 없는 것

- 허가받지 않은 클라우드 계정에 Skill 설치, API 키 설정, 도구 권한 활성화 또는 데이터베이스 생성
- 채팅 전용 모델에 shell, 파일 시스템, 영구 기억 또는 다중 모델 능력 부여
- 대상 모델·플랫폼의 콘텐츠 정책, token 제한, 개인정보 규칙 또는 네트워크 제한 재정의

전제 조건이 하나라도 없으면 [platform-compatibility.ko.md](platform-compatibility.ko.md)의 B/C/D 대안을 사용하고 배포 보고서에 비활성화된 각 기능을 나열하세요.
