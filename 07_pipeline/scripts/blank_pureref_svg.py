"""候选实验：隐藏 PureRef 2.1 中嵌入的自制 SVG 文字与底色。

此脚本只写新的候选文件，不覆盖用户保存的场景；正式变更需重开校验。
输入文件以可见的原始 SVG 字节存储，前置 32 字节为内容 MD5。
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re


def blank_svg_bytes(raw: bytes) -> tuple[bytes, int, list[int]]:
    """输入 PureRef 字节，等长替换完整 SVG 并修复校验码；残片只报告。"""
    checksum_offset = 40
    content_offset = 104
    stored = raw[checksum_offset:content_offset].decode('utf-16-be')
    if stored != hashlib.md5(raw[content_offset:]).hexdigest():
        raise ValueError('PureRef 全局校验码不匹配，不编辑该文件')
    result = bytearray(raw)
    matches = list(re.finditer(rb'<svg\b.*?</svg>', raw, re.S))
    patched = 0
    fragments = []
    for match in matches:
        original = match.group()
        md5 = hashlib.md5(original).hexdigest().encode('ascii')
        hash_start = match.start() - 32
        if raw[hash_start:match.start()] != md5:
            # PureRef 保存时可留下不完整的旧资源残片；它们不是可呈现的完整SVG。
            fragments.append(match.start())
            continue
        if b'pureref_board/' not in raw[max(0, match.start()-180):match.start()]:
            raise ValueError(f'发现并非本项目生成的 SVG，停止在偏移 {match.start()}')
        # 属性长保持不变，使场景的内部偏移继续有效。
        replacement = re.sub(rb'fill="#[0-9A-Fa-f]{6}"', b'fill="none   "', original)
        replacement = re.sub(rb'(<text\b[^>]*>)(.*?)(</text>)',
                             lambda m: m.group(1)+b' '*len(m.group(2))+m.group(3),
                             replacement, flags=re.S)
        if len(replacement) != len(original):
            raise ValueError('替换必须等长')
        result[hash_start:match.start()] = hashlib.md5(replacement).hexdigest().encode('ascii')
        result[match.start():match.end()] = replacement
        patched += 1
    result[checksum_offset:content_offset] = hashlib.md5(result[content_offset:]).hexdigest().encode('utf-16-be')
    return bytes(result), patched, fragments


def main():
    """读取源场景，执行等长补丁，输出独立候选文件供 PureRef 验证。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    if args.candidate.exists():
        raise FileExistsError(args.candidate)
    raw = args.source.read_bytes()
    fixed, count, fragments = blank_svg_bytes(raw)
    args.candidate.write_bytes(fixed)
    print(f'Patched SVGs: {count}; pre-existing incomplete fragments: {fragments}; '
          f'size: {len(raw)} -> {len(fixed)}; source_SHA256={hashlib.sha256(raw).hexdigest()}')


if __name__ == '__main__':
    main()
