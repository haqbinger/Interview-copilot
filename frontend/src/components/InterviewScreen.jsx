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
    <div>
      <div className="question-header">
        <span className="question-number mono">
          Question {questionIndex + 1} of {totalQuestions || '?'}
        </span>
        <div className="question-meta">
          <span className="category-badge">{question.category}</span>
          <DifficultyDots difficulty={question.difficulty} />
        </div>
      </div>

      <p className="question-text">{question.text}</p>

      {!evaluation && (
        <form onSubmit={handleSubmit}>
          <textarea
            className="textarea"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Type your answer..."
          />
          {error && <p className="error-text">{error}</p>}
          <button className="btn" type="submit" disabled={!answer.trim() || submitting}>
            {submitting ? 'Evaluating...' : 'Submit Answer'}
          </button>
        </form>
      )}

      {evaluation && (
        <div className="eval-box">
          <div className="eval-score-row">
            <span className="eval-score mono">{evaluation.score}/5</span>
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
                <ul className="missing-concepts-list">
                  {evaluation.missing_concepts.map((concept) => (
                    <li key={concept}>{concept}</li>
                  ))}
                </ul>
              )}
            </>
          )}

          <button className="btn" onClick={handleNext}>
            Next Question
          </button>
        </div>
      )}
    </div>
  )
}

export default InterviewScreen
