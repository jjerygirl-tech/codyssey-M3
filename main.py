import json
import math
import random
import re
import time
from pathlib import Path


# 1e-9은 일반적인 부동소수점 누적 오차를 허용하면서 실제 점수 차이는
# 구분하기 위한 절대 허용오차입니다. 값의 규모가 크게 달라지면 조정할 수 있습니다.
EPSILON = 1e-9
MEASURE_REPEATS = 10
DATA_FILE = Path("data.json")


def normalize_label(label):
    if not isinstance(label, str):
        return None

    value = label.strip().lower()

    if value in ("+", "cross"):
        return "Cross"
    if value in ("x",):
        return "X"
    return None


def read_label(name):
    while True:
        value = input(f"{name} 라벨 (Cross/+ 또는 X/x): ").strip()
        normalized = normalize_label(value)

        if normalized is not None:
            return normalized

        print("라벨 입력 오류: Cross, +, X, x 중 하나를 입력해주세요.")


def validate_matrix(matrix, size, name="행렬"):
    if not isinstance(matrix, list) or len(matrix) != size:
        return False, f"{name}의 행 수가 {size}가 아닙니다."

    for row_number, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != size:
            return False, f"{name} {row_number}행의 열 수가 {size}가 아닙니다."

        for value in row:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"{name}에 숫자가 아닌 값이 있습니다."
            if not math.isfinite(float(value)):
                return False, f"{name}에 NaN 또는 무한대가 있습니다."

    return True, ""


def parse_row(text, size):
    parts = text.strip().split()

    if len(parts) != size:
        raise ValueError(f"각 줄에 {size}개의 숫자를 입력해야 합니다.")

    values = [float(part) for part in parts]

    if not all(math.isfinite(value) for value in values):
        raise ValueError("NaN 또는 무한대는 입력할 수 없습니다.")

    return values


def read_matrix(size, name):
    while True:
        print(f"\n{name} ({size}줄, 각 줄에 숫자 {size}개)")
        matrix = []

        try:
            for row_number in range(1, size + 1):
                text = input(f"{row_number}행: ")
                matrix.append(parse_row(text, size))
            return matrix
        except ValueError as error:
            print(f"입력 형식 오류: {error}")
            print(f"예시: {' '.join(['0'] * size)}")
            print("행렬 전체를 다시 입력해주세요.")


def mac_score(pattern, filter_matrix):
    size = len(pattern)
    score = 0.0

    for row in range(size):
        for column in range(size):
            score += pattern[row][column] * filter_matrix[row][column]

    return score


def mac_score_1d(pattern, filter_matrix):
    pattern_1d = [value for row in pattern for value in row]
    filter_1d = [value for row in filter_matrix for value in row]
    return sum(
        pattern_value * filter_value
        for pattern_value, filter_value in zip(pattern_1d, filter_1d)
    )


def classify(score_a, score_b):
    difference = abs(score_a - score_b)

    if difference < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return "Cross"
    return "X"


def measure_average_ms(function, repeats=MEASURE_REPEATS):
    """I/O를 제외하고 MAC 함수 호출 구간만 반복 측정합니다."""
    elapsed_times = []

    for _ in range(repeats):
        start = time.perf_counter()
        function()
        end = time.perf_counter()
        elapsed_times.append(end - start)

    return sum(elapsed_times) / len(elapsed_times) * 1000


def make_cross(size):
    center = size // 2
    return [
        [
            1.0 if row == center or column == center else 0.0
            for column in range(size)
        ]
        for row in range(size)
    ]


def make_x(size):
    return [
        [
            1.0 if column == row or column == size - row - 1 else 0.0
            for column in range(size)
        ]
        for row in range(size)
    ]


