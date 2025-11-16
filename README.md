# Karakeep Integration for Home Assistant

This custom integration allows you to monitor your Karakeep statistics in Home Assistant. Karakeep is a bookmarking and content management service that helps you organize your digital content with features like bookmarks, favorites, highlights, and tags.

## Features

- Monitor the number of bookmarks, favorites, archived items, highlights, lists, and tags in your Karakeep account
- Configurable update interval
- Secure API token authentication
- Diagnostic sensors for easy monitoring

## Installation

### HACS Installation (Recommended)

1. Ensure that [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/sli-cka/karakeep-homeassistant` as the repository URL
   - Select "Integration" as the category
   - Click "Add"
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

1. Go to **Settings** > **Devices & Services**
2. Click the **+ Add Integration** button
3. Search for "Karakeep" and select it

### Required Configuration Parameters

- **Karakeep API URL**: The URL of your Karakeep API (e.g., `https://api.karakeep.com`)
- **API Token**: Your Karakeep API authentication token
- **Scan Interval**: How often to update the data (in seconds, minimum 30 seconds, default 300 seconds)

### Obtaining Your API Token

To obtain your Karakeep API token:

1. Log in to your Karakeep account
2. Navigate to your account settings
3. Look for the API or Developer section
4. Generate a new API token
5. Copy the token for use in Home Assistant

## Available Sensors

The integration creates the following sensors:

| Sensor | Description | Icon |
|--------|-------------|------|
| `sensor.karakeep_bookmarks` | Number of bookmarks | mdi:bookmark |
| `sensor.karakeep_favorites` | Number of favorites | mdi:star |
| `sensor.karakeep_archived` | Number of archived items | mdi:archive |
| `sensor.karakeep_highlights` | Number of highlights | mdi:marker |
| `sensor.karakeep_lists` | Number of lists | mdi:format-list-bulleted |
| `sensor.karakeep_tags` | Number of tags | mdi:tag |

## Requirements

- Home Assistant 2023.1.0 or newer
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

To get more detailed logs for troubleshooting, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.karakeep: debug
```

Restart Home Assistant after making these changes to apply the new logging configuration.

## Contributing

Contributions to improve the Karakeep integration are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/sli-cka/ha-karakeep).

## License

This integration is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, funded, or in any way associated with Karakeep. It is a community-developed integration for Home Assistant.