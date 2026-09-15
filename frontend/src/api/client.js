import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://interview-copilot-backend-gopz.onrender.com',
})

export async function startSession(githubUrl, mode, apiKeys = []) {
  const body = { github_url: githubUrl, mode }
  if (apiKeys && apiKeys.length > 0) {
    body.api_keys = apiKeys
  }

  const response = await client.post('/api/v1/session/start', body)
  return response.data
}

export async function submitExplanation(sessionId, answer) {
  const response = await client.post(`/api/v1/session/${sessionId}/explain`, {
    session_id: sessionId,
    answer,
  })
  return response.data
}

export async function submitAnswer(sessionId, answer) {
  const response = await client.post(`/api/v1/session/${sessionId}/answer`, {
    session_id: sessionId,
    answer,
  })
  return response.data
}

export async function getStatus(sessionId) {
  const response = await client.get(`/api/v1/session/${sessionId}/status`)
  return response.data
}

export default client
