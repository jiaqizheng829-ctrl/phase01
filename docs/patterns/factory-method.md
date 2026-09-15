# Factory Method

## Problem

The greenhouse can create different sensor types. Each sensor type needs its
own device type and default configuration. If API routes created sensor classes
directly, every new sensor type would require changes in the route.

## Solution

This project uses the Factory Method pattern. `SensorCreator` is the creator
interface. `MoistureSensorCreator` and `LightSensorCreator` are concrete
creators. Each creator produces a `Sensor` with its own defaults.

The registry maps the short API keys `moisture` and `light` to creators. The
application service resolves a creator from the registry, creates the sensor,
and then asks the repository to store it.

## Code path

1. The client sends `POST /api/sensors`.
2. The API router passes the requested type to `SensorService`.
3. `SensorService` gets a creator from the registry.
4. The creator creates a `Sensor` domain object.
5. `DeviceRepository` stores it in the `devices` table.

## Extension exercise

To add a temperature sensor, I would create a new
`TemperatureSensorCreator`, give it a key and default configuration, and add
it to the registry. The API route does not need to know the concrete sensor
class.
