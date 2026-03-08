# Task별 문제 분석

Run: `run_20260306_190435`

참고 소스:
- `eval1_results/run_20260306_190435/run_config.json`
- `eval1_results/run_20260306_190435/summary.json`
- `biomni/eval/biomni_eval1.py`
- `biomni/eval/pipeline.py`

## 범위와 한계

이 문서는 task 단위 summary만을 바탕으로 한 1차 진단이다.
이번 run 디렉터리에는 per-instance 출력, trajectory, tool trace, raw model response가
저장되어 있지 않기 때문에, 아래 내용은 근거 기반 가설이지 완전히 확정된 root cause는 아니다.

여기서 accuracy는 `correct / done`으로 계산했다. 이번 run에서는 모든 task에서
`partial = 0`이므로 metric 해석의 모호성은 없다.

## Run 전체 관찰

- 이번 run은 정상적으로 완료되었고, `crispr_delivery`만이 아니라 Eval1의 10개 task 전체를 포함한다.
- 전체 평가 케이스 수: `433`
- 전체 accuracy: `220 / 433 = 50.8%`
- 가중 평균 latency: `53.3s / instance`
- 가중 평균 tokens: `24,045 / instance`
- 비용이 큰 실패 패턴은 주로 아래 task에 집중되어 있다.
  - `gwas_variant_prioritization`
  - `lab_bench_dbqa`
  - `rare_disease_diagnosis`
  - `screen_gene_retrieval`
- `patient_gene_detection`은 특수 케이스다. 이 task는 pipeline이 LLM 호출 없이 local KG shortcut으로
  풀 수 있기 때문에 다른 task와 직접 비교하면 안 된다.

## Task별 진단

### 1. crispr_delivery

지표:
- Accuracy: `20.0%` (`2/10`)
- Avg latency: `5.0s`
- Avg tokens: `18,762`

문제:
- 이 task는 빠르게 끝나지만, 대부분 틀리고 있다.
- 낮은 accuracy를 감안하면 token 사용량도 충분히 작지 않다. 즉, latency는 낮지만
  낭비가 큰 task다.

가능한 원인:
- evaluator는 `A-F` 중 정확한 한 글자 답을 요구한다.
- scorer의 normalizer는 자유 형식 출력에서 한 글자를 추출한다. 모델이 엄격한 최종 선택지 대신
  설명이 많은 텍스트를 출력하면 이 추출 과정은 취약해질 수 있다.
- 추출이 맞더라도, 모델이 최종 선택지를 고르는 근거가 약할 가능성이 크다.

시사점:
- 이건 search depth의 문제가 아니다.
- 최종 선택지 결정이나 답안 형식 제어 문제일 가능성이 더 크다.

### 2. gwas_causal_gene_gwas_catalog

지표:
- Accuracy: `60.0%` (`30/50`)
- Avg latency: `47.4s`
- Avg tokens: `21,127`

문제:
- 정확도는 중간 수준이지만, exact-match gene task에서 여전히 `40%`를 놓치고 있다.

가능한 원인:
- evaluator가 정확한 gene match를 요구한다.
- 시스템은 많은 케이스에서 충분한 근거를 가져오고 있을 가능성이 있지만, 최종 gene 선택이
  일관되게 잘 보정되지 않는다.
- candidate ranking 또는 gene canonicalization이 `opentargets` variant보다 약할 수 있다.

시사점:
- 핵심 문제는 runaway cost라기보다 retrieval/ranking의 잔여 오차다.

### 3. gwas_causal_gene_opentargets

지표:
- Accuracy: `76.0%` (`38/50`)
- Avg latency: `44.8s`
- Avg tokens: `19,842`

문제:
- GWAS causal-gene task 중에서는 가장 건강한 편이지만, 여전히 `24%`는 틀린다.

가능한 원인:
- 남은 오답은 심한 formatting failure라기보다 exact gene selection 문제일 가능성이 높다.
- evidence ranking은 다른 GWAS causal-gene task보다 낫지만, 애매한 케이스를 안정적으로
  닫기에는 아직 충분히 강하지 않다.

시사점:
- 이 task는 상대적으로 안정적이다.
- 더 약한 GWAS task를 디버깅할 때 기준 동작으로 삼기 좋은 task다.

### 4. gwas_causal_gene_pharmaprojects

지표:
- Accuracy: `70.0%` (`35/50`)
- Avg latency: `48.6s`
- Avg tokens: `22,834`

