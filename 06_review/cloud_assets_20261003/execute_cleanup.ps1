# 用途：按已审计清单迁移最新源并删除缓存；所有路径必须解析到本项目内。
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cleanup_plan.json') -Raw | ConvertFrom-Json
if ($plan.root -ne $projectRoot) { throw '清单根目录与当前项目不匹配' }

function Get-ProjectPath([string]$Relative) {
    # 输入项目相对路径；返回经过边界与链接检查的绝对路径，越界即停止。
    $target = [IO.Path]::GetFullPath((Join-Path $projectRoot $Relative))
    if (-not $target.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "清单路径越界：$Relative"
    }
    $cursor = $target
    while ($cursor.Length -gt $projectRoot.Length) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "禁止沿链接清理：$Relative"
            }
        }
        $cursor = Split-Path -Parent $cursor
    }
    return $target
}

# 先完整检查文件尺寸/时间及目标空闲；发现用户新保存时不执行任何删除。
foreach ($row in $plan.deletions) {
    $path = Get-ProjectPath $row.path
    $item = Get-Item -LiteralPath $path
    if ($item.Length -ne $row.bytes -or $item.LastWriteTimeUtc.Ticks -ne ([datetime]$row.modified).ToUniversalTime().Ticks) {
        throw "文件在检查后已改变：$($row.path)"
    }
}
foreach ($row in $plan.moves) {
    $source = Get-ProjectPath $row.source
    $destination = Get-ProjectPath $row.destination
    if (-not (Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $destination)) {
        throw "迁移源缺失或目标已存在：$($row.source)"
    }
}
if (-not $Apply) { Write-Output "验证通过：迁移 $($plan.moves.Count)，删除 $($plan.delete_files)；传入 -Apply 执行。"; return }

$moved = @()
foreach ($row in $plan.moves) {
    $source = Get-ProjectPath $row.source
    $destination = Get-ProjectPath $row.destination
    $digest = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Move-Item -LiteralPath $source -Destination $destination
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest) {
        throw "迁移哈希不一致：$($row.destination)"
    }
    $moved += [pscustomobject]@{source=$row.source; destination=$row.destination; sha256=$digest}
}
$moved | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'moved.json') -Encoding utf8

$deleted = @()
foreach ($row in $plan.deletions) {
    $path = Get-ProjectPath $row.path
    Remove-Item -LiteralPath $path -Force
    if (Test-Path -LiteralPath $path) { throw "未成功删除：$($row.path)" }
    $deleted += $row
}
$deleted | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deleted.json') -Encoding utf8
# 删除空缓存目录；已先验证每个实际路径，保留缓存根供后续工具使用。
$cacheRoot = Get-ProjectPath '07_pipeline/cache'
Get-ChildItem -LiteralPath $cacheRoot -Directory -Recurse | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object {
    $checked = Get-ProjectPath $_.FullName.Substring($projectRoot.Length + 1)
    if (-not (Get-ChildItem -LiteralPath $checked -Force | Select-Object -First 1)) {
        Remove-Item -LiteralPath $checked -Force
    }
}
Write-Output "清理完成：删除 $($deleted.Count) 个文件；迁移 $($moved.Count) 项并验证 SHA256。"
