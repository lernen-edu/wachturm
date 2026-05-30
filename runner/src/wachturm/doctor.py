"""Host pre-flight checks for Wachturm (`make doctor` / `wachturm doctor`).

Stdlib-only and standalone: this module imports nothing from the
`wachturm` package, so `make doctor` works on a bare `git clone` with
no dependencies installed (`python3 runner/src/wachturm/doctor.py`). It
is also wired into the Typer CLI as `wachturm doctor` for installed use.

Cross-platform: RAM via POSIX `sysconf` (Linux + macOS, incl. WSL2);
Windows is reported as "unknown" rather than crashing. Thresholds match
the locked decision in PRD §6 / ARCHITECTURE.md §8: 8 GB floor, 16 GB
recommended, 40 GB disk.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys

MIN_DOCKER_MAJOR = 24  # PRD §8.5
RAM_FLOOR_GIB = 8.0  # P4: hard floor
RAM_RECOMMENDED_GIB = 16.0  # P4: comfortable
DISK_RECOMMENDED_GIB = 40.0


def _to_gib(num_bytes: int) -> float:
    """Bytes -> GiB, rounded to one decimal (pure; unit-tested)."""
    return round(num_bytes / (1024**3), 1)


def _total_ram_bytes() -> int | None:
    """Total physical RAM in bytes, or None if it can't be determined."""
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):
        return None


def _run(cmd: list[str]) -> str | None:
    """Run a command, return stripped stdout, or None if it fails/missing."""
    if shutil.which(cmd[0]) is None:
        return None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _parse_major(version_text: str) -> int | None:
    """Pull the leading major version integer out of a version string."""
    match = re.search(r"(\d+)", version_text)
    return int(match.group(1)) if match else None


def _is_wsl() -> bool:
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def _compose_fix_hint() -> None:
    if sys.platform == "darwin":
        print("      Fix: mkdir -p ~/.docker/cli-plugins && \\")
        print("           ln -sf /usr/local/cli-plugins/docker-compose ~/.docker/cli-plugins/docker-compose")
        print("      Or:  brew install docker-compose")
    elif _is_wsl():
        print("      Fix: enable WSL integration in Docker Desktop (Settings → Resources → WSL Integration)")
    else:
        print("      Fix: sudo apt-get install docker-compose-plugin   # Debian/Ubuntu")
        print("           See https://docs.docker.com/compose/install/ for other distros")


def _buildx_fix_hint() -> None:
    if sys.platform == "darwin":
        print("      Fix: brew install docker-buildx && \\")
        print("           ln -sf /opt/homebrew/opt/docker-buildx/bin/docker-buildx ~/.docker/cli-plugins/docker-buildx")
    elif _is_wsl():
        print("      Fix: enable WSL integration in Docker Desktop (Settings → Resources → WSL Integration)")
    else:
        print("      Fix: sudo apt-get install docker-buildx-plugin   # Debian/Ubuntu")
        print("           Or upgrade to Docker Engine 23+ which includes buildx")


def _daemon_fix_hint() -> None:
    if shutil.which("colima"):
        if _run(["colima", "status"]) is None:
            print("FAIL  Docker daemon not reachable. Colima is not running.")
            print("      Fix: colima start")
            print("      For core+casemgmt (~12 GiB needed): colima stop && colima start --memory 14")
        else:
            print("FAIL  Docker daemon not reachable (Colima is running — socket path mismatch?).")
    elif _is_wsl():
        print("FAIL  Docker daemon not reachable. Start Docker Desktop and enable WSL integration.")
        print("      Docker Desktop → Settings → Resources → WSL Integration → enable your distro")
    elif sys.platform == "linux":
        print("FAIL  Docker daemon not reachable.")
        print("      Fix: sudo systemctl start docker")
    else:
        print("FAIL  Docker daemon not reachable. Is Docker Desktop running?")


def _memory_fix_hint() -> None:
    if shutil.which("colima"):
        print("      Fix: colima stop && colima start --memory 14")
    elif _is_wsl():
        print("      Fix: Docker Desktop → Settings → Resources → Memory → set to 14 GB")
        print("           Or add 'memory=14GB' to %USERPROFILE%\\.wslconfig and restart WSL")
    elif sys.platform == "darwin":
        print("      Fix: Docker Desktop → Settings → Resources → Memory → set to 14 GB")