def run_user_mode():
    print("\n[1] 필터 입력")
    filter_a = read_matrix(3, "필터 A")
    filter_b = read_matrix(3, "필터 B")
    label_a = read_label("필터 A")
    label_b = read_label("필터 B")

    print("\n[2] 패턴 입력")
    pattern = read_matrix(3, "패턴")

    score_a = mac_score(pattern, filter_a)
    score_b = mac_score(pattern, filter_b)
    raw_decision = classify(score_a, score_b)
    decision = raw_decision
    if raw_decision == "Cross":
        decision = label_a
    elif raw_decision == "X":
        decision = label_b
    time_a = measure_average_ms(lambda: mac_score(pattern, filter_a))
    time_b = measure_average_ms(lambda: mac_score(pattern, filter_b))

    print("\n[3] MAC 결과")
    print(f"필터 A ({label_a}) 점수: {score_a:.10f}")
    print(f"필터 B ({label_b}) 점수: {score_b:.10f}")
    print(
        f"평균 연산 시간(ms, {MEASURE_REPEATS}회): "
        f"A={time_a:.6f}, B={time_b:.6f}"
    )
    if raw_decision == "UNDECIDED":
        print("판정: 판정 불가 (UNDECIDED, 사용자 모드에서는 PASS/FAIL 집계 없음)")
    else:
        print(f"판정: {decision}")
    print("비교 정책: abs(A-B) < 1e-9이면 UNDECIDED")

    run_optimization_demo(pattern, filter_a)


