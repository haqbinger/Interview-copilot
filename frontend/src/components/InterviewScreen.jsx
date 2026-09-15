import { useState } from 'react'

function DifficultyDots({ difficulty }) {
  return (
    <div className="difficulty-dots">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={`dot${n <= difficulty ? ' filled' : ''}`} />
      ))}
    </div>
  )
}

function scoreColorClass(score) {
  if (score >= 4) return 'score-high'
  if (score === 3) return 'score-mid'
  return 'score-low'
}

function InterviewScreen({
  question,
  questionIndex,
  totalQuestions,
  onSubmitAnswer,
  onAdvanceQuestion,
}) {
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [nextQuestion, setNextQuestion] = useState(null)
  const [showMissing, setShowMissing] = useState(false)
  const [error, setError] = useState(null)

  if (!question) return null

  async function handleSubmit(event) {
    event.preventDefault()
    if (!answer.trim() || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const response = await onSubmitAnswer(answer.trim())
      if (response.data.question) {
        setEvaluation(response.data.evaluation)
        setNextQuestion(response.data.question)
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function handleNext() {
    onAdvanceQuestion(nextQuestion)
    setAnswer('')
    setEvaluation(null)
    setNextQuestion(null)
    setShowMissing(false)
  }

  return (
    <div className="interview-arena">
      <div className="interview-topbar">
        <span className="interview-progress mono">
          Question {questionIndex + 1} of {totalQuestions || '?'}
        </span>
        <div className="interview-meta">
          <span className="category-badge">{question.category}</span>
          <DifficultyDots difficulty={question.difficulty} />
        </div>
      </div>

      <p className="question-text" key={question.id}>
        {question.text}
      </p>

      {!evaluation && (
        <form onSubmit={handleSubmit}>
          <textarea
            className="textarea"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Type your answer..."
            aria-label="Your answer"
          />
          {error && <p className="error-text">{error}</p>}
          <button
            className="btn interview-submit-btn"
            type="submit"
            disabled={!answer.trim() || submitting}
          >
            {submitting ? (
              <>
                <span className="spinner"></span>
                Evaluating...
              </>
            ) : (
              'Submit Answer'
            )}
          </button>
        </form>
      )}

      {evaluation && (
        <div className="eval-panel">
          <div className={`eval-score mono ${scoreColorClass(evaluation.score)}`}>
            {evaluation.score}/5
          </div>
          <p className="eval-verdict">{evaluation.verdict}</p>

          {evaluation.missing_concepts?.length > 0 && (
            <>
              <button
                type="button"
                className="collapsible-toggle"
                onClick={() => setShowMissing((prev) => !prev)}
              >
                {showMissing ? 'Hide' : 'Show'} missing concepts
              </button>
              {showMissing && (
                <div className="missing-concepts-panel">
                  <ul className="missing-concepts-list">
                    {evaluation.missing_concepts.map((concept) => (
                      <li key={concept}>{concept}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          <button className="btn interview-next-btn" onClick={handleNext}>
            Next Question
          </button>
        </div>
      )}
    </div>
  )
}

export default InterviewScreen
