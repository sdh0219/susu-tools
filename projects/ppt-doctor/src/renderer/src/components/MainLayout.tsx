import React from 'react'
import InputBar from './InputBar'
import OutlineEditor from './OutlineEditor'
import PptPreview from './PptPreview'
import Toolbar from './Toolbar'
import ModelStatus from './ModelStatus'
import { useStore } from '../store/useStore'

const MainLayout: React.FC = () => {
  const setShowSettings = useStore((s) => s.setShowSettings)

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 24px', background: '#fff', borderBottom: '1px solid #e8e8e8', height: 56
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 24 }}>🏥</span>
          <span style={{ fontSize: 18, fontWeight: 'bold', color: '#1B3A5C' }}>PPT医生</span>
        </div>
        <InputBar />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ModelStatus />
          <button
            className="btn"
            onClick={() => setShowSettings(true)}
            title="模型设置"
          >
            ⚙️ 设置
          </button>
          <Toolbar />
        </div>
      </header>
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{
          width: '40%', background: '#fafafa', borderRight: '1px solid #e8e8e8',
          overflow: 'auto'
        }}>
          <OutlineEditor />
        </div>
        <div style={{ flex: 1, background: '#f0f2f5', overflow: 'auto' }}>
          <PptPreview />
        </div>
      </div>
    </div>
  )
}

export default MainLayout
