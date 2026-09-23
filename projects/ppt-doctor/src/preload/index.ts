import { contextBridge, ipcRenderer } from 'electron'

export interface ProviderConfig {
  id: string
  name: string
  apiKey: string
  baseUrl: string
  modelName: string
  enabled: boolean
  isDefault: boolean
}

export interface ElectronAPI {
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

const api: ElectronAPI = {
  providerGetAll: () => ipcRenderer.invoke('provider:get-all'),
  providerGetById: (id: string) => ipcRenderer.invoke('provider:get-by-id', id),
  providerGetActive: () => ipcRenderer.invoke('provider:get-active'),
  providerAdd: (provider: Omit<ProviderConfig, 'id'>) => ipcRenderer.invoke('provider:add', provider),
  providerUpdate: (id: string, updates: Partial<ProviderConfig>) =>
    ipcRenderer.invoke('provider:update', id, updates),
  providerDelete: (id: string) => ipcRenderer.invoke('provider:delete', id),
  providerSetDefault: (id: string) => ipcRenderer.invoke('provider:set-default', id),
  providerTestConnection: (provider: ProviderConfig) =>
    ipcRenderer.invoke('provider:test-connection', provider),
  providerFetchModels: (provider: ProviderConfig) =>
    ipcRenderer.invoke('provider:fetch-models', provider),
  aiGenerateOutline: (topic: string) => ipcRenderer.invoke('ai:generate-outline', topic),
  aiExpandContent: (slideTitle: string, bulletPoints: string[]) =>
    ipcRenderer.invoke('ai:expand-content', slideTitle, bulletPoints),
  aiRefineOutline: (outlineJson: string) => ipcRenderer.invoke('ai:refine-outline', outlineJson),
  pptExport: (outline: unknown) => ipcRenderer.invoke('ppt:export', outline),
  pptGenerate: (outlineJson: string, templateJson: string) =>
    ipcRenderer.invoke('ppt:generate', outlineJson, templateJson),
  pptSave: (outlineJson: string, templateJson: string) =>
    ipcRenderer.invoke('ppt:save', outlineJson, templateJson),
  pptExportPreview: (outlineJson: string, templateJson: string) =>
    ipcRenderer.invoke('ppt:export-preview', outlineJson, templateJson)
}

contextBridge.exposeInMainWorld('electronAPI', api)
