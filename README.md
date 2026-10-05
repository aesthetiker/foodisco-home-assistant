# Foodisco for Home Assistant

Connect your [Foodisco](https://foodisco.app) nutrition diary to your home — set up like any other
integration: type a pairing code, done. No tokens to copy, no YAML to edit.

**What you get**

- **Sensors** per person: calories remaining / today, protein today, water today, last meal (timestamp,
  with the meal type as attribute), tonight's planned dinner.
- **A "Meal logged" event entity** that fires once per newly logged meal (`breakfast`, `lunch`, `dinner`,
  `snack`). It never fires on a restart or a reconnect — only for a meal logged after the last one seen.
- **A service `foodisco.report_event`** to tell Foodisco that something happened at home. Today: `oven_finished`.
  Foodisco then decides, after 20 minutes and only at meal time, whether to ask what you cooked.
- **Blueprints** (UI, no YAML): vacuum the kitchen after lunch/dinner once nobody has been in it for
  10 minutes; report "oven finished".

Foodisco polls nothing in your home and your Home Assistant needs no external URL: this integration asks
Foodisco once a minute, and reports events outward.

## Install

1. In HACS: **⋮ → Custom repositories** → add `https://github.com/aesthetiker/foodisco-home-assistant`
   as category **Integration**, install **Foodisco**, restart Home Assistant.
2. In the Foodisco app: **Profile → Integrations → Smart Home (Labs) → Home Assistant → Create pairing code**.
3. In Home Assistant: **Settings → Devices & services → Add integration → Foodisco**, enter the code
   (`ABCD-EFGH`; valid 10 minutes, usable once).

Every person pairs their own Foodisco account — add the integration once per person.

## Blueprints

[![Import vacuum blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Faesthetiker%2Ffoodisco-home-assistant%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffoodisco%2Fvacuum_after_meal.yaml)
[![Import oven blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Faesthetiker%2Ffoodisco-home-assistant%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffoodisco%2Foven_finished.yaml)

- **Vacuum after meals** — pick the Foodisco event entity (or several, one per person — they share the cooldown), a "kitchen occupied" binary sensor, your vacuum
  and the button that starts its after-meal programme.
- **Oven finished** — pick the oven's state sensor (e.g. Home Connect operation state), the value that means
  "finished", and the Foodisco account to tell.

## What is shared

| Direction | Data |
|---|---|
| Foodisco → Home Assistant | Calories and protein today, water, the last meal (type and time), tonight's planned dinner title. No foods, no weight, no health values. |
| Home Assistant → Foodisco | `oven_finished` and the time. Nothing else — no rooms, no people, no device names. |

The two access tokens live in Home Assistant's config entry. Revoke them any time in the Foodisco app
(Home Assistant → "Your accesses"); Home Assistant then asks for a new code. Events are deleted after 30 days.

## Without the integration

If you would rather not install a custom integration, Foodisco also works with plain REST sensors:
see `blueprints/automation/foodisco/vacuum_after_meal_rest.yaml` and the YAML in the app's
"Without the integration" section.

## Deutsch

Foodisco für Home Assistant: einmal in HACS als benutzerdefiniertes Repository hinzufügen, in der Foodisco-App
unter *Profil → Integrationen → Home Assistant* einen Kopplungscode erzeugen und ihn in Home Assistant unter
*Einstellungen → Geräte & Dienste → Integration hinzufügen → Foodisco* eingeben. Kein Token-Kopieren, keine
YAML-Datei. Die Blueprints (Sauger nach dem Essen, Backofen fertig) richtest du in der Oberfläche ein.

## Development

```bash
pip install -r requirements_test.txt
python -m pytest -q
```

The tests cover the Home-Assistant-free parts (API client, meal detection). MIT licence.
