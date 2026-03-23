param(
  [int]$Port = 8001
)

$ErrorActionPreference = "Stop"

$env:API_PORT = "$Port"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
  throw "docker compose up failed with exit code $LASTEXITCODE"
}

$base = "http://localhost:$Port"

for ($i = 0; $i -lt 60; $i++) {
  try {
    $health = Invoke-RestMethod -Method Get -Uri "$base/health"
    if ($health.status -eq "ok") { break }
  } catch {
    Start-Sleep -Seconds 1
  }
  if ($i -eq 59) {
    throw "API did not become healthy on $base"
  }
}

$orders = Invoke-RestMethod -Method Get -Uri "$base/orders"
if (-not $orders -or $orders.Count -lt 1) {
  throw "Expected orders to be non-empty"
}

$orderId = $orders[0].id

$payment = Invoke-RestMethod -Method Post `
  -Uri "$base/orders/$orderId/payments" `
  -ContentType "application/json" `
  -Body '{"amount":"100.00","payment_type":"cash"}'

if (-not $payment -or -not $payment.id) {
  throw "Expected payment to be created"
}

Invoke-RestMethod -Method Post `
  -Uri "$base/payments/$($payment.id)/refund" | Out-Null

Write-Host "SMOKE OK"
