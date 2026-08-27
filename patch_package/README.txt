Mario Golf: Toadstool Tour Archipelago ISO patch
================================================

Supported source:
  Game ID: GFTE01
  Region: USA
  Size: 1,459,978,240 bytes
  SHA-256: 08a1f0c1f7336418fa814a19907f2094d81062d5e7636ab096a43c41132410f0

Windows 10/11
-------------

1. Extract this ZIP.
2. Open PowerShell in the extracted folder.
3. Run:

   powershell -ExecutionPolicy Bypass -File .\Apply-MGTTPatch.ps1 "C:\path\to\Mario Golf - Toadstool Tour (USA).iso"

The script creates a new file beside the source named
"Mario Golf - Toadstool Tour (USA)-Archipelago.iso". It refuses to overwrite
the source or an existing destination.

Python alternative (Windows, macOS, or Linux)
----------------------------------------------

Run:

  python mgtt_patch.py apply "/path/to/clean.iso" "/path/to/the-included.mgttpatch" "/path/to/MGTT-Archipelago.iso"

Both applicators verify the clean ISO, every patch chunk, and the completed
output against the hashes embedded in the included patch manifest. Both refuse
to overwrite the source or an existing destination. The PowerShell applicator
requires exactly one `.mgttpatch` file beside the script, preventing an old
patch from being selected accidentally.

This archive contains only a sparse binary patch and patching tools. It does
not contain or redistribute the game disc image.
