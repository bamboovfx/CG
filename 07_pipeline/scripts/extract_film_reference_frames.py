"""从作者公开 1080p 视频流按精确时间提取 PNG；保留编码黑边，不做锐化增细节。"""
from pathlib import Path
import subprocess
import json
import hashlib
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[2]
video=ROOT/'01_preproduction/references/video/drop_official_1080p.mp4'
out=video.parent/'frames'
out.mkdir(exist_ok=True)
records=[]
for sec in [154,156,158,160,162,164,166,168]:
    p=out/f'drop_{sec:03d}s.png'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-ss',str(sec),'-i',str(video),'-frames:v','1','-y',str(p)],check=True)
    records.append({'timestamp_seconds':sec,'timecode_24fps':f'00:02:{sec-120:02d}:00',
                    'path':str(p.relative_to(ROOT)).replace('\\','/'),'resolution':[1920,1080]})
manifest={'title':'dro:p','creator':'Tasuku Nakagawa','author_page':'https://vimeo.com/394614203',
          'official_public_video':'https://www.youtube.com/watch?v=czgCk8bcTqE',
          'stream':'public video-only format 137, H.264, 1920x1080, 24 fps; not an original production master',
          'path':str(video.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
          'frame_processing':'lossless PNG extraction from compressed source; encoded letterboxing retained; no sharpening/upscale',
          'frames':records}
(video.parent/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('EXACT_FILM_FRAMES_READY')
