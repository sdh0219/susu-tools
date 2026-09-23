import React, { useState } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api'
import type { Outline, SlideOutline } from '../types'

const InputBar: React.FC = () => {
  const [topic, setTopic] = useState('')
  const generating = useStore((s) => s.generating)
  const setGenerating = useStore((s) => s.setGenerating)
  const setOutline = useStore((s) => s.setOutline)
  const setSelectedSlideId = useStore((s) => s.setSelectedSlideId)
  const activeProvider = useStore((s) => s.activeProvider)
  const setShowSettings = useStore((s) => s.setShowSettings)

  const handleGenerate = async () => {
    if (!topic.trim()) return
    if (!activeProvider || !activeProvider.apiKey) {
      alert('请先在设置中配置AI模型供应商')
      setShowSettings(true)
      return
    }
    setGenerating(true)
    try {
      const { result } = await api.aiGenerateOutline(topic.trim())
      const parsed = JSON.parse(result) as Outline
      const slides: SlideOutline[] = parsed.slides.map((slide, index) => ({
        id: `slide-${Date.now()}-${index}`,
        title: slide.title || '',
        bulletPoints: slide.bulletPoints || [],
        notes: slide.notes || '',
        layout: slide.layout || (index === 0 ? 'title' : 'content')
      }))
      setOutline({
        title: parsed.title || topic.trim(),
        subtitle: parsed.subtitle || '',
        slides
      })
      setSelectedSlideId(slides[0]?.id || null)
    } catch (err) {
      alert(`生成失败：${err}`)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, maxWidth: 600 }}>
      <input
        className="input"
        placeholder="输入主题，如：高血压的诊断与治疗"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
        disabled={generating}
        style={{ flex: 1 }}
      />
      <button
        className="btn btn-primary"
        onClick={handleGenerate}
        disabled={generating}
      >
        {generating ? '⏳ 生成中...' : '📤 生成'}
      </button>
    </div>
  )
}

export default InputBar
