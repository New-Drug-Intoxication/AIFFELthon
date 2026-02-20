# Biomni_MSA

Biomni_MSA는 생의학 문제 해결을 위한 독립형 멀티 에이전트 오케스트레이션 프로젝트입니다.
기존 Biomni의 단일 에이전트 스타일을 실행 중심(Execution-centric) MSA 워크플로우로 전환하는 것을 목표로 합니다.

설계 기준:

- 아키텍처 기준 문서: `MSA.txt`
- 목표: Biomni의 리소스/툴 강점은 유지하고, 오케스트레이션 구조를 개선

## 한눈에 보기

- Router가 도메인 에이전트와 `act_required`를 결정
- Plan은 다중 라운드(`R1 -> R2 -> R2.1 -> R3 -> R3.1`)로 진행
- Execution은 스텝 단위(`Exec R1 코드 실행 -> Exec R2 검증`)로 반복
- 재계획은 Verifier의 `PLAN_REVISION`으로만 트리거
- 최종 답변은 실행 결과 근거를 바탕으로 Synthesizer가 생성

## 저장소 구조

상위 디렉터리/파일:

- `biomni_msa/`: 코어 런타임 패키지
- `resources/`: 도메인 리소스 정의 + 생성 인덱스
- `prompts/`: 시스템/런타임 프롬프트
- `scripts/`: 다운로드/평가/설치 보조 CLI
- `run_msa_agent.py`: 단일 질의 실행 엔트리포인트
- `INSTALLATION_CHECKLIST.md`: 환경/의존성 설치 체크리스트
- `msa_migration_execution_plan.txt`: 마이그레이션 메모

### `biomni_msa/` 상세

- `biomni_msa/agent.py`
  - 메인 오케스트레이터 (`MSAAgent.go`)
  - 라우팅, 플랜 라운드, 실행 루프, 부분 재계획, 합성 처리
- `biomni_msa/schemas.py`
  - 워크플로우 상태/페이로드 스키마
- `biomni_msa/llm_backend.py`
  - 단계별 strict JSON 생성/검증 백엔드
- `biomni_msa/config.py`
  - 경로/런타임 설정 (`MSAPaths`, 실행 옵션)
- `biomni_msa/prompt_store.py`
  - `prompts/runtime` 프롬프트 로더
- `biomni_msa/resource_store.py`
  - 인덱스 기반 리소스 조회 및 선택 ID resolve
- `biomni_msa/data_lake.py`
  - data lake 선택/다운로드 보조 로직
- `biomni_msa/core/`
  - 독립 실행용 호환 모듈 (`llm`, `execution`, `data_utils`, `config`)
- `biomni_msa/know_how/`
  - know-how 문서 및 로더
- `biomni_msa/eval/`
  - Eval1 호환 평가기 및 답변 정규화

### `resources/` 상세

- `resources/source/`
  - 도메인별 리소스 원본
  - 공통 패턴: `descriptions/*.py`, `tools/*.py`, `env_desc.py`
- `resources/index/master_index.json`
  - 런타임에서 사용하는 생성 인덱스
  - `tools`, `data_lake`, `libraries`, `know_how` 포함
- `resources/scripts/build_master_index.py`
  - `master_index.json` 재생성
- `resources/scripts/resolve_selected_resources.py`
  - 선택 리소스 ID를 사람이 읽을 수 있는 스펙으로 변환

### `prompts/` 상세

- `prompts/runtime/`
  - 실제 런타임에서 사용하는 프롬프트
- `prompts/raw/`
  - 원본 프롬프트 보관

## Workflow (MSA.txt 기반)

실행 관점의 핵심 흐름:

`User Query -> Router -> Plan -> Execution Loop -> (필요 시 Replan) -> Synthesizer`

### 1) Router

- 입력: `user_query`
- 출력: `selected_agents`, `route_reason`, `act_required`, `domain_scores`
- 규칙: Router는 라우팅만 담당 (계획/실행/검증을 수행하지 않음)
- 분기:
  - `act_required=false` -> 바로 Synth 응답
  - `act_required=true` -> Plan 진입

### 2) Plan (Debate-free, Multi-round)

- R1: 각 도메인이 리소스 ID 선택 (`tools`, `data_lake`, `libraries`, `know_how`)
- R2: 각 도메인이 실행 가능한 체크리스트 스텝 초안 작성
- R2.1: Orchestrator가 초안 병합 (`draft_master_plan`)
- R3: 도메인별 비평
- R3.1: Orchestrator가 비평 반영 후 최종 계획 확정 (`final_master_plan`)

핵심 규칙:

- Debate-free: 도메인 간 직접 토론 없이 라운드별 독립 응답
- Single-owner: 각 스텝은 반드시 한 명의 `owner_agent`
- 각 스텝은 검증 가능한 `success_criteria`를 포함

### 3) Execution Loop (스텝 단위 반복)

