import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [activeTab, setActiveTab] = useState('forgery') // 'forgery' or 'hashing'

  // Hashing State
  const [hashFile, setHashFile] = useState(null)
  const [hashResult, setHashResult] = useState(null)
  const [compareFile, setCompareFile] = useState(null)
  const [compareResult, setCompareResult] = useState(null)
  const [originalHash, setOriginalHash] = useState('')

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
      setResult(null)
      setError(null)
    }
  }

  const handleHashFileChange = (e) => {
    setHashFile(e.target.files[0])
    setHashResult(null)
  }

  const handleCompareFileChange = (e) => {
    setCompareFile(e.target.files[0])
    setCompareResult(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('http://localhost:8000/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      setResult(response.data)
    } catch (err) {
      console.error(err)
      const msg = err.response?.data?.detail || 'Analysis failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const generateHash = async () => {
    if (!hashFile) return
    setLoading(true)
    const formData = new FormData()
    formData.append('file', hashFile)
    try {
      const res = await axios.post('http://localhost:8000/hash', formData)
      setHashResult(res.data.hash)
      setOriginalHash(res.data.hash) // Auto-fill for comparison
    } catch (err) {
      console.error(err)
      const msg = err.response?.data?.detail || 'Hashing failed'
      alert(msg)
    } finally {
      setLoading(false)
    }
  }

  const compareImage = async () => {
    if (!compareFile || !originalHash) return
    setLoading(true)
    const formData = new FormData()
    formData.append('file', compareFile)
    try {
      const res = await axios.post(`http://localhost:8000/compare?original_hash=${originalHash}`, formData)
      setCompareResult(res.data)
    } catch (err) {
      alert('Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = async () => {
    if (!result || !file) return

    try {
      const response = await axios.post(`http://localhost:8000/report?filename=${file.name}&is_tampered=${result.is_tampered}&confidence=${result.confidence}`, {}, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_${file.name}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Failed to download report')
    }
  }

  const downloadHashingReport = async () => {
    if (!compareResult || !compareFile) return

    try {
      const response = await axios.post(`http://localhost:8000/report/hashing?filename=${compareFile.name}&is_authentic=${compareResult.is_authentic}&distance=${compareResult.distance}&original_hash=${compareResult.original_hash}&suspect_hash=${compareResult.suspect_hash}`, {}, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `integrity_report_${compareFile.name}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Failed to download report')
    }
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Image Authentication System</h1>
        <p>Detect digital tampering using Deep Learning & Classical Hashing</p>
      </header>

      <div className="tabs">
        <button
          className={`tab-btn ${activeTab === 'forgery' ? 'active' : ''}`}
          onClick={() => setActiveTab('forgery')}
        >
          Forgery Detection (Deep Learning)
        </button>
        <button
          className={`tab-btn ${activeTab === 'hashing' ? 'active' : ''}`}
          onClick={() => setActiveTab('hashing')}
        >
          Integrity Check (Hashing)
        </button>
      </div>

      <main className="main-content">
        {activeTab === 'forgery' ? (
          // --- FORGERY DETECTION TAB ---
          !result ? (
            <div className="upload-section">
              <div className="upload-box">
                <input
                  type="file"
                  id="file-upload"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="file-input"
                />
                <label htmlFor="file-upload" className="file-label">
                  {preview ? (
                    <img src={preview} alt="Preview" className="preview-image" />
                  ) : (
                    <div className="placeholder">
                      <span>Drag & Drop or Click to Upload</span>
                    </div>
                  )}
                </label>
              </div>

              {file && (
                <button
                  onClick={handleUpload}
                  disabled={loading}
                  className="upload-btn"
                >
                  {loading ? 'Analyzing...' : 'Analyze Image'}
                </button>
              )}

              {error && <div className="error-msg">{error}</div>}
            </div>
          ) : (
            <div className="result-section">
              <div className="result-header">
                <h2>Analysis Result</h2>
                <div className={`status-badge ${result.is_tampered ? 'fake' : 'real'}`}>
                  {result.is_tampered ? 'TAMPERED DETECTED' : 'AUTHENTIC'}
                </div>
                <p>Confidence: {(result.confidence * 100).toFixed(2)}%</p>
                <button onClick={downloadReport} className="download-btn">Download Report (PDF)</button>
              </div>

              <div className="images-grid">
                <div className="image-card">
                  <h3>Original</h3>
                  <img src={preview} alt="Original" />
                </div>
                <div className="image-card">
                  <h3>ELA Analysis</h3>
                  <img src={result.ela_image} alt="ELA" />
                </div>
                <div className="image-card">
                  <h3>Forgery Mask</h3>
                  <img src={result.mask_image} alt="Mask" />
                </div>
              </div>

              <button onClick={reset} className="reset-btn">Analyze Another Image</button>
            </div>
          )
        ) : (
          // --- HASHING TAB ---
          <div className="hashing-section">
            <div className="card">
              <h3>1. Generate Original Hash</h3>
              <input type="file" onChange={handleHashFileChange} />
              <button onClick={generateHash} disabled={loading}>Generate Hash</button>
              {hashResult && <div className="hash-display">Hash: <code>{hashResult}</code></div>}
            </div>

            <div className="card">
              <h3>2. Verify Image Integrity</h3>
              <input
                type="text"
                placeholder="Enter Original Hash"
                value={originalHash}
                onChange={(e) => setOriginalHash(e.target.value)}
                className="hash-input"
              />
              <input type="file" onChange={handleCompareFileChange} />
              <button onClick={compareImage} disabled={loading}>Verify Integrity</button>

              {compareResult && (
                <div className={`result-box ${compareResult.is_authentic ? 'success' : 'danger'}`}>
                  <h4>{compareResult.message}</h4>
                  <p>Original Hash: <code>{compareResult.original_hash}</code></p>
                  <p>Suspect Hash: <code>{compareResult.suspect_hash}</code></p>
                  <p>Distance: {compareResult.distance}</p>
                  <button onClick={downloadHashingReport} className="download-btn">Download Report (PDF)</button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
