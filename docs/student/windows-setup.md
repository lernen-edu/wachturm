# Running Wachturm on Windows

Wachturm is built and tested on macOS, and runs the same way on Linux. **On Windows the supported path is WSL2** (Windows Subsystem for Linux) **+ Docker Desktop** — which is really just the Linux path running inside Windows. Once WSL2 is set up, every command in the rest of the docs works exactly as written: you run them in the **Ubuntu (WSL2) terminal**, and you use your normal **Windows browser** for the tool UIs.

> **You need:** 64-bit Windows 10 (version 2004+) or Windows 11, with virtualization enabled in the BIOS/UEFI; **16 GB RAM** and **~40 GB free disk** for the full lab.

> This guide follows the standard WSL2 + Docker Desktop flow. It's verified against that well-trodden pattern rather than on a Windows host directly — if a Docker Desktop menu has moved in a newer version, the **setting name** will still match what's described here.

## 1. Install WSL2 + Ubuntu

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu. **Reboot when prompted.** After the reboot, Ubuntu opens and asks you to create a Linux username + password — do that (it's your WSL2 account, separate from your Windows login).

Confirm you're on WSL **version 2**:

```powershell
wsl -l -v
```

The `VERSION` column should read `2`. If it says `1`, run `wsl --set-version Ubuntu 2` and wait for it to convert.

## 2. Give WSL2 enough memory

The full lab needs ~9.5 GB of RAM for Docker, and WSL2's default cap can be too low. Create a file at **`C:\Users\<you>\.wslconfig`** (your Windows home folder) containing:

```ini
[wsl2]
memory=16GB
processors=4
```

Then, in PowerShell: `wsl --shutdown`. WSL2 restarts on next use with the new limits.

## 3. Install Docker Desktop (WSL2 backend)

Install **Docker Desktop for Windows** from [docker.com](https://www.docker.com/products/docker-desktop/). Then:

- **Settings → General** — make sure **"Use the WSL 2 based engine"** is checked.
- **Settings → Resources → WSL Integration** — turn **on** integration for your **Ubuntu** distro. Click **Apply & restart**.

This puts `docker` and `docker compose` *inside* your Ubuntu shell, which is where Wachturm runs. Verify from an **Ubuntu** terminal:

```bash
docker version          # prints both Client and Server
docker compose version
```

## 4. Install the basics in Ubuntu

In the **Ubuntu** terminal:

```bash
sudo apt update
sudo apt install -y make git
```

## 5. Clone Wachturm *inside* WSL2 — this matters

Clone into your **Linux home directory** (`~`), **not** a Windows path like `/mnt/c/...`. Two reasons: Docker bind-mounts from the Windows filesystem are slow, and Windows line-ending conversion (CRLF) corrupts the shell scripts. From the Ubuntu terminal:

```bash
cd ~
git clone https://github.com/lernen-edu/wachturm
cd wachturm
```

> Keeping the repo under `/mnt/c/...` gives you slow I/O and `\r`/"command not found" script errors. Don't — clone in `~`.

## 6. Run it (exactly like the main docs)

Everything from here is the normal flow, run **in the Ubuntu terminal**:

```bash
make doctor             # checks Docker + RAM (reads correctly under WSL2)
cp .env.example .env
make up-casemgmt        # the full v1.0 stack; the first build is slow
make first-run-creds    # prints the tool URLs + sealed-lab logins
make scenario SCN=SCN-001
```

Open the tool UIs in your **normal Windows browser** — Docker Desktop forwards WSL2's localhost to Windows, so the URLs are identical to macOS/Linux:

- Portal — <http://localhost:8000>
- Wazuh — <https://127.0.0.1:8443>
- DFIR-IRIS — <https://127.0.0.1:9000>
- Cortex — <http://127.0.0.1:9001>

Accept the self-signed-certificate warnings on the HTTPS ones; that's expected for a local lab. From here, follow [`02-first-shift.md`](02-first-shift.md) and the rest of the curriculum normally — nothing else is Windows-specific.

## 7. The tutor (`make tutor`) on Windows

The Socratic tutor runs an agentic CLI (Claude Code, Codex, Gemini CLI, OpenCode, or Pi). **Install it inside Ubuntu (WSL2)** — the Linux build — because `make tutor` runs inside WSL2, not on the Windows side.

Then run `make tutor` from the Ubuntu terminal. WSL2 has no graphical terminal of its own, so the tutor opens **in your current terminal** (it prints a note saying so). The clean setup:

- Open **two Ubuntu tabs** in Windows Terminal (the `+` button, or `Ctrl+Shift+T`): one for `make tutor` (your coach), one for `make scenario` / `make score` (your work).
- Keep your **browser tabs** for Wazuh / IRIS / Cortex.

That's the same "tutor in its own window, work in another" model the tutor docs describe — just with WSL2 tabs. If `make tutor` ever misbehaves on your setup, you can start the tutor by hand: `bash tools/launch-tutor.sh --dry-run` prints the exact agent command; run that in a second Ubuntu tab.

## Troubleshooting

- **`make: command not found`** — you're in PowerShell, not Ubuntu (or you skipped step 4). Run everything in the Ubuntu terminal.
- **`docker: command not found` in Ubuntu** — Docker Desktop's WSL Integration isn't enabled for your distro (step 3).
- **Scripts fail with `\r` or odd "command not found" errors** — you cloned on the Windows filesystem; re-clone inside `~` (step 5).
- **Containers get OOM-killed, or Wazuh keeps restarting** — WSL2 has too little memory; raise the `.wslconfig` limit (step 2) and run `wsl --shutdown`.
- **`make doctor` says "RAM: could not determine (Windows?)"** — that only happens on *native* Windows; inside WSL2 it reads RAM fine. If you see it, you're not in the Ubuntu shell.
- **First `make up-casemgmt` is very slow** — normal; it's building images. Later starts are quick.

---

*Windows = WSL2 + Docker Desktop. If you can open the Ubuntu terminal and `docker version` works there, the rest of Wachturm is identical to macOS and Linux.*
