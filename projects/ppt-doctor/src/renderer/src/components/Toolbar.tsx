import React from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api'

const Toolbar: React.FC = () => {
  const outline = useStore((s) => s.outline)
  const generating = useStore((s) => s.generating)
  const setGenerating = useStore((s) => s.setGenerating)
  const setOutline = useStore((s) => s.setOutline)

  const handleExport = async () => {
    if (!outline) return
    try {
      await api.pptExport(outline)
    } catch (err) {
      alert(`导出失败：${err}`)
    }
  }

  const handleRegenerate = async () => {
    if (!outline) return
    setGenerating(true)
    try {
      const { result } = await api.aiGenerateOutline(outline.title)
      const parsed = JSON.parse(result)
      setOutline({ ...parsed, slides: parsed.slides })
    } catch (err) {
      alert(`重新生成失败：${err}`)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <button
        className="btn btn-sm"
        onClick={handleRegenerate}
        disabled={generating || !outline}
      >
        🔄 重新生成
      </button>
      <button
        className="btn btn-sm btn-primary"
        onClick={handleExport}
        disabled={!outline}
      >
        💾 导出PPT
      </button>
    </div>
  )
}

export default Toolbar
