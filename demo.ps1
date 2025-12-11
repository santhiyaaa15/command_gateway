$API = "http://localhost:5000"  # Adjust to your API host
$ALICE_KEY = ""

Write-Host "Seeding rules..."
powershell -ExecutionPolicy Bypass -File .\seed_rules.ps1

# Create user 'alice'
Write-Host "`nCreating member user 'alice'..."
$userBody = @{ "name" = "alice" } | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri "$API/admin/users" -Method POST -ContentType "application/json" -Body $userBody
$ALICE_KEY = $response.api_key
Write-Host "ALICE_KEY: $ALICE_KEY"

# Whoami
Write-Host "`nWhoami (alice):"
$whoami = Invoke-RestMethod -Uri "$API/me" -Headers @{ "Authorization" = $ALICE_KEY }
$whoami | Format-Table -Property credits,name,role

# Submit safe command
Write-Host "`nSubmit safe command (ls -la):"
$safeCmdBody = @{ "text" = "ls -la" } | ConvertTo-Json -Compress
try {
    $safeCmd = Invoke-RestMethod -Uri "$API/commands" -Method POST -Headers @{ "Authorization" = $ALICE_KEY } -ContentType "application/json" -Body $safeCmdBody
    $safeCmd | Format-List
} catch { Write-Host $_.Exception.Message }

# Submit dangerous command
Write-Host "`nSubmit dangerous command (rm -rf /):"
$dangerCmdBody = @{ "text" = "rm -rf /" } | ConvertTo-Json -Compress
try {
    $dangerCmd = Invoke-RestMethod -Uri "$API/commands" -Method POST -Headers @{ "Authorization" = $ALICE_KEY } -ContentType "application/json" -Body $dangerCmdBody
    $dangerCmd | Format-List
} catch { Write-Host $_.Exception.Message }

# View alice commands
Write-Host "`nView alice commands:"
$cmds = Invoke-RestMethod -Uri "$API/admin/commands" -Headers @{ "Authorization" = $ALICE_KEY }
$cmds.value | Format-Table id,text,status,created_at

# Admin audit logs
Write-Host "`nAdmin audit logs (first page):"
try {
    $auditLogs = Invoke-RestMethod -Uri "$API/admin/audit" -Headers @{ "Authorization" = $ALICE_KEY }
    $auditLogs | Format-Table id,user_id,command_id,action,metadata,created_at
} catch { Write-Host $_.Exception.Message }
