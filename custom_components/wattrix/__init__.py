import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator, get_device_serial
from custom_components.wattrix.wattrix_host import WattrixHost

DOMAIN = "wattrix"
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "select", "number"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wattrix from YAML (optional)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wattrix from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    serial_number = await get_device_serial(host)
    if serial_number and len(serial_number) > 0:
        _LOGGER.info("Using serial number: %s", serial_number)
    else:
        _LOGGER.error("No serial number found for Wattrix device.")
        return False

    host = WattrixHost(hass, host)

    coordinator = WattrixDataUpdateCoordinator(hass, host)
    try:
        await coordinator.async_refresh()
    except Exception as e:
        # Log warning and return False so HA will retry later
        _LOGGER.warning("Wattrix not available during startup: %s", e)
        return False  # HA will retry setup automatically later


    serial_number_old = await host.async_get_serial_number()
    await migrate_unique_ids(hass, DOMAIN, serial_number_old, serial_number)


    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "coordinator": coordinator,
    }

    # Forward setup to sensor and select platforms
    await hass.config_entries.async_forward_entry_setups(entry,  ["sensor", "number", "select", "button"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Migrating Wattrix config entry: %s", entry.entry_id)

    # Example: Check config entry version and update
    if entry.version == 1:
        # Do migration logic if needed
        entry.version = 2
        hass.config_entries.async_update_entry(entry)
        _LOGGER.info("Wattrix config entry migrated to version 2")

    return True

async def migrate_unique_ids(hass, domain, serial_number_old, serial_number_new):
    """Migrate old Wattrix unique IDs to new format based on serial number."""

    entity_registry = async_get_entity_registry(hass)
    migration_keys = [
        ("sensor", "current_power"),
        ("sensor", "target_power"),
        ("sensor", "power_limit_percentage"),
        ("sensor", "timeout_seconds"),
        ("sensor", "serial_number"),
        ("sensor", "version"),
        ("sensor", "thermal_sensor"),
        ("sensor", "setpoint"),
        ("binary_sensor", "online"),

        ("select", "mode"),
        ("number", "mode_percentage"),
        ("number", "mode_timeout"),
        ("number", "mode_setpoint"),

        ("number", "power_limit_percentage"),

        ("button", "mode_reapply"),
    ]


    for platform, key in migration_keys:
        old_unique_id = f"wattrix_{key}_{serial_number_old}"
        new_unique_id = f"wattrix_{key}_{serial_number_new}"

        old_entity_id = entity_registry.async_get_entity_id(platform, domain, old_unique_id)

        if old_entity_id and old_unique_id != new_unique_id:
            try:
                entity_registry.async_update_entity(old_entity_id, new_unique_id=new_unique_id)
                _LOGGER.info(f"Migrated {old_entity_id}: {old_unique_id} → {new_unique_id}")
            except Exception as e:
                _LOGGER.warning(f"Migration failed for {old_entity_id}: {e}")