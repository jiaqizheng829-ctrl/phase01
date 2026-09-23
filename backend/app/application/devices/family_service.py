from app.domain.devices.entity import Device
from app.domain.devices.family_factory import get_device_factory
from app.infrastructure.device_repository import DeviceRepository


class DeviceFamilyService:
    def __init__(self, repository: DeviceRepository) -> None:
        self.repository = repository

    def provision_family(self, family: str) -> list[Device]:
        factory = get_device_factory(family)
        devices = factory.create_device_set()
        return self.repository.save_many(devices)

    def list_devices(
        self,
        family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self.repository.list_devices(
            family=family,
            role=role,
        )