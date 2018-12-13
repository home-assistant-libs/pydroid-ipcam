"""PyDroidIPCam api for android ipcam."""
import asyncio
import logging

import aiohttp
from yarl import URL

_LOGGER = logging.getLogger(__name__)

ALLOWED_ORIENTATIONS = [
    'landscape', 'upsidedown', 'portrait', 'upsidedown_portrait'
]


class PyDroidIPCam:
    """The Android device running IP Webcam."""

    def __init__(self, loop, websession, host, port, username=None,
                 password=None, timeout=10):
        """Initialize the data oject."""
        self.loop = loop
        self.websession = websession
        self.status_data = None
        self.sensor_data = None
        self._host = host
        self._port = port
        self._auth = None
        self._timeout = None
        self._available = True

        if username and password:
            self._auth = aiohttp.BasicAuth(username, password=password)

    @property
    def base_url(self):
        """Return the base url for endpoints."""
        return "http://{}:{}".format(self._host, self._port)

    @property
    def mjpeg_url(self):
        """Return mjpeg url."""
        return "{}/video".format(self.base_url)

    @property
    def image_url(self):
        """Return snapshot image url."""
        return "{}/shot.jpg".format(self.base_url)

    @property
    def available(self):
        """Return True if is available."""
        return self._available

    async def _request(self, path):
        """Make the actual request and return the parsed response."""
        url = '{}{}'.format(self.base_url, path)
        data = None

        try:
            async with self.websession.get(url, auth=self._auth, timeout=self._timeout) as response:
                if response.status == 200:
                    if response.headers['content-type'] == 'application/json':
                        data = await response.json()
                    else:
                        data = await response.text()

        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error('Failed to communicate with IP Webcam: %s', error)
            self._available = False
            return

        self._available = True
        if isinstance(data, str):
            return data.find("Ok") != -1
        return data

    async def update(self):
        """Fetch the latest data from IP Webcam."""
        status_data = await self._request('/status.json?show_avail=1')

        if status_data:
            self.status_data = status_data

            sensor_data = await self._request('/sensors.json')
            if sensor_data:
                self.sensor_data = sensor_data

    @property
    def current_settings(self):
        """Return dict with all config include."""
        settings = {}
        if not self.status_data:
            return settings

        for (key, val) in self.status_data.get('curvals', {}).items():
            try:
                val = float(val)
            except ValueError:
                val = val

            if val in ('on', 'off'):
                val = (val == 'on')

            settings[key] = val

        return settings

    @property
    def enabled_sensors(self):
        """Return the enabled sensors."""
        if self.sensor_data is None:
            return []
        return list(self.sensor_data.keys())

    @property
    def enabled_settings(self):
        """Return the enabled settings."""
        if self.status_data is None:
            return []
        return list(self.status_data.get('curvals', {}).keys())

    @property
    def available_settings(self):
        """Return dict of lists with all available config settings."""
        available = {}
        if not self.status_data:
            return available

        for (key, val) in self.status_data.get('avail', {}).items():
            available[key] = []
            for subval in val:
                try:
                    subval = float(subval)
                except ValueError:
                    subval = subval

                if val in ('on', 'off'):
                    subval = (subval == 'on')

                available[key].append(subval)

        return available

    def export_sensor(self, sensor):
        """Return (value, unit) from a sensor node."""
        value = None
        unit = None
        try:
            container = self.sensor_data.get(sensor)
            unit = container.get('unit')
            data_point = container.get('data', [[0, [0.0]]])
            if data_point and data_point[0]:
                value = data_point[0][-1][0]
        except (ValueError, KeyError, AttributeError):
            pass

        return (value, unit)

    def change_setting(self, key, val):
        """Change a setting.

        Return a coroutine.
        """
        if isinstance(val, bool):
            payload = 'on' if val else 'off'
        else:
            payload = val
        return self._request('/settings/{}?set={}'.format(key, payload))

    def torch(self, activate=True):
        """Enable/disable the torch.

        Return a coroutine.
        """
        path = '/enabletorch' if activate else '/disabletorch'
        return self._request(path)

    def focus(self, activate=True):
        """Enable/disable camera focus.

        Return a coroutine.
        """
        path = '/focus' if activate else '/nofocus'
        return self._request(path)

    def record(self, record=True, tag=None):
        """Enable/disable recording.

        Return a coroutine.
        """
        path = '/startvideo?force=1' if record else '/stopvideo?force=1'
        if record and tag is not None:
            path = '/startvideo?force=1&tag={}'.format(URL(tag).raw_path)

        return self._request(path)

    def set_front_facing_camera(self, activate=True):
        """Enable/disable the front-facing camera.

        Return a coroutine.
        """
        return self.change_setting('ffc', activate)

    def set_night_vision(self, activate=True):
        """Enable/disable night vision.

        Return a coroutine.
        """
        return self.change_setting('night_vision', activate)

    def set_overlay(self, activate=True):
        """Enable/disable the video overlay.

        Return a coroutine.
        """
        return self.change_setting('overlay', activate)

    def set_gps_active(self, activate=True):
        """Enable/disable GPS.

        Return a coroutine.
        """
        return self.change_setting('gps_active', activate)

    def set_quality(self, quality=100):
        """Set the video quality.

        Return a coroutine.
        """
        return self.change_setting('quality', quality)

    def set_motion_detect(self, activate=True):
        """Set motion detection on/off.
        Return a coroutine.
        """
        return self.change_setting('motion_detect', activate)

    def set_orientation(self, orientation='landscape'):
        """Set the video orientation.

        Return a coroutine.
        """
        if orientation not in ALLOWED_ORIENTATIONS:
            _LOGGER.debug('%s is not a valid orientation', orientation)
            return False
        return self.change_setting('orientation', orientation)

    def set_zoom(self, zoom):
        """Set the zoom level.

        Return a coroutine.
        """
        return self._request('/settings/ptz?zoom={}'.format(zoom))

    def set_scenemode(self, scenemode='auto'):
        """Set the video scene mode.

        Return a coroutine.
        """
        if scenemode not in self.available_settings['scenemode']:
            _LOGGER.debug('%s is not a valid scenemode', scenemode)
            return False
        return self.change_setting('scenemode', scenemode)