def run() -> int:
    """Print a pre-flight report. Return 0 if usable, 1 on a hard blocker."""
    print("Wachturm doctor — host pre-flight\n" + "-" * 40)
    blockers = 0

    docker_ver = _run(["docker", "--version"])
    if docker_ver is None:
        print("FAIL  Docker: not found. Install Docker 24.x+ (PRD §8.5).")
        blockers += 1
    else:
        major = _parse_major(docker_ver)
        if major is not None and major < MIN_DOCKER_MAJOR:
            print(f"WARN  Docker: {docker_ver} (want >= {MIN_DOCKER_MAJOR}.x)")
        else:
            print(f"OK    Docker: {docker_ver}")

        if _run(["docker", "info"]) is None:
            _daemon_fix_hint()
            blockers += 1
        else:
            raw = _run(["docker", "info", "--format", "{{.MemTotal}}"])
            if raw and raw.isdigit():
                dmem = _to_gib(int(raw))
                if dmem < 12:
                    print(f"WARN  Docker memory: {dmem} GiB allocated (core+casemgmt needs ~12 GiB).")
                    _memory_fix_hint()
                else:
                    print(f"OK    Docker memory: {dmem} GiB")

    compose_ver = _run(["docker", "compose", "version"])
    if compose_ver is not None:
        print(f"OK    Compose: {compose_ver}")
    else:
        compose_ver = _run(["docker-compose", "version"])
        if compose_ver is None:
            print("FAIL  Docker Compose v2: not found ('docker compose' nor 'docker-compose').")
            _compose_fix_hint()
            blockers += 1
        elif re.search(r"(?:^|\s)v?2\.", compose_ver):
            print(f"OK    Compose (standalone v2): {compose_ver}")
        else:
            print(f"WARN  Compose (standalone): {compose_ver} — looks like v1; upgrade recommended.")

    buildx_ver = _run(["docker", "buildx", "version"])
    if buildx_ver is not None:
        print(f"OK    BuildKit: {buildx_ver}")
    else:
        print("FAIL  Docker BuildKit (buildx): not found.")
        _buildx_fix_hint()
        blockers += 1

    ram = _total_ram_bytes()
    if ram is None:
        print("WARN  RAM: could not determine (Windows? check manually: need 8 GB+).")
    else:
        gib = _to_gib(ram)
        if gib < RAM_FLOOR_GIB:
            print(f"FAIL  RAM: {gib} GiB (< {RAM_FLOOR_GIB:g} GiB floor).")
            blockers += 1
        elif gib < RAM_RECOMMENDED_GIB:
            print(f"WARN  RAM: {gib} GiB (tight; {RAM_RECOMMENDED_GIB:g} GiB recommended).")
        else:
            print(f"OK    RAM: {gib} GiB")

    cpus = os.cpu_count() or 0
    cpu_status = "OK  " if cpus >= 4 else "WARN"
    print(f"{cpu_status}  CPU: {cpus or 'unknown'} cores (want 4+)")

    free_disk = _to_gib(shutil.disk_usage(os.getcwd()).free)
    if free_disk < DISK_RECOMMENDED_GIB:
        print(f"WARN  Disk: {free_disk} GiB free (< {DISK_RECOMMENDED_GIB:g} GiB recommended).")
    else:
        print(f"OK    Disk: {free_disk} GiB free")

    # AGENTS §4: doctor checks available host ports. A taken port is a
    # WARN (fixable via .env), not a hard blocker.
    dash_port = int(os.environ.get("WAZUH_DASHBOARD_PORT", "8443"))
    for label, port in (("Wazuh dashboard", dash_port), ("portal", 8000)):
        if _port_in_use(port):
            print(f"WARN  Port {port} ({label}) in use — set WAZUH_DASHBOARD_PORT in .env.")
        else:
            print(f"OK    Port {port} ({label}) free")

    print("-" * 40)
    if blockers:
        print(f"{blockers} blocker(s) — resolve before `make up`.")
        return 1
    print("Host looks usable. (Phase 0: services are not built yet.)")
    return 0


def _port_in_use(port: int) -> bool:
    """True if something is already listening on 127.0.0.1:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    sys.exit(run())
