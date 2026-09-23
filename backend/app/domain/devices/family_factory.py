from abc import ABC, abstractmethod

from app.domain.devices.entity import Device
from app.domain.sensors import (
    LightSensorCreator,
    MoistureSensorCreator,
)


class UnknownDeviceFamily(ValueError):
    pass


class DeviceFamilyFactory(ABC):
    family: str

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        """Create a matching kit of two sensors and two actuators."""
        raise NotImplementedError

    def _create_kit(
        self,
        label: str,
        protocol: str,
        simulated: bool,
    ) -> list[Device]:
        common_config = {
            "protocol": protocol,
            "simulated": simulated,
        }
        devices: list[Device] = []

        # Reuse the Phase 2 Factory Method creators.
        for creator in (
            MoistureSensorCreator(),
            LightSensorCreator(),
        ):
            sensor = creator.create_sensor()

            devices.append(
                Device(
                    id=None,
                    device_type=sensor.device_type,
                    role="sensor",
                    device_family=self.family,
                    display_name=f"{label} {sensor.display_name}",
                    default_config={
                        **sensor.default_config,
                        **common_config,
                    },
                )
            )

        actuator_specs = (
            (
                "water_pump",
                "Water pump",
                {"flow_rate_l_min": 2, "enabled": False},
            ),
            (
                "grow_light",
                "Grow light",
                {"brightness_percent": 70, "enabled": False},
            ),
        )

        for device_type, name, config in actuator_specs:
            devices.append(
                Device(
                    id=None,
                    device_type=device_type,
                    role="actuator",
                    device_family=self.family,
                    display_name=f"{label} {name}",
                    default_config={
                        **config,
                        **common_config,
                    },
                )
            )

        return devices


class SimulationDeviceFactory(DeviceFamilyFactory):
    family = "simulation"

    def create_device_set(self) -> list[Device]:
        return self._create_kit(
            label="Simulation",
            protocol="simulation",
            simulated=True,
        )


class EdgeHardwareFactory(DeviceFamilyFactory):
    family = "edge"

    def create_device_set(self) -> list[Device]:
        # Hardware configuration only; no real GPIO access in this phase.
        return self._create_kit(
            label="Edge",
            protocol="gpio_stub",
            simulated=False,
        )


FACTORIES: dict[str, DeviceFamilyFactory] = {
    "simulation": SimulationDeviceFactory(),
    "edge": EdgeHardwareFactory(),
}


def get_device_factory(family: str) -> DeviceFamilyFactory:
    try:
        return FACTORIES[family]
    except KeyError as error:
        raise UnknownDeviceFamily(
            f"Unknown device family: {family}"
        ) from error