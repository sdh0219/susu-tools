import { useRef, useCallback } from 'react'
import axios from 'axios'
import type { FrameData, VideoInfo } from '../App'

interface VideoUploaderProps {
  onProcessed: (info: VideoInfo, frames: FrameData[]) => void
  processing: boolean
  setProcessing: (v: boolean) => void
  progress: string
  setProgress: (v: string) => void
}

export function VideoUploader({ onProcessed, processing, setProcessing, progress, setProgress }: VideoUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUpload = useCallback(async (file: File) => {
    setProcessing(true)
    setProgress('上传视频中...')

    try {
      const formData = new FormData()
      formData.append('video', file)

      // Step 1: Upload and start processing
      const uploadRes = await axios.post('/api/video/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const { task_id, total_frames, fps, width, height } = uploadRes.data

      setProgress(`视频已上传，正在提取帧和估计深度...`)

      // Step 2: Poll for processing status
      let completed = false
      while (!completed) {
        await new Promise(r => setTimeout(r, 2000))
        const statusRes = await axios.get(`/api/video/status/${task_id}`)
        const { status, progress: pct, current_frame } = statusRes.data

        if (status === 'completed') {
          completed = true
          setProgress('处理完成，加载帧数据...')
        } else if (status === 'failed') {
          throw new Error('处理失败')
        } else {
          setProgress(`处理中... ${pct}% (帧 ${current_frame}/${total_frames})`)
        }
      }

      // Step 3: Load frame data
      const framesRes = await axios.get(`/api/video/frames/${task_id}`)
      const frameUrls: FrameData[] = framesRes.data.frames.map((f: any) => ({
        frameIndex: f.index,
        imageUrl: `/api/video/frame/${task_id}/${f.index}/rgb`,
        depthUrl: `/api/video/frame/${task_id}/${f.index}/depth`,
        width,
        height,
      }))

      onProcessed({ totalFrames: total_frames, fps, width, height, taskId: task_id }, frameUrls)
      setProgress('')
    } catch (err: any) {
      setProgress(`错误: ${err.message}`)
    } finally {
      setProcessing(false)
    }
  }, [onProcessed, setProcessing, setProgress])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '14px', marginBottom: '12px', color: '#ccc' }}>视频上传</h3>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: '2px dashed #333',
          borderRadius: '8px',
          padding: '24px',
          textAlign: 'center',
          cursor: processing ? 'wait' : 'pointer',
          transition: 'border-color 0.2s',
          background: '#0a0a1a',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        {processing ? (
          <div>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>&#x23F3;</div>
            <div style={{ fontSize: '12px', color: '#aaa' }}>{progress}</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>&#x1F4F9;</div>
            <div style={{ fontSize: '12px', color: '#888' }}>点击或拖拽上传视频</div>
            <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>支持 MP4, AVI, MOV</div>
          </div>
        )}
      </div>
    </div>
  )
}
