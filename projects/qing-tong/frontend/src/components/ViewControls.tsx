interface ViewControlsProps {
  viewMode: 'original' | 'firstPerson' | 'free'
  onViewModeChange: (mode: 'original' | 'firstPerson' | 'free') => void
  currentFrame: number
  totalFrames: number
  onFrameChange: (frame: number) => void
}

export function ViewControls({ viewMode, onViewModeChange, currentFrame, totalFrames, onFrameChange }: ViewControlsProps) {
  const modes = [
    { key: 'original' as const, label: '原始视角', desc: '视频原始画面' },
    { key: 'firstPerson' as const, label: '第一人称', desc: '切换到场景中人物视角' },
    { key: 'free' as const, label: '自由视角', desc: '自由移动相机探索场景' },
  ]

  return (
    <div style={{ padding: '16px', borderTop: '1px solid #2a2a4a' }}>
      <h3 style={{ fontSize: '14px', marginBottom: '12px', color: '#ccc' }}>视角模式</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {modes.map(({ key, label, desc }) => (
          <button
            key={key}
            onClick={() => onViewModeChange(key)}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              border: viewMode === key ? '1px solid #667eea' : '1px solid #2a2a4a',
              background: viewMode === key ? 'linear-gradient(135deg, #1a1a3e, #2a2a5e)' : '#0a0a1a',
              color: viewMode === key ? '#fff' : '#888',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: 600 }}>{label}</div>
            <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>{desc}</div>
          </button>
        ))}
      </div>

      {viewMode === 'free' && (
        <div style={{
          marginTop: '12px',
          padding: '8px',
          background: '#0a0a1a',
          borderRadius: '4px',
          fontSize: '11px',
          color: '#666',
          lineHeight: 1.6,
        }}>
          操作说明：<br />
          - 鼠标左键拖拽：旋转视角<br />
          - 鼠标右键拖拽：平移视角<br />
          - 滚轮：缩放<br />
          - WASD：前后左右移动
        </div>
      )}
    </div>
  )
}
