function BriefingScreen({ briefing, onReady }) {
  if (!briefing) return null

  return (
    <div>
      <h2>Here's what we found in your repo.</h2>

      <p className="section-heading">Tech Stack</p>
      <div className="pill-row">
        {briefing.tech_stack.map((tech) => (
          <span key={tech} className="pill">
            {tech}
          </span>
        ))}
      </div>

      <p className="section-heading">Key Data Flows</p>
      <ol className="data-flow-list">
        {briefing.key_data_flows.map((flow) => (
          <li key={flow}>{flow}</li>
        ))}
      </ol>

      <p className="section-heading">Opening Prompt</p>
      <div className="opening-prompt-box">{briefing.opening_prompt}</div>

      <button className="btn" onClick={onReady}>
        I'm ready to explain
      </button>
    </div>
  )
}

export default BriefingScreen
