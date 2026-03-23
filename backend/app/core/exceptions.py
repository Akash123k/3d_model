"""
Custom exceptions for the application
"""

from fastapi import HTTPException, status


class STEPProcessingError(HTTPException):
    """Exception raised when STEP file processing fails"""
    
    def __init__(self, message: str = "Failed to process STEP file", details: str = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "STEP_PROCESSING_ERROR",
                "message": message,
                "details": details
            }
        )


class FileUploadError(HTTPException):
    """Exception raised when file upload fails"""
    
    def __init__(self, message: str = "File upload failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "FILE_UPLOAD_ERROR",
                "message": message
            }
        )


class ModelNotFoundError(HTTPException):
    """Exception raised when requested model is not found"""
    
    def __init__(self, model_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MODEL_NOT_FOUND",
                "message": f"Model with ID {model_id} not found"
            }
        )


class GeometryExtractionError(HTTPException):
    """Exception raised when geometry extraction fails"""
    
    def __init__(self, message: str = "Failed to extract geometry"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "GEOMETRY_EXTRACTION_ERROR",
                "message": message
            }
        )


class InvalidFileFormatError(HTTPException):
    """Exception raised when uploaded file has invalid format"""
    
    def __init__(self, message: str = "Invalid file format. Only STEP files (.step, .stp) are allowed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_FILE_FORMAT",
                "message": message
            }
        )


class FileSizeLimitError(HTTPException):
    """Exception raised when file exceeds size limit"""
    
    def __init__(self, max_size_mb: float):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "FILE_SIZE_LIMIT_EXCEEDED",
                "message": f"File size exceeds maximum limit of {max_size_mb}MB"
            }
        )
