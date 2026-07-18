# Publish Seneschal to PyPI.
#
# Run it, do not copy lines out of it:
#     powershell -ExecutionPolicy Bypass -File scripts\publish.ps1
#
# Requires $HOME\.pypirc to exist with the API token. Write that file in
# Notepad, never by pasting into a console. A console paste corrupts the
# token with control characters and PyPI answers 403, which looks like a
# permissions problem and is not.
#
#     [pypi]
#     username = __token__
#     password = pypi-<token>
#
# The script deletes .pypirc when it finishes, on success or failure.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$pypirc = Join-Path $HOME ".pypirc"

function Cleanup {
    if (Test-Path $pypirc) {
        Remove-Item $pypirc -Force
        Write-Host "[ok] .pypirc deleted (it held the token in clear text)" -ForegroundColor Green
    }
}

try {
    if (-not (Test-Path $pypirc)) {
        Write-Host "[!] $pypirc not found. Create it in Notepad first:" -ForegroundColor Yellow
        Write-Host "    notepad `$HOME\.pypirc"
        exit 1
    }

    Write-Host "== rebuilding ==" -ForegroundColor Cyan
    Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
    python -m build
    if ($LASTEXITCODE -ne 0) { throw "build failed" }

    Write-Host "== validating ==" -ForegroundColor Cyan
    python -m twine check dist\*
    if ($LASTEXITCODE -ne 0) { throw "twine check failed" }

    Write-Host "== uploading ==" -ForegroundColor Cyan
    python -m twine upload dist\*
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Upload failed. What the status code means:" -ForegroundColor Yellow
        Write-Host "  429  PyPI's new-project rate limit. Nothing is wrong with the"
        Write-Host "       package or the token. Wait and run this again."
        Write-Host "  403  The token is corrupt, almost always from pasting it into a"
        Write-Host "       console. Rewrite .pypirc in Notepad."
        Write-Host "  400  That version already exists. Bump the version; PyPI never"
        Write-Host "       allows replacing a released file."
        throw "upload failed"
    }

    Write-Host ""
    Write-Host "[ok] published. Verify it actually installs:" -ForegroundColor Green
    Write-Host "     pip install seneschal"
    Write-Host "     seneschal health --strict"
}
finally {
    Cleanup
}
