from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    code: str
    donor: Optional[str] = None
    budget: float = 0.0
    currency: str = "USD"
    nas_folder_path: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    donor: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    nas_folder_path: Optional[str] = None
    description: Optional[str] = None

class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
