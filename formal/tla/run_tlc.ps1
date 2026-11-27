param([Parameter(Mandatory=$true)][string]$Jar)
$ErrorActionPreference = 'Continue'
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) { $PSNativeCommandUseErrorActionPreference = $false }
$Jar = (Resolve-Path -LiteralPath $Jar -ErrorAction Stop).Path
$root = $PSScriptRoot
$protocol = Join-Path $root 'protocol'
$configs = Join-Path $protocol 'configs'
$runId = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$out = Join-Path $root "results/tlc/$runId"
$cache = Join-Path $root ".tlc/$runId"
New-Item -ItemType Directory -Path $out, $cache -Force | Out-Null
Push-Location $protocol
try {
    (Get-FileHash -Algorithm SHA256 $Jar).Hash | Set-Content (Join-Path $out 'jar_sha256.txt')
    & java -version 2>&1 | Out-File (Join-Path $out 'java_version.txt')
    $negative = @{
        ResourceProtocol_U_N = 'BudgetSafety'
        ResourceProtocol_U_VBC = 'BudgetSafety'
        ResourceProtocol_U_VBC_Agreed = 'ActiveAgreementBudgetSafety'
    }
    $results = foreach ($cfg in Get-ChildItem -Path $configs -Filter 'ResourceProtocol_*.cfg' -File | Sort-Object Name) {
        $name = $cfg.BaseName
        Write-Host "Checking $name"
        $log = Join-Path $out "$name.log"
        $stateDir = Join-Path $cache $name
        & java -jar $Jar -workers 1 -metadir $stateDir -config $cfg.FullName ResourceProtocol.tla 2>&1 | Out-File -FilePath $log
        $code = $LASTEXITCODE
        $content = Get-Content -Raw $log
        if ($negative.ContainsKey($name)) {
            $inv = $negative[$name]
            $ok = ($code -eq 12) -and ($content -match ('Invariant\s+' + [regex]::Escape($inv) + '\s+is violated'))
        } else {
            $inv = ''
            $ok = ($code -eq 0) -and ($content -match 'No error has been found')
        }
        [PSCustomObject]@{Config=$name; ExitCode=$code; ExpectedViolation=$inv; Passed=$ok}
    }
    $results | Export-Csv -NoTypeInformation (Join-Path $out 'summary.csv')
    $results | Format-Table -AutoSize
    Write-Host "Logs: $out"
    if ($results | Where-Object { -not $_.Passed }) { throw 'One or more checks did not match the expected result. Inspect the logs.' }
} finally {
    Pop-Location
}
