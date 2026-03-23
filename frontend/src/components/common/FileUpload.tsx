                import React, { useRef, useState } from 'react';
import { useFileUpload } from '../../hooks';

interface FileUploadProps {
  onClose: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onClose }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { upload, isUploading, progress } = useFileUpload();
  const [error, setError] = useState<string | null>(null);
  const [hasUploaded, setHasUploaded] = useState(false); // Prevent double upload

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['.step', '.stp'];
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!validTypes.includes(fileExt)) {
        setError('Please select a valid STEP file (.step or .stp)');
        return;
      }

      // Validate file size (100MB)
      if (file.size > 100 * 1024 * 1024) {
        setError('File size must be less than 100MB');
        return;
      }

      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || hasUploaded) return;

    try {
      setHasUploaded(true); // Mark as uploaded to prevent double-click
      await upload(selectedFile);
      
      // Reset state and close
      setHasUploaded(false);
      setSelectedFile(null);
      setError(null);
      onClose();
      
      // Show notification that processing continues in background
      alert(`File uploaded successfully!\n\nProcessing will continue in the background.\nYou can view it in the dashboard.`);
    } catch (err: any) {
      setHasUploaded(false); // Allow retry on error
      setError(err.message || 'Upload failed');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Upload STEP File</h2>
        <p className="text-gray-400 mb-4">
          Select a .step or .stp file to upload (max 50MB)
        </p>

        {/* File input */}
        <div className="mb-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".step,.stp"
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full px-4 py-3 border-2 border-dashed border-gray-600 hover:border-blue-500 rounded-lg transition flex items-center justify-center gap-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            {selectedFile ? selectedFile.name : 'Choose File'}
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Progress bar */}
        {isUploading && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-400 mb-1">
              <span>Uploading...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            disabled={isUploading || hasUploaded}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading || hasUploaded}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
            title={hasUploaded ? 'Already uploaded' : ''}
          >
            {isUploading ? 'Uploading...' : hasUploaded ? 'Uploaded ✓' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
