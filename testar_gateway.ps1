Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    TESTANDO GATEWAY SIMPLES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🟢 Testando versão JavaScript..." -ForegroundColor Green
Write-Host ""
node gateway.js
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🟡 Testando versão Python..." -ForegroundColor Yellow
Write-Host ""

# Tenta diferentes comandos do Python
$pythonCommands = @("python", "py", "python3")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python encontrado com '$cmd'" -ForegroundColor Green
            & $cmd gateway.py
            break
        }
    }
    catch {
        # Continua para o próximo comando
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para instalar Python:" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. Baixe e instale" -ForegroundColor White
    Write-Host "3. IMPORTANTE: Marque 'Add Python to PATH'" -ForegroundColor White
    Write-Host "4. Reinicie o terminal" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    TESTE CONCLUÍDO!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Pressione Enter para continuar"
