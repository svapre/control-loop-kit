# Quickstart

## Install in a project
```powershell
git submodule add https://github.com/svapre/control-loop-kit.git tooling/control-loop-kit
git -C tooling/control-loop-kit fetch --tags
git -C tooling/control-loop-kit checkout v0.2.1
```

## Required local wrappers
- `scripts/control_gate.py`
- `scripts/process_guard.py`

Each wrapper should:
1. load toolkit path from `CONTROL_LOOP_KIT_PATH` or `tooling/control-loop-kit`
2. import toolkit module
3. execute `main()`

## Add policy file
Create `.control-loop/policy.json` for project-specific rules.

## CI steps
1. checkout repo with `submodules: recursive`
2. install dependencies
3. lint
4. tests
5. `python scripts/process_guard.py --mode ci --base-sha ...`
6. `python scripts/control_gate.py --mode ci`

## Local verification
```powershell
python -m ruff check .
python -m pytest -q
python scripts/process_guard.py --mode ci
python scripts/control_gate.py --mode ci
```

