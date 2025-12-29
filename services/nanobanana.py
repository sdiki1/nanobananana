import asyncio
import mimetypes
import time
from typing import Optional, Tuple

from google import genai
from google.genai import types

from config import settings
from utils.presets import get_preset


class NanoBananaClient:
    _veo_model = "veo-2.0-generate-001"

    def __init__(
        self,
        api_key: Optional[str] = None,
        nano_model: Optional[str] = None,
        pro_model: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or settings.gemini_api_key
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is required for NanoBanana generation.")
        self._nano_model = nano_model or settings.gemini_nano_model
        self._pro_model = pro_model or settings.gemini_pro_model
        self._client = genai.Client(api_key=self._api_key)

    async def generate_text2img(self, prompt: str, model: str) -> bytes:
        return await asyncio.to_thread(self._generate_image, prompt, model, None)

    async def generate_img2img(self, bot, file_id: str, preset: str, model: str) -> bytes:
        image_bytes, mime_type = await self._download_file(bot, file_id)
        preset_obj = get_preset(preset)
        prompt = preset_obj.prompt if preset_obj else "Transform the image."
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        return await asyncio.to_thread(self._generate_image, prompt, model, image_part)

    async def animate_photo(self, bot, file_id: str, preset: Optional[str] = None) -> bytes:
        image_bytes, mime_type = await self._download_file(bot, file_id)
        prompt = (
            preset
            or "generate a video where these people take glass bottles of beer, clink them and drink, laughing and discussing something in the process."
        )
        return await asyncio.to_thread(self._generate_video_from_image, image_bytes, mime_type, prompt)

    def _generate_video_from_image(self, image_bytes: bytes, mime_type: str, prompt: str) -> bytes:
        image = types.Image(image_bytes=image_bytes, mime_type=mime_type)
        config = types.GenerateVideosConfig()
        operation = self._client.models.generate_videos(
            model=self._veo_model,
            prompt=prompt,
            image=image,
            config=config,
        )
        while not operation.done:
            time.sleep(3)
            operation = self._client.operations.get(operation)
        if operation.error:
            raise RuntimeError(f"Video generation failed: {operation.error.message}")
        response = operation.response
        if not response or not response.generated_videos:
            print(response)
            raise RuntimeError("No video returned from VEO.")
        video_resource = response.generated_videos[0].video
        if not video_resource:
            raise RuntimeError("Missing video payload from VEO.")
        video_bytes = self._client.files.download(file=video_resource)
        if not video_bytes:
            raise RuntimeError("Empty video bytes received from VEO.")
        return video_bytes

    def _generate_image(self, prompt: str, model: str, image_part: Optional[types.Part]) -> bytes:
        resolved_model = self._resolve_model(model)
        parts = [types.Part.from_text(text=prompt)]
        if image_part:
            parts.append(image_part)
        contents = [
            types.Content(
                role="user",
                parts=parts,
            )
        ]
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )
        response = self._client.models.generate_content(
            model=resolved_model,
            contents=contents,
            config=config,
        )
        return self._extract_image_bytes(response)

    def _resolve_model(self, model: str) -> str:
        if model == "pro":
            return self._pro_model
        return self._nano_model

    def _extract_image_bytes(self, response) -> bytes:
        for candidate in response.candidates or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in content.parts or []:
                inline_data = getattr(part, "inline_data", None)
                data = getattr(inline_data, "data", None) if inline_data else None
                if data:
                    return data
        raise RuntimeError("No image data returned from Gemini.")

    async def _download_file(self, bot, file_id: str) -> Tuple[bytes, str]:
        file = await bot.get_file(file_id)
        file_obj = await bot.download_file(file.file_path)
        if hasattr(file_obj, "read"):
            data = file_obj.read()
        else:
            data = file_obj
        mime_type, _ = mimetypes.guess_type(file.file_path or "")
        if not mime_type:
            mime_type = "image/jpeg"
        return data, mime_type
