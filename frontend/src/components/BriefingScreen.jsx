function BriefingScreen({ briefing, onReady }) {
  if (!briefing) return null

  return (
    <div className="briefing-arena">
      <aside className="briefing-sidebar">
        <p className="briefing-label">Tech stack</p>
        <div className="briefing-pill-stack">
          {briefing.tech_stack.map((tech, index) => (
            <span key={tech} className="tech-pill" style={{ animationDelay: `${index * 60}ms` }}>
              {tech}
            </span>
          ))}
        </div>
      </aside>

      <div className="briefing-main">
        <h2 className="briefing-heading">What we found in your repo</h2>

        <p className="briefing-label">Key data flows</p>
        <ol className="flow-transcript">
          {briefing.key_data_flows.map((flow, index) => (
            <li key={flow} className="flow-row">
              <span className="flow-number mono">{String(index + 1).padStart(2, '0')}</span>
              <span className="flow-text">{flow}</span>
            </li>
          ))}
        </ol>

        <p className="briefing-label">Your opening question</p>
        <div className="opening-prompt-block">{briefing.opening_prompt}</div>

        <button className="btn briefing-ready-btn" onClick={onReady}>
          I'm ready to explain
        </button>
      </div>
    </div>
  )
}

export default BriefingScreen
