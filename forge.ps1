$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
& "d:\env\python.exe" "$scriptDir\main.py" @args
