# Biomni

Biomni는 연구자가 바로 사용하는 **실험 동반자( Co-Scientist )**를 목표로 하는 생물의학 AI 에이전트입니다.  
대규모 언어 모델(LLM) 기반 추론, 검색/리트리버, 툴 호출, 코드 실행을 통해 생물의학 질의 해결과 데이터 기반 분석을 반복 수행합니다.

이 저장소는 특히 **A1 평가 파이프라인**(실험 실행/재현) 작업공간으로 운영됩니다.

---

## 목차

- [빠른 시작](#빠른-시작)
- [실행 예시](#실행-예시)
- [평가 파이프라인](#평가-파이프라인)
- [타임아웃/안정성 정책](#타임아웃안정성-정책)
- [벤치마크 구성](#벤치마크-구성)
- [실험 결과 확인](#실험-결과-확인)
- [개발/디버깅](#개발디버깅)
- [기여](#기여)

---

## 빠른 시작

### 1) 환경 준비

```bash
conda activate biomni_e1
pip install -U biomni
pip install git+https://github.com/snap-stanford/Biomni.git@main
```

> 이 저장소에서 실험을 돌리는 경우, 모델/도구 API 키는 `~/.bashrc` 또는 `.env`에 설정합니다.

```bash
export OPENAI_API_KEY=...
# 또는
# export ANTHROPIC_API_KEY=...
```

### 2) A1 에이전트 간단 실행

```python
from biomni.agent import A1

agent = A1(path="./data", llm="gpt-4o")
agent.go("Identify likely causal genes for breast cancer within the provided locus.")
```

---

## 실행 예시

### 단일 태스크 스모크

```bash
python biomni/eval/run_eval.py \
  --benchmark biomni_eval1 \
  --tasks gwas_variant_prioritization \
  --max-instances 1 \
  --agent-timeout-seconds 120 \
  --no-wandb
```

### 다중 태스크 실행

```bash
python biomni/eval/run_eval.py \
  --benchmark biomni_eval1 \
  --tasks crispr_delivery gwas_causal_gene_gwas_catalog patient_gene_detection \
  --split val \
  --agent-timeout-seconds 120 \
  --no-wandb
```

### 이어서 실행(재개)

```bash
python biomni/eval/run_eval.py \
  --benchmark biomni_eval1 \
  --tasks gwas_variant_prioritization lab_bench_dbqa \
  --resume \
  --resume-experiment-id 22 \
  --agent-timeout-seconds 120 \
  --no-wandb
```

### 추가 벤치마크

```bash
python biomni/eval/run_eval.py --benchmark lab_bench --tasks lab_bench_dbqa --max-instances 2 --no-wandb
python biomni/eval/run_eval.py --benchmark bixbench --max-instances 2 --no-wandb
```

---

## 평가 파이프라인

1. `run_eval.py`가 실험 조건(`--benchmark`, `--tasks`, `--split`, `--max-instances`, `--agent-timeout-seconds`)을 파싱
2. benchmark adapter가 task별 instance를 로딩
3. 각 instance마다 `A1` 인스턴스를 새로 만들어 추론 실행
4. adapter의 `evaluate_result()`로 점수 계산
5. `SQLite` 또는 `wandb`에 기록 후 다음 instance로 진행

주요 옵션:

- `--benchmark`: `biomni_eval1 | lab_bench | bixbench`
- `--tasks`: task name 목록
- `--split`: `train | val | test`
- `--max-instances`: 전체 인스턴스 중 일부만 샘플링
- `--agent-timeout-seconds`: 인스턴스 단위 타임아웃 (권장 120~180)
- `--self-critic`, `--test-time-scale-round`: A1 내부 제어 플래그
- `--resume`, `--resume-experiment-id`: 중단/재실행
- `--db-path`, `--no-wandb`: 로깅 설정

---

## 타임아웃/안정성 정책

- 기본적으로 한 인스턴스의 `agent.go()`가 지정 시간 이상 수행되면 `ERROR: ...`로 종료 처리되고 해당 인스턴스만 0점 처리됨
- 파이프라인은 전체 실험을 멈추지 않고 다음 instance로 이동
- `BIOMNI_TOOL_CALL_MAX_PER_STEP`은 동일 코드 스텝에서의 도구 호출 과다를 막는 안전장치
- GWAS/외부 API는 네트워크 지연을 고려해 타임아웃/축약 전략이 적용됨

예시:

```python
# 요약 조회 (환경 변수 예시)
BIOMNI_TOOL_CALL_MAX_PER_STEP=20
BIOMNI_GWAS_READ_TIMEOUT=25
BIOMNI_GWAS_CONNECT_TIMEOUT=5
```

---

## 벤치마크 구성

### Biomni-Eval1

- 총 433개 instance, 10개 task
- 포함 task:
  - `crispr_delivery`
  - `gwas_causal_gene_gwas_catalog`
  - `gwas_causal_gene_opentargets`
  - `gwas_causal_gene_pharmaprojects`
  - `gwas_variant_prioritization`
  - `lab_bench_dbqa`, `lab_bench_seqqa`
  - `patient_gene_detection`
  - `rare_disease_diagnosis`
  - `screen_gene_retrieval`

### Lab-Bench / BixBench

- `lab_bench`: `futurehouse/lab-bench` subset 기반(대표: DbQA, SeqQA)
- `bixbench`: `futurehouse/bixbench` 기반
- 공통적으로 instance 단위 순차 추론 + 채점

---

## 실험 결과 확인

기본 DB: `biomni_eval.db`

```python
import sqlite3

con = sqlite3.connect("biomni_eval.db")
cur = con.cursor()
for row in cur.execute(
    "SELECT experiment_id, task_name, instance_id, score, prediction, error "
    "FROM results ORDER BY id DESC LIMIT 50"
):
    print(row)
con.close()
```

---

## 개발/디버깅

- 로그는 실험 진행(전체 진행률, timeout, 오류)을 중심으로 확인
- 긴 출력은 `output is too long` 같은 메시지와 함께 요약 보조 함수(`preview`, `summarize_df`)를 통해 후처리 가능
- 문제 해결 시점:
  - timeout이 잦은 태스크는 `--agent-timeout-seconds` 축소
  - tool call 과부하는 `BIOMNI_TOOL_CALL_MAX_PER_STEP` 조정
  - 네트워크 민감 태스크는 task별로 분할/재개 실행

---

## 기여

버그 수정, 벤치마크/툴 개선, 결과 해석 자동화 스크립트 모두 환영합니다.  
기여 전 `run_eval.py` 실행 옵션, 기본 timeout 정책, 결과 스키마를 먼저 확인해 주세요.

---

## 라이선스

- Core 라이선스는 Apache-2.0 기반
- 각 도구/데이터셋의 상위 라이선스/상업 사용 조건을 반드시 별도 확인

