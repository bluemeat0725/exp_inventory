import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import SsoLogin from './pages/SsoLogin'
import SsoCallback from './pages/SsoCallback'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<SsoLogin />} />
        <Route path="/login" element={<SsoLogin />} />
        <Route path="/login/callback" element={<SsoCallback />} />
      </Routes>
    </Layout>
  )
}

export default App
