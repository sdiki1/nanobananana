import asyncio
from typing import Optional


class NanoBananaClient:
    async def generate_text2img(self, prompt: str, model: str) -> str:
        await asyncio.sleep(1)
        seed = abs(hash(f"{prompt}:{model}")) % 10000
        return f"https://picsum.photos/seed/{seed}/768/768"

    async def generate_img2img(self, file_id: str, preset: str) -> str:
        await asyncio.sleep(1)
        seed = abs(hash(f"{file_id}:{preset}")) % 10000
        return f"https://picsum.photos/seed/{seed}/768/768"

    async def animate_photo(self, file_id: str, preset: Optional[str] = None) -> str:
        await asyncio.sleep(1)
        return "https://sample-videos.com/video321/mp4/240/big_buck_bunny_240p_1mb.mp4"
