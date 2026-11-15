from .core import TEST_CASES, rubric_score


def main():
    print(f"{'case':<24}{'v1 avg':<10}{'v2 avg':<10}{'delta':<8}")
    v1_sum = v2_sum = 0.0
    for case in TEST_CASES:
        v1 = rubric_score(case["v1_raw"], case["ground_truth"], case["review"])
        v2 = rubric_score(case["v2_raw"], case["ground_truth"], case["review"])
        v1_sum += v1["avg"]; v2_sum += v2["avg"]
        print(f"{case['id']:<24}{v1['avg']:<10}{v2['avg']:<10}{v2['avg']-v1['avg']:<8.2f}")
    n = len(TEST_CASES)
    print(f"\nOverall v1: {v1_sum/n:.2f}   Overall v2: {v2_sum/n:.2f}")


if __name__ == "__main__":
    main()
