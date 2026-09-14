import { useState } from 'react'

const MIN_CHARS = 100

function ExplainScreen({ openingPrompt, onSubmit, loading }) {
  const [explanation, setExplanation] = useState('')

  const belowMin = explanation.length < MIN_CHARS

  function handleSubmit(event) {
    event.preventDefault()
    if (belowMin || loading) return
    onSubmit(explanation.trim())
  }

  return (
    <div>
      <h2>Explain your project.</h2>
      <p className="opening-prompt-box">{openingPrompt}</p>

      <form onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="explanation">
          In your own words
        </label>
        <textarea
          id="explanation"
          className="textarea"
          value={explanation}
          onChange={(event) => setExplanation(event.target.value)}
          placeholder="Walk me through what this project does, how it's built, and the decisions behind it..."
        />
        <p className={`char-count${belowMin ? ' below-min' : ''}`}>
          {explanation.length} / {MIN_CHARS} characters minimum
        </p>

        <button className="btn" type="submit" disabled={belowMin || loading}>
          {loading ? 'Submitting...' : 'Submit Explanation'}
        </button>
      </form>
    </div>
  )
}

export default ExplainScreen
