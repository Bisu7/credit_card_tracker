import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  File, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  FileText,
  Image,
  FileSpreadsheet
} from 'lucide-react';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

const DocumentUpload: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const { uploadDocuments } = useApi();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending'
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'text/html': ['.html', '.htm'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: true,
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id));
  };

  const getFileIcon = (file: File) => {
    const type = file.type;
    if (type.includes('pdf')) return <File className="w-5 h-5 text-red-500" />;
    if (type.includes('word') || type.includes('document')) return <FileText className="w-5 h-5 text-blue-500" />;
    if (type.includes('image')) return <Image className="w-5 h-5 text-green-500" />;
    if (type.includes('sheet') || type.includes('excel')) return <FileSpreadsheet className="w-5 h-5 text-green-600" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return;

    setIsUploading(true);
    const filesToUpload = uploadedFiles.map(uf => uf.file);

    // Update status to uploading
    setUploadedFiles(prev => 
      prev.map(file => ({ ...file, status: 'uploading' as const }))
    );

    try {
      const result = await uploadDocuments(filesToUpload);
      
      if (result.success) {
        setUploadedFiles(prev => 
          prev.map(file => ({ ...file, status: 'success' as const }))
        );
        toast.success(`Successfully processed ${result.documents_processed} documents}`);
        toast.success(`Created ${result.total_chunks} text chunks`);
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error: any) {
      setUploadedFiles(prev => 
        prev.map(file => ({ 
          ...file, 
          status: 'error' as const, 
          error: error.message 
        }))
      );
      toast.error('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const clearAll = () => {
    setUploadedFiles([]);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Document Upload
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Upload documents to enhance your research capabilities
        </p>
      </div>

      {/* Upload Area */}
      <div className="card p-8 mb-6">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            or click to select files
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Supports PDF, DOC, DOCX, TXT, MD, HTML, JSON, CSV, XLS, XLSX (max 10MB each)
          </p>
        </div>
      </div>

      {/* File List */}
      {uploadedFiles.length > 0 && (
        <div className="card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Files to Upload ({uploadedFiles.length})
            </h3>
            <button
              onClick={clearAll}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-3">
            {uploadedFiles.map((uploadedFile) => (
              <div
                key={uploadedFile.id}
                className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {getFileIcon(uploadedFile.file)}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {uploadedFile.file.name}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(uploadedFile.file.size)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {uploadedFile.status === 'pending' && (
                    <button
                      onClick={() => removeFile(uploadedFile.id)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}

                  {uploadedFile.status === 'uploading' && (
                    <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />
                  )}

                  {uploadedFile.status === 'success' && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}

                  {uploadedFile.status === 'error' && (
                    <div className="flex items-center space-x-1">
                      <AlertCircle className="w-4 h-4 text-red-500" />
                      <span className="text-xs text-red-500">{uploadedFile.error}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

            <div className="mt-6 flex items-center justify-end space-x-3">
              <button
                onClick={clearAll}
                className="btn-secondary"
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={isUploading || uploadedFiles.length === 0}
                className="btn-primary"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Documents
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Instructions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Upload Guidelines
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">
              Supported Formats
            </h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• PDF documents</li>
              <li>• Word documents (.doc, .docx)</li>
              <li>• Text files (.txt, .md)</li>
              <li>• HTML files (.html, .htm)</li>
              <li>• JSON files (.json)</li>
              <li>• CSV files (.csv)</li>
              <li>• Excel files (.xls, .xlsx)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">
              Best Practices
            </h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Use clear, descriptive filenames</li>
              <li>• Ensure documents are readable</li>
              <li>• Upload related documents together</li>
              <li>• Maximum file size: 10MB</li>
              <li>• Documents will be processed for search</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
