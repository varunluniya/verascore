# verascore

A small, tested, fully-automated 4-dimension evaluation rubric (format
adherence, completeness, accuracy, relevance) for scoring structured-output
extraction from product reviews, plus a 6-case test set (one deliberately
ambiguous) and a before/after comparison between two prompt versions.

**Disclosure:** the "raw model output" strings used in the demo and tests
are deterministic, hand-written stand-ins chosen to be representative of
real model behavior — including realistic failure modes (a code fence, a
preamble sentence, an invented out-of-enum category) — not captured API
responses. All scoring logic is real, automated code; nothing is hand-eyeballed.

## Usage

```bash
pip install -e .
python -m verascore.cli
```

## What it demonstrates

Closing one underspecified schema field (`product_category: string` to a
named enum) raises the overall average from **4.54 to 4.96** with no case
regressing — and the rubric's per-dimension breakdown is what pinpoints
*why*: format and accuracy were the two dimensions actually dragging the
baseline down, both for the same underlying reason (an open-ended field
inviting invented labels). The deliberately ambiguous review case improves
the least, because its difficulty was never a schema problem — a rubric
tells you which kind of failure a structural change can and can't reach.

## Tests

```bash
pytest -v
```

26/26 passing.

## License

MIT
