"""Built-in profile module registry."""

from . import artlist, pexels, pixabay, storyblocks, adobe_stock, shutterstock, envato_elements, motion_array, vimeo, youtube_cc, generic

BUILTIN_MODULES = (
    artlist,
    pexels,
    pixabay,
    storyblocks,
    adobe_stock,
    shutterstock,
    envato_elements,
    motion_array,
    vimeo,
    youtube_cc,
    generic,
)


def register_builtin_profiles(site_profile_cls):
    for module in BUILTIN_MODULES:
        site_profile_cls.register(module.build(site_profile_cls))


def iter_contracts():
    for module in BUILTIN_MODULES:
        yield module.PROFILE_NAME, module.CONTRACT, module


__all__ = [
    "BUILTIN_MODULES",
    "register_builtin_profiles",
    "iter_contracts",
]
