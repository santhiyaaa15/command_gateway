# seed_users.ps1
$API = "http://localhost:5000"
$API_KEY = "YOUR_ADMIN_API_KEY_HERE"

Write-Host "Seeding test users..."

$users = @(
    @{ "name"="test_member"; "role"="member"; "credits"=50 },
    @{ "name"="another_admin"; "role"="admin"; "credits"=500 }
)

foreach ($user in $users) {
    $jsonBody = $user | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$API/admin/users" -Method POST -ContentType "application/json" -Body $jsonBody -Headers @{ "Authorization" = "Bearer $API_KEY" }
        Write-Host "Created $($user.name) - API Key: $($response.api_key)"
    } catch {
        Write-Host "Error: $($_.Exception.Message)"
    }
}

Write-Host "Done!"