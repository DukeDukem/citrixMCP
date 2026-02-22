"""
Citrix proof-of-concept runner: focus the Citrix window, then run the agent with vision
to create folder 'test' on the Citrix desktop, create a text file there, write 'test test', and save.

Uses a LOCAL vision model (Ollama) by default — no Google or other API key needed.
Install Ollama (https://ollama.com), then run: ollama pull llava
Override with env: LLM=google (and set GOOGLE_API_KEY) to use Gemini instead.
Run from project root: python scratchspace/run_citrix_demo.py
"""
import os
import sys

# Ensure project root is on path and load env from repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

from dotenv import load_dotenv
load_dotenv()

from windows_use.agent import Agent
from rich.console import Console
from rich.markdown import Markdown

# Default Citrix window title (override with env CITRIX_WINDOW_TITLE)
CITRIX_WINDOW_TITLE = os.environ.get("CITRIX_WINDOW_TITLE", "RDSH Agenten YMMD - Desktop Viewer")

# LLM: "ollama" = local vision model (no API key). "google" = Gemini (needs GOOGLE_API_KEY).
LLM_CHOICE = os.environ.get("LLM", "ollama").lower()
OLLAMA_VISION_MODEL = os.environ.get("OLLAMA_MODEL", "llava")

TASK = (
    "On the desktop, create a folder named 'test'. Open that folder. "
    "Create a text file, write 'test test' in it, and save it in the test folder."
)


def _get_llm():
    """Use local Ollama vision model by default; no API key required."""
    if LLM_CHOICE == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    # Default: Ollama with vision model (e.g. llava). Run: ollama pull llava
    from langchain_ollama import ChatOllama
    return ChatOllama(model=OLLAMA_VISION_MODEL)


def main():
    console = Console()
    console.print(f"[dim]Using LLM: {LLM_CHOICE} (vision model)[/dim]")
    llm = _get_llm()
    agent = Agent(
        llm=llm,
        browser="chrome",
        use_vision=True,
        target_window_title=CITRIX_WINDOW_TITLE,
    )
    desktop = agent.desktop

    # Populate desktop_state so switch_app can find windows
    console.print("[yellow]Getting desktop state and focusing Citrix window...[/yellow]")
    desktop.get_state(use_vision=True)
    msg, status = desktop.switch_app(CITRIX_WINDOW_TITLE)
    if status != 0:
        console.print(f"[red]Warning: {msg}[/red]")
        console.print("[yellow]Continuing anyway; ensure the Citrix window is visible on the second monitor.[/yellow]")
    else:
        console.print(f"[green]{msg}[/green]")

    console.print("[yellow]Running agent task (this may take a while)...[/yellow]")
    result = agent.invoke(TASK)
    if result.is_done and result.content:
        console.print(Markdown(result.content))
    else:
        console.print(f"[red]Error or not done: {result.error or 'Unknown'}[/red]")
    return result


if __name__ == "__main__":
    main()
