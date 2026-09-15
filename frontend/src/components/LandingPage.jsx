import { useState } from 'react'

const MODES = [
  { value: 'BEGINNER', label: 'Beginner' },
  { value: 'TECHNICAL', label: 'Technical' },
  { value: 'DEEP_DIVE', label: 'Deep Dive' },
  { value: 'STRESS', label: 'Stress' },
]

const PROVIDERS = [
  {
    value: 'openai',
    name: 'OpenAI',
    description: 'GPT-4o and reasoning models (o1/o3)',
    link: 'https://platform.openai.com/api-keys',
    placeholder: 'sk-...',
    keyField: 'openaiApiKey',
  },
  {
    value: 'gemini',
    name: 'Gemini',
    description: '2M token context, generous free tier',
    link: 'https://aistudio.google.com/apikey',
    placeholder: 'AQ.Ab... or AIza...',
    keyField: 'geminiApiKey',
  },
  {
    value: 'claude',
    name: 'Claude',
    description: 'Best-in-class for coding and complex reasoning',
    link: 'https://console.anthropic.com/settings/keys',
    placeholder: 'sk-ant-...',
    keyField: 'anthropicApiKey',
  },
  {
    value: 'deepseek',
    name: 'DeepSeek',
    description: 'Elite reasoning at a fraction of the cost',
    link: 'https://platform.deepseek.com/api_keys',
    placeholder: 'sk-...',
    keyField: 'deepseekApiKey',
  },
  {
    value: 'openrouter',
    name: 'OpenRouter',
    description: 'One key, access to 200+ models',
    link: 'https://openrouter.ai/keys',
    placeholder: 'sk-or-...',
    keyField: 'openrouterApiKey',
  },
  {
    value: 'groq',
    name: 'Groq',
    description: 'Fastest inference, near-instant responses',
    link: 'https://console.groq.com/keys',
    placeholder: 'gsk_...',
    keyField: 'groqApiKey',
  },
  {
    value: 'mistral',
    name: 'Mistral',
    description: "Europe's top provider, strong privacy standards",
    link: 'https://console.mistral.ai/api-keys',
    placeholder: '...',
    keyField: 'mistralApiKey',
  },
]

const MAX_BACKUP_KEYS = 2

