# Run from Citrix project root. Tests capture then starts MCP server for Cursor.
Set-Location $PSScriptRoot\..

Write-Host "[1/2] Testing Citrix window capture..." -ForegroundColor Cyan
python scratchspace\test_citrix_capture.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Make sure the Citrix session is open on the second monitor." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""
Write-Host "[2/2] Starting MCP server. Keep this window open and add the server in Cursor MCP settings." -ForegroundColor Cyan
Write-Host "      See scratchspace\MCP_SETUP.md for Cursor config." -ForegroundColor Gray
Write-Host ""
python scratchspace\mcp_citrix_server.py
Read-Host "Press Enter to exit"