def load_json_data():
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("최상위 JSON 구조가 객체가 아닙니다.")
        return data
    except FileNotFoundError:
        print(f"{DATA_FILE} 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError as error:
        print(f"JSON 형식 오류: {error}")
    except OSError as error:
        print(f"파일 읽기 오류: {error}")
    except ValueError as error:
        print(f"데이터 형식 오류: {error}")
    return None


def get_size_from_key(key):
    match = re.fullmatch(r"size_(\d+)_\d+", key)
    return int(match.group(1)) if match else None


def get_filter_pair(filters, size):
    size_key = f"size_{size}"
    size_filters = filters.get(size_key)

    if not isinstance(size_filters, dict):
        raise ValueError(f"{size_key} 필터가 없습니다.")

    cross = size_filters.get("cross")
    x_filter = size_filters.get("x")

    for label, matrix in (("Cross", cross), ("X", x_filter)):
        valid, reason = validate_matrix(matrix, size, f"{size_key} {label}")
        if not valid:
            raise ValueError(reason)

    return cross, x_filter


def analyze_json_mode():
    data = load_json_data()

    if data is None:
        return

    filters = data.get("filters")
    patterns = data.get("patterns")

    if not isinstance(filters, dict) or not isinstance(patterns, dict):
        print("FAIL: filters 또는 patterns 구조가 없습니다.")
        return

    total = 0
    passed = 0
    failed = 0
    undecided = 0
    failures = []
    failure_types = {}
    performance_inputs = {}

    print("\n[1] JSON 필터·패턴 분석")

    for case_key, case_data in patterns.items():
        total += 1
        reason = ""

        try:
            size = get_size_from_key(case_key)
            if size is None:
                raise ValueError("패턴 키가 size_N_index 형식이 아닙니다.")

            if not isinstance(case_data, dict):
                raise ValueError("패턴 데이터가 객체가 아닙니다.")

            pattern = case_data.get("input")
            expected_raw = case_data.get("expected")
            expected = normalize_label(expected_raw)

            valid, validation_reason = validate_matrix(
                pattern,
                size,
                f"{case_key} input",
            )
            if not valid:
                raise ValueError(validation_reason)

            if expected is None:
                raise ValueError(
                    f"expected 라벨을 정규화할 수 없습니다: {expected_raw}"
                )

            cross_filter, x_filter = get_filter_pair(filters, size)
            print(
                f"\n{case_key} -> N={size} -> "
                f"size_{size}의 Cross/X 필터 사용"
            )

            cross_score = mac_score(pattern, cross_filter)
            x_score = mac_score(pattern, x_filter)
            decision = classify(cross_score, x_score)
            result = "PASS" if decision == expected else "FAIL"

            if decision == "UNDECIDED":
                undecided += 1

            print(f"Cross 점수: {cross_score:.10f}")
            print(f"X 점수: {x_score:.10f}")
            print(f"판정: {decision} | expected: {expected} | {result}")

            performance_inputs.setdefault(
                size,
                (pattern, cross_filter),
            )

            if result == "PASS":
                passed += 1
            else:
                failed += 1
                reason = f"판정 {decision}, expected {expected}"
                failure_types["동점(UNDECIDED)"] = (
                    failure_types.get("동점(UNDECIDED)", 0) + 1
                )

        except (TypeError, ValueError, KeyError) as error:
            failed += 1
            reason = str(error)
            failure_types["데이터/스키마 오류"] = (
                failure_types.get("데이터/스키마 오류", 0) + 1
            )
            print(f"{case_key}: FAIL - {reason}")

        if reason:
            failures.append((case_key, reason))

    print_performance_table(performance_inputs)

    print("\n[결과 요약]")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    print(f"UNDECIDED: {undecided}개")

    if failure_types:
        print("실패 유형별 집계:")
        for failure_type, count in failure_types.items():
            print(f"- {failure_type}: {count}개")

    if failures:
        print("실패 케이스:")
        for case_key, reason in failures:
            print(f"- {case_key}: {reason}")
    else:
        print("실패 케이스가 없습니다.")


def print_performance_table(performance_inputs):
    print("\n[성능 분석: MAC 평균/10회]")
    print("크기(NxN) | 평균 시간(ms) | 연산 횟수(N^2)")
    print("-" * 48)

    for size in (3, 5, 13, 25):
        pattern, filter_matrix = performance_inputs.get(
            size,
            (make_cross(size), make_cross(size)),
        )
        average_ms = measure_average_ms(
            lambda p=pattern, f=filter_matrix: mac_score(p, f)
        )
        print(f"{size:>4}x{size:<4} | {average_ms:>14.6f} | {size * size:>14}")


def run_optimization_demo(pattern, filter_matrix):
    score_2d = mac_score(pattern, filter_matrix)
    score_1d = mac_score_1d(pattern, filter_matrix)
    time_2d = measure_average_ms(lambda: mac_score(pattern, filter_matrix))
    time_1d = measure_average_ms(
        lambda: mac_score_1d(pattern, filter_matrix)
    )

    print("\n[보너스 1: 2D/1D MAC 비교]")
    print(f"2D 점수: {score_2d:.10f}, 평균: {time_2d:.6f} ms")
    print(f"1D 점수: {score_1d:.10f}, 평균: {time_1d:.6f} ms")
    print(f"점수 일치: {math.isclose(score_2d, score_1d, abs_tol=EPSILON)}")


def run_pattern_generator():
    while True:
        try:
            size = int(input("생성할 패턴 크기 N(홀수): ").strip())
            if size < 3 or size % 2 == 0:
                print("3 이상의 홀수를 입력해주세요.")
                continue
            break
        except ValueError:
            print("정수만 입력해주세요.")

    cross = make_cross(size)
    x_pattern = make_x(size)

    print("\n[보너스 2: 패턴 자동 생성]")
    print(f"{size}x{size} Cross 패턴")
    print_matrix(cross)
    print(f"\n{size}x{size} X 패턴")
    print_matrix(x_pattern)


def print_matrix(matrix):
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


def main():
    print("=== Mini NPU Simulator ===")

    try:
        while True:
            print("\n[모드 선택]")
            print("1. 사용자 입력 (3x3)")
            print("2. data.json 분석")
            print("3. 보너스 패턴 생성")
            print("4. 종료")

            choice = input("선택: ").strip()

            if choice == "1":
                run_user_mode()
            elif choice == "2":
                analyze_json_mode()
            elif choice == "3":
                run_pattern_generator()
            elif choice == "4":
                print("프로그램을 종료합니다.")
                break
            else:
                print("1부터 4 사이의 번호를 입력해주세요.")

    except (KeyboardInterrupt, EOFError):
        print("\n입력이 중단되어 안전하게 종료합니다.")


if __name__ == "__main__":
    main()
