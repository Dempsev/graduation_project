$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root 'preprocess\build_snake_based_archetype_expansion_pilot_v1.py'

python $script
