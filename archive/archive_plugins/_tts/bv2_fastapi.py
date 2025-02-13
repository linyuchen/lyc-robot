import tempfile
import traceback
from pathlib import Path

import requests


class BV2Fastapi:

    def __init__(self, api_host="http://localhost:5001"):
        self.api_host = api_host
        self.models_info = {}
        self.default_params = {
            "sdp_ratio": 0.2,
            "noise": 0.2,
            "noisew": 0.9,
            "length": 1,
            "language": "AUTO",
            "auto_translate": False
        }

    def get_models(self) -> list[str]:
        try:
            resp = requests.get(self.api_host + "/models/info")
        except:
            traceback.print_exc()
            return []
        models_info = resp.json()
        self.models_info = models_info
        speakers = []
        for spk_list in [model["spk2id"] for _, model in models_info.items()]:
            speakers.extend(spk_list)

        return list(set(speakers))

    def tts(self, text, speaker) -> Path:
        if not self.models_info:
            self.get_models()
        model_id = list(self.models_info.keys())[0]
        speaker_name = list(list(self.models_info.values())[0]["spk2id"].keys())[0]
        for _model_id, model_info in self.models_info.items():
            if speaker in model_info["spk2id"]:
                speaker_name = speaker
                model_id = _model_id
                break

        data = {
            "model_id": model_id,
            "speaker_name": speaker_name,
            **self.default_params
        }
        wav_data = requests.post(self.api_host + "/voice", params=data, data={"text": text}).content
        wav_path = Path(tempfile.mktemp(suffix=".wav"))
        wav_path.write_bytes(wav_data)
        return wav_path


if __name__ == '__main__':
    bv2 = BV2Fastapi()
    print(bv2.get_models())
    print(bv2.tts("你好,hello,こんにちは", "丁真"))


