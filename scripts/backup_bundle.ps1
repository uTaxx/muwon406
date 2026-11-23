# 저장소 전체를 bundle 파일 하나로 백업한다(윈도우 PowerShell).
# 사용: 저장소 폴더에서 .\scripts\backup_bundle.ps1 [-Dest "백업폴더"]
param([string]$Dest = (Join-Path $HOME 'Backups\muwon406'))

$ErrorActionPreference = 'Stop'
$root = git rev-parse --show-toplevel
if (-not $root) { throw 'git 저장소 안에서 실행해야 한다.' }
Set-Location $root

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$file = Join-Path $Dest "muwon406-$stamp.bundle"

git bundle create $file --all
git bundle verify $file
Write-Host "백업 완료: $file"
