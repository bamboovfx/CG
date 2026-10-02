# 按已经审计的逐文件清单清理；限于 Shot_Test，先验证全部路径、源哈希和文件修改时间。
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$cgRoot = (Resolve-Path -LiteralPath 'D:/00_projects/10_CG/Shot_Test').Path.TrimEnd('\')
$cgPrefix = $cgRoot + '\'
$cgPlanPath = Join-Path $cgRoot '06_review/cleanup_20260927/manifest.json'
$cgReceiptPath = Join-Path $cgRoot '06_review/cleanup_20260927/deleted.json'
if (Test-Path -LiteralPath $cgReceiptPath) { throw '清理已执行；禁止重复使用旧清单。' }
$cgPlan = Get-Content -LiteralPath $cgPlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([IO.Path]::GetFullPath($cgPlan.root).TrimEnd('\') -ne $cgRoot) { throw '清单根目录不匹配。' }

function Confirm-CleanupPath {
    # 输入绝对路径；检查目标位于根目录内，且所有祖先都不是链接或联接点；返回真实路径。
    param([string]$Candidate)
    $absolute = [IO.Path]::GetFullPath($Candidate)
    if (-not $absolute.StartsWith($cgPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "越界路径：$absolute" }
    $item = Get-Item -LiteralPath $absolute -Force
    $cursor = $item
    while ($null -ne $cursor -and $cursor.FullName -ne $cgRoot) {
        if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "链接路径：$($cursor.FullName)" }
        $cursor = if ($cursor.PSIsContainer) { $cursor.Parent } else { $cursor.Directory }
    }
    return $item
}

# 源工程在清理准备期间若被保存过，停止并重新核查依赖。
foreach ($source in $cgPlan.protected_sources) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $source.path).Hash.ToLowerInvariant()
    if ($actual -ne $source.sha256) { throw "源工程已变化，需要重新核查：$($source.path)" }
}
$cgTargets = @()
foreach ($entry in $cgPlan.items) {
    $target = Confirm-CleanupPath (Join-Path $cgRoot $entry.path)
    if ($target.PSIsContainer) { throw "文件清单出现目录：$($entry.path)" }
    if ($target.Length -ne $entry.bytes -or $target.LastWriteTimeUtc.Ticks -ne [long]$entry.mtime_ticks) {
        throw "清单生成后文件已变化：$($entry.path)"
    }
    if ($cgPlan.protected_resources -contains $target.FullName) { throw "目标属于保护资源：$($entry.path)" }
    $cgTargets += [pscustomobject]@{ Path = $target.FullName; Entry = $entry }
}
if (-not $Apply) {
    @{ validated_files = $cgTargets.Count; bytes = $cgPlan.planned_bytes; applied = $false } | ConvertTo-Json
    exit 0
}

$cgDeleted = [Collections.Generic.List[object]]::new()
try {
    foreach ($target in $cgTargets) {
        # 每个文件删除前再检查，清理过程中新增或修改的内容不纳入本批。
        $current = Confirm-CleanupPath $target.Path
        if ($current.Length -ne $target.Entry.bytes -or $current.LastWriteTimeUtc.Ticks -ne [long]$target.Entry.mtime_ticks) {
            throw "执行中检测到变化：$($target.Entry.path)"
        }
        Remove-Item -LiteralPath $current.FullName -Force
        $cgDeleted.Add($target.Entry)
    }
    # 只移除已经为空的子目录，保留项目顶层职责目录；从不递归删除未知内容。
    $cgDirectories = Get-ChildItem -LiteralPath $cgRoot -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending
    foreach ($directory in $cgDirectories) {
        if ($directory.Parent.FullName -eq $cgRoot) { continue }
        $checked = Confirm-CleanupPath $directory.FullName
        if ([IO.Directory]::GetFileSystemEntries($checked.FullName).Length -eq 0) {
            Remove-Item -LiteralPath $checked.FullName -Force
        }
    }
} finally {
    # 即使遇到并发修改而停止，也记录已经删掉的项目，不宣称整批成功。
    @{ finished_at = (Get-Date).ToString('o'); planned_count = $cgTargets.Count;
       deleted_count = $cgDeleted.Count; deleted_bytes = ($cgDeleted | Measure-Object -Property bytes -Sum).Sum;
       complete = ($cgDeleted.Count -eq $cgTargets.Count); items = $cgDeleted } |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $cgReceiptPath -Encoding UTF8
}
Get-Content -LiteralPath $cgReceiptPath -Raw | ConvertFrom-Json |
    Select-Object complete,deleted_count,deleted_bytes | ConvertTo-Json
