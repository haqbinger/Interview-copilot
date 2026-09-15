import { useState } from 'react'

const REVISION_ITEMS_OPEN_BY_DEFAULT = 2
const REVISION_TITLE_MAX_CHARS = 80
const RING_RADIUS = 60
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS
const SHARE_URL = 'interview-copilot-49i7.onrender.com'

function formatMode(mode) {
  return mode
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function qualitativeLabel(score) {
  if (score >= 80) return 'Interview ready. Strong performance.'
  if (score >= 60) return 'Solid foundation. Keep going.'
  if (score >= 40) return 'Needs preparation. Gaps identified.'
  return 'Needs significant work. Start the revision plan.'
}

function scoreBand(score) {
  if (score >= 60) return 'score-high'
  if (score >= 40) return 'score-mid'
  return 'score-low'
}

function scoreColorVar(score) {
  if (score >= 60) return 'var(--secondary)'
  if (score >= 40) return 'var(--accent)'
  return '#c0392b'
}

function CategoryRow({ category, score, maxScore }) {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0
  return (
    <div className="category-row">
      <div className="category-row-label">
        <span className="category-dot" aria-hidden="true" />
        <span className="category-name">{capitalize(category)}</span>
      </div>
      <div className="category-bar-track">
        <div className={`category-bar-fill ${scoreBand(pct)}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="category-pct mono">{pct}%</span>
    </div>
  )
}

function RevisionTimeline({ items }) {
  const [expanded, setExpanded] = useState(
    () => new Set(items.slice(0, REVISION_ITEMS_OPEN_BY_DEFAULT).map((_, index) => index))
  )

  function toggle(index) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  return (
    <ol className="revision-timeline">
      {items.map((item, index) => {
        const isOpen = expanded.has(index)
        const isLast = index === items.length - 1
        const title =
          item.length > REVISION_TITLE_MAX_CHARS
            ? `${item.slice(0, REVISION_TITLE_MAX_CHARS)}...`
            : item

        return (
          <li key={item} className="revision-item">
            <div className="revision-marker">
              <span className="revision-circle mono">{index + 1}</span>
              {!isLast && <span className="revision-connector" />}
            </div>
            <div className="revision-content">
              <button
                type="button"
                className="revision-title-btn"
                onClick={() => toggle(index)}
                aria-expanded={isOpen}
              >
                <span className="revision-title">{title}</span>
                <span className="revision-caret">{isOpen ? '−' : '+'}</span>
              </button>
              {isOpen && <p className="revision-body">{item}</p>}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function FollowUpSection({ questions }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div>
      <button
        type="button"
        className="collapsible-toggle"
        onClick={() => setExpanded((prev) => !prev)}
      >
        Prepare for these follow-ups {expanded ? '↑' : '↓'}
      </button>
      {expanded && (
        <ol className="followup-list">
          {questions.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ol>
      )}
    </div>
  )
}

function ReportScreen({ report, onReset }) {
  const [copied, setCopied] = useState(false)
  const [practiceCopied, setPracticeCopied] = useState(false)

  if (!report) return null

  const score = Math.max(0, Math.min(100, report.overall_score))
  const ringOffset = RING_CIRCUMFERENCE * (1 - score / 100)

  function handleShare() {
    const text = `I scored ${Math.round(report.overall_score)}/100 on Interview Copilot. ${SHARE_URL}`
    navigator.clipboard?.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handlePracticeWeakAreas() {
    const text = report.weak_areas.map((area) => `- ${area}`).join('\n')
    navigator.clipboard?.writeText(text)
    setPracticeCopied(true)
    setTimeout(() => setPracticeCopied(false), 2000)
  }

  return (
    <div className="report-v2">
      <section className="report-hero">
        <div className="report-hero-ring-wrap" role="img" aria-label={`Score ${Math.round(report.overall_score)} out of 100`}>
          <svg className="report-hero-ring" viewBox="0 0 136 136" width="136" height="136">
            <circle className="report-hero-ring-track" cx="68" cy="68" r={RING_RADIUS} strokeWidth="8" fill="none" />
            <circle
              className="report-hero-ring-progress"
              cx="68"
              cy="68"
              r={RING_RADIUS}
              strokeWidth="8"
              fill="none"
              stroke={scoreColorVar(score)}
              strokeDasharray={RING_CIRCUMFERENCE}
              strokeDashoffset={ringOffset}
              strokeLinecap="round"
            />
          </svg>
          <div className="report-hero-score-wrap">
            <div className="report-hero-score mono">
              {Math.round(report.overall_score)}
              <span className="report-hero-score-unit">/100</span>
            </div>
          </div>
        </div>
        <p className="report-hero-label">{qualitativeLabel(score)}</p>
        <div className="report-hero-meta">
          <span className="mode-badge">{formatMode(report.mode)}</span>
          <span className="report-hero-progress-text">
            {report.answered_questions} of {report.total_questions} questions answered
          </span>
        </div>
      </section>

      <div className="report-hero-separator" />

      <section className="report-section">
        <p className="report-section-title">Category breakdown</p>
        <div className="category-rows">
          {report.category_scores.map((cat) => (
            <CategoryRow
              key={cat.category}
              category={cat.category}
              score={cat.score}
              maxScore={cat.max_score}
            />
          ))}
        </div>
      </section>

      <section className="report-section">
        <div className="strong-weak-grid">
          <div className="strong-card">
            <p className="report-section-title">Strong areas</p>
            {report.strong_areas.length === 0 ? (
              <p className="card-empty-state">Answer more questions to surface your strengths.</p>
            ) : (
              <ul className="strong-areas-list">
                {report.strong_areas.map((area) => (
                  <li key={area}>
                    <span className="strong-bullet">✓</span>
                    <span>{area}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="weak-card">
            <p className="report-section-title">Weak areas</p>
            {report.weak_areas.length === 0 ? (
              <p className="card-empty-state">No weak areas identified yet</p>
            ) : (
              <ul className="weak-areas-list">
                {report.weak_areas.map((area) => (
                  <li key={area}>
                    <span className="weak-bullet">•</span>
                    <span>{area}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      <section className="report-section">
        <p className="report-section-title">Revision plan</p>
        <RevisionTimeline items={report.revision_plan} />
        <button type="button" className="practice-btn" onClick={handlePracticeWeakAreas}>
          {practiceCopied ? 'Copied!' : 'Practice Weak Areas'}
        </button>
      </section>

      <section className="report-section">
        <p className="report-section-title">Follow-up questions</p>
        <FollowUpSection questions={report.follow_up_questions} />
      </section>

      <section className="report-section report-actions">
        <button className="btn start-new-btn" onClick={onReset}>
          Start New Interview
        </button>
        <button type="button" className="share-btn" onClick={handleShare}>
          {copied ? 'Copied!' : 'Share your score'}
        </button>
      </section>
    </div>
  )
}

export default ReportScreen
