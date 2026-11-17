from app.application.devices.dto import DeviceDto
from app.domain.actuators.context import ActuatorContext
from app.domain.devices.entity import Device


def to_device_dto(device: Device) -> DeviceDto:
    if device.id is None:
        raise ValueError(
            "A device must be saved before returning it through the API"
        )

    state = None
    allowed_commands: list[str] = []

    if device.role == "actuator" and device.state is not None:
        context = ActuatorContext(
            device.state,
            device_type=device.device_type,
        )
        state = context.state
        allowed_commands = context.allowed_commands()

    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=dict(device.default_config),
        zone_id=device.zone_id,
        location_id=device.location_id,
        state=state,
        allowed_commands=allowed_commands,
    )