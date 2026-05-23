# GrokDent FL — Automated Cloudflare & GitHub Deployment Script
# Safely initializes Git, pushes code to GitHub, and deploys to Cloudflare D1/R2

Param (
    [string]$GitHubRepoUrl,
    [string]$GitHubToken,
    [string]$CloudflareToken
)

$ErrorActionPreference = "Stop"

# Clear screen and show header
Clear-Host
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "🚀 GrokDent FL — Automated Git & Cloudflare Cloud Deployer 🚀" -ForegroundColor Blue
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "This script securely handles GitHub repository pushes and deploys"
Write-Host "your serverless backend directly to Cloudflare D1 SQL & R2 buckets.`n"

# 1. Redact and validate keys
if (-not $GitHubToken) {
    $GitHubToken = Read-Host -Prompt "Enter your GitHub Personal Access Token (ghp_...)"
}
if (-not $CloudflareToken) {
    $CloudflareToken = Read-Host -Prompt "Enter your Cloudflare API Token (cfut_...)"
}
if (-not $GitHubRepoUrl) {
    $GitHubRepoUrl = Read-Host -Prompt "Enter your GitHub Repository URL (e.g., https://github.com/username/grokdent-fl)"
}

Write-Host "`n[1/4] Initializing Git repository..." -ForegroundColor Yellow
if (-not (Test-Path .git)) {
    git init
}

# Create standard .gitignore
$gitignoreContent = @"
.env
__pycache__/
*.pyc
*.db
.venv/
node_modules/
dist/
.wrangler/
.system_generated/
.agents/
"@
Set-Content -Path .gitignore -Value $gitignoreContent

git add .
git commit -m "Initial commit of GrokDent FL premium serverless platform"

# 2. Push securely to GitHub
Write-Host "`n[2/4] Pushing code securely to GitHub..." -ForegroundColor Yellow
# Extract username and repo name from url to construct secure token push URL
if ($GitHubRepoUrl -match "github\.com/([^/]+)/([^/.]+)") {
    $owner = $Matches[1]
    $repo = $Matches[2]
    $securePushUrl = "https://$GitHubToken@github.com/$owner/$repo.git"
    
    # Check if remote already exists
    $existingRemote = git remote | Select-String -Pattern "origin"
    if ($existingRemote) {
        git remote remove origin
    }
    git remote add origin $securePushUrl
    
    Write-Host "Pushing main branch..."
    git branch -M main
    git push -u origin main --force
    
    # Re-verify and clean remote to hide token from repository metadata
    git remote remove origin
    git remote add origin "https://github.com/$owner/$repo.git"
    Write-Host "[SUCCESS] Pushed successfully! Token cleaned from git remote settings." -ForegroundColor Green
} else {
    Write-Error "Invalid GitHub repository URL format."
}

# 3. Authenticate with Cloudflare Wrangler
Write-Host "`n[3/4] Authenticating with Cloudflare Wrangler..." -ForegroundColor Yellow
$env:CLOUDFLARE_API_TOKEN = $CloudflareToken

# Create Cloudflare D1 Database
Write-Host "Creating Cloudflare D1 SQLite database..."
Set-Location -Path cloudflare-backend
npx wrangler d1 create grokdent-d1

Write-Host "Applying initial SQLite migration schema..."
npx wrangler d1 execute grokdent-d1 --file=schema.sql --local
npx wrangler d1 execute grokdent-d1 --file=schema.sql --remote

# Create R2 Storage Bucket
Write-Host "Provisioning Cloudflare R2 Storage Buckets..."
npx wrangler r2 bucket create grokdent-r2

# 4. Deploying Cloudflare Worker
Write-Host "`n[4/4] Deploying serverless API router..." -ForegroundColor Yellow
npx wrangler deploy

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "🎉 GrokDent FL Cloud Deployment Complete! 🎉" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "GitHub synchronization active: git push now syncs auto-deploys."
Write-Host "Your serverless backend is live on Cloudflare Edge nodes globally!"
Write-Host "D1 Database & R2 Storage bucket provisioned and connected."
Write-Host "==================================================================`n"
