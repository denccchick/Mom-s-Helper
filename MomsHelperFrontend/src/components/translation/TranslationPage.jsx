import React, { useState } from 'react';
import {
  Upload,
  FileText,
  Download,
  RefreshCw,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
  FileSpreadsheet
} from 'lucide-react';
import '../../styles/components/translation/TranslationPage.css';

const TranslationPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.docx')) {
      setSelectedFile(file);
      setDownloadUrl(null);
    } else if (file) {
      alert('Выберите файл .docx');
      setSelectedFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.docx')) {
      setSelectedFile(file);
      setDownloadUrl(null);
    } else if (file) {
      alert('Нужен .docx');
    }
  };

  const handleTranslate = async () => {
    if (!selectedFile) {
      alert('Выберите файл');
      return;
    }
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    const backendUrl = window.location.origin.replace(':3000', ':8000');
    try {
      const res = await fetch(`${backendUrl}/api/v1/translation/translate-docx`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl && selectedFile) {
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `translated_${selectedFile.name}`;
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

  return (
    <div className="translation-container">
      <div className="translation-card">
        <div className="header-section">
          <FileSpreadsheet size={32} className="header-icon" />
          <h1>Перевод документов</h1>
          <p>Загрузите DOCX и получите переведённый файл</p>
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
            accept=".docx"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          {selectedFile ? (
            <div className="file-info">
              <FileText size={24} />
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              <button className="clear-btn" onClick={clearFile}>
                <X size={18} />
              </button>
            </div>
          ) : (
            <div className="drop-placeholder">
              <Upload size={48} />
              <p>Нажмите или перетащите файл</p>
              <small>Только .docx</small>
            </div>
          )}
        </div>

        <div className="button-group">
          {!downloadUrl ? (
            <button
              onClick={handleTranslate}
              disabled={!selectedFile || isLoading}
              className="primary-btn"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="spinning" />
                  <span>Переводим...</span>
                </>
              ) : (
                <span>Перевести</span>
              )}
            </button>
          ) : (
            <button onClick={handleNew} className="primary-btn">
              <span>Новый перевод</span>
            </button>
          )}
          {downloadUrl && (
            <button onClick={handleDownload} className="download-btn">
              <span>Скачать DOCX</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TranslationPage;
