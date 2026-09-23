import { useState } from 'react'
import { VideoUploader } from './components/VideoUploader'
import { SceneViewer } from './components/SceneViewer'
import { ViewControls } from './components/ViewControls'

export interface FrameData {
  frameIndex: number
  imageUrl: string
  depthUrl: string
  width: number
  height: number
}

export interface VideoInfo {
  totalFrames: number
  fps: number
  width: number
  height: number
  taskId: string
}

function App() {
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [frames, setFrames] = useState<FrameData[]>([])
  const [currentFrame, setCurrentFrame] = useState(0)
  const [viewMode, setViewMode] = useState<'original' | 'firstPerson' | 'free'>('original')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState('')

  const handleVideoProcessed = (info: VideoInfo, frameData: FrameData[]) => {
    setVideoInfo(info)
    setFrames(frameData)
    setCurrentFrame(0)
  }

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        padding: '12px 24px',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        borderBottom: '1px solid #2a2a4a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 style={{
            fontSize: '20px',
            fontWeight: 700,
            background: 'linear-gradient(90deg, #667eea, #764ba2)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            千瞳
          </h1>
          <span style={{ fontSize: '12px', color: '#888' }}>视角转换器 v0.1</span>
        </div>
        {videoInfo && (
          <div style={{ fontSize: '12px', color: '#aaa' }}>
            {videoInfo.width}x{videoInfo.height} | {videoInfo.fps}fps | {videoInfo.totalFrames}帧
          </div>
        )}
      </header>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Panel - Controls */}
        <div style={{
          width: '320px',
          background: '#111122',
          borderRight: '1px solid #2a2a4a',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto',
          flexShrink: 0,
        }}>
          <VideoUploader
            onProcessed={handleVideoProcessed}
            processing={processing}
            setProcessing={setProcessing}
            progress={progress}
            setProgress={setProgress}
          />

          {frames.length > 0 && (
            <>
              <ViewControls
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                currentFrame={currentFrame}
                totalFrames={frames.length}
                onFrameChange={setCurrentFrame}
              />

              {/* Frame Preview */}
              <div style={{ padding: '16px' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                  当前帧: {currentFrame + 1} / {frames.length}
                </div>
                <input
                  type="range"
                  min={0}
                  max={frames.length - 1}
                  value={currentFrame}
                  onChange={(e) => setCurrentFrame(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
            </>
          )}
        </div>

        {/* Right Panel - 3D Viewer */}
        <div style={{ flex: 1, position: 'relative' }}>
          {frames.length > 0 ? (
            <SceneViewer
              frames={frames}
              currentFrame={currentFrame}
              viewMode={viewMode}
              videoInfo={videoInfo!}
            />
          ) : (
            <div style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '16px',
              color: '#555',
            }}>
              <div style={{ fontSize: '48px' }}>&#x1F441;</div>
              <div style={{ fontSize: '16px' }}>上传视频开始体验视角切换</div>
              <div style={{ fontSize: '12px', maxWidth: '400px', textAlign: 'center', lineHeight: 1.6 }}>
                支持将普通2D视频转换为可交互的3D场景，<br />
                你可以在场景中自由移动相机，切换第一人称视角
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
