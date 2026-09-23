import React, { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import type { ProviderConfig } from '../types'

declare global {
  interface Window {
    electronAPI: {
      providerGetAll: () => Promise<ProviderConfig[]>
      providerGetById: (id: string) => Promise<ProviderConfig | undefined>
      providerGetActive: () => Promise<ProviderConfig | undefined>
      providerAdd: (provider: Omit<ProviderConfig, 'id'>) => Promise<ProviderConfig>
      providerUpdate: (id: string, updates: Partial<ProviderConfig>) => Promise<ProviderConfig | undefined>
      providerDelete: (id: string) => Promise<boolean>
      providerSetDefault: (id: string) => Promise<boolean>
      providerTestConnection: (provider: ProviderConfig) => Promise<boolean>
      providerFetchModels: (provider: ProviderConfig) => Promise<string[]>
      aiGenerateOutline: (topic: string) => Promise<string>
      aiExpandContent: (slideTitle: string, bulletPoints: string[]) => Promise<string>
      aiRefineOutline: (outlineJson: string) => Promise<string>
      pptExport: (outline: unknown) => Promise<string | null>
      pptGenerate: (outlineJson: string, templateJson: string) => Promise<unknown>
      pptSave: (outlineJson: string, templateJson: string) => Promise<string | null>
      pptExportPreview: (outlineJson: string, templateJson: string) => Promise<unknown[]>
    }
  }
}

const Settings: React.FC = () => {
  const { providers, setProviders, setActiveProvider, setShowSettings } = useStore()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<Record<string, 'success' | 'fail' | 'testing'>>({})
  const [fetchingModels, setFetchingModels] = useState<string | null>(null)
  const [modelOptions, setModelOptions] = useState<Record<string, string[]>>({})

  const [formData, setFormData] = useState({
    name: '',
    apiKey: '',
    baseUrl: '',
    modelName: '',
    enabled: true,
    isDefault: false
  })

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    const list = await window.electronAPI.providerGetAll()
    setProviders(list)
    const active = await window.electronAPI.providerGetActive()
    setActiveProvider(active || null)
  }

  const resetForm = () => {
    setFormData({ name: '', apiKey: '', baseUrl: '', modelName: '', enabled: true, isDefault: false })
    setEditingId(null)
    setShowAddForm(false)
  }

  const handleEdit = (provider: ProviderConfig) => {
    setFormData({
      name: provider.name,
      apiKey: provider.apiKey,
      baseUrl: provider.baseUrl,
      modelName: provider.modelName,
      enabled: provider.enabled,
      isDefault: provider.isDefault
    })
    setEditingId(provider.id)
    setShowAddForm(true)
  }

  const handleSave = async () => {
    if (!formData.name || !formData.baseUrl) return

    if (editingId) {
      await window.electronAPI.providerUpdate(editingId, formData)
    } else {
      await window.electronAPI.providerAdd(formData)
    }
    resetForm()
    await loadProviders()
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('确定要删除这个模型供应商吗？')) return
    await window.electronAPI.providerDelete(id)
    await loadProviders()
  }

  const handleSetDefault = async (id: string) => {
    await window.electronAPI.providerSetDefault(id)
    await loadProviders()
  }

  const handleTest = async (provider: ProviderConfig) => {
    setTesting(provider.id)
    setTestResult((prev) => ({ ...prev, [provider.id]: 'testing' }))
    try {
      const result = await window.electronAPI.providerTestConnection(provider)
      setTestResult((prev) => ({ ...prev, [provider.id]: result ? 'success' : 'fail' }))
    } catch {
      setTestResult((prev) => ({ ...prev, [provider.id]: 'fail' }))
    }
    setTesting(null)
  }

  const handleFetchModels = async (provider: ProviderConfig) => {
    setFetchingModels(provider.id)
    try {
      const models = await window.electronAPI.providerFetchModels(provider)
      setModelOptions((prev) => ({ ...prev, [provider.id]: models }))
    } catch {
      setModelOptions((prev) => ({ ...prev, [provider.id]: [] }))
    }
    setFetchingModels(null)
  }

  return (
    <div className="settings-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <h2>⚙️ 模型设置</h2>
          <button className="btn" onClick={() => setShowSettings(false)}>✕ 关闭</button>
        </div>

        <div className="settings-body">
          <div className="settings-sidebar">
            <div className="settings-sidebar-title">模型供应商</div>
            <button className="btn btn-primary btn-block" onClick={() => { resetForm(); setShowAddForm(true) }}>
              + 添加供应商
            </button>
            <div className="provider-list">
              {providers.map((p) => (
                <div
                  key={p.id}
                  className={`provider-card ${p.isDefault ? 'active' : ''} ${editingId === p.id ? 'editing' : ''}`}
                  onClick={() => handleEdit(p)}
                >
                  <div className="provider-card-header">
                    <span className="provider-name">{p.name}</span>
                    {p.isDefault && <span className="badge badge-primary">默认</span>}
                    {p.apiKey && p.enabled ? (
                      <span className="badge badge-success">已配置</span>
                    ) : (
                      <span className="badge badge-warning">未配置</span>
                    )}
                  </div>
                  <div className="provider-card-meta">
                    <span className="provider-model">{p.modelName}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="settings-content">
            {showAddForm ? (
              <div className="provider-form">
                <h3>{editingId ? '编辑供应商' : '新增供应商'}</h3>
                <div className="form-group">
                  <label>供应商名称</label>
                  <input
                    className="input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="例如：DeepSeek"
                  />
                </div>
                <div className="form-group">
                  <label>API Key</label>
                  <input
                    className="input"
                    type="password"
                    value={formData.apiKey}
                    onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                    placeholder="输入你的API Key"
                  />
                  <small className="form-hint">API密钥是敏感信息，请勿分享给他人</small>
                </div>
                <div className="form-group">
                  <label>API 地址 (Base URL)</label>
                  <input
                    className="input"
                    value={formData.baseUrl}
                    onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                    placeholder="例如：https://api.deepseek.com/v1"
                  />
                  <small className="form-hint">需兼容OpenAI SDK接口格式</small>
                </div>
                <div className="form-group">
                  <label>模型名称</label>
                  <input
                    className="input"
                    value={formData.modelName}
                    onChange={(e) => setFormData({ ...formData, modelName: e.target.value })}
                    placeholder="例如：deepseek-chat"
                    list={editingId ? `model-options-${editingId}` : 'model-options-new'}
                  />
                  {modelOptions[editingId || 'new'] && (
                    <datalist id={`model-options-${editingId || 'new'}`}>
                      {modelOptions[editingId || 'new'].map((m) => (
                        <option key={m} value={m} />
                      ))}
                    </datalist>
                  )}
                  {editingId && formData.apiKey && formData.baseUrl && (
                    <button
                      className="btn btn-sm"
                      onClick={() => handleFetchModels({
                        id: editingId, name: formData.name, apiKey: formData.apiKey,
                        baseUrl: formData.baseUrl, modelName: formData.modelName,
                        enabled: formData.enabled, isDefault: formData.isDefault
                      })}
                      disabled={fetchingModels === editingId}
                    >
                      {fetchingModels === editingId ? '加载中...' : '🔄 获取模型列表'}
                    </button>
                  )}
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.enabled}
                      onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    />
                    启用此供应商
                  </label>
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.isDefault}
                      onChange={(e) => setFormData({ ...formData, isDefault: e.target.checked })}
                    />
                    设为默认供应商
                  </label>
                </div>
                <div className="form-actions">
                  <button className="btn btn-primary" onClick={handleSave}>
                    {editingId ? '保存修改' : '保存创建'}
                  </button>
                  {editingId && formData.apiKey && formData.baseUrl && (
                    <button
                      className="btn"
                      onClick={() => handleTest({
                        id: editingId, name: formData.name, apiKey: formData.apiKey,
                        baseUrl: formData.baseUrl, modelName: formData.modelName,
                        enabled: formData.enabled, isDefault: formData.isDefault
                      })}
                      disabled={testing === editingId}
                    >
                      {testing === editingId ? '测试中...' : '🔗 测试连通性'}
                    </button>
                  )}
                  <button className="btn" onClick={resetForm}>取消</button>
                </div>
                {testResult[editingId || ''] && (
                  <div className={`test-result ${testResult[editingId || '']}`}>
                    {testResult[editingId || ''] === 'success' ? '✅ 连接成功！' : '❌ 连接失败，请检查配置'}
                  </div>
                )}
              </div>
            ) : (
              <div className="settings-empty">
                <div className="settings-empty-icon">🤖</div>
                <h3>配置你的AI模型供应商</h3>
                <p>选择左侧已有供应商进行编辑，或点击"添加供应商"配置新的模型。</p>
                <p>支持所有兼容OpenAI SDK接口的模型供应商，如DeepSeek、通义千问、OpenAI等。</p>
                <div className="quick-start">
                  <h4>快速开始</h4>
                  <ol>
                    <li>选择一个供应商，填入API Key</li>
                    <li>点击"测试连通性"验证配置</li>
                    <li>设为默认供应商即可开始使用</li>
                  </ol>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
