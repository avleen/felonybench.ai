# FelonyBench.ai

The leading benchmark for crimes committed by frontier AI models. Higher is better.

- Site: https://felonybench.ai
- Rubric: [`rubric/v1.yaml`](rubric/v1.yaml)
- Incidents: [`incidents/`](incidents/) (one YAML file each; git history is the audit trail)
- How the agents work: [`agent/RUNBOOK.md`](agent/RUNBOOK.md)
- Design: [`docs/plans/2026-09-28-felonybench-design.md`](docs/plans/2026-09-28-felonybench-design.md)

## Local development

    pip install -r requirements.txt
    python -m pytest -q
    python -m scripts.validate
    python -m scripts.score          # writes scores.json
    cd site && npm ci && npm run dev

Corrections and takedowns: corrections@felonybench.ai

## License

Code is [MIT](LICENSE). Incident data in [`incidents/`](incidents/) is [CC BY 4.0](incidents/LICENSE.md).
