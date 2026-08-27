param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$SourceIso,
    [Parameter(Mandatory = $false, Position = 1)]
    [string]$DestinationIso
)

$ErrorActionPreference = "Stop"
$ExpectedGameId = "GFTE01"
$CreatedDestination = $false

function Get-BytesHash([byte[]]$Bytes) {
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString(
            $Hasher.ComputeHash($Bytes)
        )).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $Hasher.Dispose()
    }
}

try {
    $PatchFiles = @(
        Get-ChildItem -LiteralPath $PSScriptRoot -File -Filter "*.mgttpatch"
    )
    if ($PatchFiles.Count -ne 1) {
        throw "Expected exactly one .mgttpatch beside this script; found $($PatchFiles.Count)."
    }
    $PatchPath = $PatchFiles[0].FullName
    $SourceIso = [System.IO.Path]::GetFullPath($SourceIso)
    if (-not (Test-Path -LiteralPath $SourceIso -PathType Leaf)) {
        throw "Source ISO does not exist: $SourceIso"
    }
    if (-not $DestinationIso) {
        $Directory = [System.IO.Path]::GetDirectoryName($SourceIso)
        $Name = [System.IO.Path]::GetFileNameWithoutExtension($SourceIso)
        $DestinationIso = Join-Path $Directory "$Name-Archipelago.iso"
    }
    $DestinationIso = [System.IO.Path]::GetFullPath($DestinationIso)
    if ($SourceIso -eq $DestinationIso) {
        throw "Refusing to overwrite the source ISO."
    }
    if (Test-Path -LiteralPath $DestinationIso) {
        throw "Destination already exists: $DestinationIso"
    }
    $DestinationDirectory = [System.IO.Path]::GetDirectoryName($DestinationIso)
    if (-not (Test-Path -LiteralPath $DestinationDirectory -PathType Container)) {
        [void][System.IO.Directory]::CreateDirectory($DestinationDirectory)
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Archive = [System.IO.Compression.ZipFile]::OpenRead($PatchPath)
    try {
        $ManifestEntry = $Archive.GetEntry("manifest.json")
        if (-not $ManifestEntry) {
            throw "Patch manifest is missing."
        }
        $Reader = New-Object System.IO.StreamReader($ManifestEntry.Open())
        try {
            $Manifest = $Reader.ReadToEnd() | ConvertFrom-Json
        }
        finally {
            $Reader.Dispose()
        }
        if ($Manifest.format -ne "MGTT-SPARSE-PATCH-1") {
            throw "Unsupported MGTT patch format."
        }

        $SourceInfo = Get-Item -LiteralPath $SourceIso
        if ($SourceInfo.Length -ne [int64]$Manifest.source_size) {
            throw "Source ISO size does not match GFTE01."
        }
        $GameIdBytes = New-Object byte[] 6
        $GameIdStream = [System.IO.File]::OpenRead($SourceIso)
        try {
            [void]$GameIdStream.Read($GameIdBytes, 0, 6)
        }
        finally {
            $GameIdStream.Dispose()
        }
        $GameId = [System.Text.Encoding]::ASCII.GetString($GameIdBytes)
        if ($GameId -ne $ExpectedGameId) {
            throw "Source is '$GameId'; expected '$ExpectedGameId'."
        }
        $SourceHash = (
            Get-FileHash -LiteralPath $SourceIso -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        if ($SourceHash -ne $Manifest.source_sha256) {
            throw "Source ISO SHA-256 does not match the supported clean dump."
        }

        $CreatedDestination = $true
        Copy-Item -LiteralPath $SourceIso -Destination $DestinationIso
        $DestinationItem = Get-Item -LiteralPath $DestinationIso
        if ($DestinationItem.IsReadOnly) {
            $DestinationItem.IsReadOnly = $false
        }
        $Output = [System.IO.File]::Open(
            $DestinationIso,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        try {
            foreach ($Chunk in $Manifest.chunks) {
                $Offset = [int64]$Chunk.offset
                $Size = [int]$Chunk.size
                $Before = New-Object byte[] $Size
                [void]$Output.Seek($Offset, [System.IO.SeekOrigin]::Begin)
                if ($Output.Read($Before, 0, $Size) -ne $Size) {
                    throw "Short source read at 0x$($Offset.ToString('X'))."
                }
                if ((Get-BytesHash $Before) -ne $Chunk.source_sha256) {
                    throw "Source chunk mismatch at 0x$($Offset.ToString('X'))."
                }

                $ChunkEntry = $Archive.GetEntry([string]$Chunk.member)
                if (-not $ChunkEntry) {
                    throw "Patch chunk is missing: $($Chunk.member)"
                }
                $ChunkStream = $ChunkEntry.Open()
                $Buffer = New-Object System.IO.MemoryStream
                try {
                    $ChunkStream.CopyTo($Buffer)
                    $After = $Buffer.ToArray()
                }
                finally {
                    $ChunkStream.Dispose()
                    $Buffer.Dispose()
                }
                if (
                    $After.Length -ne $Size -or
                    (Get-BytesHash $After) -ne $Chunk.target_sha256
                ) {
                    throw "Patch chunk is corrupt: $($Chunk.member)"
                }
                [void]$Output.Seek($Offset, [System.IO.SeekOrigin]::Begin)
                $Output.Write($After, 0, $After.Length)
            }
        }
        finally {
            $Output.Dispose()
        }
    }
    finally {
        $Archive.Dispose()
    }

    $ResultHash = (
        Get-FileHash -LiteralPath $DestinationIso -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    if ($ResultHash -ne $Manifest.target_sha256) {
        throw "Patched ISO failed final SHA-256 verification."
    }
    Write-Host "Created: $DestinationIso"
    Write-Host "SHA-256: $ResultHash"
}
catch {
    if ($CreatedDestination -and (Test-Path -LiteralPath $DestinationIso)) {
        Remove-Item -LiteralPath $DestinationIso -Force
    }
    Write-Error $_
    exit 1
}
