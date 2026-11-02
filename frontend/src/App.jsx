
import { useEffect, useState } from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  Search,
  LockKeyhole,
  Activity,
  Globe,
  ArrowUpRight,
  AlertTriangle,
  CheckCircle2,
  LoaderCircle,
  ScanSearch,
  MessageSquareText,
  Link2,
  QrCode,
  ImagePlus,
  X,
  Wallet,
  Upload
} from 'lucide-react'

import './App.css'

const URL_API = 'http://127.0.0.1:8000/api/scan/analyze'
const MESSAGE_API = 'http://127.0.0.1:8000/api/message/analyze'
const QR_API = 'http://127.0.0.1:8000/api/qr/analyze'

function App() {
  const [mode, setMode] = useState('url')

  const [url, setUrl] = useState('')
  const [message, setMessage] = useState('')

  const [qrFile, setQrFile] = useState(null)
  const [qrPreview, setQrPreview] = useState('')
  const [dragging, setDragging] = useState(false)

  const [result, setResult] = useState(null)
  const [qrResult, setQrResult] = useState(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    return () => {
      if (qrPreview) {
        URL.revokeObjectURL(qrPreview)
      }
    }
  }, [qrPreview])

  const resetResult = (nextMode) => {
    setMode(nextMode)
    setResult(null)
    setQrResult(null)
    setError('')
  }

  const handleQrFile = (file) => {
    if (!file) return

    if (!['image/png', 'image/jpeg'].includes(file.type)) {
      setError('Please upload a PNG or JPEG image.')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image size must not exceed 5 MB.')
      return
    }

    setQrFile(file)
    setQrPreview(URL.createObjectURL(file))
    setQrResult(null)
    setError('')
  }

  const removeQrFile = () => {
    setQrFile(null)
    setQrPreview('')
    setQrResult(null)
    setError('')
  }

  const handleScan = async (event) => {
    event.preventDefault()

    const submittedUrl = url.trim()

    if (!submittedUrl) {
      setError('Please enter a URL to scan.')
      return
    }

    try {
      const parsed = new URL(submittedUrl)

      if (!['http:', 'https:'].includes(parsed.protocol)) {
        setError('Only HTTP and HTTPS URLs are supported.')
        return
      }
    } catch {
      setError('Please enter a valid URL, including https:// or http://.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(URL_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: submittedUrl })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'URL analysis failed.')
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot connect to Deceptrix API. Make sure the backend is running.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  const handleMessageScan = async (event) => {
    event.preventDefault()

    const submittedMessage = message.trim()

    if (!submittedMessage) {
      setError('Please paste a message to analyze.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(MESSAGE_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: submittedMessage })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Message analysis failed.')
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot connect to Deceptrix API. Make sure the backend is running.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  const handleQrScan = async () => {
    if (!qrFile) {
      setError('Please upload a QR code image.')
      return
    }

    setLoading(true)
    setError('')
    setQrResult(null)

    try {
      const formData = new FormData()
      formData.append('file', qrFile)

      const response = await fetch(QR_API, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'QR analysis failed.')
      }

      setQrResult(data)
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot connect to Deceptrix API. Make sure the backend is running.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  const formatScore = (score) => {
    const value = Number(score)

    return Number.isFinite(value)
      ? `${(value * 100).toFixed(2)}%`
      : 'N/A'
  }

  const formatRisk = (score) => {
    const value = Number(score)

    return Number.isFinite(value)
      ? value.toFixed(2)
      : 'N/A'
  }

  const isUrlMode = mode === 'url'
  const isMessageMode = mode === 'message'
  const isQrMode = mode === 'qr'

  const urlAssessment = result?.overall_assessment
  const urlMlResult = result?.analysis?.url_ml?.result
  const isPhishing = urlAssessment?.model_prediction === 'phishing'
  const isSpam = result?.message_assessment === 'spam'

  const qrUrlResult = qrResult?.url_analysis
  const qrIsPhishing = qrUrlResult?.prediction === 'phishing'

  const renderRiskBar = (score, dangerous) => (
    <div className="risk-track">
      <div
        className={`risk-fill ${dangerous ? 'fill-danger' : 'fill-safe'}`}
        style={{
          width: `${Math.min(100, Math.max(0, Number(score) || 0))}%`
        }}
      />
    </div>
  )

  return (
    <div className="app">
      <nav className="navbar">
        <a href="/" className="brand">
          <div className="brand-icon">
            <ShieldCheck size={23} />
          </div>
          <span>
            deceptrix<span className="brand-dot">.</span>
          </span>
        </a>

        <div className="nav-right">
          <span className="nav-status">
            <span className="status-dot" />
            Detection system active
          </span>
          <span className="version">AI ENGINE v1.0</span>
        </div>
      </nav>

      <main>
        <section className="hero">
          <div className="eyebrow">
            <span className="eyebrow-line" />
            AI-POWERED CYBERSECURITY
            <span className="eyebrow-line" />
          </div>

          <h1>
            Don't trust the link.
            <br />
            <span>Verify it first.</span>
          </h1>

          <p className="hero-description">
            Detect suspicious URLs, fraudulent messages and potentially
            malicious QR codes using machine learning.
          </p>

          <div className="scanner-card">
            <div className="scanner-heading">
              <div className="scanner-heading-icon">
                {isUrlMode && <ScanSearch size={19} />}
                {isMessageMode && <MessageSquareText size={19} />}
                {isQrMode && <QrCode size={19} />}
              </div>

              <div>
                <h2>
                  {isUrlMode && 'URL Security Scanner'}
                  {isMessageMode && 'Message Security Scanner'}
                  {isQrMode && 'QR Security Scanner'}
                </h2>

                <p>
                  {isUrlMode && 'Analyze a suspicious URL instantly'}
                  {isMessageMode && 'Analyze message content and embedded links'}
                  {isQrMode && 'Upload and inspect a suspicious QR code'}
                </p>
              </div>

              <span className="scanner-badge">LIVE SCANNER</span>
            </div>

            <div className="scanner-tabs">
              <button
                type="button"
                className={`scanner-tab ${isUrlMode ? 'active' : ''}`}
                onClick={() => resetResult('url')}
                disabled={loading}
              >
                <Globe size={16} />
                URL Scanner
              </button>

              <button
                type="button"
                className={`scanner-tab ${isMessageMode ? 'active' : ''}`}
                onClick={() => resetResult('message')}
                disabled={loading}
              >
                <MessageSquareText size={16} />
                Message Scanner
              </button>

              <button
                type="button"
                className={`scanner-tab ${isQrMode ? 'active' : ''}`}
                onClick={() => resetResult('qr')}
                disabled={loading}
              >
                <QrCode size={16} />
                QR Scanner
              </button>
            </div>

            {isUrlMode && (
              <form onSubmit={handleScan}>
                <label htmlFor="url-input">Enter website URL</label>

                <div className="input-wrapper">
                  <Globe size={19} className="input-icon" />

                  <input
                    id="url-input"
                    type="text"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(event) => {
                      setUrl(event.target.value)
                      setError('')
                    }}
                    disabled={loading}
                  />

                  <button type="submit" disabled={loading || !url.trim()}>
                    {loading ? (
                      <>
                        <LoaderCircle className="spin" size={17} />
                        Scanning
                      </>
                    ) : (
                      <>
                        <Search size={17} />
                        Scan URL
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {isMessageMode && (
              <form onSubmit={handleMessageScan}>
                <label htmlFor="message-input">Paste your message</label>

                <textarea
                  id="message-input"
                  className="message-input"
                  placeholder="Paste an SMS, WhatsApp message, email text or any suspicious message here..."
                  value={message}
                  onChange={(event) => {
                    setMessage(event.target.value)
                    setError('')
                  }}
                  disabled={loading}
                  maxLength={10000}
                />

                <div className="message-form-footer">
                  <span>{message.length}/10000 characters</span>

                  <button
                    type="submit"
                    disabled={loading || !message.trim()}
                  >
                    {loading ? (
                      <>
                        <LoaderCircle className="spin" size={17} />
                        Analyzing
                      </>
                    ) : (
                      <>
                        <Search size={17} />
                        Analyze Message
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {isQrMode && (
              <div>
                <label className="upload-title">Upload QR code image</label>

                <div
                  className={`qr-upload-area ${dragging ? 'dragging' : ''}`}
                  onDragOver={(event) => {
                    event.preventDefault()
                    setDragging(true)
                  }}
                  onDragLeave={(event) => {
                    event.preventDefault()
                    setDragging(false)
                  }}
                  onDrop={(event) => {
                    event.preventDefault()
                    setDragging(false)
                    handleQrFile(event.dataTransfer.files[0])
                  }}
                >
                  <input
                    id="qr-file-input"
                    type="file"
                    accept="image/png,image/jpeg"
                    hidden
                    onChange={(event) => {
                      handleQrFile(event.target.files[0])
                      event.target.value = ''
                    }}
                  />

                  {qrPreview ? (
                    <div className="qr-preview">
                      <img
                        src={qrPreview}
                        alt="Uploaded QR code preview"
                      />

                      <strong>{qrFile?.name}</strong>

                      <button
                        type="button"
                        className="qr-remove"
                        onClick={removeQrFile}
                        disabled={loading}
                      >
                        <X size={15} />
                        Remove image
                      </button>
                    </div>
                  ) : (
                    <label
                      htmlFor="qr-file-input"
                      className="qr-upload-label"
                    >
                      <div className="qr-upload-icon">
                        <ImagePlus size={30} />
                      </div>

                      <strong>Upload your QR code</strong>

                      <span>
                        Drag and drop your image here or browse files
                      </span>

                      <small>PNG or JPEG · Maximum 5 MB</small>
                    </label>
                  )}
                </div>

                <button
                  type="button"
                  className="qr-scan-button"
                  onClick={handleQrScan}
                  disabled={loading || !qrFile}
                >
                  {loading ? (
                    <>
                      <LoaderCircle className="spin" size={17} />
                      Analyzing QR
                    </>
                  ) : (
                    <>
                      <ScanSearch size={17} />
                      Scan QR Code
                    </>
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="error-message">
                <AlertTriangle size={17} />
                {error}
              </div>
            )}

            <div className="scanner-footer">
              <span>
                <LockKeyhole size={14} />
                {isUrlMode && 'URL-based ML analysis'}
                {isMessageMode && 'Message and URL analysis'}
                {isQrMode && 'QR decoding + URL analysis'}
              </span>

              <span>
                {isUrlMode && '37 features analyzed'}
                {isMessageMode && 'Text classification + URL extraction'}
                {isQrMode && 'PNG / JPEG image analysis'}
              </span>
            </div>
          </div>
        </section>

        {loading && (
          <section className="loading-panel">
            <div className="loading-icon">
              <Activity size={25} />
            </div>

            <h3>
              {isUrlMode && 'Analyzing URL'}
              {isMessageMode && 'Analyzing Message'}
              {isQrMode && 'Analyzing QR Code'}
            </h3>

            <p>
              {isUrlMode && 'Extracting URL features and evaluating the machine learning model...'}
              {isMessageMode && 'Classifying message content and checking embedded URLs...'}
              {isQrMode && 'Decoding the QR image and analyzing its contents...'}
            </p>

            <div className="loading-bar">
              <div />
            </div>
          </section>
        )}

        {result && !loading && isUrlMode && (
  <section className={`result-card unified-result ${isPhishing ? 'danger' : 'safe'}`}>
    <div className="result-top">
      <div className="result-icon">
        {isPhishing ? <ShieldAlert size={29} /> : <ShieldCheck size={29} />}
      </div>

      <div className="result-heading">
        <span className="result-label">COMPREHENSIVE URL SCAN</span>
        <h2>
          {isPhishing
            ? 'Potential Phishing Detected'
            : 'No Strong Phishing Indicators Detected'}
        </h2>
        <p>
          {result.overall_assessment?.recommendation ||
            'Assessment based on URL machine-learning analysis and supporting DNS and SSL/TLS checks.'}
        </p>
      </div>

      <span className={`result-pill ${isPhishing ? 'pill-danger' : 'pill-safe'}`}>
        {result.overall_assessment?.risk_level ||
          (isPhishing ? 'HIGH RISK' : 'LOW RISK')}
      </span>
    </div>

    <div className="scanned-url">
      <Globe size={16} />
      <span>{result.url}</span>
      <ArrowUpRight size={15} />
    </div>

    <div className="result-metrics">
      <div className="metric">
        <span>Risk score</span>
        <strong>
          {formatRisk(urlAssessment?.risk_score)}
          <small>/100</small>
        </strong>
        {renderRiskBar(urlAssessment?.risk_score ?? 0, isPhishing)}
      </div>

      <div className="metric">
        <span>Phishing probability</span>
        <strong>{formatScore(urlAssessment?.phishing_probability)}</strong>
      </div>

      <div className="metric">
        <span>Detection model</span>
        <strong className="model-name">
          {urlMlResult?.model || 'Random Forest'}
        </strong>
      </div>

      <div className="metric">
        <span>Features evaluated</span>
        <strong>{urlMlResult?.features_used ?? 'N/A'}</strong>
      </div>
    </div>

    <div className="scan-engine-section">
      <div className="scan-section-heading">
        <h3>Security engine status</h3>
        <span>Analysis components</span>
      </div>

      <div className="engine-status-grid">
        {[
          { name: 'URL Intelligence', status: result.engine_status?.url_ml },
          { name: 'DNS Analysis', status: result.engine_status?.dns },
          { name: 'SSL / TLS Analysis', status: result.engine_status?.ssl_tls }
        ].map((engine) => (
          <div className="engine-status-card" key={engine.name}>
            <div className="engine-status-heading">
              <span>{engine.name}</span>
              {engine.status === 'completed' ? (
                <CheckCircle2 size={17} />
              ) : (
                <AlertTriangle size={17} />
              )}
            </div>
            <strong className={`engine-status-value status-${engine.status || 'unavailable'}`}>
              {(engine.status || 'unavailable').replaceAll('_', ' ')}
            </strong>
          </div>
        ))}
      </div>
    </div>

    <div className="scan-engine-section">
      <div className="scan-section-heading">
        <h3>Security evidence</h3>
        <span>{result.evidence_summary?.total ?? result.evidence?.length ?? 0} observations</span>
      </div>

      {Array.isArray(result.evidence) && result.evidence.length > 0 ? (
        <div className="evidence-list">
          {result.evidence.map((item, index) => (
            <div
              className={`evidence-item evidence-${item.severity || 'informational'}`}
              key={`${item.title || item.message || 'evidence'}-${index}`}
            >
              <div className="evidence-indicator">
                {item.severity === 'high' ? (
                  <ShieldAlert size={18} />
                ) : item.severity === 'medium' ? (
                  <AlertTriangle size={18} />
                ) : (
                  <CheckCircle2 size={18} />
                )}
              </div>

              <div className="evidence-content">
                <div className="evidence-heading">
                  <strong>{item.title || item.message || 'Security observation'}</strong>
                  <span className="evidence-severity">
                    {item.severity || 'informational'}
                  </span>
                </div>
                {item.description && <p>{item.description}</p>}
                {item.details && <p>{item.details}</p>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="no-evidence">No additional security evidence was returned.</p>
      )}
    </div>

    {result.notice && (
      <div className="assessment-recommendation">
        <AlertTriangle size={18} />
        <p>{result.notice}</p>
      </div>
    )}

    <div className="result-disclaimer">
      Automated security assessment. A low risk score does not guarantee that a URL is safe.
    </div>
  </section>
)}

        {result && !loading && isMessageMode && (
          <section className="message-results">
            <div className={`result-card ${isSpam ? 'danger' : 'safe'}`}>
              <div className="result-top">
                <div className="result-icon">
                  {isSpam
                    ? <ShieldAlert size={29} />
                    : <ShieldCheck size={29} />}
                </div>

                <div className="result-heading">
                  <span className="result-label">MESSAGE SCAN RESULT</span>

                  <h2>
                    {isSpam
                      ? 'Potential Spam Detected'
                      : 'Model Classified as Legitimate'}
                  </h2>

                  <p>
                    {isSpam
                      ? 'The model identified patterns associated with spam messages.'
                      : 'The model did not identify strong spam indicators in this message.'}
                  </p>
                </div>

                <span className={`result-pill ${isSpam ? 'pill-danger' : 'pill-safe'}`}>
                  {isSpam ? 'SPAM' : 'LEGITIMATE'}
                </span>
              </div>

              <div className="message-preview">
                <MessageSquareText size={17} />
                <p>{message}</p>
              </div>

              <div className="result-metrics">
                <div className="metric">
                  <span>Spam risk score</span>
                  <strong>{formatRisk(result.risk_score)}<small>/100</small></strong>
                  {renderRiskBar(result.risk_score, isSpam)}
                </div>

                <div className="metric">
                  <span>Spam probability</span>
                  <strong>{formatScore(result.spam_probability)}</strong>
                </div>

                <div className="metric">
                  <span>Detection model</span>
                  <strong className="model-name">{result.model}</strong>
                </div>

                <div className="metric">
                  <span>Embedded URLs found</span>
                  <strong>{result.urls_found}</strong>
                </div>
              </div>

              <div className="result-disclaimer">
                <AlertTriangle size={17} />
                <p>
                  This model is trained for SMS spam classification.
                  Its result is not a definitive phishing verdict.
                </p>
              </div>
            </div>

            <div className="embedded-links-section">
              <div className="embedded-links-heading">
                <div>
                  <span className="result-label">LINK ANALYSIS</span>
                  <h2>Embedded URL Analysis</h2>
                </div>

                <span className="link-count">
                  {result.urls_found} URL{result.urls_found === 1 ? '' : 's'} found
                </span>
              </div>

              {result.urls_found === 0 ? (
                <div className="no-links">
                  <Link2 size={24} />
                  <p>No URLs were found in this message.</p>
                </div>
              ) : (
                <div className="url-analysis-list">
                  {result.url_analysis.map((item, index) => {
                    const phishing = item.prediction === 'phishing'

                    return (
                      <article
                        className={`url-analysis-card ${phishing ? 'danger' : 'safe'}`}
                        key={`${item.url}-${index}`}
                      >
                        <div className="url-analysis-top">
                          <div className="url-analysis-icon">
                            {phishing
                              ? <ShieldAlert size={21} />
                              : <ShieldCheck size={21} />}
                          </div>

                          <div className="url-analysis-content">
                            <span className="result-label">EXTRACTED URL</span>
                            <p>{item.url}</p>
                          </div>

                          <span className={`result-pill ${phishing ? 'pill-danger' : 'pill-safe'}`}>
                            {item.error
                              ? 'ERROR'
                              : phishing ? 'PHISHING' : 'LEGITIMATE'}
                          </span>
                        </div>

                        {item.error ? (
                          <p className="url-error">{item.error}</p>
                        ) : (
                          <div className="url-analysis-metrics">
                            <div>
                              <span>Phishing probability</span>
                              <strong>{formatScore(item.phishing_probability)}</strong>
                            </div>

                            <div>
                              <span>Risk score</span>
                              <strong>{formatRisk(item.risk_score)}/100</strong>
                            </div>

                            <div>
                              <span>Model</span>
                              <strong>{item.model}</strong>
                            </div>

                            <div>
                              <span>Features</span>
                              <strong>{item.features_used}</strong>
                            </div>
                          </div>
                        )}
                      </article>
                    )
                  })}
                </div>
              )}

              <div className="result-disclaimer">
                <AlertTriangle size={17} />
                <p>
                  Embedded URLs are analyzed using URL characteristics only.
                  Deceptrix does not automatically open or visit these links.
                </p>
              </div>
            </div>
          </section>
        )}

        {qrResult && !loading && isQrMode && (
          <section className="qr-results">
            <div className="result-card">
              <div className="result-top">
                <div className="result-icon">
                  <QrCode size={29} />
                </div>

                <div className="result-heading">
                  <span className="result-label">QR SCAN RESULT</span>
                  <h2>QR Code Successfully Decoded</h2>
                  <p>Deceptrix extracted the encoded content.</p>
                </div>

                <span className="result-pill pill-safe">DECODED</span>
              </div>

              <div className="qr-payload">
                <span className="result-label">PAYLOAD TYPE</span>

                <h3>
                  {qrResult.payload_type?.replaceAll('_', ' ').toUpperCase()}
                </h3>

                {qrResult.decoded_url && (
                  <p>{qrResult.decoded_url}</p>
                )}

                {qrResult.decoded_text && (
                  <p>{qrResult.decoded_text}</p>
                )}
              </div>

              {qrUrlResult && (
                <div className={`url-analysis-card ${qrIsPhishing ? 'danger' : 'safe'}`}>
                  <div className="url-analysis-top">
                    <div className="url-analysis-icon">
                      {qrIsPhishing
                        ? <ShieldAlert size={21} />
                        : <ShieldCheck size={21} />}
                    </div>

                    <div className="url-analysis-content">
                      <span className="result-label">URL SECURITY ASSESSMENT</span>
                      <p>
                        {qrIsPhishing
                          ? 'Potential Phishing Detected'
                          : 'Model Classified as Legitimate'}
                      </p>
                    </div>

                    <span className={`result-pill ${qrIsPhishing ? 'pill-danger' : 'pill-safe'}`}>
                      {qrUrlResult.prediction?.toUpperCase()}
                    </span>
                  </div>

                  <div className="url-analysis-metrics">
                    <div>
                      <span>Phishing probability</span>
                      <strong>{formatScore(qrUrlResult.phishing_probability)}</strong>
                    </div>

                    <div>
                      <span>Risk score</span>
                      <strong>{formatRisk(qrUrlResult.risk_score)}/100</strong>
                    </div>

                    <div>
                      <span>Detection model</span>
                      <strong>{qrUrlResult.model}</strong>
                    </div>

                    <div>
                      <span>Features evaluated</span>
                      <strong>{qrUrlResult.features_used}</strong>
                    </div>
                  </div>
                </div>
              )}

              {qrResult.error && (
                <div className="error-message">
                  <AlertTriangle size={17} />
                  {qrResult.error}
                </div>
              )}

              {qrResult.payment_details && (
                <div className="qr-payload">
                  <h3>
                    <Wallet size={17} />
                    Payment information
                  </h3>

                  {Object.entries(qrResult.payment_details).map(([key, value]) => (
                    value && (
                      <p key={key}>
                        <strong>{key.replaceAll('_', ' ')}:</strong> {value}
                      </p>
                    )
                  ))}

                  <div className="result-disclaimer">
                    <AlertTriangle size={17} />
                    <p>{qrResult.security_notice}</p>
                  </div>
                </div>
              )}

              {qrResult.message && (
                <p className="qr-result-message">{qrResult.message}</p>
              )}

              <div className="result-disclaimer">
                <AlertTriangle size={17} />
                <p>
                  Decoding a QR code does not verify its destination or sender.
                  Deceptrix does not automatically open URLs or initiate payments.
                </p>
              </div>
            </div>
          </section>
        )}

        <section className="features">
          <div className="section-heading">
            <span>WHY DECEPTRIX</span>
            <h2>Security starts with awareness.</h2>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon purple">
                <Activity size={21} />
              </div>
              <h3>Machine Learning</h3>
              <p>
                Machine learning models analyze URL characteristics and
                message patterns.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon blue">
                <ShieldAlert size={21} />
              </div>
              <h3>Phishing Detection</h3>
              <p>
                Identify suspicious links before interacting with
                potentially harmful websites.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon green">
                <LockKeyhole size={21} />
              </div>
              <h3>Safer Browsing</h3>
              <p>
                Make more informed decisions when you encounter
                unfamiliar links or messages.
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer>
        <a href="/" className="footer-brand">
          DECEPTRIX<span>.</span>
        </a>
        <p>AI-powered protection against digital deception.</p>
        <span>Machine learning assessment · v1.0</span>
      </footer>
    </div>
  )
}

export default App
