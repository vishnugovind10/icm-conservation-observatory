param(
    [string]$Config = "config/fuji.example.json",
    [string]$PublicDemoUrl = "",
    [switch]$LiveVerify
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
$argsList = @("-m", "icm_observatory.readiness", "--config", $Config)
if ($PublicDemoUrl) {
    $argsList += @("--public-demo-url", $PublicDemoUrl)
}
if ($LiveVerify) {
    $argsList += @("--live-verify")
}
python @argsList
exit $LASTEXITCODE
