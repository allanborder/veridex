import React, { useState, useEffect, useRef } from 'react';
import { 
  fetchDocuments, 
  uploadMultipleDocuments, 
  deleteDocument, 
  reindexDocuments, 
  downloadDocument 
} from '../services/api';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  RefreshCw, 
  Download, 
  Eye, 
  Loader2, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';
import SourceModal from './SourceModal';

export default function KnowledgeView() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [viewingFile, setViewingFile] = useState(null);
  const [reindexing, setReindexing] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFiles = async (fileList) => {
    if (!fileList || !fileList.length) return;
    const files = Array.from(fileList);

    setUploadStatus({ state: 'uploading', message: 'Uploading document…' });

    const tExtract = setTimeout(() => {
      setUploadStatus({ state: 'extracting', message: 'Processing document…' });
    }, 400);

    const tIndex = setTimeout(() => {
      setUploadStatus({ state: 'indexing', message: 'Indexing and generating embeddings…' });
    }, 900);

    try {
      await uploadMultipleDocuments(files);
      clearTimeout(tExtract);
      clearTimeout(tIndex);
      setUploadStatus({ state: 'ready', message: 'Document ready and indexed.' });
      await loadData();
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err) {
      clearTimeout(tExtract);
      clearTimeout(tIndex);
      setUploadStatus({ state: 'failed', message: err.message || 'Failed to process document.' });
    }
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete "${filename}" from authorized knowledge base?`)) return;
    try {
      await deleteDocument(filename);
      await loadData();
    } catch (err) {
      alert(`Could not delete document: ${err.message}`);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await reindexDocuments();
      await loadData();
    } catch (err) {
      alert(`Reindex failed: ${err.message}`);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div style={{ maxWidth: '780px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingTop: '0.5rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.25rem 0', color: '#fff', letterSpacing: '-0.02em' }}>
            Knowledge
          </h2>
          <p style={{ color: '#8E8E93', margin: 0, fontSize: '0.86rem' }}>
            Authorized repository of documents used to ground question answers.
          </p>
        </div>

        <button
          onClick={handleReindex}
          disabled={reindexing || loading}
          className="apple-btn"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '12px',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#8E8E93',
            fontSize: '0.8rem',
            cursor: reindexing ? 'wait' : 'pointer'
          }}
        >
          <RefreshCw size={13} className={reindexing ? 'animate-spin' : ''} />
          {reindexing ? 'Reindexing…' : 'Reindex'}
        </button>
      </div>

      {/* Upload Drop Area (Apple Spatial Glass) */}
      <div
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
        }}
        className="apple-glass"
        style={{
          border: isDragOver ? '1.5px dashed #0A84FF' : '1.5px dashed rgba(255, 255, 255, 0.15)',
          borderRadius: '20px',
          padding: '2.25rem 1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.6rem',
          backgroundColor: isDragOver ? 'rgba(10, 132, 255, 0.06)' : 'var(--glass-bg)',
          transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
          multiple
          onChange={(e) => {
            if (e.target.files.length) handleFiles(e.target.files);
            e.target.value = '';
          }}
        />
        <UploadCloud size={30} color={isDragOver ? '#0A84FF' : '#8E8E93'} />
        <div style={{ color: '#fff', fontSize: '0.96rem', fontWeight: 600 }}>
          {isDragOver ? 'Release to upload' : 'Add knowledge'}
        </div>
        <div style={{ color: '#8E8E93', fontSize: '0.78rem' }}>
          PDF, DOCX, XLSX, CSV, TXT, MD
        </div>
      </div>

      {/* Upload Progress Status */}
      {uploadStatus && (
        <div
          className="apple-glass"
          style={{
            padding: '10px 14px',
            borderRadius: '14px',
            backgroundColor: uploadStatus.state === 'failed' ? 'rgba(255, 69, 58, 0.08)' : 'rgba(10, 132, 255, 0.08)',
            border: `1px solid ${uploadStatus.state === 'failed' ? 'rgba(255, 69, 58, 0.22)' : 'rgba(10, 132, 255, 0.22)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.84rem',
            color: uploadStatus.state === 'failed' ? '#FF453A' : '#70b4ff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {uploadStatus.state === 'ready' ? (
              <CheckCircle2 size={16} color="#30D158" />
            ) : uploadStatus.state === 'failed' ? (
              <AlertCircle size={16} color="#FF453A" />
            ) : (
              <Loader2 size={16} className="animate-spin" />
            )}
            <span>{uploadStatus.message}</span>
          </div>

          {uploadStatus.state === 'failed' && (
            <button
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
              className="apple-btn"
              style={{
                background: 'none',
                border: 'none',
                color: '#FF453A',
                textDecoration: 'underline',
                cursor: 'pointer',
                fontSize: '0.78rem'
              }}
            >
              Try again
            </button>
          )}
        </div>
      )}

      {/* Documents List (Apple Grouped Table) */}
      <div
        className="apple-glass"
        style={{
          borderRadius: '20px',
          overflow: 'hidden'
        }}
      >
        {loading && documents.length === 0 ? (
          <div style={{ padding: '2.5rem', textAlign: 'center', color: '#8E8E93', fontSize: '0.88rem' }}>
            Loading authorized documents…
          </div>
        ) : documents.length === 0 ? (
          <div style={{ padding: '2.5rem', textAlign: 'center', color: '#8E8E93', fontSize: '0.88rem' }}>
            No documents in knowledge base. Upload your first document above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {documents.map((doc, idx) => {
              const ext = doc.filename.split('.').pop().toUpperCase();
              return (
                <div
                  key={doc.document_id || idx}
                  style={{
                    padding: '14px 18px',
                    borderBottom: idx < documents.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    transition: 'background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.025)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                    <FileText size={18} color="#0A84FF" />
                    <div style={{ minWidth: 0 }}>
                      <div style={{
                        color: '#ffffff',
                        fontSize: '0.88rem',
                        fontWeight: 500,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {doc.filename}
                      </div>
                      <div style={{ fontSize: '0.74rem', color: '#8E8E93', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>{ext}</span>
                        <span>&bull;</span>
                        <span>{doc.chunk_count} chunk{doc.chunk_count > 1 ? 's' : ''}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      color: '#30D158',
                      backgroundColor: 'rgba(48, 209, 88, 0.09)',
                      padding: '2px 8px',
                      borderRadius: '8px',
                      fontWeight: 600
                    }}>
                      ✓ Ready
                    </span>

                    <button
                      onClick={() => setViewingFile(doc.filename)}
                      title="View document"
                      className="apple-btn"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#8E8E93',
                        cursor: 'pointer',
                        padding: '5px'
                      }}
                    >
                      <Eye size={15} />
                    </button>

                    <button
                      onClick={() => downloadDocument(doc.filename)}
                      title="Download document"
                      className="apple-btn"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#8E8E93',
                        cursor: 'pointer',
                        padding: '5px'
                      }}
                    >
                      <Download size={15} />
                    </button>

                    <button
                      onClick={() => handleDelete(doc.filename)}
                      title="Delete document"
                      className="apple-btn"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'rgba(255, 69, 58, 0.7)',
                        cursor: 'pointer',
                        padding: '5px'
                      }}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {viewingFile && (
        <SourceModal filename={viewingFile} onClose={() => setViewingFile(null)} />
      )}

    </div>
  );
}
