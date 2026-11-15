"""
verascore: an automated 4-dimension evaluation rubric (format adherence,
completeness, accuracy, relevance) for structured-output extraction from
product reviews (sentiment, rating 1-5, mentions_price, product_category).

DISCLOSURE: "raw model output" strings used in the demo/tests are
deterministic, hand-written stand-ins chosen to be representative of real
model behavior (including realistic failure modes: a code fence, a preamble
sentence, an invented out-of-enum category) -- not captured API responses.
All scoring logic below is real, automated, non-simulated code.
"""
import json
import re

REQUIRED_KEYS = {"sentiment": str, "rating": int, "mentions_price": bool, "product_category": str}

CATEGORY_KEYWORDS = {
    "electronics": {"earbuds", "battery", "app", "device", "wireless", "bluetooth", "gadget"},
    "clothing": {"jacket", "stitching", "wash", "fabric", "fit", "apparel"},
    "home": {"lamp", "living room", "grill", "house", "supply closet"},
    "beauty": {"serum", "skin", "bottle", "absorbs", "skincare"},
}

POSITIVE_WORDS = {"amazing", "great", "love", "excellent", "happy", "recommend", "best", "good", "nice"}
NEGATIVE_WORDS = {"disappoint", "bad", "terrible", "worst", "regret", "undone", "broken", "not worth", "not mad"}


def parse_response(raw: str):
    """Defensive parse with a format-adherence score. Returns (parsed_or_None, format_score, note)."""
    text = raw.strip()
    had_fence = "```" in text
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None, 1, "no JSON object found"
    candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None, 2, "braces present but invalid JSON"
    stray = cleaned.replace(candidate, "", 1).strip()
    if had_fence and not stray:
        return parsed, 4, "fence-wrapped, otherwise clean"
    if stray:
        return parsed, 3, "stray prose around the JSON object"
    return parsed, 5, "valid JSON, zero cleanup needed"


def score_completeness(parsed) -> int:
    if parsed is None:
        return 1
    missing = [k for k in REQUIRED_KEYS if k not in parsed]
    if len(missing) >= 3:
        return 1
    if len(missing) == 2:
        return 2
    if len(missing) == 1:
        return 3
    wrong_type = [k for k in REQUIRED_KEYS if not isinstance(parsed.get(k), REQUIRED_KEYS[k])]
    return 4 if wrong_type else 5


def score_accuracy(parsed, ground_truth: dict) -> int:
    if parsed is None:
        return 1
    matches = 0
    for key in ("sentiment", "rating", "mentions_price", "product_category"):
        gt = ground_truth.get(key)
        val = parsed.get(key)
        if key == "rating":
            try:
                if val is not None and abs(int(val) - int(gt)) <= 1:
                    matches += 1
            except (TypeError, ValueError):
                pass
        elif val == gt:
            matches += 1
    return {4: 5, 3: 4, 2: 3, 1: 2, 0: 1}[matches]


def score_relevance(parsed, review_text: str) -> int:
    if parsed is None:
        return 1
    text = review_text.lower()
    category = parsed.get("product_category")
    keywords = CATEGORY_KEYWORDS.get(category)
    # Disclosed limit: an unfamiliar/invented category has no keyword list to
    # check against, so it isn't penalized here -- only accuracy catches it.
    cat_ok = True if not keywords else any(k in text for k in keywords)
    pos = sum(w in text for w in POSITIVE_WORDS)
    neg = sum(w in text for w in NEGATIVE_WORDS)
    sentiment = parsed.get("sentiment")
    sent_ok = True
    if sentiment == "positive" and neg > pos:
        sent_ok = False
    if sentiment == "negative" and pos > neg:
        sent_ok = False
    if cat_ok and sent_ok:
        return 5
    if cat_ok != sent_ok:
        return 3
    return 1


def rubric_score(raw: str, ground_truth: dict, review_text: str) -> dict:
    parsed, fmt, note = parse_response(raw)
    completeness = score_completeness(parsed)
    accuracy = score_accuracy(parsed, ground_truth)
    relevance = score_relevance(parsed, review_text)
    avg = round((fmt + completeness + accuracy + relevance) / 4, 2)
    return {
        "format": fmt, "completeness": completeness, "accuracy": accuracy,
        "relevance": relevance, "avg": avg, "note": note, "parsed": parsed,
    }


TEST_CASES = [
    {
        "id": "earbuds_positive",
        "review": "These wireless earbuds still sound amazing. Paid just $34 and honestly expected way worse.",
        "ground_truth": {"sentiment": "positive", "rating": 4, "mentions_price": True, "product_category": "electronics"},
        "v1_raw": '```json\n{"sentiment": "positive", "rating": 4, "mentions_price": true, "product_category": "electronics"}\n```',
        "v2_raw": '{"sentiment": "positive", "rating": 4, "mentions_price": true, "product_category": "electronics"}',
    },
    {
        "id": "jacket_negative",
        "review": "The stitching on this jacket came undone after one wash. Complete disappointment.",
        "ground_truth": {"sentiment": "negative", "rating": 1, "mentions_price": False, "product_category": "clothing"},
        "v1_raw": 'Here is the extracted data:\n{"sentiment": "negative", "rating": 1, "mentions_price": false, "product_category": "apparel"}',
        "v2_raw": '{"sentiment": "negative", "rating": 1, "mentions_price": false, "product_category": "clothing"}',
    },
    {
        "id": "serum_mixed",
        "review": "This serum smells nice and absorbs quickly, but at $58 for a tiny bottle it's hard to justify.",
        "ground_truth": {"sentiment": "mixed", "rating": 3, "mentions_price": True, "product_category": "beauty"},
        "v1_raw": '{"sentiment": "mixed", "rating": 3, "mentions_price": true, "product_category": "skincare"}',
        "v2_raw": '{"sentiment": "mixed", "rating": 3, "mentions_price": true, "product_category": "beauty"}',
    },
    {
        "id": "lamp_positive_inferred",
        "review": "This lamp is exactly what our living room needed -- highly recommend.",
        "ground_truth": {"sentiment": "positive", "rating": 5, "mentions_price": True, "product_category": "home"},
        "v1_raw": '{"sentiment": "positive", "rating": 4, "mentions_price": true, "product_category": "home goods"}',
        "v2_raw": '{"sentiment": "positive", "rating": 5, "mentions_price": true, "product_category": "home"}',
    },
    {
        "id": "messy_app_review",
        "review": "ok so i ordered this app-controlled gadget thinking it was gonna be like my cousin's but nah. "
                  "works i guess? not mad not happy. might return it might not.",
        "ground_truth": {"sentiment": "neutral", "rating": 3, "mentions_price": False, "product_category": "electronics"},
        "v1_raw": '{"sentiment": "negative", "rating": 2, "mentions_price": false, "product_category": "gadgets"}',
        "v2_raw": '{"sentiment": "mixed", "rating": 3, "mentions_price": false, "product_category": "electronics"}',
    },
    {
        "id": "grill_negative_messy",
        "review": "Not worth what I paid for this grill, honestly regretting this purchase.",
        "ground_truth": {"sentiment": "negative", "rating": 2, "mentions_price": True, "product_category": "home"},
        "v1_raw": 'Sure, here\'s the JSON:\n```{"sentiment": "negative", "rating": 2, "mentions_price": true, "product_category": "outdoor equipment"}```',
        "v2_raw": '{"sentiment": "negative", "rating": 2, "mentions_price": true, "product_category": "home"}',
    },
]
