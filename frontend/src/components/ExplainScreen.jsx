import { useState } from 'react'

function ExplainScreen({ openingPrompt, onSubmit, loading }) {
  const [explanation, setExplanation] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (!explanation.trim() || loading) return
    onSubmit(explanation.trim())
  }

  return (
    <div className="explain-arena">
      <p className="explain-prompt">{openingPrompt}</p>
      <div className="explain-divider" />

      <form onSubmit={handleSubmit}>
        <textarea
          className="textarea explain-textarea"
          value={explanation}
          onChange={(event) => setExplanation(event.target.value)}
          placeholder="Start talking through your project..."
          aria-label="Your explanation"
        />
        <div className="explain-footer-row">
          <span className="explain-char-count">{explanation.length} characters</span>
          <button
            className="btn explain-submit-btn"
            type="submit"
            disabled={!explanation.trim() || loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Submitting...
              </>
            ) : (
              'Submit Explanation'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ExplainScreen
