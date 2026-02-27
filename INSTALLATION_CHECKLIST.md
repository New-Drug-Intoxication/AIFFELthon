# Biomni_MAS Installation Checklist

이 프로젝트는 ACT 단계에서 로컬 코드를 실행합니다.
따라서 아래 항목들이 로컬 환경에 설치되어 있어야 합니다.

- 본 저장소는 단독 실행 기준이며 `biomni` 패키지 설치를 요구하지 않습니다.

## 1) Python (필수)

- Python 3.11 권장
- 기본 설치:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

라이브러리를 일일이 설치하지 않도록 자동 생성/설치 스크립트를 제공합니다.

```bash
python scripts/generate_install_assets.py
python scripts/install_from_index.py --all --dry-run
# 실제 설치:
python scripts/install_from_index.py --python
python scripts/install_from_index.py --r
python scripts/install_from_index.py --cli
```

- 생성 결과 파일:
  - `generated/requirements.python.txt`
  - `generated/requirements.r.txt`
  - `generated/requirements.cli.txt`

## 2) LLM API 환경 변수 (필수)

fallback 없이 strict JSON 모드이므로, LLM 응답이 반드시 필요합니다.

권장 기본값(메인 GPT + 키 2개 등록):

```bash
export MAS_LLM="gpt-4o"
export MAS_LLM_SOURCE="OpenAI"

export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."  # Claude 전용 툴 사용 대비
export MAS_CLAUDE_TOOL_MODEL="claude-4-sonnet-latest"  # Claude 전용 툴 모델(메인 GPT와 분리)

export MAS_PROTOCOLS_IO_ACCESS_TOKEN="..."  # protocols.io 사용 시
```

- `advanced_web_search_claude`는 메인 모델과 별개로 `MAS_CLAUDE_TOOL_MODEL` + `ANTHROPIC_API_KEY`를 사용하도록 분리되어 있습니다.

## 3) Data Lake 경로/다운로드 설정 (권장)

```bash
export MAS_DATA_LAKE_ROOT="/absolute/path/to/data_lake"
export MAS_S3_BUCKET_URL="https://biomni-release.s3.amazonaws.com"
```

- `MAS_DATA_LAKE_ROOT`는 실제 데이터 파일 저장 경로입니다.
- 데이터레이크가 크기 때문에 디스크 용량(최소 수십 GB) 확보가 필요합니다.

필요 시 에이전트 실행 없이 data lake만 단독 다운로드할 수 있습니다.

```bash
python scripts/download_data_lake.py --all
# 또는 도메인별/ID별 다운로드
python scripts/download_data_lake.py --domain Genomics
python scripts/download_data_lake.py --ids 1,2,3
```

## 4) R 런타임 (선택이지만 권장)

프롬프트/실행 코드에서 `#!R` 경로를 타면 R이 필요합니다.

macOS 예시:

```bash
brew install r
```

R 패키지는 사용 도메인에 따라 추가 설치가 필요합니다.

## 5) Bash/CLI 생물정보학 도구 (도메인별 선택)

도메인 툴이 외부 바이너리를 호출하면 로컬 설치가 필요합니다.

자주 쓰는 예시:

```bash
brew install blast samtools bedtools bcftools
```

## 6) 설치 확인 커맨드

```bash
python -m py_compile biomni_mas/*.py run_mas_agent.py
python run_mas_agent.py "test query" --no-trace
```

## 7) 문제 발생 시 빠른 점검

- Router 단계에서 `not_dict` 오류:
  - API 키/모델 설정 확인
  - 모델이 JSON만 출력하도록 프롬프트/응답 형식 확인
- 파일 없음 오류:
  - `MAS_DATA_LAKE_ROOT` 경로 확인
  - 데이터 파일 사전 다운로드 또는 S3 URL 설정 확인
- `ModuleNotFoundError`:
  - Python 패키지 재설치
  - 가상환경 활성화 여부 확인
