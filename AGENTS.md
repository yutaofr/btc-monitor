# Repository Guidelines

## Project Structure & Module Organization
The core application lives in `src/` and is organized by responsibility:
- `src/main.py`: Entry point for live evaluation (V3.0 Primary Path).
- `src/config.py`: Single source of truth for constants and thresholds.
- `src/indicators/`: Market signal calculations (technical, macro, valuation, sentiment).
- `src/fetchers/`: Data sourcing (Binance, FRED, Blockchain).
- `src/strategy/`: 
    - `tadr_engine.py`: V3.0 Orchestrator (Scorer -> Resolver -> Decision).
    - `factor_registry.py`: Metadata & Weight definitions.
    - `probabilistic_confidence_scorer.py`: Entropy-based confidence scoring.
    - `allocation_resolver.py`: Target allocation mapping.
- `src/monitoring/`: Correlation tracking and strategy drift detection.
Tests live in `tests/unit/`, `tests/parity/` (Shadow Testing), and `tests/acceptance/` (V3 Audit).

## Build, Test, and Development Commands
The repo is Docker-first; these are the canonical commands:

**Run Live Evaluation (V3.0):**
```bash
docker compose build
docker compose run --rm app
```

**Run All Tests (Unit + Parity):**
```bash
docker compose run --rm tests
```

**Run V3.0 Acceptance Audit:**
```bash
export PYTHONPATH=$PYTHONPATH:. && python3 tests/acceptance/verify_tadr_v3.py
```

## Coding Style & Naming Conventions
- Follow **PEP 8**.
- **Numerical Integrity**: Mandatory use of `src.strategy.factor_utils.quantize_score` for all scoring logic to ensure Bit-identical Parity.
- **Fail-Closed**: Always implement `is_valid` checks and use the registry's gating metadata.

## Testing Guidelines
- **Unit Tests**: Mirror module structure in `tests/unit/`.
- **Parity Tests**: Any change to scoring logic MUST pass `tests/parity/shadow_parity_100_samples.py`.
- **Acceptance**: Major strategy changes require a full historical audit using `tests/acceptance/verify_tadr_v3.py`.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (e.g., `feat:`, `fix:`, `test:`, `chore:`).
- PRs MUST include:
    - Evidence of `docker compose run --rm tests` passing.
    - For strategy changes: V3.0 Acceptance Audit report summary.
    - Parity verification (Bit-identical state check).

## Configuration & Security
- Copy `.env.example` to `.env` and set `FRED_API_KEY`.
- **Security**: Never log or print API keys. Protect `.env` from being staged.
