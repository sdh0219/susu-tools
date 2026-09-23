export interface SlideOutline {
  id: string
  title: string
  bulletPoints: string[]
  notes: string
  layout: 'title' | 'content' | 'section' | 'ending'
}

export interface Outline {
  title: string
  subtitle: string
  slides: SlideOutline[]
}

export interface ProviderConfig {
  id: string
  name: string
  apiKey: string
  baseUrl: string
  modelName: string
  enabled: boolean
  isDefault: boolean
}

export interface PptTemplate {
  name: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  fontTitle: string
  fontBody: string
  backgroundColor: string
}

export interface AppStore {
  outline: Outline
  setOutline: (outline: Outline) => void
  updateSlide: (id: string, slide: Partial<SlideOutline>) => void
  addSlide: (index: number) => void
  removeSlide: (id: string) => void
  moveSlide: (fromIndex: number, toIndex: number) => void
  providers: ProviderConfig[]
  setProviders: (providers: ProviderConfig[]) => void
  activeProvider: ProviderConfig | null
  setActiveProvider: (provider: ProviderConfig | null) => void
  generating: boolean
  setGenerating: (val: boolean) => void
  currentTemplate: PptTemplate
  setCurrentTemplate: (template: PptTemplate) => void
  selectedSlideId: string | null
  setSelectedSlideId: (id: string | null) => void
  pptFilePath: string | null
  setPptFilePath: (path: string | null) => void
  showSettings: boolean
  setShowSettings: (val: boolean) => void
}
