import React from 'react'
import { useStore } from '../store/useStore'
import type { SlideOutline } from '../types'

const PptPreview: React.FC = () => {
  const outline = useStore((s) => s.outline)
  const selectedSlideId = useStore((s) => s.selectedSlideId)

  if (!outline) {
    return (
      <div className="empty-state" style={{ height: '100%' }}>
        <div className="empty-state-icon">📊</div>
        <div className="empty-state-text">生成大纲后，PPT预览将在此显示</div>
      </div>
    )
  }

  const selectedSlide = outline.slides.find((s) => s.id === selectedSlideId)

  const renderSlide = (slide: SlideOutline, index: number) => {
    const isSelected = slide.id === selectedSlideId
    const isTitleSlide = slide.layout === 'title'
    const isSectionSlide = slide.layout === 'section'
    const isEndingSlide = slide.layout === 'ending'

    return (
      <div
        key={slide.id}
        onClick={() => useStore.getState().setSelectedSlideId(slide.id)}
        style={{
          width: '100%', aspectRatio: '16/9',
          background: isTitleSlide
            ? 'linear-gradient(135deg, #1B3A5C 0%, #2E86AB 100%)'
            : isSectionSlide
            ? 'linear-gradient(135deg, #2E86AB 0%, #1B3A5C 100%)'
            : isEndingSlide
            ? 'linear-gradient(135deg, #1B3A5C 0%, #2E86AB 100%)'
            : '#fff',
          borderRadius: 8,
          padding: isTitleSlide || isSectionSlide || isEndingSlide ? '10% 8%' : '6% 8%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: isTitleSlide || isSectionSlide || isEndingSlide ? 'center' : 'flex-start',
          alignItems: isTitleSlide || isSectionSlide || isEndingSlide ? 'center' : 'flex-start',
          cursor: 'pointer',
          border: isSelected ? '3px solid #1B3A5C' : '3px solid transparent',
          boxShadow: isSelected ? '0 4px 16px rgba(27,58,92,0.2)' : '0 2px 8px rgba(0,0,0,0.08)',
          transition: 'all 0.2s',
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        {isTitleSlide ? (
          <>
            <div style={{
              fontSize: 'clamp(14px, 2.5vw, 24px)', fontWeight: 'bold',
              color: '#fff', textAlign: 'center', marginBottom: 12,
              lineHeight: 1.3
            }}>
              {slide.title || outline.title}
            </div>
            <div style={{
              fontSize: 'clamp(9px, 1.5vw, 14px)', color: 'rgba(255,255,255,0.8)',
              textAlign: 'center'
            }}>
              {slide.bulletPoints[0] || outline.subtitle || ''}
            </div>
          </>
        ) : isSectionSlide ? (
          <div style={{
            fontSize: 'clamp(16px, 3vw, 28px)', fontWeight: 'bold',
            color: '#fff', textAlign: 'center'
          }}>
            {slide.title}
          </div>
        ) : isEndingSlide ? (
          <>
            <div style={{
              fontSize: 'clamp(16px, 3vw, 28px)', fontWeight: 'bold',
              color: '#fff', textAlign: 'center', marginBottom: 8
            }}>
              {slide.title || '谢谢！'}
            </div>
            {slide.bulletPoints.filter(Boolean).length > 0 && (
              <div style={{
                fontSize: 'clamp(9px, 1.5vw, 14px)', color: 'rgba(255,255,255,0.8)',
                textAlign: 'center'
              }}>
                {slide.bulletPoints.filter(Boolean).join(' · ')}
              </div>
            )}
          </>
        ) : (
          <>
            <div style={{
              fontSize: 'clamp(12px, 2vw, 20px)', fontWeight: 'bold',
              color: '#1B3A5C', marginBottom: 12, paddingBottom: 8,
              borderBottom: '2px solid #2E86AB', width: '100%'
            }}>
              {slide.title}
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              {slide.bulletPoints.filter(Boolean).map((point, pIndex) => (
                <div key={pIndex} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 8,
                  marginBottom: 6, fontSize: 'clamp(9px, 1.5vw, 14px)',
                  color: '#444', lineHeight: 1.5
                }}>
                  <span style={{
                    color: '#2E86AB', fontWeight: 'bold', flexShrink: 0, marginTop: 2
                  }}>●</span>
                  <span>{point}</span>
                </div>
              ))}
            </div>
          </>
        )}
        <div style={{
          position: 'absolute', bottom: 4, right: 8,
          fontSize: 'clamp(7px, 1vw, 10px)', color: isTitleSlide || isSectionSlide || isEndingSlide ? 'rgba(255,255,255,0.4)' : '#ccc'
        }}>
          {index + 1}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h3 style={{ marginBottom: 16, color: '#1B3A5C', fontSize: 16 }}>
        📊 PPT预览 <span style={{ fontWeight: 'normal', color: '#999', fontSize: 13 }}>（共{outline.slides.length}页）</span>
      </h3>
      {selectedSlide && (
        <div style={{ marginBottom: 24, maxWidth: 720, margin: '0 auto 24px' }}>
          {renderSlide(selectedSlide, outline.slides.indexOf(selectedSlide))}
        </div>
      )}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 16,
        maxWidth: 1200,
        margin: '0 auto'
      }}>
        {outline.slides.map((slide, index) => renderSlide(slide, index))}
      </div>
    </div>
  )
}

export default PptPreview
