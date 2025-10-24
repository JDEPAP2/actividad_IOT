from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from datetime import datetime


class IngestPayload(BaseModel):
    temp_c: Union[int, float] = Field(..., description="Temperatura en °C")
    humidity: Union[int, float] = Field(..., ge=0, le=100, description="Humedad relativa %")


    acc_x: Union[int, float]
    acc_y: Union[int, float]
    acc_z: Union[int, float]


    prediction: Union[int, float] = Field(..., description="Probabilidad o etiqueta binaria")


    timestamp: Optional[Union[str, datetime]] = Field(default=None)


    source: Optional[str] = Field(default=None)


    @field_validator('timestamp', mode='before')
    def parse_ts(cls, v):
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            return v
        try:
            if isinstance(v, str) and v.endswith('Z'):
                v = v.replace('Z', '+00:00')
            return datetime.fromisoformat(v)
        except Exception:
            raise ValueError('timestamp debe ser ISO-8601, ej: 2025-10-23T13:45:00Z')