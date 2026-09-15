from sqlalchemy.orm import Session

from app.domain.sensors import Sensor, get_sensor_creator
from app.infrastructure.device_repository import DeviceRepository


class SensorService:
    def __init__(self, session: Session) -> None:
        self.repository = DeviceRepository(session)

    def create_sensor(
        self,
        sensor_type: str,
        display_name: str | None = None,
    ) -> Sensor:
        creator = get_sensor_creator(sensor_type)
        sensor = creator.create_sensor(display_name)
        return self.repository.add_sensor(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self.repository.list_sensors()
