<p align="center">
  <img src="custom_components/simpel/brand/logo@2x.png" alt="Simpel" height="80">
</p>

# Simpel for Home Assistant

See how much of your [Simpel](https://www.simpel.nl) mobile bundle is left, right in Home Assistant: data, call minutes and SMS, the billing period, and how much data you can use per day until it resets.

The integration logs in with your Mijn Simpel account and reads the same figures the Mijn Simpel portal shows. When the session expires it logs in again by itself, so there is nothing to maintain after setup.

## Installation

### HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frankwiersma&repository=ha-simpel&category=integration)

Click the button, install **Simpel** and restart Home Assistant. Or add it by hand:

1. In HACS, open the menu (⋮) and choose **Custom repositories**.
2. Add `https://github.com/frankwiersma/ha-simpel` with type **Integration**.
3. Search for **Simpel**, install it and restart Home Assistant.

### Manual

Copy `custom_components/simpel` into the `custom_components` folder of your Home Assistant configuration and restart Home Assistant.

Home Assistant 2026.3 or newer is required.

## Setup

[![Open your Home Assistant instance and start setting up Simpel.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=simpel)

Click the button, or go to **Settings → Devices & services → Add integration → Simpel**, and log in with the username and password you use on [mijn.simpel.nl](https://mijn.simpel.nl). The integration finds your subscription on its own.

If you change your Simpel password, Home Assistant shows a repair notice and asks for the new one.

## Sensors

| Sensor | Unit | Notes |
|---|---|---|
| Data remaining | GB | What is left of the data bundle this period |
| Data used | GB | |
| Data bundle | GB | Size of the bundle |
| Data per day left | MB/day | Data remaining divided by the days left, today included |
| Days left | d | Days left in the billing period, today included |
| Minutes remaining | min | |
| Minutes used | min | |
| SMS remaining | | |
| Billing period start | date | |
| Billing period last day | date | |
| Data usage updated until | timestamp | Simpel publishes data usage in blocks of a few hours; the remaining-bundle figures are more current |

Data is refreshed every 30 minutes. Unlimited bundles report no value for the remaining amount.

## Example: warn when data runs low

```yaml
automation:
  - alias: "Simpel: data running low"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.simpel_data_remaining
        below: 5
        id: "5"
      - trigger: numeric_state
        entity_id: sensor.simpel_data_remaining
        below: 1
        id: "1"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Simpel: {{ states('sensor.simpel_data_remaining') | float | round(1) }} GB left"
          message: >-
            Below {{ trigger.id }} GB with {{ states('sensor.simpel_days_left') }} days to go,
            that is {{ states('sensor.simpel_data_per_day_left') }} MB per day.
```

Entity ids depend on your Home Assistant language; check them under **Settings → Entities**.

## Privacy

Your username and password are stored in Home Assistant's config entry, like any other integration that logs in to a cloud account, and are only sent to Simpel. Nothing else leaves your Home Assistant.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Simpel. It uses the web API behind the Mijn Simpel portal, which Simpel can change at any time. The Simpel name and logo are trademarks of their owner and are used only to identify the service this integration connects to.
