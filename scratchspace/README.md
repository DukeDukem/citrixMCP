# Scratchspace

This folder is for **testing scripts**, **result logs**, **screenshots**, and other temporary or experimental files that are not part of the Windows-Use-Agent project.

- **run_citrix_demo.py** – Citrix proof-of-concept: focuses the Citrix window (second monitor), then runs the agent with vision to create folder `test`, a text file with "test test", and save.
  - **No Google API needed by default.** The script uses a **local vision model (Ollama)** so the "AI" runs on your machine. Install [Ollama](https://ollama.com), then run `ollama pull llava`. Run from repo root: `python scratchspace/run_citrix_demo.py`.
  - Optional: use Gemini instead by setting `LLM=google` and `GOOGLE_API_KEY` in `.env`.
  - Override Citrix window title with env `CITRIX_WINDOW_TITLE`.
- **Cursor (this AI) takes over**: Use the **MCP server** so the Cursor AI you're chatting with can see and control Citrix — no Google, no Ollama. See **MCP_SETUP.md** for install and Cursor config. Run `python scratchspace/mcp_citrix_server.py` (or let Cursor start it via MCP), then in chat ask e.g. *"On the Citrix desktop, create a folder test and a text file with 'test test' in it."*
- Keep logs, screenshots, and one-off experiments in this folder so the core project stays clean.
