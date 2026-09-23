import { ipcMain, dialog, BrowserWindow } from 'electron'
import { AIService, ProviderManager, ProviderConfig } from '../services/aiService'
import { PptGenerator } from '../services/pptGenerator'

const providerManager = new ProviderManager()
const aiService = new AIService(providerManager)
const pptGenerator = new PptGenerator()

export function registerIpcHandlers(mainWindow: BrowserWindow): void {
  ipcMain.handle('provider:get-all', async () => {
    return providerManager.getAll()
  })

  ipcMain.handle('provider:get-by-id', async (_event, id: string) => {
    return providerManager.getById(id)
  })

  ipcMain.handle('provider:get-active', async () => {
    return providerManager.getActive()
  })

  ipcMain.handle('provider:add', async (_event, provider: Omit<ProviderConfig, 'id'>) => {
    return providerManager.add(provider)
  })

  ipcMain.handle('provider:update', async (_event, id: string, updates: Partial<ProviderConfig>) => {
    return providerManager.update(id, updates)
  })

  ipcMain.handle('provider:delete', async (_event, id: string) => {
    return providerManager.delete(id)
  })

  ipcMain.handle('provider:set-default', async (_event, id: string) => {
    providerManager.setDefault(id)
    return true
  })

  ipcMain.handle('provider:test-connection', async (_event, provider: ProviderConfig) => {
    return aiService.testConnection(provider)
  })

  ipcMain.handle('provider:fetch-models', async (_event, provider: ProviderConfig) => {
    return aiService.fetchModels(provider)
  })

  ipcMain.handle('ai:generate-outline', async (_event, topic: string) => {
    return aiService.generateOutline(topic)
  })

  ipcMain.handle('ai:expand-content', async (_event, slideTitle: string, bulletPoints: string[]) => {
    return aiService.expandContent(slideTitle, bulletPoints)
  })

  ipcMain.handle('ai:refine-outline', async (_event, outlineJson: string) => {
    return aiService.refineOutline(outlineJson)
  })

  ipcMain.handle('ppt:export', async (_event, outline: unknown) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: '导出PPT',
      defaultPath: '医学演示文稿.pptx',
      filters: [{ name: 'PowerPoint', extensions: ['pptx'] }]
    })
    if (canceled || !filePath) return null
    const template = {
      name: '专业蓝',
      primaryColor: '1B3A5C',
      secondaryColor: '2E86AB',
      accentColor: 'A23B72',
      fontTitle: 'Microsoft YaHei',
      fontBody: 'Microsoft YaHei',
      backgroundColor: 'FFFFFF'
    }
    return pptGenerator.saveToFile(outline as any, template, filePath)
  })

  ipcMain.handle('ppt:generate', async (_event, outlineJson: string, templateJson: string) => {
    const outline = JSON.parse(outlineJson)
    const template = JSON.parse(templateJson)
    const result = await pptGenerator.generate(outline, template)
    return result
  })

  ipcMain.handle('ppt:save', async (_event, outlineJson: string, templateJson: string) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: '保存PPT',
      defaultPath: '医学演示文稿.pptx',
      filters: [{ name: 'PowerPoint', extensions: ['pptx'] }]
    })
    if (canceled || !filePath) return null
    const outline = JSON.parse(outlineJson)
    const template = JSON.parse(templateJson)
    return pptGenerator.saveToFile(outline, template, filePath)
  })

  ipcMain.handle('ppt:export-preview', async (_event, outlineJson: string, templateJson: string) => {
    const outline = JSON.parse(outlineJson)
    const template = JSON.parse(templateJson)
    return pptGenerator.generatePreviewData(outline, template)
  })
}
