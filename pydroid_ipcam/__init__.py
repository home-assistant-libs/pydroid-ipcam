"""PyDroidIPCam API for the Android IP Webcam app."""
import asyncio
from typing import Any, Dict, List, Optional, Union, cast

import aiohttp
from yarl import URL

from .exceptions import CannotConnect, PyDroidIPCamException, Unauthorized

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
        """Initialize the data object."""
        self.websession: aiohttp.ClientSession = websession
        self.status_data: Dict[str, Any] = {}
        self.sensor_data: Dict[str, Dict[str, Any]] = {}
        self._host: str = host
        self._port: int = port
        self._auth: Optional[aiohttp.BasicAuth] = None
        self._timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
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

    async def _request(self, path: str) -> aiohttp.ClientResponse:
        """Make the actual request and return the parsed response."""
        url: str = f"{self.base_url}{path}"

        try:
            response = await self.websession.get(
                url, auth=self._auth, timeout=self._timeout, raise_for_status=True
            )

        except aiohttp.ClientResponseError as error:
            if error.status == 401:
                raise Unauthorized("Incorrect username or password") from error
            raise PyDroidIPCamException(
                f"code: {error.code}, error: {error.message}"
            ) from error
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            raise CannotConnect(error) from error

        return response

    async def update(self) -> None:
        """Fetch the latest data from IP Webcam."""
        response = await self._request("/status.json?show_avail=1")
        self.status_data = cast(Dict[str, Any], await response.json())

        response = await self._request("/sensors.json")
        self.sensor_data = cast(Dict[str, Any], await response.json())

    @property
    def current_settings(self) -> Dict[str, Any]:
        """Return dict with all config included."""
        settings: Dict[str, Any] = {}

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
        return list(self.sensor_data)

    @property
    def enabled_settings(self) -> List[str]:
        """Return the enabled settings."""
        return list(self.status_data.get("curvals", {}))

    @property
    def available_settings(self) -> Dict[str, List[Any]]:
        """Return dict of lists with all available config settings."""
        available: Dict[str, List[Any]] = {}

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

    def get_sensor_value(self, sensor: str) -> Union[str, int, float, None]:
        """Return the value from a sensor node."""
        if sensor_info := self.sensor_data.get(sensor):
            if "data" in sensor_info:
                return cast(Union[str, int, float], sensor_info["data"][-1][-1][0])
        return None

    def get_sensor_unit(self, sensor: str) -> Optional[str]:
        """Return the unit from a sensor node."""
        if sensor_info := self.sensor_data.get(sensor):
            return cast(Optional[str], sensor_info.get("unit"))
        return None

    async def change_setting(self, key: str, val: Union[str, int, bool]) -> bool:
        """Change a setting."""
        payload: Union[str, int, None] = None
        if isinstance(val, bool):
            payload = "on" if val else "off"
        else:
            payload = val
        response = await self._request(f"/settings/{key}?set={payload}")
        return "Ok" in (await response.text())

    async def torch(self, activate: bool = True) -> bool:
        """Enable/disable the torch."""
        path = "/enabletorch" if activate else "/disabletorch"
        response = await self._request(path)
        return "Ok" in (await response.text())

    async def focus(self, activate: bool = True) -> bool:
        """Enable/disable camera focus."""
        path = "/focus" if activate else "/nofocus"
        response = await self._request(path)
        return "Ok" in (await response.text())

    async def record(self, record: bool = True, tag: Optional[str] = None) -> bool:
        """Enable/disable recording."""
        path = "/startvideo?force=1" if record else "/stopvideo?force=1"
        if record and tag is not None:
            path = f"/startvideo?force=1&tag={URL(tag).raw_path}"
        response = await self._request(path)
        return "Ok" in (await response.text())

    async def set_front_facing_camera(self, activate: bool = True) -> bool:
        """Enable/disable the front-facing camera."""
        return await self.change_setting("ffc", activate)

    async def set_night_vision(self, activate: bool = True) -> bool:
        """Enable/disable night vision."""
        return await self.change_setting("night_vision", activate)

    async def set_overlay(self, activate: bool = True) -> bool:
        """Enable/disable the video overlay."""
        return await self.change_setting("overlay", activate)

    async def set_gps_active(self, activate: bool = True) -> bool:
        """Enable/disable GPS."""
        return await self.change_setting("gps_active", activate)

    async def set_quality(self, quality: int = 100) -> bool:
        """Set the video quality."""
        return await self.change_setting("quality", quality)

    async def set_motion_detect(self, activate: bool = True) -> bool:
        """Set motion detection on/off."""
        return await self.change_setting("motion_detect", activate)

    async def set_orientation(self, orientation: str = "landscape") -> bool:
        """Set the video orientation."""
        if orientation not in ALLOWED_ORIENTATIONS:
            raise RuntimeError(f"Invalid orientation {orientation}")
        return await self.change_setting("orientation", orientation)

    async def set_zoom(self, zoom: int) -> bool:
        """Set the zoom level."""
        response = await self._request(f"/settings/ptz?zoom={zoom}")
        return "Ok" in (await response.text())

    async def set_scenemode(self, scenemode: str = "auto") -> bool:
        """Set the video scene mode."""
        if scenemode not in self.available_settings["scenemode"]:
            raise RuntimeError(f"Invalid scene mode {scenemode}")
        return await self.change_setting("scenemode", scenemode)
