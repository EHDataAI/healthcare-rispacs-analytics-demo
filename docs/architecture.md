# Public demo architecture

```text
Synthetic generator
       |
       v
Source-like Parquet
       |
       +--> Minimal contract validation
       |
       +--> Data-quality checks
       |
       v
Analytics helpers
       |
       +--> Executive Pulse
       +--> Workflow Bottleneck
       +--> Reporting SLA / GES Alert Center
       +--> Safety Overview
       |
       v
Streamlit presentation
```

The public demo intentionally omits production connectors, institution-specific rules, proprietary analytical modules, and advanced optimization/predictive methods.

## Units of analysis

For this reduced public demo, one generated row represents one synthetic radiology study record. This simplification is explicitly limited to the demo and must not be interpreted as the internal production semantic model.
