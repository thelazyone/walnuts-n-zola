# Link the repo root as the theme for local exampleSite / lesnack builds.
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Link-Theme($site) {
    $themes = Join-Path $site "themes"
    $link = Join-Path $themes "walnuts-n-zola"
    New-Item -ItemType Directory -Force -Path $themes | Out-Null
    if (Test-Path $link) { Remove-Item $link -Force -Recurse }
    cmd /c mklink /J $link $root | Out-Null
    Write-Host "Linked $link -> $root"
}

Link-Theme (Join-Path $root "exampleSite")
if (Test-Path (Join-Path $root "lesnack")) {
    Link-Theme (Join-Path $root "lesnack")
}
