# Biomni_MSA_LG

`Biomni_MSA_LG`는 생의학 문제 해결용 멀티 에이전트 시스템입니다.  
핵심 오케스트레이션은 LangGraph 상태 그래프로 동작합니다.

## 핵심 흐름

`User Query -> Router -> Plan(R1/R2/R2.1/R3/R3.1) -> Execution(반복) -> Synthesizer`

- Router: 도메인 선택 + `act_required` 판단
- Plan: 리소스 선택과 통합 계획 확정
- Execution: step 실행/검증/재시도/재계획/풀리셋 분기
- Synthesizer: 실행 근거 기반 최종 응답 생성

## 디렉터리 구조

- `biomni_msa/`
  - `agent.py`: public 엔트리(`MSAAgent.go`)
  - `graph/`: LangGraph 노드/엣지/상태
  - `llm_backend.py`: strict JSON + 토큰 집계
  - `prompt_store.py`: `prompts/runtime` 로딩
  - `resource_store.py`: `resources/index/master_index.json` 기반 리소스 조회/resolve
  - `schemas.py`: 상태/페이로드 스키마
- `prompts/runtime/`: 런타임 프롬프트
- `resources/source/`: 도메인 리소스 원본
- `resources/index/master_index.json`: 리소스 인덱스
- `data_lake/`: 분석 데이터 파일
- `scripts/`: 다운로드/평가/설치 보조 스크립트
- `run_msa_agent.py`: 단일 쿼리 실행 CLI

## 빠른 실행

저장소 루트(`Biomni_MSA_LG`)에서:

```bash
export MSA_S3_BUCKET_URL="https://biomni-release.s3.amazonaws.com"
python run_msa_agent.py "Plan a genomics analysis for variant prioritization" --stream
```

웹 모니터 실행(노드별 로그 실시간 확인):

```bash
python run_msa_web.py --host 127.0.0.1 --port 8080
# 브라우저에서 http://127.0.0.1:8080 접속
```

`.env` 자동 로드:

- 저장소 루트(`Biomni_MSA_LG/.env`)가 있으면 `run_msa_agent.py`, `run_msa_web.py` 실행 시 자동 로드됩니다.
- 예시:

```bash
MSA_LLM_SOURCE=OpenAI
MSA_LLM=gpt-4o
OPENAI_API_KEY=sk-...
MSA_DATA_LAKE_ROOT=/Users/ohhakgyoun/Desktop/MSA/Biomni_MSA_LG/data_lake
```

의존성 사전 점검(권장):

```bash
python run_msa_agent.py "Plan a genomics analysis for variant prioritization" \
  --preflight-deps --preflight-install --stream
```

- `--preflight-deps`: 도구 모듈 import 사전 점검
- `--preflight-install`: 누락 패키지 자동 설치(pip)
- `--preflight-domains Genetics,Common`: 특정 도메인만 점검
- `--preflight-continue-on-missing`: 누락이 있어도 실행 계속

주의:
- end-to-end 실행에는 LLM provider 설정/키가 필요합니다.
- Router/Verifier 등 여러 단계는 strict JSON 출력 계약을 강제합니다.

## macOS 실행 예시

```bash
cd /Users/ohhakgyoun/Desktop/MSA/Biomni_MSA_LG

conda env create -n biomni_msa_e1 -f biomni_msa_env/environment.yml
conda activate biomni_msa_e1
bash biomni_msa_env/setup.sh

export MSA_LLM="gpt-4o"
export MSA_LLM_SOURCE="OpenAI"
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
export ANTHROPIC_API_KEY="<YOUR_ANTHROPIC_API_KEY>"
export MSA_DATA_LAKE_ROOT="/Users/ohhakgyoun/Desktop/MSA/Biomni_MSA_LG/data_lake"

python run_msa_agent.py "Plan a genomics analysis for variant prioritization" --stream
```

설치 실패 확인:

```bash
cat generated/failed.python.txt
cat generated/failed.r.txt
cat generated/failed.cli.txt
```

## 토큰 집계

실행 결과에 아래 필드가 포함됩니다.

- `token_usage_by_stage`
- `token_usage_total`

집계 우선순위:
1. provider가 반환한 usage 메타데이터
2. usage가 없으면 fallback 추정
   - `tiktoken` 가능 시 tokenizer 기반
   - 불가 시 문자열 길이 기반 근사치

## 재계획/풀리셋 이력

`replan_history.note`에 분기 결과가 기록됩니다.

- `plan_revision_limit_exceeded`
- `step_retry_limit_exceeded_without_plan_revision`
- `full_reset_applied`
- `full_reset_to_no_act`
- `full_reset_limit_exceeded`
- `blocked_non_verifier_full_reset`
- `blocked_non_exception_full_reset`

## Data Lake 다운로드

```bash
python scripts/download_data_lake.py --all
```

자주 쓰는 옵션:
- `--domain Genomics`
- `--ids 1,2,3`
- `--files file1,file2`
- `--dry-run`

## 평가 실행

```bash
python scripts/run_msa_eval.py --dry-run --limit 5
python scripts/run_msa_eval.py --split val --limit 5
```

## 인덱스 재생성

`resources/source` 또는 `biomni_msa/know_how` 수정 후:

```bash
python resources/scripts/build_master_index.py
```

## Troubleshooting

- `LLM strict JSON generation failed ...`
  - provider 키/모델/출력 포맷(JSON 계약) 점검
- 데이터 파일 누락
  - `MSA_S3_BUCKET_URL` 설정 후 downloader 재실행
- eval 의존성 누락
  - `pandas` + parquet 엔진(예: `pyarrow`) 설치

- tool import 오류 (`No module named ...`)
  - 먼저 preflight 실행:
    - `python scripts/preflight_deps.py`
    - 자동 설치: `python scripts/preflight_deps.py --install`
