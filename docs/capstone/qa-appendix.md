# Q&A Appendix

## Q1. Why use DuckDB instead of a server database?
DuckDB provides fast local analytical processing with minimal setup, making replication and teaching easier.

## Q2. How does the project ensure recommendation safety?
The policy engine enforces guardrails that reject harmful language and adds confidence caveats when evidence is weaker.

## Q3. How are model choices justified?
Each district model is selected using holdout-year backtest MAE among available candidates.

## Q4. Is the system reproducible by beginners?
Yes. The repository includes a complete tutorial, a one-command runner, and a checklist-driven runbook.

## Q5. What if raw files are unavailable?
Sample fixtures are versioned for demonstration, while full raw files remain local according to repository policy.

## Q6. What are the biggest methodological limitations?
Demand is proxied by bed capacity and exogenous macro shocks are not currently modeled.

## Q7. How is operational monitoring handled?
Structured logs plus persisted pipeline run summaries, stage events, and quality SLA outputs are generated for each run.

## Q8. What indicates project completion quality?
Passing pipeline, dbt, lint/type/test gates, and checklist evidence in `docs/capstone/final-acceptance-checklist.md`.
