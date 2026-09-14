import { useState } from 'react'

const MODES = [
  { value: 'BEGINNER', label: 'Beginner' },
  { value: 'TECHNICAL', label: 'Technical' },
  { value: 'DEEP_DIVE', label: 'Deep Dive' },
  { value: 'STRESS', label: 'Stress' },
]

function LandingPage({ onStart, loading }) {
  const [githubUrl, setGithubUrl] = useState('')
  const [mode, setMode] = useState('TECHNICAL')

  function handleSubmit(event) {
    event.preventDefault()
    if (!githubUrl.trim() || loading) return
    onStart(githubUrl.trim(), mode)
  }

  return (
    <div className="landing">
      <h1>Turn your GitHub project into an interview.</h1>
      <p className="subheading">
        Connect your repo. Explain your project. Defend your decisions.
      </p>

      <form className="landing-form" onSubmit={handleSubmit}>
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
        />

        <div className="mode-grid">
          {MODES.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`mode-btn${mode === option.value ? ' active' : ''}`}
              onClick={() => setMode(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <button className="btn" type="submit" disabled={loading || !githubUrl.trim()}>
          {loading ? 'Starting...' : 'Start Interview'}
        </button>
      </form>
    </div>
  )
}

export default LandingPage
