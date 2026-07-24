import React, { useState } from 'react';
import {
  Upload,
  FileText,
  Download,
  X,
  File,
  Loader2,
  ArrowRight,
  ArrowLeftRight,
  Scan
} from 'lucide-react';
import '../../styles/components/conversion/ConversionPage.css';

const ConversionPage = () => {
  const [direction, setDirection] = useState('pdf-to-docx');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const setDirectionMode = (mode) => {
    if (mode === direction) return;
    setDirection(mode);
    setSelectedFile(null);
    setDownloadUrl(null);
    document.getElementById('fileInput').value = '';
  };

  const getFileExtension = () => {
    return direction.includes('pdf-to-docx') ? '.pdf' : '.docx';
  };

  const getAccept = () => {
    return direction.includes('pdf-to-docx') ? '.pdf' : '.docx';
  };

  const getEndpoint = () => {
    if (direction === 'pdf-to-docx') return '/api/v1/conversion/pdf-to-docx';
    if (direction === 'pdf-to-docx-ocr') return '/api/v1/conversion/pdf-to-docx-ocr';
    return '/api/v1/conversion/docx-to-pdf';
  };

  const getOutputExtension = () => {
    return direction.includes('pdf-to-docx') ? '.docx' : '.pdf';
  };

  const getIcon = () => {
    return direction.includes('pdf-to-docx') ? <File size={24} /> : <FileText size={24} />;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    const ext = getFileExtension();
    if (file && file.name.toLowerCase().endsWith(ext)) {
      setSelectedFile(file);
      setDownloadUrl(null);
    } else if (file) {
      alert(`Нужен файл ${ext.toUpperCase()}`);
      setSelectedFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    const ext = getFileExtension();
    if (file && file.name.toLowerCase().endsWith(ext)) {
      setSelectedFile(file);
      setDownloadUrl(null);
    } else if (file) {
      alert(`Нужен файл ${ext.toUpperCase()}`);
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      alert('Выберите файл');
      return;
    }

    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    const backendUrl = window.location.origin.replace(':3000', ':8000');

    try {
      const response = await fetch(`${backendUrl}${getEndpoint()}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
    } catch (error) {
      alert(`Ошибка: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl && selectedFile) {
      const a = document.createElement('a');
      a.href = downloadUrl;
      const base = selectedFile.name.replace(/\.[^.]+$/, '');
      const suffix = direction === 'pdf-to-docx-ocr' ? '_ocr' : '_converted';
      a.download = `${base}${suffix}${getOutputExtension()}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }
  };

  const handleNew = () => {
    setSelectedFile(null);
    setDownloadUrl(null);
    document.getElementById('fileInput').value = '';
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    document.getElementById('fileInput').value = '';
  };

  const fromLabel = direction.includes('pdf-to-docx') ? 'PDF' : 'DOCX';
  const toLabel = direction.includes('pdf-to-docx') ? 'DOCX' : 'PDF';

  return (
    <div className="conversion-container">
      <div className="conversion-card">
        <div className="header-section">
          <ArrowLeftRight size={32} className="header-icon" />
          <h1>Конвертер документов</h1>
          <p>Конвертируйте документы и распознавайте сканы</p>
        </div>

        <div className="direction-badges">
          <button
            className={`direction-badge ${direction === 'pdf-to-docx' ? 'active' : ''}`}
            onClick={() => setDirectionMode('pdf-to-docx')}
          >
            <File size={18} />
            <span>PDF</span>
            <ArrowRight size={14} className="badge-arrow" />
            <FileText size={18} />
            <span>DOCX</span>
          </button>

          <button
            className={`direction-badge ${direction === 'pdf-to-docx-ocr' ? 'active' : ''}`}
            onClick={() => setDirectionMode('pdf-to-docx-ocr')}
          >
            <Scan size={18} />
            <span>PDF (Скан)</span>
            <ArrowRight size={14} className="badge-arrow" />
            <FileText size={18} />
            <span>DOCX</span>
          </button>

          <button
            className={`direction-badge ${direction === 'docx-to-pdf' ? 'active' : ''}`}
            onClick={() => setDirectionMode('docx-to-pdf')}
          >
            <FileText size={18} />
            <span>DOCX</span>
            <ArrowRight size={14} className="badge-arrow" />
            <File size={18} />
            <span>PDF</span>
          </button>
        </div>

        <div
          className={`drop-zone ${selectedFile ? 'has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => document.getElementById('fileInput').click()}
        >
          <input
            type="file"
            id="fileInput"
            accept={getAccept()}
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          {selectedFile ? (
            <div className="file-info">
              {getIcon()}
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              <button className="clear-btn" onClick={clearFile}>
                <X size={18} />
              </button>
            </div>
          ) : (
            <div className="drop-placeholder">
              <Upload size={48} />
              <p>Нажмите или перетащите файл {fromLabel}</p>
              <small>Только .{fromLabel.toLowerCase()}</small>
            </div>
          )}
        </div>

        <div className="button-group">
          {!downloadUrl ? (
            <button
              onClick={handleConvert}
              disabled={!selectedFile || isLoading}
              className="primary-btn"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="spinning" />
                  <span>{direction === 'pdf-to-docx-ocr' ? 'Распознаем...' : 'Конвертируем...'}</span>
                </>
              ) : (
                <span>Конвертировать</span>
              )}
            </button>
          ) : (
            <button onClick={handleNew} className="primary-btn">
              <span>Новый файл</span>
            </button>
          )}
          {downloadUrl && (
            <button onClick={handleDownload} className="download-btn">
              <Download size={18} />
              <span>Скачать {toLabel}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversionPage;