- 각 스텝은 지정된 owner 도메인만 실행
- Exec R1: 코드/호출 생성 및 실행, `observe_output` 생성
- Exec R2 Verifier는 아래 중 하나만 반환
  - `SUCCESS`: 다음 스텝 진행
  - `FAILURE`: 동일 스텝 재시도
  - `PLAN_REVISION`: 재계획 필요
- 이전 스텝 핸드오프는 길이 제한(`10000` chars) 적용

### 4) Replanning

- 재계획은 Verifier의 `PLAN_REVISION`으로만 트리거
- 기본 범위는 부분 재계획(실패 스텝 + 이후 tail)
- 실패 스텝 이전 prefix는 기본 보존
- 재진입 깊이:
  - 기본: Plan R2부터 재진입
  - 예외: 리소스 재선정 필요 시 R1부터 재진입
- Full reset은 예외 케이스(데이터 붕괴, 라우팅 무효, 안전/정책 이슈)에서만 허용

## State machine (구현 라벨)

코드 상태 라벨 (`biomni_msa/schemas.py`):

- `S_ROUTER`
- `S_PLAN_R1`
- `S_PLAN_R2`
- `S_PLAN_R21`
- `S_PLAN_R3`
- `S_PLAN_R31`
- `S_EXEC_R1`
- `S_EXEC_R2`
- `S_SYNTHESIZER`

실행 추적은 `state_transition_history`에서 확인할 수 있습니다.

## 빠른 실행

저장소 루트에서 실행:

```bash
export MSA_S3_BUCKET_URL="https://biomni-release.s3.amazonaws.com"
python run_msa_agent.py "Plan a genomics analysis for variant prioritization" --stream
```

주의:

- end-to-end 실행에는 LLM provider 설정/키가 필요합니다.
- 단계 출력은 strict JSON 계약을 따르며, 형식 불일치 시 즉시 실패합니다.

## macOS 실행 가이드 (가상환경)

`data_lake`를 이미 내려받은 상태라면 아래 순서로 바로 실행할 수 있습니다.

```bash
cd /Users/ohhakgyoun/Desktop/MSA/Biomni_MSA

# 1) 원라인 전체 설치 (Python/R/CLI 분리 설치 오케스트레이션)
conda env create -n biomni_msa_e1 -f biomni_msa_env/environment.yml

# 2) 환경 활성화
conda activate biomni_msa_e1

# 3) 설치 실행
bash biomni_msa_env/setup.sh

# 4) 환경 변수 설정 (메인 GPT + Claude 전용 툴 분리)
export MSA_LLM="gpt-4o"
export MSA_LLM_SOURCE="OpenAI"
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
export ANTHROPIC_API_KEY="<YOUR_ANTHROPIC_API_KEY>"
export MSA_CLAUDE_TOOL_MODEL="claude-4-sonnet-latest"

# 5) data lake 경로 지정 (이미 다운로드한 경우)
export MSA_DATA_LAKE_ROOT="/Users/ohhakgyoun/Desktop/MSA/Biomni_MSA/data_lake"

# 6) 실행
python run_msa_agent.py "Plan a genomics analysis for variant prioritization" --stream
```

설치 후 실패 항목 확인:

```bash
cat generated/failed.python.txt
cat generated/failed.r.txt
cat generated/failed.cli.txt
```

빠른 점검:

```bash
python run_msa_agent.py "이 시스템이 무엇을 하는지 3문장으로 설명해줘" --no-trace
```

## Data Lake

전체 data lake 다운로드:

```bash
python scripts/download_data_lake.py --all
```

자주 쓰는 옵션:

- `--domain Genomics`
- `--ids 1,2,3`
- `--files file1,file2`
- `--dry-run`

기본 경로는 `./data_lake`이며, `MSA_DATA_LAKE_ROOT`로 변경할 수 있습니다.

## Evaluation (P2)

평가 인스턴스 선택만 확인(dry-run):

```bash
python scripts/run_msa_eval.py --dry-run --limit 5
```

실제 평가 실행(LLM 설정 + pandas/parquet 필요):

```bash
python scripts/run_msa_eval.py --split val --limit 5
```

주요 옵션:

- `--dataset <local_parquet_path>`
- `--task <task_name>`
- `--split train|val`
- `--limit N`
- `--llm-model <model_name>`

## 리소스 인덱스 재생성

`resources/source` 또는 `biomni_msa/know_how`를 수정했다면 인덱스를 재생성하세요:

```bash
python resources/scripts/build_master_index.py
```

## 설치/환경 보조

실행 전 `INSTALLATION_CHECKLIST.md`를 먼저 확인하세요.

보조 스크립트:

```bash
python scripts/generate_install_assets.py
python scripts/install_from_index.py --all --dry-run
```

## Troubleshooting

- `LLM strict JSON generation failed ...`
  - provider 키/모델 설정 및 출력 포맷(JSON 계약) 확인
- 런타임에서 data lake 파일 누락
  - `MSA_S3_BUCKET_URL` 확인 후 downloader 재실행
- `Missing optional dependency for eval runner`
  - `pandas` + parquet 엔진(예: `pyarrow`) 설치
