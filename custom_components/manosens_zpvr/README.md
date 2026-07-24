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
