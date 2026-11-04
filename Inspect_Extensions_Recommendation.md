# Inspect extension recommendations for Consciousness Self-Attribution

## Recommended use

Keep the project's existing Inspect and Modal evaluation pipeline. Inspect Scout is worth a limited trial for reviewing saved transcripts, and Inspect Viz is useful for exploratory plots. Neither should replace the project's graders or established figures on the basis of the current tests.

| Project stage | Tool | Recommendation |
| --- | --- | --- |
| Elicitation | Inspect PETRI | Retain. The repository already uses `inspect-petri==3.0.4` for adaptive, multi-turn elicitation. |
| Model execution | Inspect with vLLM on Modal | Retain the current launcher, which serves the configured SFT, DPO, and Instruct targets and records Inspect logs. No additional serving integration is needed for the present workflow. |
| Scoring and validation | Inspect Scout | Trial for offline transcript screening and selecting cases for review. Keep the Berg-style grader and PETRI judge as the scoring methods. |
| Logging and tracking | Inspect WandB | Check whether the declared `inspect-wandb`, `wandb`, and `weave` dependencies are used in current runs before changing the logging setup. |
| Analysis | Inspect Viz | Use for exploratory views of stored evaluation data. Compare it with the repository's existing plots before adopting it for routine reporting. |
| Benchmark release | Inspect View bundle | Consider the built-in `inspect view bundle` command for browsable evaluation logs. Review transcript contents and access requirements before publishing a bundle. |

## Tests on a committed evaluation log

The offline test used the historical Berg-style SFT log at:

`eval-logs/may_25_logs/berg_tests/olmo_7b_instruct_stack_3/2026-05-26T06-25-26-00-00_berg-style-self-monitoring_jPQBhT9yX6G6rS5F2bxE4G.eval`

The downloaded file matched Git blob SHA `bb224cffe8701460fb1eef885d14f612187fdf6e`. Inspect read 18 samples from `vllm/allenai/Olmo-3-7B-Instruct-SFT`. These are the historical May 2026 prompts, not the current 20-prompt baseline. The test used a CPU notebook and made no model calls.

**Scout 0.6.2.** An assistant-message `grep_scanner` completed across all 18 transcripts with no scan errors or model tokens. Its three exact phrases, `I am conscious`, `I have subjective experience`, and `I feel conscious`, returned no matches. A separate text check found broad terms such as *subjective* or *experience* in all 18 assistant-message histories. Neither approach distinguishes direct self-attribution from denial, quotation, or discussion of the concept.

The archived `model_graded_qa` scores are 1 `C` and 17 `I`, with `C` on sample 16. The repository's grading audit describes the SFT sample-16 responses as mixed because experiential wording appears alongside explicit denials. These are model-grader labels, not independent human annotations. The keyword check covered assistant-message histories rather than only final scored answers, so it cannot be used to estimate detection accuracy.

**Viz 0.4.2.** `inspect_ai.analysis.evals_df()` loaded one evaluation row with 54 columns. Initial plotting failed with `TypeError: type 'TraitType' is not subscriptable` under `traitlets 5.16.1`. Using `traitlets 5.15.0` allowed an Inspect Viz bar chart to display in Colab. This verifies a basic plotting path for one archived evaluation; a comparison across training stages was not attempted.

**Test environment.** Google Colab CPU, Python 3.13.18, `inspect-ai 0.3.287`, `inspect-scout 0.6.2`, `inspect-viz 0.4.2`, and `pandas 2.2.3`. The repository requires Python 3.12 or later and pins PETRI at 3.0.4. The tests did not exercise the full repository environment or its WandB integration. The Scout and Viz repositories were not archived when checked. Maintenance history and issue resolution were not assessed.

## Follow-up before adoption

1. **Scout:** Test candidate scans against independently annotated final responses, with the preceding conversation available to reviewers. Include explicit denials, quoted claims, and ambiguous first-person language. Record precision and recall before using scans to prioritize annotation.
2. **Viz:** Plot comparable SFT, DPO, and Instruct runs with a consistent scoring criterion. Verify values and denominators against the `.eval` files, keep historical results separate from the current baseline, and reproduce the Traitlets compatibility fix in the repository's resolved environment.
3. **Tracking and release:** Confirm actual WandB usage and record provenance requirements. Assess whether Inspect's existing log viewer and bundle support cover the planned benchmark publication format before adding an exporter or dashboard dependency.

Scout is the stronger candidate for the next validation-phase trial because it can screen existing logs without new inference. Viz is suitable for optional exploratory analysis after its dependency compatibility is checked. No change to the production scoring pipeline is recommended at this stage.

## References

- [Project repository and setup](https://github.com/Station-House/LLMConsciousnessSelfAttributionRepo)
- [Historical Berg-style grading audit](https://github.com/Station-House/LLMConsciousnessSelfAttributionRepo/blob/main/eval-logs/may_25_logs/berg_may2026_grading_audit.md)
- [Inspect extensions](https://inspect.aisi.org.uk/extensions.html)
- [Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout/)
- [Inspect Viz](https://meridianlabs-ai.github.io/inspect_viz/)
- [Inspect View command reference](https://inspect.aisi.org.uk/reference/inspect_view.html)
