copy "%PROJECT_ROOT%\jarvis\claude_desktop_config.json" "%APPDATA%\Claude\claude_desktop_config.json"

icacls "%PROJECT_ROOT%\jarvis\jarvis_skill\skills.json" /grant "%USERNAME%:(M)"
icacls "%PROJECT_ROOT%\jarvis\jarvis_memory\datasets" /grant "%USERNAME%:(OI)(CI)(M)"