# ENCS351 — Process Creation and Management (Python/Linux)

> Run on Linux only. Uses `os.fork`, `/proc`, `nice`, and `exec`.

## Quick start

```bash
chmod +x process_management.py
python3 process_management.py task1 -n 3
python3 process_management.py task2 --cmd "ls -l" --cmd "date" --cmd "ps -o pid,ppid,stat,ni,comm"
python3 process_management.py task3 --mode zombie
# re-run with orphan, note: this exits the parent by design
python3 process_management.py task3 --mode orphan
python3 process_management.py task4 --pid $$          # inspect current shell PID
python3 process_management.py task5 --children 3 --base-nice 0 --step 5 --work-seconds 5
```

## Tasks

- **Task 1:** fork N children, each prints PID and PPID. Parent waits for all.
- **Task 2:** children `exec` system commands.
- **Task 3:** zombie and orphan demonstrations. Verify with `ps`.
- **Task 4:** read `/proc/[pid]/status`, `/exe`, and `/fd` data.
- **Task 5:** set different `nice()` values and observe scheduler impact.

## Expected outputs

See `output.txt` for annotated samples. PIDs and timing vary per run.

## Requirements

- Linux with Python 3.8+
- Permissions to read `/proc`

## Submission checklist

- [x] `process_management.py`
- [x] `output.txt`
- [x] `report.pdf` (or `report.md` if PDF libs missing)
- [ ] GitHub repository URL: _add your link here_
