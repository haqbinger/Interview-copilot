import { useState } from 'react'

const WEAK_AREAS_PREVIEW_COUNT = 5
const REVISION_ITEMS_OPEN_BY_DEFAULT = 3
const REVISION_TITLE_MAX_CHARS = 60

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

function getVerdict(score) {
  if (score >= 80) return { text: 'Interview Ready', className: 'verdict-secondary' }
  if (score >= 60) return { text: 'Solid Foundation', className: 'verdict-secondary' }
  if (score >= 40) return { text: 'Needs Preparation', className: 'verdict-accent' }
  return { text: 'Significant Gaps', className: 'verdict-critical' }
}

function scoreBand(score) {
  if (score >= 60) return 'score-high'
  if (score >= 40) return 'score-mid'
  return 'score-low'
}

function CategoryBar({ category, score, maxScore }) {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0
  return (
    <div className="category-bar-row">
      <div className="category-bar-label">
        <span>{capitalize(category)}</span>
        <span className="mono">{Math.round(score)}</span>
      </div>
      <div className="category-bar-track">
        <div
          className={`category-bar-fill ${scoreBand(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function WeakAreasList({ items }) {
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? items : items.slice(0, WEAK_AREAS_PREVIEW_COUNT)
  const hasMore = items.length > WEAK_AREAS_PREVIEW_COUNT

  return (
    <>
      <ul className="weak-areas-list">
        {visible.map((area) => (
          <li key={area}>
            <span className="weak-bullet">•</span>
            <span>{area}</span>
          </li>
        ))}
      </ul>
      {hasMore && (
        <button
          type="button"
          className="collapsible-toggle"
          onClick={() => setShowAll((prev) => !prev)}
        >
          {showAll ? 'Show less' : 'Show more'}
        </button>
      )}
    </>
  )
}

function RevisionAccordion({ items }) {
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
    <ol className="revision-accordion">
      {items.map((item, index) => {
        const isOpen = expanded.has(index)
        const title =
          item.length > REVISION_TITLE_MAX_CHARS
            ? `${item.slice(0, REVISION_TITLE_MAX_CHARS)}...`
            : item

        return (
          <li key={item} className="revision-accordion-item">
            <button
              type="button"
              className="revision-accordion-header"
              onClick={() => toggle(index)}
            >
              <span className="revision-accordion-number mono">{index + 1}</span>
              <span className="revision-accordion-title">{title}</span>
              <span className="revision-accordion-caret">{isOpen ? '−' : '+'}</span>
            </button>
            {isOpen && <p className="revision-accordion-body">{item}</p>}
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

  if (!report) return null

  const verdict = getVerdict(report.overall_score)

  function handleShare() {
    const text = [
      `Interview score: ${Math.round(report.overall_score)}/100`,
      '',
      'Weak areas:',
      ...report.weak_areas.map((area) => `- ${area}`),
    ].join('\n')

    navigator.clipboard?.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div>
      <section className="report-section">
        <div className="hero-row">
          <div>
            <div className="hero-score mono">
              {Math.round(report.overall_score)}
              <span className="score-unit">/100</span>
            </div>
            <div className="hero-meta-row">
              <span className="mode-badge">{formatMode(report.mode)}</span>
              <span className="hero-progress-text">
                {report.answered_questions} of {report.total_questions} questions answered
              </span>
            </div>
          </div>
          <div className={`hero-verdict ${verdict.className}`}>{verdict.text}</div>
        </div>
      </section>

      <section className="report-section">
        <p className="report-section-title">Category scores</p>
        {report.category_scores.map((cat) => (
          <CategoryBar
            key={cat.category}
            category={cat.category}
            score={cat.score}
            maxScore={cat.max_score}
          />
        ))}
      </section>

      <section className="report-section">
        <div className="strong-weak-grid">
          <div>
            <p className="report-section-title">Strong areas</p>
            {report.strong_areas.length === 0 ? (
              <p className="empty-state-text">
                Keep going — complete more questions to see strengths.
              </p>
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
          <div>
            <p className="report-section-title">Weak areas</p>
            <WeakAreasList items={report.weak_areas} />
          </div>
        </div>
      </section>

      <section className="report-section">
        <p className="report-section-title">Revision plan</p>
        <RevisionAccordion items={report.revision_plan} />
      </section>

      <section className="report-section">
        <p className="report-section-title">Follow-up questions</p>
        <FollowUpSection questions={report.follow_up_questions} />
      </section>

      <section className="report-section">
        <div className="actions-row">
          <button className="btn" onClick={onReset}>
            Start New Interview
          </button>
          <button type="button" className="share-btn" onClick={handleShare}>
            {copied ? 'Copied to clipboard' : 'Share your score'}
          </button>
        </div>
      </section>
    </div>
  )
}

export default ReportScreen
