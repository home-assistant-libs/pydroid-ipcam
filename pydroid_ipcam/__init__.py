"""PyDroidIPCam API for the Android IP Webcam app."""
import asyncio
import logging
from typing import Any, Awaitable, Dict, List, Optional, Tuple, Union

import aiohttp
from yarl import URL

_LOGGER = logging.getLogger(__name__)

ALLOWED_ORIENTATIONS = ["landscape", "upsidedown", "portrait", "upsidedown_portrait"]


class PyDroidIPCam:
    """The Android device running IP Webcam."""

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        host: str,
        port: int = 8080,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 10,
        ssl: bool = True,
    ):
        """Initialize the data oject."""
        self.websession: aiohttp.ClientSession = websession
        self.status_data = None
        self.sensor_data = None
        self._host: str = host
        self._port: int = port
        self._auth: Optional[aiohttp.BasicAuth] = None
        self._timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
        self._available: bool = True
        self._ssl: bool = ssl

        if username and password:
            self._auth = aiohttp.BasicAuth(username, password=password)

    @property
    def base_url(self) -> str:
        """Return the base URL for endpoints."""
        protocol = "https" if self._ssl else "http"
        return f"{protocol}://{self._host}:{self._port}"

    @property
    def mjpeg_url(self) -> str:
        """Return mjpeg url."""
        return f"{self.base_url}/video"

    @property
    def h264_url(self) -> str:
        """Return h264 url."""
        return f"rtsp://{self._host}:{self._port}/h264_pcm.sdp"

    @property
    def image_url(self) -> str:
        """Return snapshot image URL."""
        return f"{self.base_url}/shot.jpg"

    @property
    def available(self) -> bool:
        """Return True if is available."""
        return self._available

    async def _request(self, path: str) -> Union[bool, Dict[str, Any]]:
        """Make the actual request and return the parsed response."""
        url: str = f"{self.base_url}{path}"
        data = None

        try:
            async with self.websession.get(
                url, auth=self._auth, timeout=self._timeout
            ) as response:
                if response.status == 200:
                    if response.headers["content-type"] == "application/json":
                        data = await response.json()
                    else:
                        data = await response.text().find("Ok") != -1

        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error("Failed to communicate with IP Webcam: %s", error)
            self._available = False
        else:
            self._available = True

        return data

    async def update(self) -> None:
        """Fetch the latest data from IP Webcam."""
        status_data = await self._request("/status.json?show_avail=1")

        if not status_data:
            return

        self.status_data = status_data

        sensor_data = await self._request("/sensors.json")
        if sensor_data:
            self.sensor_data = sensor_data

    @property
    def current_settings(self) -> Dict[str, Any]:
        """Return dict with all config include."""
        settings = {}
        if not self.status_data:
            return settings

        for (key, val) in self.status_data.get("curvals", {}).items():
            try:
                val = float(val)
            except ValueError:
                pass

            if val in ("on", "off"):
                val = val == "on"

            settings[key] = val

        return settings

    @property
    def enabled_sensors(self) -> List[str]:
        """Return the enabled sensors."""
        if self.sensor_data is None:
            return []
        return list(self.sensor_data.keys())

    @property
    def enabled_settings(self) -> List[str]:
        """Return the enabled settings."""
        if self.status_data is None:
            return []
        return list(self.status_data.get("curvals", {}).keys())

    @property
    def available_settings(self) -> Dict[str, List[Any]]:
        """Return dict of lists with all available config settings."""
        available = {}
        if not self.status_data:
            return available

        for (key, val) in self.status_data.get("avail", {}).items():
            available[key] = []
            for subval in val:
                try:
                    subval = float(subval)
                except ValueError:
                    pass

                if val in ("on", "off"):
                    subval = subval == "on"

                available[key].append(subval)

        return available

    def export_sensor(self, sensor) -> Tuple(str, Any):
        """Return (value, unit) from a sensor node."""
        value = None
        unit = None
        try:
            container = self.sensor_data.get(sensor)
            unit = container.get("unit")
            data_point = container.get("data", [[0, [0.0]]])
            if data_point and data_point[-1]:
                value = data_point[-1][-1][0]
        except (ValueError, KeyError, AttributeError):
            pass

        return (value, unit)

    def change_setting(self, key: str, val: Union[str, int, bool]) -> Awaitable[bool]:
        """Change a setting."""
        if isinstance(val, bool):
            payload = "on" if val else "off"
        else:
            payload = val
        return self._request(f"/settings/{key}?set={payload}")

    def torch(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable the torch."""
        path = "/enabletorch" if activate else "/disabletorch"
        return self._request(path)

    def focus(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable camera focus."""
        path = "/focus" if activate else "/nofocus"
        return self._request(path)

    def record(self, record: bool = True, tag: str = None) -> Awaitable[bool]:
        """Enable/disable recording."""
        path = "/startvideo?force=1" if record else "/stopvideo?force=1"
        if record and tag is not None:
            path = f"/startvideo?force=1&tag={URL(tag).raw_path}"
        return self._request(path)

    def set_front_facing_camera(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable the front-facing camera."""
        return self.change_setting("ffc", activate)

    def set_night_vision(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable night vision."""
        return self.change_setting("night_vision", activate)

    def set_overlay(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable the video overlay."""
        return self.change_setting("overlay", activate)

    def set_gps_active(self, activate: bool = True) -> Awaitable[bool]:
        """Enable/disable GPS."""
        return self.change_setting("gps_active", activate)

    def set_quality(self, quality: int = 100) -> Awaitable[bool]:
        """Set the video quality."""
        return self.change_setting("quality", quality)

    def set_motion_detect(self, activate: bool = True) -> Awaitable[bool]:
        """Set motion detection on/off."""
        return self.change_setting("motion_detect", activate)

    def set_orientation(self, orientation: str = "landscape") -> Awaitable[bool]:
        """Set the video orientation."""
        if orientation not in ALLOWED_ORIENTATIONS:
            raise RuntimeError(f"Invalid orientation {orientation}")
        return self.change_setting("orientation", orientation)

    def set_zoom(self, zoom: int) -> Awaitable[bool]:
        """Set the zoom level."""
        return self._request(f"/settings/ptz?zoom={zoom}")

    def set_scenemode(self, scenemode: str = "auto") -> Awaitable[bool]:
        """Set the video scene mode."""
        if scenemode not in self.available_settings["scenemode"]:
            raise RuntimeError(f"Invalid scene mode {scenemode}")
        return self.change_setting("scenemode", scenemode)
