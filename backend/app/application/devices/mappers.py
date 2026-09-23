from app.application.devices.dto import DeviceDto
from app.domain.devices.entity import Device


def to_device_dto(device: Device) -> DeviceDto:
    if device.id is None:
        raise ValueError(
            "A device must be saved before returning it through the API"
        )

    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=dict(device.default_config),
    )