function LandingPage({ onStart, loading }) {
  const [githubUrl, setGithubUrl] = useState('')
  const [mode, setMode] = useState('TECHNICAL')
  const [keyProvider, setKeyProvider] = useState('groq')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [backupKeys, setBackupKeys] = useState([])

  const selected = PROVIDERS.find((option) => option.value === keyProvider)
  const trimmedKey = apiKey.trim()

  function addBackupKey() {
    if (backupKeys.length >= MAX_BACKUP_KEYS) return
    setBackupKeys((prev) => [...prev, { provider: 'groq', key: '', showKey: false }])
  }

  function updateBackupKey(index, patch) {
    setBackupKeys((prev) => prev.map((entry, i) => (i === index ? { ...entry, ...patch } : entry)))
  }

  function removeBackupKey(index) {
    setBackupKeys((prev) => prev.filter((_, i) => i !== index))
  }

  function handleSubmit(event) {
    event.preventDefault()
    if (!githubUrl.trim() || !trimmedKey || loading) return

    const apiKeys = [
      { provider: keyProvider, key: trimmedKey },
      ...backupKeys
        .filter((entry) => entry.key.trim())
        .map((entry) => ({ provider: entry.provider, key: entry.key.trim() })),
    ]

    onStart(githubUrl.trim(), mode, apiKeys)
  }

  return (
    <div className="landing">
      <div className="landing-grid">
        <div className="landing-left">
          <h1>Turn your GitHub project into an interview.</h1>
          <p className="subheading">
            Connect your repo. Explain your project. Defend your decisions.
          </p>

          <form
            className="landing-form"
            onSubmit={handleSubmit}
            style={{ opacity: loading ? 0.5 : 1 }}
          >
            <label className="field-label" htmlFor="github-url">
              GitHub repository URL
            </label>
            <input
              id="github-url"
              className="input"
              type="text"
              placeholder="https://github.com/owner/repo"
              value={githubUrl}
              onChange={(event) => setGithubUrl(event.target.value)}
              disabled={loading}
            />

            <div className="mode-grid">
              {MODES.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`mode-btn${mode === option.value ? ' active' : ''}`}
                  onClick={() => setMode(option.value)}
                  disabled={loading}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <button
              className="btn"
              type="submit"
              disabled={loading || !githubUrl.trim() || !trimmedKey}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analysing repo...
                </>
              ) : !trimmedKey ? (
                'Add an API key to start'
              ) : (
                'Start Interview'
              )}
            </button>
          </form>
        </div>

        <div className="landing-right">
          <p className="byok-heading">Connect your AI provider</p>
          <p className="byok-subtext">
            Free to use. Your key goes directly to the provider — we never store it.
          </p>

          <div className="provider-grid">
            {PROVIDERS.map((option) => (
              <label
                key={option.value}
                className={`provider-card${keyProvider === option.value ? ' selected' : ''}`}
              >
                <input
                  className="provider-card-radio"
                  type="radio"
                  name="key-provider"
                  value={option.value}
                  checked={keyProvider === option.value}
                  onChange={() => setKeyProvider(option.value)}
                  disabled={loading}
                />
                <span className="provider-name">{option.name}</span>
                <span className="provider-description">{option.description}</span>
                <a
                  className="provider-link"
                  href={option.link}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(event) => event.stopPropagation()}
                >
                  Get key →
                </a>
              </label>
            ))}
          </div>

          <p className="key-row-label">Primary</p>
          <div className="api-key-field">
            <input
              id="api-key"
              className="input"
              type={showKey ? 'text' : 'password'}
              placeholder={selected.placeholder}
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              autoComplete="off"
              disabled={loading}
            />
            <button
              type="button"
              className="key-toggle-btn"
              onClick={() => setShowKey((prev) => !prev)}
              disabled={loading}
            >
              {showKey ? 'Hide' : 'Show'}
            </button>
          </div>

          <p className="byok-privacy-note">
            Your key is sent directly to {selected.name} and never stored.
          </p>

          {backupKeys.map((entry, index) => {
            const entryProvider = PROVIDERS.find((option) => option.value === entry.provider)
            return (
              <div key={index} className="backup-key-row">
                <p className="key-row-label">Backup {index + 1}</p>
                <div className="backup-key-inputs">
                  <select
                    className="input backup-provider-select"
                    value={entry.provider}
                    onChange={(event) => updateBackupKey(index, { provider: event.target.value })}
                    disabled={loading}
                  >
                    {PROVIDERS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.name}
                      </option>
                    ))}
                  </select>
                  <div className="api-key-field backup-key-field">
                    <input
                      className="input"
                      type={entry.showKey ? 'text' : 'password'}
                      placeholder={entryProvider.placeholder}
                      value={entry.key}
                      onChange={(event) => updateBackupKey(index, { key: event.target.value })}
                      autoComplete="off"
                      disabled={loading}
                    />
                    <button
                      type="button"
                      className="key-toggle-btn"
                      onClick={() => updateBackupKey(index, { showKey: !entry.showKey })}
                      disabled={loading}
                    >
                      {entry.showKey ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <button
                    type="button"
                    className="remove-key-btn"
                    onClick={() => removeBackupKey(index)}
                    disabled={loading}
                    aria-label={`Remove backup key ${index + 1}`}
                  >
                    ✕
                  </button>
                </div>
              </div>
            )
          })}

          {backupKeys.length < MAX_BACKUP_KEYS && (
            <button
              type="button"
              className="add-backup-key-btn"
              onClick={addBackupKey}
              disabled={loading}
            >
              + Add backup key
            </button>
          )}

          <p className="byok-privacy-note">
            If your primary key exhausts, backup keys are tried automatically.
          </p>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
