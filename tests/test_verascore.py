import pytest
from verascore.core import TEST_CASES, rubric_score, parse_response, score_completeness, score_accuracy, score_relevance


def test_six_cases_defined():
    assert len(TEST_CASES) == 6


def test_parse_clean_json_scores_5():
    _, fmt, _ = parse_response('{"a": 1}')
    assert fmt == 5


def test_parse_fence_wrapped_clean_scores_4():
    _, fmt, _ = parse_response('```json\n{"a": 1}\n```')
    assert fmt == 4


def test_parse_stray_prose_scores_3():
    _, fmt, _ = parse_response('Here is the data: {"a": 1}')
    assert fmt == 3


def test_parse_malformed_json_scores_2():
    _, fmt, _ = parse_response('{a: not valid}')
    assert fmt == 2


def test_parse_no_object_found_scores_1():
    _, fmt, _ = parse_response('no braces here at all')
    assert fmt == 1


def test_completeness_full_match_scores_5():
    parsed = {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"}
    assert score_completeness(parsed) == 5


def test_completeness_one_missing_scores_3():
    parsed = {"sentiment": "positive", "rating": 4, "mentions_price": True}
    assert score_completeness(parsed) == 3


def test_completeness_two_missing_scores_2():
    parsed = {"sentiment": "positive", "rating": 4}
    assert score_completeness(parsed) == 2


def test_completeness_three_missing_scores_1():
    parsed = {"sentiment": "positive"}
    assert score_completeness(parsed) == 1


def test_completeness_none_scores_1():
    assert score_completeness(None) == 1


def test_accuracy_all_four_match_scores_5():
    gt = {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"}
    parsed = dict(gt)
    assert score_accuracy(parsed, gt) == 5


def test_accuracy_rating_within_tolerance_still_matches():
    gt = {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"}
    parsed = {**gt, "rating": 5}  # within +-1
    assert score_accuracy(parsed, gt) == 5


def test_accuracy_zero_matches_scores_1():
    gt = {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"}
    parsed = {"sentiment": "negative", "rating": 1, "mentions_price": False, "product_category": "home"}
    assert score_accuracy(parsed, gt) == 1


def test_accuracy_none_scores_1():
    gt = {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"}
    assert score_accuracy(None, gt) == 1


def test_relevance_grounded_category_and_sentiment_scores_5():
    parsed = {"sentiment": "positive", "product_category": "electronics"}
    assert score_relevance(parsed, "These wireless earbuds sound amazing") == 5


def test_relevance_one_check_fails_scores_3():
    parsed = {"sentiment": "positive", "product_category": "clothing"}  # no clothing keywords in text
    score = score_relevance(parsed, "These wireless earbuds sound amazing")
    assert score == 3


def test_relevance_unfamiliar_category_not_penalized_by_relevance():
    # Disclosed limitation: an invented category with no keyword list isn't
    # caught by relevance -- only accuracy catches it (see core.py docstring).
    parsed = {"sentiment": "positive", "product_category": "gadgets"}
    score = score_relevance(parsed, "These wireless earbuds sound amazing")
    assert score == 5  # sentiment ok, category has no keyword list to fail


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["id"] for c in TEST_CASES])
def test_v2_never_regresses_vs_v1(case):
    v1 = rubric_score(case["v1_raw"], case["ground_truth"], case["review"])
    v2 = rubric_score(case["v2_raw"], case["ground_truth"], case["review"])
    assert v2["avg"] >= v1["avg"]


def test_overall_v2_average_higher_than_v1():
    v1_avg = sum(rubric_score(c["v1_raw"], c["ground_truth"], c["review"])["avg"] for c in TEST_CASES) / len(TEST_CASES)
    v2_avg = sum(rubric_score(c["v2_raw"], c["ground_truth"], c["review"])["avg"] for c in TEST_CASES) / len(TEST_CASES)
    assert v2_avg > v1_avg


def test_messy_case_is_lowest_or_tied_lowest_in_v2():
    scores = {c["id"]: rubric_score(c["v2_raw"], c["ground_truth"], c["review"])["avg"] for c in TEST_CASES}
    assert scores["messy_app_review"] <= min(scores.values()) + 1e-9
