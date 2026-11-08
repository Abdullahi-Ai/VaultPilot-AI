from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_path: str
    document_type: str = "OTHER"
    extraction_status: str = "EXTRACTED"
    extracted_data: Optional[Dict[str, Any]] = None

class DocumentCreate(DocumentBase):
    project_id: int
    investigation_id: Optional[int] = None

class DocumentOut(DocumentBase):
    id: int
    project_id: int
    investigation_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
