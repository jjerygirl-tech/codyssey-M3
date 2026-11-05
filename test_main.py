from main import (
    EPSILON,
    classify,
    mac_score,
    mac_score_1d,
    make_cross,
    make_x,
    normalize_label,
)


def test_label_normalization():
    assert normalize_label("+") == "Cross"
    assert normalize_label("cross") == "Cross"
    assert normalize_label("x") == "X"


def test_mac_and_flattened_mac_match():
    pattern = make_x(5)
    filter_matrix = make_cross(5)

    score_2d = mac_score(pattern, filter_matrix)
    score_1d = mac_score_1d(pattern, filter_matrix)

    assert abs(score_2d - score_1d) < EPSILON


def test_classification_and_generated_shapes():
    assert classify(5.0, 1.0) == "Cross"
    assert classify(1.0, 5.0) == "X"
    assert classify(1.0, 1.0 + EPSILON / 2) == "UNDECIDED"

    for size in (3, 5, 13, 25):
        assert len(make_cross(size)) == size
        assert len(make_x(size)) == size
        assert all(len(row) == size for row in make_cross(size))
        assert all(len(row) == size for row in make_x(size))


if __name__ == "__main__":
    test_label_normalization()
    test_mac_and_flattened_mac_match()
    test_classification_and_generated_shapes()
    print("Mini NPU 기본·보너스 테스트를 통과했습니다.")
