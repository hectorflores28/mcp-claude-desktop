from mcp.server.fastmcp import FastMCP
import subprocess

mcp = FastMCP("Speak")

@mcp.tool(name="say", description="Haz que el ordenador hable en voz alta")
def say(texto: str) -> str:
    # PowerShell con voz masculina tipo Jarvis
    script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.SelectVoice('Microsoft David Desktop')
    $synth.Rate = 1
    $synth.Volume = 100
    $synth.Speak('{texto}')
    """
    subprocess.run(["powershell", "-Command", script], check=False)
    return "Hablando"

if __name__ == "__main__":
    mcp.run()