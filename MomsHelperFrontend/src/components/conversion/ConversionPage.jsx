import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileText,
  Download,
  X,
  File,
  Loader2,
  ArrowRight,
  ArrowLeftRight,
  Scan,
  Eye,
  XCircle
} from 'lucide-react';
import '../../styles/components/conversion/ConversionPage.css';

const ConversionPage = () => {
  const [direction, setDirection] = useState('pdf-to-docx');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [filePath, setFilePath] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const [previewImages, setPreviewImages] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  const [isOcrMode, setIsOcrMode] = useState(false);
  const [isDownloadReady, setIsDownloadReady] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const previewContainerRef = useRef(null);
  const eventSourceRef = useRef(null);
  const requestIdRef = useRef(null);
  const xhrRef = useRef(null);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (xhrRef.current) {
        xhrRef.current.abort();
        xhrRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (previewContainerRef.current) {
      previewContainerRef.current.scrollTop = previewContainerRef.current.scrollHeight;
    }
  }, [previewImages]);

  const setDirectionMode = (mode) => {
    if (mode === direction) return;
    if (isLoading) {
      if (!confirm('Конвертация в процессе. Прервать и сменить режим?')) return;
      handleCancel();
    }
    setDirection(mode);
    setSelectedFile(null);
    setDownloadUrl(null);
    setFilePath(null);
    setProgress(0);
    setProgressStatus('');
    setPreviewImages([]);
    setShowPreview(false);
    setIsCancelled(false);
    setIsOcrMode(mode === 'pdf-to-docx-ocr');
    setIsDownloadReady(false);
    setUploadProgress(0);
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

  const handleCancel = async () => {
    if (!requestIdRef.current) return;

    setIsCancelled(true);
    setProgressStatus('Отмена операции...');

    try {
      const backendUrl = window.location.origin.replace(':3000', ':8000');
      await fetch(`${backendUrl}/api/v1/conversion/cancel/${requestIdRef.current}`, {
        method: 'POST'
      });
    } catch (e) {
      console.error('Error cancelling:', e);
    }

    if (xhrRef.current) {
      xhrRef.current.abort();
      xhrRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setIsLoading(false);
    setProgress(0);
    setProgressStatus('Отменено');
    setPreviewImages([]);
    setShowPreview(false);
    setIsDownloadReady(false);
    requestIdRef.current = null;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    const ext = getFileExtension();
    if (file && file.name.toLowerCase().endsWith(ext)) {
      setSelectedFile(file);
      setDownloadUrl(null);
      setFilePath(null);
      setProgress(0);
      setProgressStatus('');
      setPreviewImages([]);
      setShowPreview(false);
      setIsCancelled(false);
      setIsDownloadReady(false);
      setUploadProgress(0);
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
      setFilePath(null);
      setProgress(0);
      setProgressStatus('');
      setPreviewImages([]);
      setShowPreview(false);
      setIsCancelled(false);
      setIsDownloadReady(false);
      setUploadProgress(0);
    } else if (file) {
      alert(`Нужен файл ${ext.toUpperCase()}`);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank');
    }
  };

  const handleNew = () => {
    setSelectedFile(null);
    setDownloadUrl(null);
    setFilePath(null);
    setProgress(0);
    setProgressStatus('');
    setPreviewImages([]);
    setShowPreview(false);
    setIsCancelled(false);
    setIsDownloadReady(false);
    setIsLoading(false);
    setUploadProgress(0);
    document.getElementById('fileInput').value = '';
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setDownloadUrl(null);
    setFilePath(null);
    setProgress(0);
    setProgressStatus('');
    setPreviewImages([]);
    setShowPreview(false);
    setIsCancelled(false);
    setIsDownloadReady(false);
    setUploadProgress(0);
    document.getElementById('fileInput').value = '';
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      alert('Выберите файл');
      return;
    }

    setIsLoading(true);
    setIsCancelled(false);
    setProgress(0);
    setProgressStatus('Подготовка...');
    setPreviewImages([]);
    setShowPreview(false);
    setDownloadUrl(null);
    setIsDownloadReady(false);
    setUploadProgress(0);

    const backendUrl = window.location.origin.replace(':3000', ':8000');
    const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    requestIdRef.current = requestId;

    const isOcr = direction === 'pdf-to-docx-ocr';
    setIsOcrMode(isOcr);

    // Для OCR - подключаем SSE
    if (isOcr) {
      const eventSource = new EventSource(`${backendUrl}/api/v1/conversion/progress/${requestId}`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (!isCancelled) {
            setProgress(data.progress);
            if (data.status) {
              setProgressStatus(data.status);
            }
            if (data.preview) {
              setPreviewImages(prev => [...prev, data.preview]);
              setShowPreview(true);
            }
            if (data.progress >= 100) {
              setIsLoading(false);
              setIsDownloadReady(true);
              if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
              }
              fetchDownloadUrl();
            }
          }
        } catch (e) {
          console.error('Ошибка парсинга SSE:', e);
        }
      };

      eventSource.onerror = (e) => {
        if (!isCancelled && eventSourceRef.current) {
          setIsLoading(false);
        }
      };
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      let endpoint = getEndpoint();

      if (isOcr) {
        endpoint += `?request_id=${requestId}`;
      }

      const response = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhrRef.current = xhr;

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && !isCancelled) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            setUploadProgress(percentComplete);
            const totalProgress = Math.round(percentComplete * 0.3);
            setProgress(totalProgress);
            setProgressStatus(`Загрузка файла... ${percentComplete}%`);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve({
              ok: true,
              status: xhr.status,
              response: xhr.response,
              responseText: xhr.responseText,
            });
          } else {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          if (xhr.status === 0) {
            reject(new Error('Отменено пользователем'));
          } else {
            reject(new Error('Ошибка сети'));
          }
        });

        xhr.responseType = 'text';
        xhr.open('POST', `${backendUrl}${endpoint}`);
        xhr.send(formData);
      });

      if (!response.ok) {
        throw new Error('Ошибка конвертации');
      }

      const data = JSON.parse(response.responseText || '{}');

      if (data.filename) {
        const url = `${backendUrl}/api/v1/conversion/download/${encodeURIComponent(data.filename)}`;
        setDownloadUrl(url);
        setFilePath(data.file_path || data.filename);

        // Устанавливаем превью, если есть
        if (data.preview && data.preview.length > 0) {
          setPreviewImages(data.preview);
          setShowPreview(true);
        }

        // Если это не OCR - прогресс 100%
        if (!isOcr) {
          setProgress(100);
          setProgressStatus('Готово!');
          setIsLoading(false);
          setIsDownloadReady(true);
        }
      }

    } catch (error) {
      console.error('Conversion error:', error);
      if (error.message === 'Отменено пользователем' || isCancelled) {
        setProgressStatus('Отменено');
      } else {
        alert(`Ошибка: ${error.message}`);
        setProgress(0);
        setProgressStatus('');
        setPreviewImages([]);
        setShowPreview(false);
      }
      setIsLoading(false);
      setIsDownloadReady(false);
    } finally {
      if (!isOcr) {
        setIsLoading(false);
      }
    }
  };

  const fetchDownloadUrl = async () => {
    try {
      const backendUrl = window.location.origin.replace(':3000', ':8000');
      const response = await fetch(`${backendUrl}/api/v1/conversion/files`);
      const data = await response.json();

      if (data.files && data.files.length > 0) {
        const latestFile = data.files[data.files.length - 1];
        if (latestFile.name.includes('ocr')) {
          const url = `${backendUrl}/api/v1/conversion/download/${encodeURIComponent(latestFile.name)}`;
          setDownloadUrl(url);
          setIsDownloadReady(true);
        }
      }
    } catch (e) {
      console.error('Error fetching files:', e);
    }
  };

  const fromLabel = direction.includes('pdf-to-docx') ? 'PDF' : 'DOCX';
  const toLabel = direction.includes('pdf-to-docx') ? 'DOCX' : 'PDF';

  return (
    <div className="conversion-container">
      <div className={`conversion-wrapper ${showPreview && previewImages.length > 0 ? 'has-preview' : ''}`}>
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

          {(isLoading || progress > 0 || uploadProgress > 0) && (
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <div className="progress-info">
                <span className="progress-text">{progress}%</span>
                <span className="progress-status">{progressStatus}</span>
                {isOcrMode && isLoading && (
                  <button onClick={handleCancel} className="cancel-btn" title="Отменить">
                    <XCircle size={18} />
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="button-group">
            {!downloadUrl || !isDownloadReady ? (
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
            {downloadUrl && isDownloadReady && (
              <button onClick={handleDownload} className="download-btn">
                <Download size={18} />
                <span>Скачать {toLabel}</span>
              </button>
            )}
          </div>
        </div>

        {showPreview && previewImages.length > 0 && (
          <div className={`preview-sidebar ${showPreview && previewImages.length > 0 ? 'visible' : ''}`}>
            <div className="preview-header">
              <Eye size={16} />
              <h4>Предпросмотр</h4>
              <span className="preview-count">{previewImages.length} стр.</span>
            </div>
            <div className="preview-scroll" ref={previewContainerRef}>
              {previewImages.map((imgData, idx) => (
                <div key={idx} className="preview-page">
                  <img
                    src={`data:image/jpeg;base64,${imgData.base64}`}
                    alt={`Страница ${idx + 1}`}
                    style={{
                      width: '100%',
                      height: 'auto',
                      aspectRatio: imgData.width / imgData.height
                    }}
                    loading="lazy"
                  />
                  <span>Страница {idx + 1}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversionPage;
