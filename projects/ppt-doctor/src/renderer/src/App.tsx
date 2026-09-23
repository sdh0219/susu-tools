import React, { useEffect, useState } from 'react'
import { useStore } from './store/useStore'
import MainLayout from './components/MainLayout'
import Settings from './components/Settings'
import { api } from './api'
import './styles/global.css'

const App: React.FC = () => {
  const [checking, setChecking] = useState(true)
  const showSettings = useStore((s) => s.showSettings)
  const setProviders = useStore((s) => s.setProviders)
  const setActiveProvider = useStore((s) => s.setActiveProvider)

  useEffect(() => {
    initApp()
  }, [])

  const initApp = async () => {
    try {
      const list = await api.providerGetAll()
      setProviders(list)
      const active = await api.providerGetActive()
      setActiveProvider(active || null)
    } catch {
      setActiveProvider(null)
    } finally {
      setChecking(false)
    }
  }

  if (checking) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1B3A5C 0%, #2E86AB 100%)'
      }}>
        <div style={{ textAlign: 'center', color: '#fff' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🏥</div>
          <div style={{ fontSize: 24, fontWeight: 'bold' }}>PPT医生</div>
          <div style={{ fontSize: 14, marginTop: 8, opacity: 0.8 }}>正在初始化...</div>
        </div>
      </div>
    )
  }

  return (
    <>
      <MainLayout />
      {showSettings && <Settings />}
    </>
  )
}

export default App
