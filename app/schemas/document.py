from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str


class DocumentSummary(BaseModel):
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentCapabilitiesResponse(BaseModel):
    supported_extensions: list[str]
    max_upload_size_bytes: int


class DocumentDeleteResponse(BaseModel):
    filename: str
    status: str
