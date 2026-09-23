import React, { useState } from 'react'
import { useStore } from '../store/useStore'
import type { SlideOutline } from '../types'

const OutlineEditor: React.FC = () => {
  const outline = useStore((s) => s.outline)
  const setOutline = useStore((s) => s.setOutline)
  const selectedSlideId = useStore((s) => s.selectedSlideId)
  const setSelectedSlideId = useStore((s) => s.setSelectedSlideId)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  if (!outline) {
    return (
      <div className="empty-state" style={{ height: '100%' }}>
        <div className="empty-state-icon">📋</div>
        <div className="empty-state-text">输入主题生成大纲，或手动创建幻灯片</div>
      </div>
    )
  }

  const updateSlide = (id: string, updates: Partial<SlideOutline>) => {
    const newSlides = outline.slides.map((s) =>
      s.id === id ? { ...s, ...updates } : s
    )
    setOutline({ ...outline, slides: newSlides })
  }

  const addSlide = () => {
    const newSlide: SlideOutline = {
      id: `slide-${Date.now()}`,
      title: '新幻灯片',
      bulletPoints: [''],
      notes: '',
      layout: 'content'
    }
    setOutline({ ...outline, slides: [...outline.slides, newSlide] })
    setSelectedSlideId(newSlide.id)
  }

  const deleteSlide = (id: string) => {
    const newSlides = outline.slides.filter((s) => s.id !== id)
    setOutline({ ...outline, slides: newSlides })
    if (selectedSlideId === id) {
      setSelectedSlideId(newSlides[0]?.id || null)
    }
    setConfirmDelete(null)
  }

  const addBulletPoint = (slideId: string) => {
    const slide = outline.slides.find((s) => s.id === slideId)
    if (!slide) return
    updateSlide(slideId, { bulletPoints: [...slide.bulletPoints, ''] })
  }

  const updateBulletPoint = (slideId: string, index: number, value: string) => {
    const slide = outline.slides.find((s) => s.id === slideId)
    if (!slide) return
    const newBullets = [...slide.bulletPoints]
    newBullets[index] = value
    updateSlide(slideId, { bulletPoints: newBullets })
  }

  const removeBulletPoint = (slideId: string, index: number) => {
    const slide = outline.slides.find((s) => s.id === slideId)
    if (!slide) return
    updateSlide(slideId, { bulletPoints: slide.bulletPoints.filter((_, i) => i !== index) })
  }

  const moveSlide = (index: number, direction: 'up' | 'down') => {
    const newSlides = [...outline.slides]
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= newSlides.length) return
    ;[newSlides[index], newSlides[targetIndex]] = [newSlides[targetIndex], newSlides[index]]
    setOutline({ ...outline, slides: newSlides })
  }

  return (
    <div style={{ padding: 16 }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid #e8e8e8'
      }}>
        <div>
          <input
            className="input"
            value={outline.title}
            onChange={(e) => setOutline({ ...outline, title: e.target.value })}
            style={{ fontSize: 16, fontWeight: 'bold', border: 'none', background: 'transparent', padding: '4px 0' }}
          />
          <input
            className="input"
            value={outline.subtitle}
            onChange={(e) => setOutline({ ...outline, subtitle: e.target.value })}
            placeholder="副标题"
            style={{ fontSize: 13, color: '#999', border: 'none', background: 'transparent', padding: '2px 0' }}
          />
        </div>
        <button className="btn btn-sm btn-primary" onClick={addSlide}>+ 添加</button>
      </div>

      {outline.slides.map((slide, index) => (
        <div
          key={slide.id}
          onClick={() => setSelectedSlideId(slide.id)}
          style={{
            background: selectedSlideId === slide.id ? '#fff' : 'transparent',
            border: selectedSlideId === slide.id ? '2px solid #1B3A5C' : '2px solid transparent',
            borderRadius: 8,
            padding: 12,
            marginBottom: 8,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 8
          }}>
            <span style={{
              fontSize: 11, color: '#999', background: '#f0f0f0',
              padding: '2px 6px', borderRadius: 3
            }}>
              {index + 1} / {slide.layout === 'title' ? '封面' : '内容'}
            </span>
            <div style={{ display: 'flex', gap: 4 }}>
              <select
                className="select"
                value={slide.layout}
                onChange={(e) => updateSlide(slide.id, { layout: e.target.value as SlideOutline['layout'] })}
              >
                <option value="title">封面</option>
                <option value="content">内容</option>
                <option value="section">章节页</option>
                <option value="ending">结尾</option>
              </select>
              <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); moveSlide(index, 'up') }} disabled={index === 0}>↑</button>
              <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); moveSlide(index, 'down') }} disabled={index === outline.slides.length - 1}>↓</button>
              {confirmDelete === slide.id ? (
                <div style={{ display: 'flex', gap: 4 }}>
                  <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); deleteSlide(slide.id) }}>确认</button>
                  <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); setConfirmDelete(null) }}>取消</button>
                </div>
              ) : (
                <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); setConfirmDelete(slide.id) }}>×</button>
              )}
            </div>
          </div>

          <input
            className="input input-sm"
            value={slide.title}
            onChange={(e) => updateSlide(slide.id, { title: e.target.value })}
            placeholder="幻灯片标题"
            style={{ marginBottom: 6, fontWeight: 'bold' }}
            onClick={(e) => e.stopPropagation()}
          />

          {slide.bulletPoints.map((point, pIndex) => (
            <div key={pIndex} style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
              <span style={{ color: '#1B3A5C', fontSize: 12 }}>•</span>
              <input
                className="input input-sm"
                value={point}
                onChange={(e) => updateBulletPoint(slide.id, pIndex, e.target.value)}
                placeholder="要点内容"
                style={{ flex: 1 }}
                onClick={(e) => e.stopPropagation()}
              />
              <button
                className="btn btn-sm btn-danger"
                style={{ padding: '1px 6px', fontSize: 11 }}
                onClick={(e) => { e.stopPropagation(); removeBulletPoint(slide.id, pIndex) }}
              >×</button>
            </div>
          ))}
          <button
            className="btn btn-sm"
            style={{ marginTop: 4, fontSize: 11, color: '#1B3A5C' }}
            onClick={(e) => { e.stopPropagation(); addBulletPoint(slide.id) }}
          >+ 添加要点</button>

          <textarea
            className="input input-sm"
            value={slide.notes}
            onChange={(e) => updateSlide(slide.id, { notes: e.target.value })}
            placeholder="演讲备注（可选）"
            rows={2}
            style={{ marginTop: 6, resize: 'vertical' }}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      ))}
    </div>
  )
}

export default OutlineEditor
