"""Native Gemini Live audio used only by ultra-light mode."""

import asyncio

import numpy as np
import sounddevice as sd
from google import genai
from google.genai import types

from config import GEMINI_LIVE_MODEL


class GeminiLiveAudio:
    """Captures one push-to-talk turn and plays Gemini's native audio reply."""

    def run_turn(self, seconds=5):
        asyncio.run(self._run_turn(seconds))

    async def _run_turn(self, seconds):
        recording = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="int16")
        sd.wait()
        client = genai.Client()
        config = types.LiveConnectConfig(response_modalities=["AUDIO"])
        audio = types.Blob(data=np.ascontiguousarray(recording).tobytes(), mime_type="audio/pcm;rate=16000")
        output = bytearray()
        async with client.aio.live.connect(model=GEMINI_LIVE_MODEL, config=config) as session:
            await session.send_realtime_input(audio=audio)
            async for response in session.receive():
                content = getattr(response, "server_content", None)
                if content and content.model_turn:
                    for part in content.model_turn.parts:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data:
                            output.extend(inline_data.data)
                if content and content.turn_complete:
                    break
        if output:
            sd.play(np.frombuffer(output, dtype=np.int16), samplerate=24000, blocking=True)