문제:
- 정확도는 괜찮은 편이지만, 다른 두 GWAS causal-gene task보다 비용이 더 높다.

가능한 원인:
- 검색 공간이나 evidence quality의 노이즈가 더 커서, 정확도 상승 없이 reasoning이 길어지는 것으로 보인다.
- formatting 문제보다는 retrieval noise 문제에 더 가깝다.

시사점:
- 이 task는 풀리긴 하지만, 애매함을 해소하는 데 추가 token을 쓰고도 `opentargets` 수준의
  정확도에는 못 미친다.

### 5. gwas_variant_prioritization

지표:
- Accuracy: `20.9%` (`9/43`)
- Avg latency: `83.4s`
- Avg tokens: `30,952`

문제:
- 이번 run에서 가장 나쁜 축에 드는 task다.
- 느리고 비싸며, accuracy는 거의 chance-level에 가깝다.

가능한 원인:
- evaluator는 exact variant match를 요구한다.
- pipeline은 이 task에 대해 task별 tool-call 제한, step timeout, recursion limit,
  max-step limit을 따로 둔다. 즉, 코드 차원에서도 이미 어려운 task로 취급하고 있고,
  현재 제어값이 여전히 비용 대비 과도한 탐색을 허용할 수 있다.
- 시스템은 많은 비용을 들여 검색과 reasoning을 하고 있지만, 그 근거를 최종 `rs...` 답으로
  정확히 수렴시키지 못하는 것으로 보인다.

시사점:
- search efficiency와 final selection이 동시에 문제다.
- 높은 우선순위의 최적화 대상이다.

### 6. lab_bench_dbqa

지표:
- Accuracy: `22.0%` (`11/50`)
- Avg latency: `92.4s`
- Avg tokens: `23,662`

문제:
- 정확도가 매우 낮고 latency는 매우 높다.
- latency 분산이 매우 큰 점을 보면 instance별 동작이 불안정하다.

가능한 원인:
- 다른 lab-bench task처럼 평가 기준은 exact single-letter matching이다.
- agent가 multiple-choice 답을 확정하기 전에 너무 오래 reasoning하는 것으로 보인다.
- 다른 option task에서 보이는 letter extraction 취약성도 일부 영향을 줄 수 있지만,
  더 큰 문제는 결국 한 글자가 필요한 task에 비해 reasoning이 비효율적이라는 점이다.

시사점:
- 이 task는 과하게 생각하면서도 올바른 선택지를 안정적으로 고르지 못한다.
- token spike에 비해 latency가 더 크다는 점은 느리거나 불균일한 tool/reasoning path를 시사한다.

### 7. lab_bench_seqqa

지표:
- Accuracy: `44.0%` (`22/50`)
- Avg latency: `38.2s`
- Avg tokens: `26,204`

문제:
- `lab_bench_dbqa`보다는 낫지만, token 비용 대비 성능은 여전히 좋지 않다.

가능한 원인:
- 여전히 multiple-choice 최종 선택 문제로 보인다.
- token 사용량은 run 평균보다 높은데 accuracy는 `50%`보다 낮다.
- agent가 일부 케이스는 답할 만큼의 문맥을 모으고 있지만, 그 문맥을 안정적인 최종 선택지로
  바꾸지 못하는 것으로 보인다.

시사점:
- 이 task는 너무 짧게 탐색해서 실패하는 것이 아니다.
- answer construction 단계의 신뢰도가 낮아서 실패한다.

### 8. patient_gene_detection

지표:
- Accuracy: `80.0%` (`40/50`)
- Avg latency: `1.1s`
- Avg tokens: `0`

문제:
- 이번 run에서 이 task는 일반적인 LLM task가 아니다.
- 빠르고 성능도 좋지만, 이 metric을 다른 task와 직접 비교하면 안 된다.

가능한 원인:
- pipeline에 이 task용 local KG solver가 포함되어 있다.
- token이 `0`이라는 점은 local solver가 이 케이스들을 직접 처리했음을 강하게 시사한다.
- 남은 `20%` 오류는 메인 LLM agent 문제가 아니라, HPO overlap ranking heuristic이나
  confidence threshold 동작과 관련 있을 가능성이 높다.

시사점:
- 이 task는 전반적으로 건강하지만, 일반적인 LLM reasoning 품질을 재는 지표로 보면 안 된다.

### 9. rare_disease_diagnosis

지표:
- Accuracy: `30.0%` (`9/30`)
- Avg latency: `104.5s`
- Avg tokens: `36,695`

