# Installation

## Phase 1 backend

1. Install Python 3.11 if possible. Python 3.12+ may work, but Python 3.11 is
   the project baseline.
2. From the project root, run `.\scripts\check_environment.ps1`.
3. Run `.\scripts\setup.ps1` to create `.venv` and install the small
   backend dependency set.
4. Start with `.\scripts\start_backend.ps1`.
5. Verify `GET http://127.0.0.1:8000/health`.

No model or avatar download is performed by these steps.
