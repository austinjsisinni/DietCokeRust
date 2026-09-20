$ErrorActionPreference = "Stop"

function Assert-NativeSuccess([string] $Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
$RustCompiler = Join-Path $CargoBin "rustc.exe"

if (-not (Test-Path -LiteralPath $RustCompiler)) {
    throw "rustc was not found at $RustCompiler. Install Rust with rustup first."
}

# Some Windows installations have the MSVC linker and OneCore libraries but
# lack vcvarsall.bat. Locate those libraries without changing the user's global
# LIB environment variable.
if ($IsWindows) {
    $MsvcRoot = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC"
    $MsvcVersion = Get-ChildItem -LiteralPath $MsvcRoot -Directory |
        Sort-Object Name -Descending |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "lib\onecore\x64\msvcrt.lib")
        } |
        Select-Object -First 1

    $SdkRoot = "C:\Program Files (x86)\Windows Kits\10\Lib"
    $SdkVersion = Get-ChildItem -LiteralPath $SdkRoot -Directory |
        Sort-Object Name -Descending |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "um\x64\kernel32.lib")
        } |
        Select-Object -First 1

    if ($null -ne $MsvcVersion -and $null -ne $SdkVersion) {
        $LocalLibraries = @(
            (Join-Path $MsvcVersion.FullName "lib\onecore\x64"),
            (Join-Path $SdkVersion.FullName "ucrt\x64"),
            (Join-Path $SdkVersion.FullName "um\x64")
        )
        if ($env:LIB) {
            $LocalLibraries += $env:LIB
        }
        $env:LIB = $LocalLibraries -join ";"
    }
}

Push-Location $ProjectRoot
try {
    & $RustCompiler --version
    Assert-NativeSuccess "rustc version check"

    python -m unittest discover -s tests -v
    Assert-NativeSuccess "Diet Rust translator tests"

    python -m dietc examples/atlanta_plant.dc -o build/atlanta_plant.rs
    Assert-NativeSuccess "factory translation"

    python -m dietc examples/ai_native.dc `
        -o build/ai_native.rs `
        --manifest build/ai_native.manifest.json `
        --prompt quality_rule_tests `
        --prompt-output build/quality_rule_tests.prompt.md
    Assert-NativeSuccess "AI-native translation"

    & $RustCompiler --edition 2024 build/atlanta_plant.rs -o build/atlanta_plant.exe
    Assert-NativeSuccess "factory compilation"

    & (Join-Path $ProjectRoot "build\atlanta_plant.exe")
    Assert-NativeSuccess "factory execution"

    & $RustCompiler `
        --edition 2024 `
        --crate-type lib `
        build/ai_native.rs `
        -o build/ai_native.rlib
    Assert-NativeSuccess "AI-native library compilation"

    Write-Host "All local Diet Rust checks passed."
}
finally {
    Pop-Location
}