문제:
- 이번 run에서 가장 느린 task이고, 정확도도 매우 낮은 편이다.
- 비용은 큰데 성과는 낮은 전형적인 task다.

가능한 원인:
- evaluator는 정확한 `OMIM_ID`를 요구한다.
- normalizer가 이미 출력을 `{"OMIM_ID": ...}` 형태로 맞추려고 시도하므로, 핵심 문제는
  raw formatting보다는 잘못된 disease ranking일 가능성이 더 높다.
- agent가 넓은 진단 공간을 탐색하고 있지만, 최종 disease ID로 정확히 수렴하지 못하는 것으로 보인다.

시사점:
- 이건 output-format 문제라기보다 diagnosis ranking 문제에 가깝다.
- 효율 개선 우선순위가 높은 task다.

### 10. screen_gene_retrieval

지표:
- Accuracy: `48.0%` (`24/50`)
- Avg latency: `53.7s`
- Avg tokens: `42,172`

문제:
- 이번 run에서 token 사용량이 가장 높다.
- accuracy는 `50%` 아래에 머물러 있어서 token 효율이 매우 나쁘다.

가능한 원인:
- evaluator는 exact gene symbol match를 요구한다.
- agent가 retrieval이나 reasoning을 넓게 수행하지만, 최종 gene selection이 약하다.
- token 분산이 큰 점을 보면 일부 instance는 거의 runaway exploration에 가까운 경로를 타는 것으로 보인다.

시사점:
- "토큰을 더 쓴다고 정확도가 더 좋아지지 않는다"는 점이 가장 분명하게 드러나는 task다.
- search breadth와 candidate filtering을 더 강하게 통제할 필요가 있다.

## Task 간 공통 패턴

### 패턴 A: multiple-choice task가 깔끔하게 종료되지 않는다

해당 task:
- `crispr_delivery`
- `lab_bench_dbqa`
- `lab_bench_seqqa`

관찰된 패턴:
- 이 task들은 결국 한 글자 답이 필요하다.
- 그런데 agent는 그 한 글자를 내기 전에 상당한 시간이나 token을 쓰는 경우가 많다.

해석:
- 최종 답안 제어가 약하다.
- option task에서는 자유 형식 설명문보다, 반드시 최종 answer tag를 남기도록 하는 더 엄격한 terminal format이 필요하다.

### 패턴 B: exact-match retrieval task가 애매한 ranking에 너무 많은 비용을 쓴다

해당 task:
- `gwas_causal_gene_*`
- `gwas_variant_prioritization`
- `screen_gene_retrieval`
- `rare_disease_diagnosis`

관찰된 패턴:
- 이 task들은 정확한 최종 엔티티(`gene`, `variant`, `OMIM_ID`)를 요구한다.
- 검색 공간이 애매할수록 accuracy는 크게 떨어지는데, token 사용량은 계속 증가한다.

해석:
- 현재 pipeline은 검색은 하지만, 그 근거를 정확한 exact-match 출력으로 안정적으로 수렴시키지 못한다.

### 패턴 C: 특수 heuristic이 task 간 비교를 왜곡한다

해당 task:
- `patient_gene_detection`

관찰된 패턴:
- 거의 0에 가까운 비용, 매우 낮은 latency, 그리고 높은 accuracy를 보인다.

해석:
- 엔지니어링 관점에서는 좋은 결과지만, 일반적인 agent task와 직접 비교할 수는 없다.

## 수정 우선순위

1. `gwas_variant_prioritization`
2. `rare_disease_diagnosis`
3. `screen_gene_retrieval`
4. `lab_bench_dbqa`
5. `crispr_delivery`

이유:
- 이 task들은 낮은 accuracy와 높은 시간 또는 token 비용이 동시에 나타나므로,
  디버깅 대비 개선 효과가 가장 클 가능성이 높다.

## 다음 단계에서 추가해야 할 계측

- task summary뿐 아니라 per-instance 결과도 디스크에 저장하기
- 각 instance의 normalized prediction과 raw model response 저장하기
- 각 instance의 component별 runtime token usage 저장하기
- 각 instance의 tool-call count와 마지막 사용 tool 저장하기
- option task의 경우 raw text와 별도로 최종 추출된 option을 저장하기

이런 산출물이 없으면, 현재 보고서는 실패 패턴을 식별할 수는 있어도
각 instance에서 정확히 어느 단계가 실패했는지까지는 증명할 수 없다.
