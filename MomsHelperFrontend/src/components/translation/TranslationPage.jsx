import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  FileText,
  Download,
  X,
  Loader2,
  FileSpreadsheet,
  Zap,
  Gauge,
  Target,
  Eye,
  XCircle,
  Turtle
} from 'lucide-react';
import '../../styles/components/translation/TranslationPage.css';

const TranslationPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [beamMode, setBeamMode] = useState(2);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const [previewParagraphs, setPreviewParagraphs] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  const [isDownloadReady, setIsDownloadReady] = useState(false);

  const previewContainerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const readerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (readerRef.current) {
        readerRef.current.cancel();
      }
    };
  }, []);

  useEffect(() => {
    if (previewContainerRef.current) {
      previewContainerRef.current.scrollTop = previewContainerRef.current.scrollHeight;
    }
  }, [previewParagraphs]);

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (readerRef.current) {
      readerRef.current.cancel();
    }
    setIsCancelled(true);
    setIsLoading(false);
    setProgress(0);
    setProgressStatus('Отменено');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.toLowerCase().endsWith('.docx')) {
      setSelectedFile(file);
      setDownloadUrl(null);
      setProgress(0);
      setProgressStatus('');
      setPreviewParagraphs([]);
      setShowPreview(false);
      setIsCancelled(false);
      setIsDownloadReady(false);
    } else if (file) {
      alert('Выберите файл .docx');
      setSelectedFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.toLowerCase().endsWith('.docx')) {
      setSelectedFile(file);
      setDownloadUrl(null);
      setProgress(0);
      setProgressStatus('');
      setPreviewParagraphs([]);
      setShowPreview(false);
      setIsCancelled(false);
      setIsDownloadReady(false);
    } else if (file) {
      alert('Нужен .docx');
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const backendUrl = 'http://127.0.0.1:8000';
      window.open(`${backendUrl}${downloadUrl}`, '_blank');
    }
  };

  const handleNew = () => {
    setSelectedFile(null);
    setDownloadUrl(null);
    setProgress(0);
    setProgressStatus('');
    setPreviewParagraphs([]);
    setShowPreview(false);
    setIsCancelled(false);
    setIsDownloadReady(false);
    setIsLoading(false);
    document.getElementById('fileInput').value = '';
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setDownloadUrl(null);
    setProgress(0);
    setProgressStatus('');
    setPreviewParagraphs([]);
    setShowPreview(false);
    setIsCancelled(false);
    setIsDownloadReady(false);
    document.getElementById('fileInput').value = '';
  };

  const handleTranslate = async () => {
    if (!selectedFile) {
      alert('Выберите файл');
      return;
    }

    setIsLoading(true);
    setIsCancelled(false);
    setProgress(0);
    setProgressStatus('Подготовка...');
    setPreviewParagraphs([]);
    setShowPreview(false);
    setDownloadUrl(null);
    setIsDownloadReady(false);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('num_beams', String(beamMode));
    const backendUrl = 'http://127.0.0.1:8000';

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${backendUrl}/api/v1/translation/translate-docx`, {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Ошибка');
      }

      const reader = response.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Разбиваем по \n\n для SSE
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const lines = event.split('\n');
          let dataLine = '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              dataLine = line.slice(6);
              break;
            }
          }

          if (!dataLine) continue;

          try {
            const data = JSON.parse(dataLine);

            if (data.error) {
              if (data.cancelled) {
                setProgressStatus('Отменено');
              } else {
                alert(`Ошибка: ${data.error}`);
              }
              setIsLoading(false);
              return;
            }

            if (data.done) {
              setDownloadUrl(data.download_url);
              setProgress(100);
              setProgressStatus('Готово!');
              setIsLoading(false);
              setIsDownloadReady(true);
              return;
            }

            if (data.progress !== undefined) {
              setProgress(data.progress);
            }
            if (data.status) {
              setProgressStatus(data.status);
            }

            if (data.preview) {
              setPreviewParagraphs(prev => [...prev, {
                index: data.preview.paragraph_index || prev.length,
                original: data.preview.original || '',
                translated: data.preview.translated || '',
              }]);
              setShowPreview(true);
            }
          } catch (e) {
            console.error('Parse error:', e, 'Data:', dataLine);
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setProgressStatus('Отменено');
      } else {
        if (!isCancelled) {
          console.error('Translation error:', err);
          alert(`Ошибка: ${err.message}`);
        }
      }
      setIsLoading(false);
    }
  };

  const translationModes = [
    { value: 1, label: 'Быстро', icon: Zap },
    { value: 2, label: 'Баланс', icon: Gauge },
    { value: 4, label: 'Точно', icon: Turtle },
  ];

  return (
    <div className="translation-container">
      <div className={`translation-wrapper ${showPreview && previewParagraphs.length > 0 ? 'has-preview' : ''}`}>
        <div className="translation-card">
          <div className="header-section">
            <FileSpreadsheet size={32} className="header-icon" />
            <h1>Перевод документов</h1>
            <p>Загрузите DOCX и получите переведённый файл</p>
          </div>

          <div className="translation-mode-badges">
            {translationModes.map((mode) => {
              const Icon = mode.icon;
              return (
                <button
                  key={mode.value}
                  className={`translation-mode-badge ${beamMode === mode.value ? 'active' : ''}`}
                  onClick={() => setBeamMode(mode.value)}
                  disabled={isLoading}
                >
                  <Icon size={18} />
                  <span>{mode.label}</span>
                </button>
              );
            })}
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
              disabled={isLoading}
            />
            {selectedFile ? (
              <div className="file-info">
                <FileText size={24} />
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                {!isLoading && (
                  <button className="clear-btn" onClick={clearFile}>
                    <X size={18} />
                  </button>
                )}
              </div>
            ) : (
              <div className="drop-placeholder">
                <Upload size={48} />
                <p>Нажмите или перетащите файл</p>
                <small>Только .docx</small>
              </div>
            )}
          </div>

          {(isLoading || progress > 0) && (
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <div className="progress-info">
                <span className="progress-text">{progress}%</span>
                <span className="progress-status">{progressStatus}</span>
                {isLoading && (
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
            {downloadUrl && isDownloadReady && (
              <button onClick={handleDownload} className="download-btn">
                <Download size={18} />
                <span>Скачать DOCX</span>
              </button>
            )}
          </div>
        </div>

        {showPreview && previewParagraphs.length > 0 && (
          <div className={`preview-sidebar ${showPreview && previewParagraphs.length > 0 ? 'visible' : ''}`}>
            <div className="preview-header">
              <Eye size={16} />
              <h4>Живой перевод</h4>
              <span className="preview-count">{previewParagraphs.length} абз.</span>
            </div>
            <div className="preview-scroll" ref={previewContainerRef}>
              {previewParagraphs.map((item, idx) => (
                <div key={idx} className="preview-paragraph">
                  <div className="original-text">{item.original || '...'}</div>
                  <div className="arrow-translation">↓</div>
                  <div className="translated-text">{item.translated || 'Переводится...'}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TranslationPage;
