declare global {
  interface Window {
    electronAPI: {
      ollamaCheckStatus: () => Promise<{
        installed: boolean
        running: boolean
        modelReady: boolean
        modelName: string
      }>
      ollamaInstall: () => Promise<boolean>
      ollamaPullModel: (modelName: string) => Promise<void>
      ollamaStart: () => Promise<boolean>
      aiGenerateOutline: (topic: string) => Promise<string>
      aiExpandContent: (slideTitle: string, bulletPoints: string[]) => Promise<string>
      aiRefineOutline: (outlineJson: string) => Promise<string>
      pptExport: (outline: import('./index').Outline) => Promise<string | null>
      pptGenerate: (outlineJson: string, templateJson: string) => Promise<unknown>
      pptSave: (outlineJson: string, templateJson: string) => Promise<string | null>
      pptExportPreview: (outlineJson: string, templateJson: string) => Promise<unknown[]>
      onOllamaDownloadProgress: (callback: (data: { status: string; progress: number }) => void) => () => void
      onOllamaInstallProgress: (
        callback: (data: { status: string; message: string; progress?: number }) => void
      ) => () => void
    }
  }
}

export {}
