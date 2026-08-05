# Karakeep Integration for Home Assistant

This custom integration allows you to monitor your Karakeep statistics in Home Assistant. Karakeep is a bookmarking and content management service that helps you organize your digital content with features like bookmarks, favorites, highlights, and tags.

> [!IMPORTANT]
> **Karakeep is now part of Home Assistant Core**, starting with Home Assistant `2026.8`.
> This custom integration remains available during a transition period, but new
> development happens in Home Assistant Core. See
> [Migrating to the Home Assistant Core integration](#migrating-to-the-home-assistant-core-integration).

## Migrating to the Home Assistant Core integration

Once you are running Home Assistant `2026.8` or later, the built-in Karakeep
integration is available and you can switch to it.

There is no automatic migration: the built-in integration stores its
configuration differently, so you need to set it up once more. Follow the steps
in this order to keep your entity IDs and history.

1. **Delete the existing Karakeep entry first.** Go to **Settings** >
   **Devices & Services** > **Karakeep**, then delete the config entry. Doing
   this while the custom integration is still installed lets Home Assistant
   clean up its entities and device properly.
2. **Remove the custom integration** in HACS: **HACS** > **Karakeep** > **Remove**.
3. **Restart Home Assistant.**
4. **Add Karakeep again** via **Settings** > **Devices & Services** >
   **+ Add Integration**. Enter your Karakeep URL and API token.

When you follow this order, the new entities reuse the original entity IDs, so
your existing history and long-term statistics continue uninterrupted.

> [!NOTE]
> Entity customizations are not preserved. If you renamed any Karakeep entities
> or assigned them to areas, note those settings before deleting the entry.

### Feature differences

The first Home Assistant Core release covers config flow setup and the six
statistic sensors. These features are currently only available in this custom
integration:

- Health binary sensor (`binary_sensor.karakeep_health`)
- Update entity (`update.karakeep_update`)
- Repair issue when the API is unavailable
- Configurable scan interval

If you rely on any of these, stay on the custom integration for now. Automations
and dashboard cards referencing those entities stop working after switching.

### Where to report issues

- Problems with **this custom integration**: [open an issue here](https://github.com/sli-cka/karakeep-homeassistant/issues)
- Problems with the **built-in integration**: report them in [home-assistant/core](https://github.com/home-assistant/core/issues)

## Features

- Monitor the number of bookmarks, favorites, archived items, highlights, lists, and tags in your Karakeep account
- Health monitoring with diagnostic binary sensor to track API availability
- Update entity to track available Karakeep updates
- Automatic repair issue notification when API is unavailable
- Configurable update interval
- Secure API token authentication

## Installation

### HACS Installation (Recommended)

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=sli-cka&repository=karakeep-homeassistant&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

1. Ensure that [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
3. Search for "Karakeep" in the HACS Integrations store
4. Click "Install"
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/sli-cka/karakeep-homeassistant/releases)
2. Create a `custom_components` directory in your Home Assistant configuration directory if it doesn't already exist
3. Extract the `karakeep` directory from the release into the `custom_components` directory
4. Restart Home Assistant

## Configuration

The Karakeep integration is configured through the Home Assistant UI:

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=karakeep" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Open your Home Assistant instance and start setting up a new integration." /></a>

1. Go to **Settings** > **Devices & Services**
2. Click the **+ Add Integration** button
3. Search for "Karakeep" and select it

### Required Configuration Parameters

- **Karakeep URL**: The URL of your Karakeep instance (e.g., `https://try.karakeep.app/`)
- **API Token**: Your Karakeep API authentication token
- **Scan Interval**: How often to update the data (in seconds, minimum 30 seconds, default 300 seconds)

### Obtaining Your API Token

To obtain your Karakeep API token:

1. Log in to your Karakeep account
2. Navigate to your user settings
3. Look for the API Keys section
4. Generate a new API Key
5. Copy the key for use in Home Assistant

## Available Sensors

The integration creates the following sensors:

### Statistics Sensors

| Sensor | Description | Icon |
|--------|-------------|------|
| `sensor.karakeep_bookmarks` | Number of bookmarks | mdi:bookmark |
| `sensor.karakeep_favorites` | Number of favorites | mdi:star |
| `sensor.karakeep_archived` | Number of archived items | mdi:archive |
| `sensor.karakeep_highlights` | Number of highlights | mdi:marker |
| `sensor.karakeep_lists` | Number of lists | mdi:format-list-bulleted |
| `sensor.karakeep_tags` | Number of tags | mdi:tag |

### Diagnostic Sensors

| Sensor | Description | Type | Device Class |
|--------|-------------|------|--------------|
| `binary_sensor.karakeep_health` | API health status | Binary Sensor | Problem |

### Update Entity

| Entity | Description |
|--------|-------------|
| `update.karakeep_update` | Tracks installed vs latest version |

> **Note:** The update entity requires Karakeep version 0.29.0 or later.

## Repair Issues

The integration automatically creates repair issues in Home Assistant's **Settings > System > Repairs** dashboard when problems are detected:

| Issue | Description |
|-------|-------------|
| **API Unavailable** | Raised when the Karakeep server cannot be reached (connection refused, timeout, network errors). The issue is automatically resolved when connectivity is restored. |

This helps you quickly identify and troubleshoot connectivity problems with your Karakeep instance.

## Requirements

- Home Assistant
- A Karakeep account with API access
- Network access from your Home Assistant instance to the Karakeep API

## Troubleshooting

### Common Issues

- **Connection Error**: Ensure your Home Assistant instance can reach the Karakeep API URL. Check your network configuration and firewall settings.
- **Authentication Error**: Verify that your API token is correct and has not expired.
- **Invalid URL Format**: Make sure the URL includes the protocol (http:// or https://) and domain.
- **API Path Error**: Ensure the API URL is correct and points to a valid Karakeep API endpoint.
- **Timeout Error**: The connection to the Karakeep server might be slow or unstable. Try increasing the scan interval.

### Logs

To get more detailed logs for troubleshooting, click on `Enable Debug Logging` in the integration overview (via 3-dots menu) 

## Contributing

Contributions to improve the Karakeep integration are welcome! Please feel free to submit a pull request or open an issue.

## License

This integration is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, funded, or in any way associated with Karakeep. It is a community-developed integration for Home Assistant.