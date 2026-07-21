# Running the Project

Use 3 terminals in this order after Redis is already running.

## Terminal 1

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## Terminal 2

```powershell
.\.venv\Scripts\Activate.ps1
python worker_main.py
```

## Terminal 3

```powershell
.\.venv\Scripts\Activate.ps1
python test_system.py
```

## One-time note

If PowerShell blocks activation, run this once in that terminal:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Redis must already be running before you start Terminal 1.
