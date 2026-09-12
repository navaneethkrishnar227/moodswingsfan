# Push MoodswingsFan to GitHub
$destDir = "$env:LOCALAPPDATA\Programs\Git"
$env:Path = "$destDir\cmd;$env:Path"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       MoodswingsFan - Push Code to GitHub              " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$repoUrl = "https://github.com/navaneethkrishnar227/moodswingsfan"
$apiUrl = "https://api.github.com/repos/navaneethkrishnar227/moodswingsfan"

Write-Host "`n[1/3] Checking if remote repository exists on GitHub..." -ForegroundColor Yellow

$exists = $false
try {
    $res = Invoke-RestMethod -Uri $apiUrl -Headers @{"User-Agent"="PowerShell"} -ErrorAction Stop
    $exists = $true
} catch {
    $exists = $false
}

if (-not $exists) {
    Write-Host "[!] Repository not found yet on GitHub." -ForegroundColor Red
    Write-Host "[*] Opening repo creation page in your browser..." -ForegroundColor Green
    Start-Process "https://github.com/new?name=moodswingsfan"
    Write-Host "`n>>> Please click the green 'Create repository' button in your browser! <<<" -ForegroundColor Magenta
    Write-Host "Press ENTER once you have clicked 'Create repository'..."
    Read-Host
}

Write-Host "`n[2/3] Staging and committing any local changes..." -ForegroundColor Yellow
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "Update MoodswingsFan project files"
    Write-Host "[+] Local changes committed." -ForegroundColor Green
} else {
    Write-Host "[i] Working directory clean, ready to push." -ForegroundColor Green
}

Write-Host "`n[3/3] Pushing main branch to GitHub..." -ForegroundColor Yellow
Write-Host "(*) If prompted by Git Credential Manager, click 'Sign in with your browser' to authorize." -ForegroundColor Cyan

git push -u origin main


if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " SUCCESS! Code successfully pushed to:" -ForegroundColor Green
    Write-Host " $repoUrl" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Host "`n[!] Push encountered an issue. See above output." -ForegroundColor Red
}

Write-Host "`nPress any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
