import axios from 'axios'

const apiClient = axios.create({
  baseURL: '',
})

export const UPLOAD_TYPE_OPTIONS = [
  { value: 'company_function',   label: 'Company Function Feedback' },
  { value: 'auto_feedback',      label: 'Self / Auto Feedback' },
  { value: 'project_feedback',   label: 'Project Feedback' },
  { value: 'client_feedback',    label: 'Client Feedback' },
  { value: 'additional_feedback',label: 'Additional Feedback' },
  { value: 'pdp',                label: 'Personal Development Plan (PDP)' },
  { value: 'trainings',          label: 'Trainings' },
  { value: 'project_activity',   label: 'Project Activity' },
]

/**
 * GET /api/profiles/
 * Returns [{ id, employee_name, year, has_html, files }]
 */
export function listProfiles() {
  return apiClient.get('/api/profiles/').then((r) => r.data)
}

/**
 * POST /api/uploads/doc  (multipart/form-data)
 * Required: file, upload_type, person_name, review_year
 * Optional: uploaded_by_email
 */
export function uploadDoc({ file, upload_type, person_name, review_year, uploaded_by_email }) {
  const form = new FormData()
  form.append('file', file)
  form.append('upload_type', upload_type)
  form.append('person_name', person_name)
  form.append('review_year', String(review_year))
  if (uploaded_by_email) form.append('uploaded_by_email', uploaded_by_email)
  return apiClient.post('/api/uploads/doc', form).then((r) => r.data)
}

/**
 * GET /api/profiles/html/{personName}/{year}
 * Returns HTML blob – triggers browser download.
 */
export async function downloadHtml(personName, year) {
  const response = await apiClient.get(
    `/api/profiles/html/${encodeURIComponent(personName)}/${year}`,
    { responseType: 'blob' }
  )
  const url = URL.createObjectURL(response.data)
  const a = document.createElement('a')
  a.href = url
  const cd = response.headers['content-disposition'] ?? ''
  const match = cd.match(/filename="([^"]+)"/)
  a.download = match ? match[1] : `PR_${personName}_${year}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * GET /api/profiles/html/{personName}/{year}
 * Returns an object-URL string for iframe preview.
 */
export async function getHtmlPreviewUrl(personName, year) {
  const response = await apiClient.get(
    `/api/profiles/html/${encodeURIComponent(personName)}/${year}`,
    { responseType: 'blob' }
  )
  return URL.createObjectURL(response.data)
}

/**
 * POST /api/profiles/html/{personName}/{year}/regenerate
 */
export function regenerateHtml(personName, year) {
  return apiClient
    .post(`/api/profiles/html/${encodeURIComponent(personName)}/${year}/regenerate`)
    .then((r) => r.data)
}

/**
 * POST /api/profiles/html/{personName}/{year}/rename
 * Body: { new_name: string }
 */
export function renameProfile(personName, year, newName) {
  return apiClient
    .post(`/api/profiles/html/${encodeURIComponent(personName)}/${year}/rename`, {
      new_name: newName,
    })
    .then((r) => r.data)
}

export default apiClient
