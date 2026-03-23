"""
File upload API routes
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.logging import log, access_log
from app.core.exceptions import (
    FileUploadError, 
    InvalidFileFormatError, 
    FileSizeLimitError
)
from app.api.dependencies import get_settings
from app.models.schemas import FileUploadResponse
from app.services.model_processor import ModelProcessor
from app.db.database import get_db
from app.db.repositories import ModelRepository
from sqlalchemy.orm import Session

router = APIRouter(prefix="/upload", tags=["Upload"])


async def process_model_background(model_id: str, file_path: str, settings: dict):
    """Background task to process uploaded model - OPTIMIZED WITH MAX PARALLELISM"""
    try:
        log.info("background_processing_started", 
                model_id=model_id,
                max_workers=16,  # Increased to 16 for better parallel processing
                optimization="high_performance")
        
        # Create processor with database session
        from app.db.database import get_db
        db = next(get_db())
        
        try:
            processor = ModelProcessor(
                model_id=model_id,
                file_path=file_path,
                redis_url=settings.get("redis_url"),
                db=db,
                max_workers=16  # CRITICAL: Use 16 threads for maximum parallel performance
            )
            
            processed_data = processor.process()
            
            log.info("background_processing_completed", 
                    model_id=model_id, 
                    status=processed_data.get("status"),
                    parallel_efficiency="optimized")
        finally:
            db.close()
            
    except Exception as e:
        log.error("background_processing_failed",
                 model_id=model_id,
                 error=str(e))
        # Update status to error in database
        try:
            db = next(get_db())
            ModelRepository.update_status(db, model_id, "error")
            db.close()
        except:
            pass


@router.post("", response_model=FileUploadResponse)
async def upload_step_file(
    file: UploadFile = File(..., description="STEP file to upload"),
    background_tasks: BackgroundTasks = None,
    settings: dict = Depends(get_settings),
    db: Session = Depends(get_db)
):
    """
    Upload a STEP file for processing
    
    - **file**: STEP file (.step or .stp format)
    - Returns model_id for tracking processing status
    """
    access_log.info("file_upload_requested",
                   filename=file.filename,
                   content_type=file.content_type,
                   client_info=f"upload_request")
    
    try:
        # Validate file extension
        allowed_extensions = {".step", ".stp"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            access_log.warning("invalid_file_extension",
                              filename=file.filename,
                              extension=file_ext)
            raise InvalidFileFormatError(
                f"Invalid file extension '{file_ext}'. Allowed extensions: .step, .stp"
            )
        
        # Generate unique model ID
        model_id = str(uuid.uuid4())
        
        # Save file using streaming approach - CRITICAL FOR LARGE FILES
        upload_path = Path(settings["upload_dir"])
        upload_path.mkdir(parents=True, exist_ok=True)
        
        saved_filename = f"{model_id}{file_ext}"
        file_path = upload_path / saved_filename
        
        # Stream file directly to disk in chunks (avoids loading entire file into memory)
        # This is MUCH faster for large files
        CHUNK_SIZE = 8192  # 8KB chunks - optimal for disk I/O
        total_bytes_written = 0
        
        # Write file chunks directly (no need for threadpool since we're just doing I/O)
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                total_bytes_written += len(chunk)
        
        log.info("file_saved_successfully_streaming",
                model_id=model_id,
                file_path=str(file_path),
                file_size=total_bytes_written,
                original_filename=file.filename,
                streaming_upload=True)
        
        # Validate file is not empty
        if total_bytes_written == 0:
            access_log.warning("empty_file_upload_attempt",
                              filename=file.filename)
            raise InvalidFileFormatError("Cannot upload an empty file")
        
        # Validate file size
        max_size_mb = settings["max_upload_size"] / (1024 * 1024)
        if total_bytes_written > settings["max_upload_size"]:
            # Clean up oversized file
            file_path.unlink(missing_ok=True)
            raise FileSizeLimitError(
                f"File size ({total_bytes_written / (1024*1024):.2f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
            )
        
        # Save to database
        try:
            model_data = {
                "id": model_id,
                "filename": saved_filename,
                "original_filename": file.filename,
                "file_path": str(file_path),
                "file_size": total_bytes_written,
                "status": "processing",
                "entities_count": 0
            }
            
            model = ModelRepository.create(db, model_data)
            
            log.info("model_created_in_db",
                    model_id=str(model.id),
                    filename=model.filename,
                    status=model.status)
        except Exception as db_error:
            log.error("database_save_failed",
                     model_id=model_id,
                     error=str(db_error))
            # Don't fail the upload, just log the error
            # File is still saved and can be processed later
        
        # Add background processing task with increased parallelism
        if background_tasks:
            background_tasks.add_task(
                process_model_background,
                model_id,
                str(file_path),
                settings
            )
            log.info("background_processing_task_added", 
                    model_id=model_id,
                    max_workers=16)  # Increased from 8 to 16
        
        # Return immediately
        access_log.info("file_upload_completed",
                       model_id=model_id,
                       filename=file.filename,
                       file_size=total_bytes_written,
                       status="processing",
                       streaming_optimization=True)
        
        return FileUploadResponse(
            model_id=model_id,
            filename=file.filename,
            file_size=total_bytes_written,
            upload_time=datetime.now(),
            status="processing"
        )
        
    except InvalidFileFormatError as e:
        access_log.warning("invalid_file_format",
                          filename=file.filename if file else "unknown",
                          error=e.detail["message"])
        raise
    except FileSizeLimitError as e:
        access_log.warning("file_size_exceeded",
                          filename=file.filename if file else "unknown",
                          error=e.detail["message"])
        raise
    except Exception as e:
        access_log.error("file_upload_error",
                        filename=file.filename if file else "unknown",
                        error=str(e),
                        exc_info=True)
        # Clean up partial file on error
        try:
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)
        except:
            pass
        raise FileUploadError(f"Upload failed: {str(e)}")
