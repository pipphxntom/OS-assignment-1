#!/usr/bin/env python3
"""
ENCS351 Operating System — Lab Experiment Sheet-1
Process Creation and Management Using Python OS Module
Author: <Your Name>
Note: Run on Linux. Uses os.fork, /proc, and nice values.
"""
import os
import sys
import time
import argparse
import errno
import subprocess
from typing import List

# ---------- Utilities ----------

def is_linux() -> bool:
    return sys.platform.startswith("linux")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def wait_all_children():
    """Wait for all child processes until no children remain."""
    while True:
        try:
            pid, status = os.wait()
            print(f"[parent] waited pid={pid} status={status}", flush=True)
        except ChildProcessError:
            break

def cpu_intensive_work(seconds: int = 3):
    """Simple CPU-bound loop to consume CPU for 'seconds' seconds."""
    end = time.time() + seconds
    x = 0
    while time.time() < end:
        # Busy work: a few math ops
        x = (x + 1) ^ (x << 1) ^ (x >> 1)
    return x

# ---------- Task 1: Process Creation Utility ----------

def task1_create_children(n: int):
    """
    Fork N children. Each child prints its PID, PPID, and a custom message.
    Parent waits for all children.
    """
    if not is_linux():
        eprint("Task 1 requires Linux.")
        return 1

    print(f"[task1] forking {n} children...", flush=True)
    for i in range(n):
        pid = os.fork()
        if pid == 0:
            # Child
            print(f"[child-{i}] PID={os.getpid()} PPID={os.getppid()} msg='hello from child {i}'", flush=True)
            os._exit(0)
        else:
            # Parent continues loop
            pass
    wait_all_children()
    return 0

# ---------- Task 2: Command Execution Using exec() ----------

def task2_exec_commands(commands: List[List[str]]):
    """
    For each command, fork a child and exec the command.
    Parent waits for all children.
    Example commands: [["ls","-l"], ["date"], ["ps","-o","pid,ppid,stat,ni,comm"]]
    """
    if not is_linux():
        eprint("Task 2 requires Linux.")
        return 1

    print(f"[task2] exec for {len(commands)} commands", flush=True)
    for idx, cmd in enumerate(commands):
        pid = os.fork()
        if pid == 0:
            # Child replaces itself with the command
            try:
                print(f"[child-{idx}] exec -> {' '.join(cmd)} (PID={os.getpid()})", flush=True)
                os.execvp(cmd[0], cmd)
            except Exception as ex:
                eprint(f"[child-{idx}] exec failed: {ex}")
                os._exit(1)
        else:
            # Parent
            pass
    wait_all_children()
    return 0

# ---------- Task 3: Zombie & Orphan Processes ----------

def task3_zombie():
    """
    Create a zombie by forking a child that exits quickly while the parent does not wait immediately.
    Verify with: ps -el | grep defunct   or   ps -o pid,ppid,stat,comm | grep Z
    """
    if not is_linux():
        eprint("Task 3 requires Linux.")
        return 1

    pid = os.fork()
    if pid == 0:
        print(f"[child] exiting immediately to become zombie; PID={os.getpid()} PPID={os.getppid()}", flush=True)
        os._exit(0)
    else:
        print(f"[parent] spawned child PID={pid} and will sleep without wait()", flush=True)
        time.sleep(5)
        # Show process table snapshot
        try:
            print("[parent] ps snapshot (looking for Z/defunct):", flush=True)
            subprocess.run(["bash", "-lc", "ps -o pid,ppid,stat,comm | grep -E 'STAT| Z '"], check=False)
        except Exception as ex:
            eprint(f"[parent] ps failed: {ex}")
        # Reap the child to clean up
        try:
            wpid, status = os.waitpid(pid, 0)
            print(f"[parent] finally waited zombie pid={wpid} status={status}", flush=True)
        except ChildProcessError:
            pass
    return 0

def task3_orphan():
    """
    Create an orphan: parent exits before child finishes. The child should get reparented to PID 1.
    Note: Running this will terminate the parent process (this script) early by design.
    """
    if not is_linux():
        eprint("Task 3 requires Linux.")
        return 1

    pid = os.fork()
    if pid == 0:
        print(f"[child] start PID={os.getpid()} original PPID={os.getppid()}", flush=True)
        time.sleep(5)
        print(f"[child] after parent exit, new PPID={os.getppid()} (likely 1)", flush=True)
        os._exit(0)
    else:
        print(f"[parent] exiting immediately to orphanize child PID={pid}", flush=True)
        os._exit(0)  # Exit without waiting; makes the child orphan

# ---------- Task 4: Inspecting Process Info from /proc ----------

