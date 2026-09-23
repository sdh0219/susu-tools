import React from 'react'
import { useStore } from '../store/useStore'

const ModelStatus: React.FC = () => {
  const activeProvider = useStore((s) => s.activeProvider)

  if (activeProvider && activeProvider.apiKey) {
    return (
      <span className="tag tag-success">
        ● {activeProvider.name} · {activeProvider.modelName}
      </span>
    )
  }
  return <span className="tag tag-error">● 未配置模型</span>
}

export default ModelStatus
