# Defense Deck Outline and Speaking Notes

## Slide 1: Title and Context
- Title: Vocational Resilience Auditor
- Context: District-level workforce resilience for healthcare policy
- Speaking note: Emphasize reproducibility and explainability

## Slide 2: Problem and Decision Need
- Fragmented source systems create blind spots
- Stakeholders need comparable district risk signals
- Speaking note: Explain policy planning impact window

## Slide 3: Data Sources and Constraints
- Vocational enrollment CSV
- Hospital capacity CSV
- Vocational graduates XML
- Speaking note: Mention encoding and schema heterogeneity challenge

## Slide 4: Architecture (Bronze/Silver/Gold)
- Bronze for ingestion quality
- Silver for normalization and conformed tables
- Gold for scoring and policy-facing outputs
- Speaking note: Show how each layer reduces risk

## Slide 5: Forecasting and Model Selection
- Candidate models: naive, linear, Prophet (if available)
- District-level backtest MAE chooses best model
- Speaking note: Justify transparent model benchmark strategy

## Slide 6: Resilience Methodology
- Score formula and risk bands
- Confidence and sensitivity flags
- Outlier handling notes
- Speaking note: Connect methodology to decision confidence

## Slide 7: Observability and Reliability
- Structured logs and stage-level retries
- Pipeline run summary/events
- Quality SLA tracking
- Speaking note: Highlight production-readiness posture

## Slide 8: Dashboard and Policy Layer
- Overview, trends, policy recommendations, data explorer
- Guardrails for recommendation safety
- Speaking note: Explain how non-technical users consume outcomes

## Slide 9: Validation and Acceptance Evidence
- CI gates and local reproducibility
- dbt tests and quality gates
- Runbook-backed replication path
- Speaking note: Demonstrate no hidden setup assumptions

## Slide 10: Limitations and Next Steps
- Geospatial choropleth integration
- Additional external regressors
- Enhanced codebook mapping
- Speaking note: Present a realistic improvement roadmap
