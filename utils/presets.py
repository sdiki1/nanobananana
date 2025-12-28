from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Preset:
    key: str
    title: str
    prompt: str
    preview_url: str


_PRESETS: List[Preset] = [
    Preset(
        key="cinema",
        title="Кино-портрет",
        prompt="Киношный портрет, мягкий свет, 35mm, драматичное настроение",
        preview_url="https://picsum.photos/seed/cinema/512/512",
    ),
    Preset(
        key="anime",
        title="Аниме",
        prompt="Аниме-стиль, чистые линии, мягкие тени, яркие цвета",
        preview_url="https://picsum.photos/seed/anime/512/512",
    ),
    Preset(
        key="cyberpunk",
        title="Киберпанк",
        prompt="Киберпанк, неон, ночной город, отражения, контраст",
        preview_url="https://picsum.photos/seed/cyberpunk/512/512",
    ),
    Preset(
        key="vintage",
        title="Старинное фото",
        prompt="Старинная фотография, зерно, теплые тона, ретро",
        preview_url="https://picsum.photos/seed/vintage/512/512",
    ),
    Preset(
        key="pixel",
        title="Пиксель-арт",
        prompt="Пиксель-арт, 16-bit, четкие пиксели, ретро-игра",
        preview_url="https://picsum.photos/seed/pixel/512/512",
    ),
    Preset(
        key="watercolor",
        title="Акварель",
        prompt="Акварельная иллюстрация, мягкие переходы, легкие брызги",
        preview_url="https://picsum.photos/seed/watercolor/512/512",
    ),
]

PRESET_MAP: Dict[str, Preset] = {preset.key: preset for preset in _PRESETS}


def list_presets() -> List[Preset]:
    return list(_PRESETS)


def get_preset(key: str) -> Optional[Preset]:
    return PRESET_MAP.get(key)
