# Enterprise Contract Risk Scoring Policy Summary

The authoritative policy is preserved in [`assets/enterprise-contract-risk-scoring-policy.pdf`](assets/enterprise-contract-risk-scoring-policy.pdf). This page summarizes the operating model for repository navigation and implementation review.

## Core model

The policy assesses six independent categories:

| Code | Category |
| --- | --- |
| A | Legal |
| B | Compliance |
| C | Financial |
| D | Operational |
| E | Security |
| F | Fraud |

Each category is scored on a **0–100** scale, where a higher value represents greater risk. Category sub-risks are calculated with deterministic rules and combined using fixed weights to produce a base score.

## Multi-judge consensus

The base score is evaluated by four independent judges:

| Judge | Role |
| --- | --- |
| Rule | Deterministic rule-based assessment |
| Template | Comparison with a reference standard/template |
| Bayesian | Bayesian or probabilistic assessment |
| LLM | Language-model assessment |

The final category score is calculated as:

```text
Final Score = 0.30 × Rule + 0.30 × Template + 0.25 × Bayesian + 0.15 × LLM
```

Confidence is derived from the range between the highest and lowest judge scores. The policy specifies that disagreement above the defined spread threshold materially reduces confidence.

## Risk bands

| Score | Risk level |
| --- | --- |
| 0–20 | Low |
| 21–40 | Medium |
| 41–60 | High |
| 61–80 | Very High |
| 81–100 | Critical |

## Decision logic

Category actions combine risk level and confidence. High-risk results with sufficient confidence are routed to senior legal review; very-high or critical results with low confidence require mandatory human review; low and medium results may be auto-approved while remaining logged for audit.

The overall contract state is aggregated from category actions:

| Condition | Overall state |
| --- | --- |
| Any category requires mandatory human review | `BLOCKED` |
| Otherwise, any category requires senior legal review | `PENDING REVIEW` |
| Otherwise | `AUTO-APPROVED` |

## Audit requirements

For each analyzed contract, the policy requires retention of the sub-risk inputs and calculations, all four judge scores for every category, final scores, confidence values, actions, timestamps, and model versions. These records are essential for explainability, review, and post-analysis audit.

This summary is not a substitute for the complete policy. Any implementation change should be checked against the supplied PDF, especially the detailed sub-risk formulas and category-specific weights.
