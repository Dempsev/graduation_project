$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root 'preprocess\build_bilobe_only_contact_aware_snake_pilot_v1.py'

python $script
