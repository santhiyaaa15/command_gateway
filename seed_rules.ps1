# seed_rules.ps1
$API = "http://localhost:5000"
$API_KEY = "24ecb7cc02054cbb8e2c3129fddd400f"  # Paste from console

Write-Host "Seeding rules..."

$rules = @(
    @{ "name"="safe_ls"; "pattern"="^ls.*"; "action"="AUTO_ACCEPT"; "order"=1 },
    @{ "name"="safe_pwd"; "pattern"="^pwd$"; "action"="AUTO_ACCEPT"; "order"=2 },
    @{ "name"="dangerous_rm"; "pattern"="^rm -rf.*"; "action"="AUTO_REJECT"; "order"=3 }
)

foreach ($rule in $rules) {
    $jsonBody = $rule | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$API/admin/rules" -Method POST -ContentType "application/json" -Body $jsonBody -Headers @{ "Authorization" = "Bearer $API_KEY" }
        Write-Host "Created: $($rule.name) (ID: $($response.rule_id))"
    } catch {
        Write-Host "Error: $($_.Exception.Message)"
    }
}

Write-Host "Seeding complete!"