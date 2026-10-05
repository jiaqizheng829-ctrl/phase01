import asyncio
import logging
from datetime import datetime, timezone

from app.application.readings.sampler import SimulationSampler
from app.application.readings.service import ReadingIngest
from app.infrastructure.adapters.sensors.selector import (
    select_sensor_adapter,
)
from app.infrastructure.db import SessionLocal
from app.infrastructure.device_repository import DeviceRepository
from app.infrastructure.reading_repository import ReadingRepository
from app.infrastructure.sampling_device_repository import (
    SamplingDeviceRepository,
)


logger = logging.getLogger(__name__)


def run_sampling_tick() -> int:
    # Each tick owns its database session.
    with SessionLocal() as session:
        readings = ReadingRepository(session)

        ingest = ReadingIngest(
            DeviceRepository(session),
            readings,
            select_sensor_adapter,
        )

        sampler = SimulationSampler(
            SamplingDeviceRepository(session),
            readings,
            ingest,
            select_sensor_adapter,
        )

        return sampler.run_once(datetime.now(timezone.utc))


async def run_sampling_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            # Database work runs outside the API's event loop.
            await asyncio.to_thread(run_sampling_tick)
        except Exception:
            logger.exception("Simulation sampling tick failed")

        try:
            await asyncio.wait_for(stop.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass