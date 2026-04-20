---
name: benchmark
description: Empirically verify algorithmic complexity by running a function at varying input sizes and fitting a Big O curve. Manual only — for hard data after optimization or to catch regressions.
disable-model-invocation: true
allowed-tools: "Read Write Bash"
argument-hint: "[test-file or function-path]"
---

# Empirical Benchmark: $ARGUMENTS

Actually runs code to measure Big O complexity. Uses the `bigO` library to fit a complexity curve at input sizes [10, 50, 100, 500, 1000] and report the best-fit class with statistical confidence.

**Not a static check.** For pattern-based complexity review, use `/complexity-check`.

## Steps

1. If `$ARGUMENTS` is empty, run all tests in `tests/perf/`:
   ```
   .venv/bin/pytest tests/perf/ -v
   ```

2. If `$ARGUMENTS` is a function path (e.g., `src/app/engine/matching/walker.py::search_best_chain`):
   - Create a perf test at `tests/perf/test_<module>.py` if it doesn't exist
   - Use the bigO decorator pattern:
     ```python
     from bigO import BigO
     import pytest

     @pytest.mark.perf
     def test_search_best_chain_complexity():
         tester = BigO()
         tester.test(
             func=lambda n: search_best_chain(make_graph(n), 0, target_tf, target_len),
             input_sizes=[10, 50, 100, 500, 1000],
             label="search_best_chain",
         )
         assert tester.complexity in ("O(n)", "O(n log n)", "O(n^2)"), \
             f"Unexpected complexity: {tester.complexity}"
     ```

3. Report the fitted complexity class and confidence interval.

4. If complexity is worse than expected:
   - Review `.claude/whitelist.yaml` under `complexity:` — is it already accepted?
   - If not, suggest either:
     - Add to whitelist with justification
     - Refactor to improve complexity

## When to Use

- After optimizing a hot path — verify it actually got faster
- Before adding a function to the whitelist — confirm its actual complexity
- Periodically on core algorithms to catch regressions
- When `/complexity-check` flagged something as `review` and you want concrete data

## Dependencies

The `bigO` package must be installed:
```
uv add --dev bigO
```

Install lazily — only when you actually run a benchmark.
