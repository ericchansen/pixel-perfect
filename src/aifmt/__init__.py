"""aifmt: Make visual text content just work."""

__version__ = "0.1.0"

from aifmt.lib.visual_width import (
    RenderProfile,
    get_profile,
    list_profiles,
    register_profile,
    visual_width,
    visual_width_precise,
)

__all__ = [
    "RenderProfile",
    "get_profile",
    "list_profiles",
    "register_profile",
    "visual_width",
    "visual_width_precise",
]
