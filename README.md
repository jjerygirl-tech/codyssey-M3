# AI가 계산하는 방식을 흉내 내는 작은 계산기 만들기

## 프로젝트 개요

이 프로젝트는 AI에서 사용되는 MAC(Multiply-Accumulate) 연산을 Python 반복문으로 흉내 내는 작은 시뮬레이터입니다. 패턴과 필터를 같은 위치끼리 곱한 뒤 모두 더해 Cross와 X 중 어떤 필터와 더 가까운지 판정합니다.

## 개발 환경

- Python 3.8 이상
- Python 표준 라이브러리만 사용
- NumPy, pandas 등 외부 라이브러리 미사용

## 실행 방법

```powershell
python main.py
```

메뉴는 다음과 같습니다.

1. 사용자 입력(3×3)
2. `data.json` 분석
3. 보너스 패턴 생성
4. 종료

## 구현 요약

### MAC 연산

`mac_score()`는 이중 반복문으로 패턴과 필터의 같은 위치 값을 곱하고 누적합니다.
크기가 N×N이면 총 N²번의 곱셈·덧셈을 수행하므로 시간 복잡도는 O(N²)입니다.

### 라벨 정규화

JSON의 `+`와 `cross`는 내부 표준 라벨 `Cross`로 바꾸고, `x`는 `X`로 바꿉니다.
입력 표기가 달라도 같은 의미를 비교할 수 있도록 정규화합니다.

### 동점 처리

`EPSILON = 1e-9`을 사용합니다.
두 점수의 차이가 `1e-9`보다 작으면 부동소수점 오차로 보고 `UNDECIDED`로 판정합니다.

### 성능 측정

`time.perf_counter()`로 MAC 함수 호출 구간만 측정하고, 크기별로 10회 반복한 평균을 출력합니다.
입력, 출력, JSON 파일 읽기 시간은 측정에 포함하지 않습니다.

## 사용자 입력 모드

필터 A, 필터 B, 패턴을 각각 3×3으로 한 줄씩 입력합니다.
행의 숫자 개수가 맞지 않거나 숫자 파싱에 실패하면 행렬 전체를 다시 입력합니다.

예를 들어 Cross 필터와 X 필터를 입력해 비교할 수 있습니다.

## JSON 분석 모드

`data.json`에서 다음 구조를 읽습니다.

- `filters.size_5`, `filters.size_13`, `filters.size_25`
- `patterns.size_N_index`
- 각 패턴의 `input`, `expected`

패턴 키에서 N을 추출해 같은 크기의 Cross/X 필터를 선택합니다.
각 케이스는 크기와 행렬 구조를 검증하고, 문제가 있으면 해당 케이스만 FAIL 처리합니다.

## 실제 JSON 분석 결과

제공된 원본 `data.json`은 총 6개 케이스였습니다.

- 통과: 3개
- 실패: 3개

실패 케이스는 다음과 같습니다.

- `size_5_1`: Cross와 X 점수가 같아 `UNDECIDED`인데 expected가 `X`
- `size_13_2`: Cross와 X 점수가 같아 `UNDECIDED`인데 expected가 `Cross`
- `size_25_1`: Cross와 X 점수가 같아 `UNDECIDED`인데 expected가 `X`

이 결과는 원본 정답 데이터를 수정하지 않고 epsilon 동점 정책을 적용한 결과입니다. 따라서 실패 원인은 MAC 로직이 아니라 데이터의 expected 라벨과 동점 판정 정책의 차이로 분류했습니다.

실행 시 측정된 성능 예시는 다음과 같습니다. 시간은 컴퓨터 상태에 따라 달라질 수 있습니다.

| 크기 | 평균 시간(ms) | 연산 횟수 |
|---|---:|---:|
| 3×3 | 0.004200 | 9 |
| 5×5 | 0.004960 | 25 |
| 13×13 | 0.022930 | 169 |
| 25×25 | 0.075740 | 625 |

연산 횟수는 N²에 비례하며, 크기가 커질수록 평균 시간도 증가합니다. 위 시간은 한 번의 영구적인 성능 보장이 아니라 해당 PC에서 10회 반복해 측정한 예시입니다.

## 보너스 과제

### 보너스 1: 2D/1D MAC 비교

`mac_score_1d()`는 2차원 배열을 1차원으로 펼친 뒤 같은 위치끼리 곱합니다.
2D 결과와 1D 결과가 `EPSILON` 안에서 같은지 비교하고 두 방식의 평균 시간을 출력합니다.

### 보너스 2: 패턴 자동 생성

메뉴 3에서 3 이상의 홀수 크기를 입력하면 Cross와 X 패턴을 자동 생성합니다.
홀수 크기는 가운데 행과 가운데 열을 명확히 정할 수 있어 Cross 생성에 사용했습니다.

## 테스트

```powershell
python test_main.py
```

테스트 항목:

- 라벨 정규화
- 2D/1D MAC 점수 일치
- epsilon 동점 판정
- 3×3, 5×5, 13×13, 25×25 패턴 크기

## 파일 구조

```text
mission3_mini_npu/
├── main.py
├── data.json
├── test_main.py
├── README.md
└── .gitignore
```

## 클래스와 함수 책임

이번 구현은 작은 콘솔 애플리케이션의 흐름이 명확하도록 기능별 함수로 나누었습니다.

- `mac_score`: 2D MAC 계산
- `mac_score_1d`: 1D MAC 계산
- `normalize_label`: 라벨 표준화
- `validate_matrix`: 행렬 구조와 숫자 검증
- `analyze_json_mode`: JSON 케이스별 분석
- `measure_average_ms`: 반복 성능 측정
- `make_cross`, `make_x`: 패턴 자동 생성

## 향후 개선

1000×1000 대형 입력에서는 Python 리스트 전체를 메모리에 만드는 비용과 반복문 실행 시간이 커질 수 있습니다. 행 단위 처리로 메모리를 줄이거나, 실제 측정 후 더 적절한 자료구조와 병렬 처리 방식을 검토할 수 있습니다.

## 실행 증빙

- [3×3 사용자 입력 결과](docs/screenshots/mode1_user_input.png)
- [JSON 케이스별 분석](docs/screenshots/mode2_cases.png)
- [JSON 결과 요약](docs/screenshots/mode2_summary.png)
- [성능 분석표](docs/screenshots/performance.png)
- [보너스 패턴 생성](docs/screenshots/bonus_patterns.png)

이번 과제에서는 CPU에서 표준 Python 반복문으로 실행했으며, 실제 NPU 하드웨어에서 실행한 결과는 아닙니다. NPU는 많은 MAC 연산을 병렬로 처리할 수 있지만, 데이터 이동과 메모리 대역폭도 병목이 될 수 있습니다.
