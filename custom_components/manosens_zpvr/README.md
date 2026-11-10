# ManoSens ZPVR Custom Component for Home Assistant

This custom component integrates the ManoSens ZPVR device with Home Assistant, allowing you to monitor sensor data and control certain aspects of the device.

## Services

This integration provides the following services to interact with your ManoSens ZPVR device.

### `manosens_zpvr.set_pressure`

Sets the pressure value on the ManoSens ZPVR device.

| Service Data | Type      | Description                               | Example |
| :----------- | :-------- | :---------------------------------------- | :------ |
| `value`      | `float`   | The desired pressure value to set (0.0 - 5.0). | `3.1`   |

**Example Usage in Home Assistant Automation/Script:**

```yaml
service: manosens_zpvr.set_pressure
data:
  value: 3.1
```

### `manosens_zpvr.set_start_stop`

Controls the start/stop state of the ManoSens ZPVR device.

| Service Data | Type      | Description                               | Example |
| :----------- | :-------- | :---------------------------------------- | :------ |
| `value`      | `boolean` | Set to `true` to start the device, `false` to stop it. | `true`  |

**Example Usage in Home Assistant Automation/Script:**

```yaml
service: manosens_zpvr.set_start_stop
data:
  value: true # To start the device
```

```yaml
service: manosens_zpvr.set_start_stop
data:
  value: false # To stop the device
```


## Behaviour notes (0.2.0)

- **Config-only packets.** The device sometimes answers `/get-rs-data` with `"data": {}` and a `config` object. These no longer make the entities unavailable: the last valid measurement is kept for up to 45 seconds. Any real HTTP or network error, or a malformed measurement, makes the entities unavailable on the next poll.
- **`set_pressure` is verified.** The call succeeds only if the device accepts the POST *and* a following `/get-rs-data` read reports `config.required_pressure` matching the requested value (±0.051 bar). It makes at most 4 reads, 0.5 s apart, and never repeats the POST. Otherwise the service raises an error. This confirms the setpoint, not the physical water pressure.
- **`set_start_stop`** raises an error if the HTTP command fails. A successful response does not prove what the pump physically did.
- Services are registered even while the device is offline, but refuse to send commands unless exactly one device is loaded and its last update succeeded.
