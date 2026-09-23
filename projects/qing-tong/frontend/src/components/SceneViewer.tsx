import { useRef, useEffect, useCallback } from 'react'
import * as THREE from 'three'
import type { FrameData, VideoInfo } from '../App'

interface SceneViewerProps {
  frames: FrameData[]
  currentFrame: number
  viewMode: 'original' | 'firstPerson' | 'free'
  videoInfo: VideoInfo
}

// Number of depth layers for parallax rendering
const NUM_LAYERS = 10
// Maximum depth spread (how far apart the layers are)
const DEPTH_SPREAD = 3.0
// Camera movement speed for WASD
const MOVE_SPEED = 0.03

export function SceneViewer({ frames, currentFrame, viewMode, videoInfo }: SceneViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const layerGroupRef = useRef<THREE.Group | null>(null)
  const keysRef = useRef<Set<string>>(new Set())
  const animFrameRef = useRef<number>(0)
  const originalCameraPos = useRef<THREE.Vector3>(new THREE.Vector3(0, 0, 3))
  const originalCameraRot = useRef<THREE.Euler>(new THREE.Euler(0, 0, 0))

  // Create layered parallax meshes from RGB + Depth
  const createParallaxLayers = useCallback((rgb: HTMLImageElement, depth: HTMLImageElement, width: number, height: number) => {
    const group = new THREE.Group()
    const aspect = width / height
    const meshWidth = aspect * 2
    const meshHeight = 2

    // Read depth data
    const depthCanvas = document.createElement('canvas')
    depthCanvas.width = depth.width
    depthCanvas.height = depth.height
    const depthCtx = depthCanvas.getContext('2d')!
    depthCtx.drawImage(depth, 0, 0)
    const depthData = depthCtx.getImageData(0, 0, depth.width, depth.height).data

    // Read RGB data
    const rgbCanvas = document.createElement('canvas')
    rgbCanvas.width = rgb.width
    rgbCanvas.height = rgb.height
    const rgbCtx = rgbCanvas.getContext('2d')!
    rgbCtx.drawImage(rgb, 0, 0)
    const rgbData = rgbCtx.getImageData(0, 0, rgb.width, rgb.height).data

    const dw = depth.width
    const dh = depth.height
    const rw = rgb.width
    const rh = rgb.height

    // Build depth histogram to determine layer boundaries
    const depthValues: number[] = []
    for (let i = 0; i < dw * dh; i++) {
      depthValues.push(depthData[i * 4] / 255.0)
    }
    depthValues.sort((a, b) => a - b)

    // Create layer boundaries using percentile-based splitting
    const layerBoundaries: number[] = [0]
    for (let i = 1; i < NUM_LAYERS; i++) {
      const idx = Math.floor((i / NUM_LAYERS) * depthValues.length)
      layerBoundaries.push(depthValues[Math.min(idx, depthValues.length - 1)])
    }
    layerBoundaries.push(1.0)

    // Create each layer
    for (let layerIdx = 0; layerIdx < NUM_LAYERS; layerIdx++) {
      const minDepth = layerBoundaries[layerIdx]
      const maxDepth = layerBoundaries[layerIdx + 1]

      // Z position: back layers (high depth value = far) are further away
      const avgDepth = (minDepth + maxDepth) / 2
      const zPos = avgDepth * DEPTH_SPREAD

      // Create layer texture canvas
      const layerCanvas = document.createElement('canvas')
      layerCanvas.width = rw
      layerCanvas.height = rh
      const layerCtx = layerCanvas.getContext('2d')!

      // Start with transparent background
      layerCtx.clearRect(0, 0, rw, rh)

      // Create image data for this layer
      const layerImgData = layerCtx.createImageData(rw, rh)

      for (let y = 0; y < rh; y++) {
        for (let x = 0; x < rw; x++) {
          // Map to depth map coordinates
          const dx = Math.floor((x / rw) * dw)
          const dy = Math.floor((y / rh) * dh)
          const depthVal = depthData[(dy * dw + dx) * 4] / 255.0

          const outIdx = (y * rw + x) * 4
          const inIdx = (y * rw + x) * 4

          if (depthVal >= minDepth && depthVal < maxDepth) {
            // This pixel belongs to this layer
            layerImgData.data[outIdx] = rgbData[inIdx]
            layerImgData.data[outIdx + 1] = rgbData[inIdx + 1]
            layerImgData.data[outIdx + 2] = rgbData[inIdx + 2]
            layerImgData.data[outIdx + 3] = 255
          } else {
            // Transparent - but we need to fill background layers
            // For layers behind, fill with nearest depth color to avoid gaps
            layerImgData.data[outIdx + 3] = 0
          }
        }
      }

      layerCtx.putImageData(layerImgData, 0, 0)

      // For background layers, also paint the full image with reduced opacity
      // to fill gaps between layers
      if (layerIdx >= NUM_LAYERS / 2) {
        layerCtx.globalCompositeOperation = 'destination-over'
        layerCtx.globalAlpha = 0.3
        layerCtx.drawImage(rgb, 0, 0, rw, rh)
        layerCtx.globalAlpha = 1.0
        layerCtx.globalCompositeOperation = 'source-over'
      }

      // Create Three.js texture
      const texture = new THREE.CanvasTexture(layerCanvas)
      texture.minFilter = THREE.LinearFilter
      texture.magFilter = THREE.LinearFilter
      texture.generateMipmaps = false

      // Create plane geometry
      const geometry = new THREE.PlaneGeometry(meshWidth, meshHeight)
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: layerIdx === NUM_LAYERS - 1, // Only back layer writes depth
      })

      const mesh = new THREE.Mesh(geometry, material)
      mesh.position.z = -zPos

      group.add(mesh)
    }

    // Add a full background layer at the very back
    const bgCanvas = document.createElement('canvas')
    bgCanvas.width = rw
    bgCanvas.height = rh
    const bgCtx = bgCanvas.getContext('2d')!
    bgCtx.drawImage(rgb, 0, 0, rw, rh)
    // Apply slight blur to background for depth-of-field feel
  const bgTexture = new THREE.CanvasTexture(bgCanvas)
    bgTexture.minFilter = THREE.LinearFilter
    bgTexture.magFilter = THREE.LinearFilter

    const bgGeometry = new THREE.PlaneGeometry(meshWidth * 1.1, meshHeight * 1.1)
    const bgMaterial = new THREE.MeshBasicMaterial({
      map: bgTexture,
      side: THREE.DoubleSide,
      depthWrite: true,
    })
    const bgMesh = new THREE.Mesh(bgGeometry, bgMaterial)
    bgMesh.position.z = -DEPTH_SPREAD - 0.1
    group.add(bgMesh)

    return group
  }, [])

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // Scene
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0a)
    sceneRef.current = scene

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 100)
    camera.position.set(0, 0, 1)
    cameraRef.current = camera

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Add ambient grid for spatial reference
    const gridHelper = new THREE.GridHelper(20, 40, 0x222244, 0x111133)
    gridHelper.position.y = -1.5
    scene.add(gridHelper)

    // Mouse controls for free view
    let isDragging = false
    let isRightDragging = false
    let prevMouse = { x: 0, y: 0 }
    let yaw = 0
    let pitch = 0

    const onMouseDown = (e: MouseEvent) => {
      if (e.button === 0) isDragging = true
      if (e.button === 2) isRightDragging = true
      prevMouse = { x: e.clientX, y: e.clientY }
    }

    const onMouseMove = (e: MouseEvent) => {
      const dx = e.clientX - prevMouse.x
      const dy = e.clientY - prevMouse.y
      prevMouse = { x: e.clientX, y: e.clientY }

      if (viewMode !== 'free') return

      if (isDragging) {
        yaw -= dx * 0.003
        pitch -= dy * 0.003
        pitch = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, pitch))
        camera.rotation.order = 'YXZ'
        camera.rotation.y = yaw
        camera.rotation.x = pitch
      }

      if (isRightDragging) {
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion)
        const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion)
        camera.position.addScaledVector(right, -dx * 0.003)
        camera.position.addScaledVector(up, dy * 0.003)
      }
    }

    const onMouseUp = () => {
      isDragging = false
      isRightDragging = false
    }

    const onWheel = (e: WheelEvent) => {
      if (viewMode !== 'free') return
      const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion)
      camera.position.addScaledVector(forward, e.deltaY * 0.003)
    }

    const onKeyDown = (e: KeyboardEvent) => {
      keysRef.current.add(e.key.toLowerCase())
    }

    const onKeyUp = (e: KeyboardEvent) => {
      keysRef.current.delete(e.key.toLowerCase())
    }

    const onContextMenu = (e: Event) => e.preventDefault()

    container.addEventListener('mousedown', onMouseDown)
    container.addEventListener('mousemove', onMouseMove)
    container.addEventListener('mouseup', onMouseUp)
    container.addEventListener('wheel', onWheel)
    container.addEventListener('contextmenu', onContextMenu)
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)

    // Resize handler
    const onResize = () => {
      const w = container.clientWidth
      const h = container.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', onResize)

    // Animation loop
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate)

      // WASD movement
      if (viewMode === 'free' && cameraRef.current) {
        const cam = cameraRef.current
        const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion)
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion)

        if (keysRef.current.has('w')) cam.position.addScaledVector(forward, MOVE_SPEED)
        if (keysRef.current.has('s')) cam.position.addScaledVector(forward, -MOVE_SPEED)
        if (keysRef.current.has('a')) cam.position.addScaledVector(right, -MOVE_SPEED)
        if (keysRef.current.has('d')) cam.position.addScaledVector(right, MOVE_SPEED)
      }

      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
      container.removeEventListener('mousedown', onMouseDown)
      container.removeEventListener('mousemove', onMouseMove)
      container.removeEventListener('mouseup', onMouseUp)
      container.removeEventListener('wheel', onWheel)
      container.removeEventListener('contextmenu', onContextMenu)
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      window.removeEventListener('resize', onResize)
      renderer.dispose()
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, []) // Only init once

  // Update layers when frame changes
  useEffect(() => {
    if (!sceneRef.current || currentFrame >= frames.length) return

    const frame = frames[currentFrame]
    let cancelled = false

    const loadTextures = async () => {
      const [rgbImg, depthImg] = await Promise.all([
        new Promise<HTMLImageElement>((resolve, reject) => {
          const img = new Image()
          img.crossOrigin = 'anonymous'
          img.onload = () => resolve(img)
          img.onerror = reject
          img.src = frame.imageUrl
        }),
        new Promise<HTMLImageElement>((resolve, reject) => {
          const img = new Image()
          img.crossOrigin = 'anonymous'
          img.onload = () => resolve(img)
          img.onerror = reject
          img.src = frame.depthUrl
        }),
      ])
      return { rgb: rgbImg, depth: depthImg }
    }

    loadTextures().then(({ rgb, depth }) => {
      if (cancelled) return

      // Remove old layers
      if (layerGroupRef.current) {
        sceneRef.current!.remove(layerGroupRef.current)
        layerGroupRef.current.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.geometry.dispose()
            if (child.material instanceof THREE.Material) {
              if ((child.material as THREE.MeshBasicMaterial).map) {
                (child.material as THREE.MeshBasicMaterial).map!.dispose()
              }
              child.material.dispose()
            }
          }
        })
      }

      // Create new parallax layers
      const group = createParallaxLayers(rgb, depth, videoInfo.width, videoInfo.height)
      sceneRef.current!.add(group)
      layerGroupRef.current = group
    })

    return () => { cancelled = true }
  }, [currentFrame, frames, createParallaxLayers, videoInfo])

  // Update camera based on view mode
  useEffect(() => {
    if (!cameraRef.current) return
    const camera = cameraRef.current

    switch (viewMode) {
      case 'original': {
        // Default front view - see the layered scene from the front
        camera.position.set(0, 0, 1)
        camera.rotation.set(0, 0, 0)
        camera.fov = 60
        camera.updateProjectionMatrix()
        break
      }
      case 'firstPerson': {
        // Move camera slightly into the scene for immersive feel
        camera.position.set(0, 0, -0.5)
        camera.rotation.set(0, 0, 0)
        camera.fov = 90 // Wider FOV for immersive feel
        camera.updateProjectionMatrix()
        break
      }
      case 'free': {
        // Free camera mode
        camera.position.set(0, 0, 1)
        camera.rotation.set(0, 0, 0)
        camera.fov = 75
        camera.updateProjectionMatrix()
        break
      }
    }
  }, [viewMode])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        cursor: viewMode === 'free' ? 'grab' : 'default',
      }}
    />
  )
}
