"""取得CC0锈蚀参考及原生8K通道，保留API校验和与来源许可。"""
import json
from concurrent.futures import ThreadPoolExecutor
import fetch_wood_detail_sources as source


def main():
    """读取三份公开纹理资料，下载研究色图与选定锈蚀8K源，返回清单。"""
    source.DEST = source.ROOT / '02_assets/textures/external/polyhaven_chair_metal'
    source.DEST.mkdir(parents=True, exist_ok=True)
    jobs = []
    for asset in ['rusty_metal', 'rust_coarse_01', 'rusty_painted_metal']:
        files = source.request_json('https://api.polyhaven.com/files/' + asset)
        (source.DEST / (asset + '_files.json')).write_text(json.dumps(files, indent=2), encoding='utf-8')
        jobs.append((asset, 'Diffuse', '1k', 'jpg', files['Diffuse']['1k']['jpg']))
        if asset == 'rust_coarse_01':
            for channel in ['Diffuse', 'Rough', 'Displacement']:
                jobs.append((asset, channel, '8k', 'jpg', files[channel]['8k']['jpg']))
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(source.fetch, jobs))
    (source.DEST / 'manifest.json').write_text(json.dumps({'sources': records,
        'use': 'Rust microcolour and high-pass relief only; chair damage placement authored separately'},
        ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
