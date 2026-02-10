# ==============================================================================
# MEDI-MINDER API - AUTOMATED SETUP SCRIPT (Windows PowerShell)
# ==============================================================================
# Purpose: Automates the complete setup and initialization of the Medi-Minder
#          API backend on Windows environments using Docker containerization.
#
# Prerequisites:
#   - Docker Desktop for Windows (with Docker Compose)
#   - Windows PowerShell 5.1 or higher
#
# Usage:
#   .\setup.ps1
#
# What this script does:
#   1. Validates Docker and Docker Compose installations
#   2. Creates and configures .env file with secure defaults
#   3. Cleans up any existing container instances
#   4. Builds fresh Docker images for all services
#   5. Starts containerized services (API, Database, Redis)
#   6. Performs health checks to verify successful deployment
# ==============================================================================

# Stop execution immediately on any error.
$ErrorActionPreference = "Stop"

# ==============================================================================
# HELPER FUNCTION: Write-ColorOutput
# ==============================================================================
# Displays colored console output for better readability and status indication.
#
# Parameters:
#   $ForegroundColor - Color name (e.g., 'Green', 'Red', 'Yellow', 'Blue')
#   $args - Text content to display
# ==============================================================================
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue @"
========================================================================
    MEDI-MINDER API - AUTOMATED SETUP
========================================================================
"@

# ==============================================================================
# STEP 1: Docker Installation Validation
# ==============================================================================
# Verifies that Docker Engine is installed and accessible from the command line.
# Exits with error code 1 if Docker is not found.
# ==============================================================================
Write-ColorOutput Yellow "[1/6] Checking Docker installation..."
try {
    $dockerVersion = docker --version
    Write-ColorOutput Green "✅ Docker is installed: $dockerVersion"
} catch {
    Write-ColorOutput Red "❌ Docker is not installed. Please install Docker Desktop first."
    Write-Host "Visit: https://docs.docker.com/desktop/windows/install/"
    exit 1
}

# ==============================================================================
# STEP 2: Docker Compose Validation
# ==============================================================================
# Verifies that Docker Compose is available for orchestrating multi-container
# deployments. Exits with error code 1 if not found.
# ==============================================================================
Write-ColorOutput Yellow "[2/6] Checking Docker Compose installation..."
try {
    $composeVersion = docker-compose --version
    Write-ColorOutput Green "✅ Docker Compose is installed: $composeVersion"
} catch {
    Write-ColorOutput Red "❌ Docker Compose is not available."
    exit 1
}

# ==============================================================================
# STEP 3: Environment Configuration
# ==============================================================================
# Creates a .env file from the .env.example template if one doesn't exist.
# Automatically generates a cryptographically secure SECRET_KEY for JWT tokens.
# Prompts user to manually configure remaining environment variables.
# ==============================================================================
Write-ColorOutput Yellow "[3/6] Setting up environment variables..."
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..."
    Copy-Item .env.example .env

    # Generate a cryptographically secure random SECRET_KEY for JWT signing.
    # Uses 32 bytes (256 bits) for strong security.
    try {
        $bytes = New-Object Byte[] 32
        [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        $SECRET_KEY = [System.BitConverter]::ToString($bytes) -replace '-', ''

        $envContent = Get-Content .env -Raw
        $envContent = $envContent -replace 'your-super-secret-jwt-key-change-this-in-production-min-32-chars', $SECRET_KEY.ToLower()
        Set-Content .env $envContent -NoNewline

        Write-ColorOutput Green "✅ Generated random SECRET_KEY"
    } catch {
        Write-ColorOutput Yellow "⚠️  Could not generate SECRET_KEY. Please manually update it in .env"
    }

    Write-ColorOutput Green "✅ Created .env file"
    Write-ColorOutput Yellow "⚠️  Please edit .env file with your actual credentials before proceeding"
    Write-Host ""
    Read-Host "Press Enter to continue after editing .env file"
} else {
    Write-ColorOutput Green "✅ .env file already exists"
}

# ==============================================================================
# STEP 4: Container Cleanup
# ==============================================================================
# Stops and removes any existing containers from previous deployments to ensure
# a clean slate. Errors are suppressed if no containers are currently running.
# ==============================================================================
Write-ColorOutput Yellow "[4/6] Stopping any running containers..."
try {
    docker-compose down 2>$null
} catch {
    # Ignore errors if no containers are running.
}
Write-ColorOutput Green "✅ Cleaned up old containers"

# ==============================================================================
# STEP 5: Docker Image Build
# ==============================================================================
# Builds fresh Docker images for all services defined in docker-compose.yml.
# Uses --no-cache flag to ensure a completely clean build without cached layers.
# This step may take several minutes depending on network speed and system resources.
# ==============================================================================
Write-ColorOutput Yellow "[5/6] Building Docker images..."
Write-Host "This may take a few minutes..."
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "❌ Failed to build Docker images"
    exit 1
}
Write-ColorOutput Green "✅ Docker images built successfully"

# ==============================================================================
# STEP 6: Service Startup
# ==============================================================================
# Starts all containerized services in detached mode (-d flag).
# Services include: API (FastAPI), Database (PostgreSQL), and Cache (Redis).
# ==============================================================================
Write-ColorOutput Yellow "[6/6] Starting services..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "❌ Failed to start services"
    exit 1
}
Write-ColorOutput Green "✅ Services started successfully"

# ==============================================================================
# API HEALTH CHECK
# ==============================================================================
# Polls the API /health endpoint to verify successful startup and readiness.
# Attempts up to 30 times with 2-second intervals (60 seconds total timeout).
# ==============================================================================
Write-Host ""
Write-ColorOutput Yellow "⏳ Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Check if API is responding
Write-ColorOutput Yellow "🔍 Checking API health..."
$maxAttempts = 30
$attempt = 0
$apiHealthy = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput Green "✅ API is healthy and responding!"
            $apiHealthy = $true
            break
        }
    } catch {
        # Display progress indicator while waiting for API to respond.
        Write-Host "." -NoNewline
    }
    $attempt++
    Start-Sleep -Seconds 2
}

Write-Host ""

if (-not $apiHealthy) {
    Write-ColorOutput Yellow "⚠️  API health check timed out. Check logs with: docker-compose logs api"
}

# ==============================================================================
# SETUP COMPLETION SUMMARY
# ==============================================================================
# Displays setup completion status with useful endpoints and commands for
# interacting with the deployed services.
# ==============================================================================
Write-ColorOutput Green @"

========================================================================
    🎉 SETUP COMPLETE!
========================================================================

"@

Write-Host "Your Medi-Minder API is now running!"
Write-Host ""
Write-Host "📍 API Endpoint:      http://localhost:8000"
Write-Host "📚 API Documentation: http://localhost:8000/docs"
Write-Host "🔧 Redoc:            http://localhost:8000/redoc"
Write-Host "🗄️  PostgreSQL:       localhost:5432"
Write-Host "⚡ Redis:            localhost:6379"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  • View logs:        docker-compose logs -f api"
Write-Host "  • Stop services:    docker-compose down"
Write-Host "  • Restart API:      docker-compose restart api"
Write-Host "  • View all logs:    docker-compose logs -f"
Write-Host ""
Write-ColorOutput Yellow "⚠️  Remember to configure your email and SMS credentials in .env"
Write-Host ""
