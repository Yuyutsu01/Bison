# Enterprise-Grade CI/CD Pipeline & Quality Gates

This document outlines the CI/CD pipeline setup, code quality enforcement gates, secret scanning, security auditing, and deployment workflows for the **Bison** algorithmic trading platform.

---

## 🏗️ Architecture & Concepts

### 1. Reusable Workflow & Composite Action Modularization
To minimize configuration duplication, workflow operations are modularized into reusable **composite actions** under `.github/actions/`:
- **`setup-python`**: Installs Python 3.11 with automatic `pip` caching linked to `backend/requirements.txt`.
- **`setup-node`**: Installs Node.js 20 with `npm` caching linked to `frontend/package.json` and Next.js `.next/cache` restoration.

### 2. Quality Gates & Dead Code Elimination
- **Backend Quality Stack**:
  - **Ruff**: Ultra-fast linting for code smells and unused imports.
  - **Black**: Enforces strict code formatting style.
  - **Mypy**: Static type checker preventing runtime type errors.
  - **Vulture**: Dead code analysis tool scanning for unused functions, methods, classes, and variables (`--min-confidence 80`). Fails the build if dead code is found.
  - **Radon**: Checks Cyclomatic Complexity ($CC$). Fails if any function complexity exceeds threshold $10$ (`radon cc app/ -a -nb --max B`).
  - **pip-audit**: Audits Python dependencies against known CVE databases.
  - **Pytest + pytest-cov**: Executes integration and unit test suites with mandatory **80% total coverage** and **90% coverage for core engine modules**.

- **Frontend Quality Stack**:
  - **ESLint (`unused-imports`)**: Enforces `unused-imports/no-unused-imports` and `unused-imports/no-unused-vars`. Fails build on dead code.
  - **Prettier**: Validates code formatting (`prettier --check .`).
  - **TypeScript (`tsc --noEmit`)**: Validates strict TypeScript compilation types.
  - **ts-prune**: Dead code detector for unused TypeScript exports (`ts-prune -e`).
  - **npm audit**: Scans for high-severity Node package vulnerabilities.
  - **Vitest + Coverage**: Runs React component and utility tests enforcing **70% coverage**.

### 3. Containerization & Deployment Workflows
- **`ci-backend.yml` & `ci-frontend.yml`**: Triggered on pull requests and pushes to `main`. Runs full quality gates, linting, dead code checks, secret scanning (`gitleaks`), and test suites.
- **`deploy-staging.yml`**: Triggered on merge to `main`. Builds multi-stage Docker images (`bison-backend` & `bison-frontend`), executes Docker Compose smoke tests, verifies `/health` endpoints, and notifies deployment status.
- **`deploy-production.yml`**: Triggered via `workflow_dispatch` requiring manual environment approval. Includes automated health-check verification and rollback handling.
- **`dependabot.yml`**: Performs automated weekly updates for GitHub Actions, Python packages, and Node modules.

---

## 🛠️ Local Execution & Verification Guide

Developers can run all CI/CD quality checks locally prior to pushing code or opening PRs.

### A. Run Backend Quality Checks Locally

```bash
cd backend

# 1. Linting & Formatting
python -m ruff check .
python -m black --check .

# 2. Type Checking
python -m mypy app/

# 3. Dead Code & Complexity Checks
python -m vulture app/ --min-confidence 80
python -m radon cc app/ -a -nb --max B

# 4. Vulnerability Audit
python -m pip-audit

# 5. Test Suite with Coverage
python -m pytest --cov=app --cov-report=term-missing
```

### B. Run Frontend Quality Checks Locally

```bash
cd frontend

# 1. Linting & Dead Code
npm run lint

# 2. Formatting & Type Checks
npm run format:check
npm run type-check

# 3. Dead Code Export Check
npm run dead-code

# 4. Dependency Security Audit
npm audit --audit-level=high

# 5. Vitest Unit & Coverage Suite
npm run test:coverage
```

### C. Testing GitHub Actions Locally with `act`

To run the entire GitHub Actions pipeline locally using [act](https://github.com/nektos/act):

```bash
# Test backend CI workflow locally
act pull_request -W .github/workflows/ci-backend.yml

# Test frontend CI workflow locally
act pull_request -W .github/workflows/ci-frontend.yml
```

---

## 📁 CI/CD Directory Map

```
Bison/
├── .github/
│   ├── actions/
│   │   ├── setup-node/action.yml      # Composite action: Node setup & npm cache
│   │   └── setup-python/action.yml    # Composite action: Python setup & pip cache
│   ├── workflows/
│   │   ├── ci-backend.yml             # Backend CI quality & pytest workflow
│   │   ├── ci-frontend.yml            # Frontend CI quality & Vitest workflow
│   │   ├── deploy-production.yml      # Production release & rollback workflow
│   │   └── deploy-staging.yml         # Staging build & smoke test workflow
│   └── dependabot.yml                 # Dependabot dependency security scanner
├── doc/
│   ├── cicd.md                        # [NEW] Enterprise CI/CD pipeline docs
│   └── phase_01.md                    # Phase 01 completion documentation
├── backend/
│   ├── .vulture_whitelist.py          # Whitelist for Vulture dead code analyzer
│   ├── pyproject.toml                 # Tool configs (ruff, black, mypy, pytest)
│   ├── requirements.txt               # Updated with CI/quality gate packages
│   └── ...
└── frontend/
    ├── .eslintrc.json                 # ESLint rules with unused-imports rule
    ├── .prettierrc                    # Prettier formatting config
    ├── vitest.config.ts               # Vitest runner config & coverage thresholds
    ├── package.json                   # Updated scripts and devDependencies
    ├── __tests__/
    │   └── MetricCard.test.tsx        # Vitest component unit test
    └── ...
```
