"""Support for Rfplayer sensors."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RfplayerDevice
from .const import (
    CONF_AUTOMATIC_ADD,
    DATA_DEVICE_REGISTER,
    DATA_ENTITY_LOOKUP,
    DOMAIN,
    EVENT_KEY_ID,
    EVENT_KEY_SENSOR,
    EVENT_KEY_UNIT,
)
from .rflib.rfpparser import PACKET_FIELDS, UNITS

_LOGGER = logging.getLogger(__name__)

SENSOR_ICONS = {
    "humidity": "mdi:water-percent",
    "battery": "mdi:battery",
    "temperature": "mdi:thermometer",
}


def lookup_unit_for_sensor_type(sensor_type):
    """Get unit for sensor type.

    Async friendly.
    """
    field_abbrev = {v: k for k, v in PACKET_FIELDS.items()}

    return UNITS.get(field_abbrev.get(sensor_type))


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Rfplayer platform."""
    config = entry.data
    options = entry.options

    # add jamming entity
    async_add_entities(
        [RfplayerSensor(protocol="JAMMING", device_id=0, name="Jamming detection")]
    )

    async def add_new_device(device_info):
        """Check if device is known, otherwise create device entity."""
        device_id = device_info[EVENT_KEY_ID]

        # create entity
        device = RfplayerSensor(
            protocol=device_id.split("_")[0],
            device_id=device_id.split("_")[1],
            unit_of_measurement=device_info[EVENT_KEY_UNIT],
            initial_event=device_info,
        )
        _LOGGER.debug("Add sensor entity %s", device_id)
        async_add_entities([device])

    if CONF_DEVICES in config:
        for device in config[CONF_DEVICES].values():
            if EVENT_KEY_SENSOR in device:
                await add_new_device(device)

    if options.get(CONF_AUTOMATIC_ADD, config[CONF_AUTOMATIC_ADD]):
        hass.data[DOMAIN][DATA_DEVICE_REGISTER][EVENT_KEY_SENSOR] = add_new_device


class RfplayerSensor(RfplayerDevice):
    """Representation of a Rfplayer sensor."""

    def __init__(
        self,
        protocol,
        device_id,
        unit_of_measurement=None,
        initial_event=None,
        name=None,
        **kwargs,
    ) -> None:
        """Handle sensor specific args and super init."""
        self._state: float | None = None
        self._protocol = protocol
        self._device_id = device_id
        self._attr_name = name
        self._attr_unit_of_measurement = unit_of_measurement
        super().__init__(
            protocol, device_id=device_id, initial_event=initial_event, **kwargs
        )

    async def async_added_to_hass(self) -> None:
        """Register update callback."""
        # Register id and aliases
        await super().async_added_to_hass()

        self.hass.data[DOMAIN][DATA_ENTITY_LOOKUP][EVENT_KEY_SENSOR][
            self._initial_event[EVENT_KEY_ID]
        ] = self.entity_id

    def _handle_event(self, event):
        """Domain specific event handler."""
        self._state = float(event["value"])

    @property
    def state(self) -> float | None:
        """Return value."""
        return self._state
