import { useState } from 'react'
import './App.css'
import {
  startSession,
  submitExplanation,
  submitAnswer,
  getStatus,
} from './api/client'
import LandingPage from './components/LandingPage'
import BriefingScreen from './components/BriefingScreen'
import ExplainScreen from './components/ExplainScreen'
import InterviewScreen from './components/InterviewScreen'
import ReportScreen from './components/ReportScreen'

const INITIAL_STATE = {
  screen: 'landing',
  mode: 'TECHNICAL',
  sessionId: null,
  briefing: null,
  currentQuestion: null,
  questionIndex: 0,
  totalQuestions: 0,
  evaluations: [],
  report: null,
}

function App() {
  const [state, setState] = useState(INITIAL_STATE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleStartSession(githubUrl, mode) {
    setLoading(true)
    setError(null)
    try {
      const response = await startSession(githubUrl, mode)
      console.log(response.data)
      if (!response.data || !response.data.briefing) {
        console.error('Unexpected startSession response shape:', response)
        setError('Something went wrong analysing this repo. Please try again.')
        return
      }
      setState((prev) => ({
        ...prev,
        sessionId: response.session_id,
        briefing: response.data.briefing,
        mode,
        screen: 'briefing',
      }))
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleReady() {
    setState((prev) => ({ ...prev, screen: 'explaining' }))
  }

  async function handleSubmitExplanation(explanation) {
    setLoading(true)
    setError(null)
    try {
      const response = await submitExplanation(state.sessionId, explanation)
      console.log(response.data)
      if (!response.data || !response.data.question) {
        console.error('Unexpected submitExplanation response shape:', response)
        setError('Something went wrong generating your first question. Please try again.')
        return
      }
      const status = await getStatus(state.sessionId)
      setState((prev) => ({
        ...prev,
        currentQuestion: response.data.question,
        questionIndex: 0,
        totalQuestions: status.total_questions,
        screen: 'interviewing',
      }))
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitAnswer(answer) {
    setError(null)
    const response = await submitAnswer(state.sessionId, answer)
    console.log(response.data)
    if (!response.data || (!response.data.question && !response.data.report)) {
      console.error('Unexpected submitAnswer response shape:', response)
      setError('Something went wrong evaluating your answer. Please try again.')
      return response
    }
    setState((prev) => ({
      ...prev,
      evaluations: [...prev.evaluations, response.data.evaluation],
    }))
    if (response.state === 'COMPLETE' || response.state === 'REPORTING') {
      setState((prev) => ({
        ...prev,
        report: response.data.report,
        screen: 'report',
      }))
    }
    return response
  }

  function handleAdvanceQuestion(nextQuestion) {
    setState((prev) => ({
      ...prev,
      currentQuestion: nextQuestion,
      questionIndex: prev.questionIndex + 1,
    }))
  }

  function handleReset() {
    setState(INITIAL_STATE)
    setError(null)
  }

  return (
    <div className="app-shell screen-fade" key={state.screen}>
      {error && <p className="error-text">{error}</p>}

      {state.screen === 'landing' && (
        <LandingPage onStart={handleStartSession} loading={loading} />
      )}

      {state.screen === 'briefing' && (
        <BriefingScreen briefing={state.briefing} onReady={handleReady} />
      )}

      {state.screen === 'explaining' && (
        <ExplainScreen
          openingPrompt={state.briefing?.opening_prompt}
          onSubmit={handleSubmitExplanation}
          loading={loading}
        />
      )}

      {state.screen === 'interviewing' && (
        <InterviewScreen
          question={state.currentQuestion}
          questionIndex={state.questionIndex}
          totalQuestions={state.totalQuestions}
          onSubmitAnswer={handleSubmitAnswer}
          onAdvanceQuestion={handleAdvanceQuestion}
        />
      )}

      {state.screen === 'report' && (
        <ReportScreen report={state.report} onReset={handleReset} />
      )}
    </div>
  )
}

export default App
