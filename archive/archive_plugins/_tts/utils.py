import base64
import mimetypes
import tempfile

from pathlib import Path

import av
import pilk


def to_pcm(in_path: Path) -> Path:
    out_path = Path(tempfile.mktemp(suffix='.pcm'))
    with av.open(str(in_path)) as in_container:
        in_stream = in_container.streams.audio[0]
        sample_rate = 24000
        with av.open(str(out_path), 'w', 's16le') as out_container:
            out_stream = out_container.add_stream(
                'pcm_s16le',
                rate=sample_rate,
                layout='mono'
            )
            try:
                for frame in in_container.decode(in_stream):
                    frame.pts = None
                    for packet in out_stream.encode(frame):
                        out_container.mux(packet)
            except:
                pass
    return out_path


def convert_to_silk(media_path: Path, silk_path: Path = None) -> Path:
    pcm_path = to_pcm(media_path)
    if not silk_path:
        silk_path = tempfile.mktemp(suffix='.silk')
    pilk.encode(str(pcm_path), str(silk_path), pcm_rate=24000, tencent=True)
    return Path(silk_path)


def wav2silk_base64(wav_path: Path) -> str:
    silk_path = convert_to_silk(wav_path)
    # data = encode_url_or_file_to_base64(silk_path)
    with open(silk_path, "rb") as file:
        encoded_string = base64.b64encode(file.read())
        base64_str = str(encoded_string, "utf-8")
        filename = str(silk_path)
        if filename.endswith(".vtt"):
            return "text/vtt"
        mimetype = mimetypes.guess_type(filename)[0]
        if mimetype is not None:
            mimetype = mimetype.replace("x-wav", "wav").replace("x-flac", "flac")
        return (
            "data:"
            + (mimetype if mimetype is not None else "")
            + ";base64,"
            + base64_str
        )


def wav2amr(wav_path: Path, amr_path: Path = None) -> Path:
    if not amr_path:
        amr_path = tempfile.mktemp(suffix=".amr")
    convert_to_silk(wav_path, silk_path=amr_path)
    return Path(amr_path)


if __name__ == '__main__':
    # print(convert_to_silk(Path("d:/audio.wav")))
    print(wav2amr(Path("/Users/linyuchen/Downloads/1.wav"), Path("/Users/linyuchen/Downloads/1.amr")))
