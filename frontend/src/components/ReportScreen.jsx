function CategoryBar({ category, score, maxScore }) {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0
  return (
    <div className="category-bar-row">
      <div className="category-bar-label">
        <span>{category}</span>
        <span className="mono">{Math.round(score)}</span>
      </div>
      <div className="category-bar-track">
        <div className="category-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function ReportScreen({ report, onReset }) {
  if (!report) return null

  return (
    <div>
      <h2>Interview Report</h2>

      <div className="overall-score mono">
        {Math.round(report.overall_score)}
        <span className="score-unit">/100</span>
      </div>

      <p className="section-heading">Category Scores</p>
      {report.category_scores.map((cat) => (
        <CategoryBar
          key={cat.category}
          category={cat.category}
          score={cat.score}
          maxScore={cat.max_score}
        />
      ))}

      <div className="two-column">
        <div>
          <p className="section-heading">Strong Areas</p>
          <ul>
            {report.strong_areas.map((area) => (
              <li key={area}>{area}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="section-heading">Weak Areas</p>
          <ul>
            {report.weak_areas.map((area) => (
              <li key={area}>{area}</li>
            ))}
          </ul>
        </div>
      </div>

      <p className="section-heading">Revision Plan</p>
      <ol className="revision-plan">
        {report.revision_plan.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ol>

      <p className="section-heading">Follow-Up Questions</p>
      <ul>
        {report.follow_up_questions.map((question) => (
          <li key={question}>{question}</li>
        ))}
      </ul>

      <div className="actions-row">
        <button className="btn" onClick={onReset}>
          Start New Interview
        </button>
      </div>
    </div>
  )
}

export default ReportScreen
