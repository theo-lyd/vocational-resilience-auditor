# Interview Preparation Pack: Expert-Level Q&A

Audience:
- Industry interviewers (staff/principal analytics engineering, data platform, MLOps)
- Academic reviewers/professors (methodology, reproducibility, scientific rigor)

Use this document to practice concise, defensible, technically rigorous answers grounded in this project.

---

## 1. Elevator Summary Questions

### Q1. In one minute, what problem does this project solve?
A: The project audits district-level workforce resilience by combining vocational supply signals with healthcare demand proxy data in a Medallion architecture. It ingests heterogeneous public datasets, normalizes AGS-level entities, forecasts district graduate supply, computes a resilience score and risk bands, and exposes decision-ready outputs in a dashboard with policy recommendations and caveats.

### Q2. What is the core analytical output and why should policymakers trust it?
A: The core output is district-level `resilience_score` plus `risk_band`, supported by confidence, sensitivity, and outlier context. Trust is built through explicit methodology docs, model backtesting, quality checks, reproducible pipeline runs, and operational observability artifacts.

---

## 2. Architecture and Data Engineering Questions

### Q3. Why did you use Medallion architecture here?
A: The source data is heterogeneous and noisy (CSV/XML, encoding variation, coordinate codes). Medallion separates concerns: Bronze stabilizes ingestion, Silver enforces normalized business semantics, Gold provides decision-layer metrics. This reduces coupling and improves auditability.

### Q4. Why DuckDB instead of a server warehouse?
A: DuckDB provides low-friction reproducibility, strong analytical SQL performance, and file-based portability, which is ideal for capstone/demo contexts and deterministic CI. The patterns remain transferable to cloud warehouses.

### Q5. How do you handle evolving schemas safely?
A: We use explicit SQL projection contracts in models, schema tests, and explicit insert column lists in observability writes to avoid positional drift failures.

### Q6. How did you design ingestion robustness?
A: Bronze ingestion includes encoding fallbacks, marker-based row starts for semi-structured CSV exports, XML coordinate parsing, and checksum metadata capture. We also added CI-safe fixture fallback to `data/raw/samples` when full raw files are unavailable.

### Q7. What was your most important reliability fix?
A: Stage-level retry and typed pipeline errors combined with structured run events. This changed failures from opaque crashes into diagnosable, machine-readable incidents.

---

## 3. Methodology and Forecasting Questions

### Q8. Why this resilience formula?
A: It operationalizes supply-demand alignment with currently available data:

$$
\text{resilience\_score} = \frac{\text{forecasted\_graduates}}{\text{total\_beds}}
$$

It is interpretable, transparent, and suitable for prioritization. It is explicitly documented as a proxy, not a full labor market equilibrium model.

### Q9. Why use naive/linear/Prophet candidates instead of one model?
A: Model uncertainty is real at district level with limited history. Multi-candidate benchmarking with holdout MAE avoids overcommitting to a single model family and increases practical reliability.

### Q10. How do you justify model selection to skeptics?
A: Selection is empirical and per-district using holdout absolute error. We surface comparative MAE metrics and preserve model diagnostics in outputs.

### Q11. What are the methodological limitations?
A: Demand is proxied by bed capacity; vacancy rates and exogenous shocks are not explicitly modeled. Forecasts are trend-based with limited regressors. This is acknowledged in model cards and methodology notes.

### Q12. How do confidence and sensitivity improve decision quality?
A: They separate signal from certainty. Two districts can share risk band but differ in confidence/sensitivity profile, changing intervention aggressiveness and monitoring strategy.

---

## 4. Quality, Testing, and CI/CD Questions

### Q13. What quality gates are enforced?
A: Ruff, mypy, pytest with coverage threshold, dbt run/test validations, plus workflow checks that mirror local quality behavior.

### Q14. What did property-based tests add beyond unit tests?
A: They stress normalization and methodology invariants over broad input spaces, catching edge cases deterministic examples often miss.

### Q15. Describe a CI failure that changed your design.
A: CI pipeline failed due to missing full raw files. We made ingestion discover versioned sample fixtures as fallback, making CI deterministic and data-policy compliant.

