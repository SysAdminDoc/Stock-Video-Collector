"""Official API connector registry."""

from .adobe_stock import AdobeStockConnector
from .base import (
    DEFAULT_PER_PAGE,
    MAX_PAGE_LIMIT,
    ApiConnectorError,
    ApiPage,
    ApiRequest,
    ApiResponse,
    query_from_config,
)
from .pexels import PexelsConnector
from .pixabay import PixabayConnector
from .vimeo import VimeoConnector


CONNECTOR_CLASSES = (
    PexelsConnector,
    PixabayConnector,
    VimeoConnector,
    AdobeStockConnector,
)


def connector_for_profile(profile_name, cfg):
    for cls in CONNECTOR_CLASSES:
        if cls.profile_name == profile_name:
            return cls(cfg)
    return None


def configured_connectors_for_profiles(profile_names, cfg):
    connectors = []
    for profile_name in profile_names:
        connector = connector_for_profile(profile_name, cfg)
        if connector and connector.is_configured():
            connectors.append(connector)
    return connectors


def connector_profile_names():
    return [cls.profile_name for cls in CONNECTOR_CLASSES]
