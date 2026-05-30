# Running Wachturm on Windows

Wachturm is built and tested on macOS, and runs the same way on Linux. **On Windows the supported path is WSL2** (Windows Subsystem for Linux) **+ Docker Desktop** — which is really just the Linux path running inside Windows. Once WSL2 is set up, every command in the rest of the docs works exactly as written: you run them in the **Ubuntu (WSL2) terminal**, and you use your normal **Windows browser** for the tool UIs.

> **You need:** 64-bit Windows 10 (version 2004+) or Windows 11, with virtualization enabled in the BIOS/UEFI; **16 GB RAM** and **~40 GB free disk** for the full lab.

> This guide follows the standard WSL2 + Docker Desktop flow. It's verified against that well-trodden pattern rather than on a Windows host directly — if a Docker Desktop menu has moved in a newer version, the **setting name** will still match what's described here.

## 1. Install WSL2 + Ubuntu

**Open PowerShell as Administrator:** click the **Start** button, type `PowerShell`, right-click **Windows PowerShell** in the results, and choose **Run as administrator** (click **Yes** if Windows asks permission). A dark window opens — that's PowerShell. In it, run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu. **Reboot when prompted.** After the reboot, an **Ubuntu** window opens and asks you to create a Linux username + password — do that. It's your WSL2 account, separate from your Windows login, and **you'll need this password later for every `sudo` command, so remember it.** Note: when you type a Linux password, *nothing appears on screen* — no dots or stars. That's normal; type it and press Enter.

> **You'll juggle two kinds of terminal — keep them straight.** **PowerShell** runs the `wsl ...` setup commands; **Ubuntu** runs everything else. To open **Ubuntu** any time: **Start → type `Ubuntu` → Enter**. For the smoothest experience, install **Windows Terminal** from the Microsoft Store (Windows 11 already has it) — it gives you tabs, so PowerShell, Ubuntu, and a second Ubuntu tab can sit side by side.

Back in **PowerShell**, confirm you're on WSL **version 2**:

```powershell
wsl -l -v
```

The `VERSION` column should read `2`. If it says `1`, run `wsl --set-version Ubuntu 2` (in PowerShell) and wait for it to convert.

## 2. Give WSL2 enough memory

The full lab needs ~9.5 GB of RAM for Docker, and WSL2's default cap can be too low. You'll create a small file named `.wslconfig` in your Windows home folder (`C:\Users\<your-windows-username>\`):

1. Open **Notepad** (Start → type `Notepad` → Enter).
2. Paste exactly this:

   ```ini
   [wsl2]
   memory=16GB
   processors=4
   ```

3. **File → Save As.** Browse to **This PC → Local Disk (C:) → Users → _your username_**. **Important:** set **"Save as type" to "All Files"** (not "Text Documents"), then type the file name **`.wslconfig`** and click **Save**.

   > The "All Files" step matters. If you leave it on "Text Documents," Windows silently saves the file as `.wslconfig.txt` and the memory limit won't take effect — which shows up later as mysterious container crashes, not an error now.

4. In **PowerShell**, run `wsl --shutdown`. WSL2 restarts with the new limits the next time you open Ubuntu.

## 3. Install Docker Desktop (WSL2 backend)

Install **Docker Desktop for Windows** from [docker.com](https://www.docker.com/products/docker-desktop/), then **launch it** (Start → Docker Desktop) and wait for the **whale icon** in the taskbar tray (bottom-right) to stop animating — Docker Desktop must be *running* for any `docker` command to work. Then open its settings:

- **Settings → General** — make sure **"Use the WSL 2 based engine"** is checked.
- **Settings → Resources → WSL Integration** — turn **on** integration for **Ubuntu** (the entry labelled *Ubuntu* in the list). Click **Apply & restart**.

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

Clone into your **Linux home directory** (`~`), **not** a Windows path like `/mnt/c/...`. Two reasons: Docker reading files from the Windows side is much slower, and Windows line-ending conversion (CRLF) corrupts the shell scripts. From the Ubuntu terminal:

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
```

Open the tool UIs in your **normal Windows browser** — Docker Desktop forwards WSL2's localhost to Windows, so the URLs are identical to macOS/Linux:

- Portal — <http://localhost:8000>
- Wazuh — <https://127.0.0.1:8443>
- DFIR-IRIS — <https://127.0.0.1:9000>
- Cortex — <http://127.0.0.1:9001>

Accept the self-signed-certificate warnings on the HTTPS ones; that's expected for a local lab. Once the portal shows **Wazuh** and **DFIR-IRIS** online, your setup is done — now follow **[`02-first-shift.md`](02-first-shift.md)**, which runs your first scenario and walks you through triaging it. (It runs `make scenario` for you, so don't run it here.) Nothing from here on is Windows-specific.

## 7. The tutor (`make tutor`) on Windows

The Socratic tutor is **optional** — you can do the whole course without it. It runs an agentic CLI: Claude Code, Codex, Gemini CLI, OpenCode, or Pi. You need **one** of them installed **inside Ubuntu (WSL2)** — the Linux build — because `make tutor` runs inside WSL2, not on the Windows side. Install it by following that tool's own Linux instructions *in the Ubuntu terminal* — for **Claude Code**, that's the official guide at <https://docs.claude.com/en/docs/claude-code>. If you don't have one, skip this section.

Then run `make tutor` from the Ubuntu terminal. WSL2 has no graphical terminal of its own, so the tutor opens **in your current terminal** (it prints a note saying so). The clean setup:

- Open **two Ubuntu tabs** in Windows Terminal (the `+` button, or `Ctrl+Shift+T`): one for `make tutor` (your coach), one for `make scenario` / `make score` (your work).
- Keep your **browser tabs** for Wazuh / IRIS / Cortex.

That's the same "tutor in its own window, work in another" model the tutor docs describe — just with WSL2 tabs. Whichever way `make tutor` opens it, talk to the tutor in *that* window and keep a separate Ubuntu tab for your `make` commands.

## Troubleshooting

- **`make: command not found`** — you're in PowerShell, not Ubuntu (or you skipped step 4). Run everything in the Ubuntu terminal.
- **`docker: command not found` in Ubuntu** — Docker Desktop's WSL Integration isn't enabled for Ubuntu (step 3).
- **`Cannot connect to the Docker daemon`** (or "the system cannot find the file specified") — Docker Desktop isn't *running*. Launch it (Start → Docker Desktop), wait for the whale icon in the tray to go steady, and retry.
- **Scripts fail with `\r` or odd "command not found" errors** — you cloned on the Windows filesystem; re-clone inside `~` (step 5).
- **Containers get OOM-killed, or Wazuh keeps restarting** — WSL2 has too little memory; raise the `.wslconfig` limit (step 2) and run `wsl --shutdown`. Also double-check the file is named exactly **`.wslconfig`**, not `.wslconfig.txt` (re-save from Notepad with **Save as type: All Files**).
- **`make doctor` says "RAM: could not determine (Windows?)"** — that only happens on *native* Windows; inside WSL2 it reads RAM fine. If you see it, you're not in the Ubuntu shell.
- **First `make up-casemgmt` is very slow** — normal; it's building images. Later starts are quick.

---

*Windows = WSL2 + Docker Desktop. If you can open the Ubuntu terminal and `docker version` works there, the rest of Wachturm is identical to macOS and Linux.*