def read_first_line(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.readline().strip()
    except Exception as ex:
        return f"<error reading {path}: {ex}>"

def task4_inspect_proc(pid: int):
    """
    Read and print process info from /proc/[pid].
    - name, state, VmRSS from /proc/[pid]/status
    - executable path from /proc/[pid]/exe
    - open FDs from /proc/[pid]/fd
    """
    if not is_linux():
        eprint("Task 4 requires Linux.")
        return 1

    status_path = f"/proc/{pid}/status"
    exe_path = f"/proc/{pid}/exe"
    fd_dir = f"/proc/{pid}/fd"

    try:
        with open(status_path, "r") as f:
            status_lines = f.readlines()
        # Extract a few keys
        wanted = {}
        for line in status_lines:
            if line.startswith(("Name:", "State:", "VmRSS:", "VmSize:", "Threads:")):
                k, v = line.split(":", 1)
                wanted[k.strip()] = v.strip()
        print("[task4] /proc/[pid]/status:", flush=True)
        for k in ("Name", "State", "VmRSS", "VmSize", "Threads"):
            if k in wanted:
                print(f"  {k}: {wanted[k]}", flush=True)
    except FileNotFoundError:
        eprint(f"/proc/{pid} does not exist. Is the PID valid?")
        return 1

    try:
        exe_real = os.readlink(exe_path)
        print(f"[task4] /proc/{pid}/exe -> {exe_real}", flush=True)
    except Exception as ex:
        eprint(f"cannot read exe: {ex}")

    try:
        fds = os.listdir(fd_dir)
        print(f"[task4] /proc/{pid}/fd count = {len(fds)}", flush=True)
        # Show a small sample
        for fd in sorted(fds)[:10]:
            target = os.readlink(os.path.join(fd_dir, fd))
            print(f"   fd {fd} -> {target}", flush=True)
    except Exception as ex:
        eprint(f"cannot list fd: {ex}")

    return 0

# ---------- Task 5: Process Prioritization with nice() ----------

def task5_priority(n_children: int = 3, base_nice: int = 0, step: int = 5, work_seconds: int = 5):
    """
    Spawn n_children. Each child sets a different nice value and runs CPU work.
    Log start and end to observe scheduler effects.
    Note: Increasing nice lowers priority.
    """
    if not is_linux():
        eprint("Task 5 requires Linux.")
        return 1

    children = []
    for i in range(n_children):
        pid = os.fork()
        if pid == 0:
            try:
                target_nice = base_nice + i * step
                try:
                    cur = os.nice(0)
                    delta = target_nice - cur
                    if delta != 0:
                        os.nice(delta)
                except OSError as ex:
                    eprint(f"[child-{i}] nice change failed: {ex}")

                cur_nice = os.nice(0)
                start = time.time()
                print(f"[child-{i}] PID={os.getpid()} PPID={os.getppid()} nice={cur_nice} start={start}", flush=True)
                cpu_intensive_work(work_seconds)
                end = time.time()
                print(f"[child-{i}] PID={os.getpid()} finished at {end} elapsed={end - start:.2f}s", flush=True)
            finally:
                os._exit(0)
        else:
            children.append(pid)
    wait_all_children()
    return 0

# ---------- CLI ----------

def parse_args():
    p = argparse.ArgumentParser(description="Process management tasks (Linux only).")
    sub = p.add_subparsers(dest="task", required=True)

    # task1
    p1 = sub.add_parser("task1", help="Process creation with fork and wait")
    p1.add_argument("-n", "--num", type=int, default=3, help="Number of children")

    # task2
    p2 = sub.add_parser("task2", help="Exec commands from children")
    p2.add_argument("--cmd", action="append", help="Command to run (space-separated). Can be given multiple times. Example: --cmd 'ls -l' --cmd 'date'")

    # task3
    p3 = sub.add_parser("task3", help="Zombie and Orphan demos")
    p3.add_argument("--mode", choices=["zombie", "orphan"], required=True)

    # task4
    p4 = sub.add_parser("task4", help="Inspect /proc for a PID")
    p4.add_argument("--pid", type=int, required=True)

    # task5
    p5 = sub.add_parser("task5", help="Priority with nice() and CPU-bound work")
    p5.add_argument("--children", type=int, default=3)
    p5.add_argument("--base-nice", type=int, default=0)
    p5.add_argument("--step", type=int, default=5)
    p5.add_argument("--work-seconds", type=int, default=5)

    return p.parse_args()

def main():
    args = parse_args()
    if args.task in {"task1", "task2", "task3", "task4", "task5"} and not is_linux():
        eprint("This program requires Linux. Exiting.")
        sys.exit(1)

    if args.task == "task1":
        sys.exit(task1_create_children(args.num))

    if args.task == "task2":
        if not args.cmd:
            # default commands
            cmds = [["ls", "-l"], ["date"], ["ps", "-o", "pid,ppid,stat,ni,comm"]]
        else:
            cmds = [c.strip().split() for c in args.cmd]
        sys.exit(task2_exec_commands(cmds))

    if args.task == "task3":
        if args.mode == "zombie":
            sys.exit(task3_zombie())
        else:
            # orphan mode will exit the parent intentionally
            task3_orphan()
            # unreachable in parent
            return

    if args.task == "task4":
        sys.exit(task4_inspect_proc(args.pid))

    if args.task == "task5":
        sys.exit(task5_priority(args.children, args.base_nice, args.step, args.work_seconds))

if __name__ == "__main__":
    main()
