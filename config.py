import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    INFLUX_URL: str = os.getenv('INFLUX_URL', 'http://localhost:8086')
    INFLUX_TOKEN: str = os.getenv('INFLUX_TOKEN', '')
    INFLUX_ORG: str = os.getenv('INFLUX_ORG', 'my-org')
    INFLUX_BUCKET: str = os.getenv('INFLUX_BUCKET', 'sensor-data')


settings = Settings()