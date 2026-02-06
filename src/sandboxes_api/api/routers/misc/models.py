from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="The status of the API")
