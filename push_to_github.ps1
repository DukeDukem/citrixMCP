# Push citrixMCP to GitHub. Run from project root in PowerShell (ensure Git is in PATH).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found in PATH. Install Git for Windows or add it to PATH, then run this script again."
    exit 1
}

if (-not (Test-Path .git)) {
    Write-Host "Initializing git repo..."
    git init
    git add README.md
    git add .
    git commit -m "first commit"
} else {
    Write-Host "Existing repo detected. Adding and committing changes..."
    git add .
    $status = git status --porcelain
    if ($status) {
        git commit -m "citrixMCP: MCP server, Explorer content clicks, Windows UI patterns"
    }
}

git branch -M main
$remote = git remote get-url origin 2>$null
if (-not $remote) {
    git remote add origin https://github.com/DukeDukem/citrixMCP.git
}
Write-Host "Pushing to origin main..."
git push -u origin main
Write-Host "Done."