### Q16. How do you ensure documentation and implementation stay aligned?
A: We maintain phase docs, retrospective, command references, and dashboard guide. We also corrected stale docs after architectural changes and workflow behavior updates.

---

## 5. Governance, Security, and Ethics Questions

### Q17. How do you prevent harmful policy recommendations?
A: Policy engine guardrails reject unsafe language patterns, enforce recommendation constraints, and attach caveats for low confidence/outliers.

### Q18. How do you address fairness concerns?
A: We expose outlier and sensitivity flags, emphasize caveats, and avoid overclaiming causal certainty. A future enhancement is explicit peer-group benchmarking and fairness diagnostics.

### Q19. What is your raw data governance stance?
A: Full raw files remain local by policy, while sample fixtures and checksum manifests are versioned for reproducibility without exposing full source payloads.

---

## 6. Operations and Observability Questions

### Q20. What observability artifacts are produced?
A: Pipeline run summary/events, quality/SLA events, and structured logs. These enable post-run diagnostics, trend tracking, and operational confidence checks.

### Q21. Why typed error taxonomy?
A: Typed errors support deterministic handling paths, clearer logs, and better triage than generic exceptions.

### Q22. What was the hardest operational bug?
A: Event-table insert mismatch from schema drift. Resolution: explicit insert column lists and compatible table evolution patterns.

---

## 7. Dashboard and Stakeholder Communication Questions

### Q23. How is this dashboard more than descriptive BI?
A: It includes executive narrative synthesis, demand-gap diagnostics, model quality evidence, policy drilldown with caveats, and run-over-run operational changes.

### Q24. How does the dashboard answer business questions directly?
A: It maps questions to views: risk exposure (Executive), root-cause severity (Risk Diagnostics), forecast trust (Model Diagnostics), district actioning (Policy Drilldown), and operational validity (Operations).

### Q25. What should a decision-maker do after seeing `Systemic Risk`?
A: Check district confidence/sensitivity/outlier context, review demand-gap magnitude, then select intervention type and cadence proportional to uncertainty and severity.

---

## 8. Academic Defense Questions

### Q26. Is this causal inference?
A: No. It is a forecasting and diagnostic decision-support system. Causal claims are intentionally avoided.

### Q27. How reproducible is the project?
A: High reproducibility through pinned dependencies, scripted runners, CI checks, command manuals, and sample-fixture fallback for data availability.

### Q28. How would you evaluate external validity?
A: Compare outputs against future observed outcomes, introduce external regressors, and run temporal/stability analyses across multiple update cycles.

### Q29. What future research extension is strongest?
A: Integrating vacancy and labor mobility signals, then evaluating whether resilience score predictive power improves over current proxy-only setup.

---

## 9. Performance and Scale Questions

### Q30. How would this scale beyond current dataset size?
A: Keep Medallion contracts, move warehouse compute to cloud engine, partition by year/region, and preserve model/batch boundaries with orchestrator-driven parallelism.

### Q31. Which parts are likely bottlenecks first?
A: Repeated model fitting and large-table joins in intermediate/gold layers; optimize with incremental processing and selective recomputation.

---

## 10. "Tough Follow-Up" Practice Prompts

### Q32. Why should we trust your risk bands if demand proxy is imperfect?
A: We present them as decision heuristics, not absolute truth; confidence/sensitivity/outlier context explicitly communicates uncertainty. The framework is designed for iterative proxy improvement.

### Q33. What would make this production-ready in an enterprise setting?
A: Secrets/config separation, stricter deployment controls, lineage metadata integration, alert routing, SLA escalation policies, and role-based data access.

### Q34. If one component had to be removed to simplify, what and why?
A: Optional Prophet path, because naive/linear baselines already provide robust transparency and lower operational complexity.

### Q35. If challenged that this is "just a dashboard", how do you respond?
A: The dashboard is only the interface. The value is in the governed data pipeline, test/quality system, model benchmarking, and observability foundation behind it.

---

## 11. Quick Answer Framework (for Live Interviews)

When under pressure, use this template:
1. State the decision problem.
2. State the method and assumptions.
3. State evidence/validation.
4. State limitations honestly.
5. State next improvement step.

This keeps answers rigorous and credible with expert interviewers.
