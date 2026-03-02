# Biomni_MAS_LG

Biomni MAS 기반의 생의학 멀티 에이전트 실행/모니터링 저장소입니다.

## 개요

핵심 실행 흐름:

`User Query -> Router -> Plan -> Execution(verify/retry/replan) -> Synthesizer`

주요 엔트리:

- `run_mas_agent.py`: 단일 쿼리 CLI 실행
- `run_mas_web.py`: 웹 모니터 (노드 로그/평가 진행 확인)

## 디렉터리

- `biomni_mas/`: 에이전트/그래프/백엔드 코드
- `resources/`: 리소스 인덱스/도메인 소스
- `prompts/runtime/`: 런타임 프롬프트
- `data_lake/`: 분석 데이터 파일
- `scripts/`: 설치/다운로드/평가 보조 스크립트
- `eval1_test/`: Eval1 웹 모드 실행 결과 산출 디렉터리

## 빠른 시작

저장소 루트에서 실행:

```bash
conda activate biomni_mas_e1
pip install -r requirements.txt
python run_mas_web.py --host 127.0.0.1 --port 8080
# http://127.0.0.1:8080
```

단일 쿼리 CLI:

```bash
python run_mas_agent.py "Plan a genomics analysis for variant prioritization" --stream
```

## 환경 변수(.env)

`.env`가 저장소 루트에 있으면 `run_mas_agent.py`, `run_mas_web.py`에서 자동 로드됩니다.

예시:

```bash
MAS_LLM_SOURCE=OpenAI
MAS_LLM=gpt-5-mini
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
MAS_DATA_LAKE_ROOT=data_lake

# optional
MAS_OPENAI_USE_RESPONSES_API=false
ANTHROPIC_API_KEY=<OPTIONAL>
MAS_CLAUDE_TOOL_MODEL=claude-4-sonnet-latest
```

## 의존성 점검

```bash
python scripts/preflight_deps.py
python scripts/preflight_deps.py --install
```

또는 실행 시 함께:

```bash
python run_mas_agent.py "Query" --preflight-deps --preflight-install --stream
```

## Eval1 (Web Monitor)

Web UI에서 `Eval1 mode`를 켜면 task-wise batch 실행이 가능합니다.

현재 Eval1 split 사용 기준:

- `val` 기준 사용 (`train` 가이드 제거)

### 실행 옵션

- `Per-task limit`: task당 최대 실행 수
- `Task scope`:
  - `All tasks`
  - `Start from task`
  - `Only selected tasks`
- `Selected tasks`: 클릭 토글 체크박스

### 결과 산출물

`eval1_test/run_YYYYmmdd_HHMMSS/` 아래 생성:

- `run_config.json`: 실행 설정
- `<task>/case_xxxx.py`: 케이스 로그
- `<task>/case_xxxx.summary.json`: 케이스 요약/채점
- `<task>/case_xxxx.trace.json`: 실행 트레이스
- `<task>/case_xxxx.raw_events.jsonl`: raw 이벤트 스트림
- `<task>/task_summary.json`: task 요약
- `summary_all_tasks.json|md`: 전체 요약
- `run_index.json`: 케이스 인덱스

## Data Lake 다운로드

```bash
python scripts/download_data_lake.py --all
```

자주 쓰는 옵션:

- `--domain Genomics`
- `--ids 1,2,3`
- `--files file1,file2`
- `--dry-run`

## 인덱스 재생성

`resources/source` 또는 `biomni_mas/know_how` 수정 후:

```bash
python resources/scripts/build_master_index.py
```

## 트러블슈팅

- `LLM strict JSON generation failed ...`
  - 모델/키/JSON 출력 계약 점검
- 데이터 파일 누락
  - `MAS_DATA_LAKE_ROOT` 경로 확인, downloader 재실행
- Eval 로딩 실패
  - `pandas`, parquet 엔진(`pyarrow`), `huggingface_hub` 확인

## 참고

- `.pybiomart.sqlite`는 `pybiomart` 캐시 SQLite 파일입니다.
- `eval1_test/`는 실행 결과 아카이브 용도이므로 커질 수 있습니다.
