# Biomni

Biomni는 연구자가 바로 사용하는 **동료 과학자(Co-Scientist)** 를 목표로 하는 생물의학 AI 에이전트입니다.  
대규모 언어 모델(LLM) 기반 추론, 검색/리트리버, 툴 호출, 코드 실행을 통해 생물의학 질의 해결과 데이터 기반 분석을 반복 수행합니다.

이 저장소는 특히 **A1 평가 파이프라인**(실험 실행/재현) 작업공간으로 운영됩니다.

본 프로젝트는 [Stanford Biomni](https://github.com/snap-stanford/Biomni)를 기반으로 하여 평가 파이프라인/실험 구성 작업을 수행한 커스터마이징 버전입니다.


---

## 목차

- [Biomni](#biomni)
  - [목차](#목차)
  - [빠른 시작](#빠른-시작)
    - [1) 환경 준비](#1-환경-준비)
    - [2) A1 에이전트 간단 실행](#2-a1-에이전트-간단-실행)
  - [웹 모니터 (run\_web)](#웹-모니터-run_web)
    - [run\_web.py — 기본 웹 서버](#run_webpy--기본-웹-서버)
    - [run\_web\_pa.py — 병렬 평가 웹 서버](#run_web_papy--병렬-평가-웹-서버)
  - [실행 예시](#실행-예시)
    - [단일 태스크 스모크](#단일-태스크-스모크)
    - [다중 태스크 실행](#다중-태스크-실행)
    - [추가 벤치마크](#추가-벤치마크)
  - [평가 파이프라인](#평가-파이프라인)
  - [벤치마크 구성](#벤치마크-구성)
    - [Biomni-Eval1](#biomni-eval1)
    - [Lab-Bench / BixBench](#lab-bench--bixbench)
  - [실험 결과 확인](#실험-결과-확인)
  - [라이선스](#라이선스)

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

## 웹 모니터 (run\_web)

브라우저에서 Eval1 평가를 실행하고 진행 상황을 실시간으로 확인할 수 있는 웹 서버입니다.
평가 로직은 `biomni/eval/run_eval.py` (터미널 baseline) 와 동일합니다.

### 평가 흐름 (웹과 터미널 동일)

```
EvaluationPipeline (biomni/eval/pipeline.py)
  ├── make_agent_factory()  → A1 인스턴스 생성 (인스턴스마다 새로 생성)
  ├── BiomniEval1Adapter()  → 태스크 로딩 및 채점
  └── _WebSSELogger(BaseLogger) → 결과를 SSE로 브라우저에 스트리밍
```

병렬화는 **태스크 단위**: 각 태스크가 독립 스레드에서 `EvaluationPipeline`을 실행.
태스크 내 인스턴스는 순차 실행 (REPL 글로벌 namespace 충돌 방지).

### run\_web.py — 기본 웹 서버

**포트:** 8082 (기본값)

```bash
cd /home/aiffel07/wonjin/Biomni
conda activate biomni_e1

python run_web.py
# 또는 호스트/포트 지정
python run_web.py --host 0.0.0.0 --port 8082
```

브라우저에서 `http://127.0.0.1:8082` 접속.

**UI 옵션:**

- **Per-task limit** — 태스크당 실행할 instance 수
- **Split** — `val` (기본)
- **Parallel workers** — 동시에 실행할 태스크 수 (기본 1, 최대 32)
- **Task scope** — `All tasks` / `Start from task` / `Only selected tasks`

평가 결과는 `eval1_results/run_YYYYMMDD_HHMMSS/` 아래에 저장됩니다.

```
eval1_results/run_20260306_150000/
├── run_config.json
├── summary.json
└── summary.md
```

---

### run\_web\_pa.py — 병렬 워커 카드 UI

**포트:** 8083 (기본값)

```bash
cd /home/aiffel07/wonjin/Biomni
conda activate biomni_e1

python run_web_pa.py
# 또는 호스트/포트 지정
python run_web_pa.py --host 0.0.0.0 --port 8083
```

브라우저에서 `http://127.0.0.1:8083` 접속.

`run_web.py`의 평가 로직을 그대로 상속하고, 우측 패널을 워커 카드 그리드로 교체한 버전입니다.
각 워커 슬롯이 독립 카드로 표시되어 여러 태스크가 동시 진행되는 모습을 시각적으로 확인할 수 있습니다.

**PA 전용 UI 옵션:**

- **Worker card width / height** — 카드 크기 조절 (localStorage에 저장)

**권장 설정:**

```
Per-task limit: 3
Split: val
Parallel workers: 4
Task scope: All tasks (또는 Only selected tasks)
```

> 워커 수는 API rate limit과 시스템 메모리를 고려해 설정하세요.

**Stop 버튼:** 실행 중인 모든 태스크를 즉시 취소합니다 (`/api/stop` POST 호출).

---

## 실행 예시

### 단일 태스크 스모크

```bash
python biomni/eval/run_eval.py \
  --benchmark biomni_eval1 \
  --tasks gwas_variant_prioritization \
  --max-instances 1 \
  --agent-timeout-seconds 120 \
```

### 다중 태스크 실행

```bash
python biomni/eval/run_eval.py \
  --benchmark biomni_eval1 \
  --tasks crispr_delivery gwas_causal_gene_gwas_catalog patient_gene_detection \
  --split val \
  --agent-timeout-seconds 120 \
```

### 추가 벤치마크

```bash
python biomni/eval/run_eval.py --benchmark lab_bench --tasks lab_bench_dbqa --max-instances 2
python biomni/eval/run_eval.py --benchmark bixbench --max-instances 2 
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

- `lab_bench`: `futurehouse/lab-bench` subset 기반
- `bixbench`: `futurehouse/bixbench` 기반
- 공통적으로 instance 단위 순차 추론 + 채점

---

## 실험 결과 확인

기본 DB: `data/biomni_eval.db`

```python
import sqlite3

con = sqlite3.connect("data/biomni_eval.db")
cur = con.cursor()
for row in cur.execute(
    "SELECT experiment_id, task_name, instance_id, score, prediction, error "
    "FROM results ORDER BY id DESC LIMIT 50"
):
    print(row)
con.close()
```

---

## 라이선스

- Core 라이선스는 Apache-2.0 기반
- 각 도구/데이터셋의 상위 라이선스/상업 사용 조건을 반드시 별도 확인
