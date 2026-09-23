import { create } from 'zustand'
import type { AppStore, Outline, SlideOutline, ProviderConfig, PptTemplate } from '../types'

const defaultTemplate: PptTemplate = {
  name: '专业蓝',
  primaryColor: '1B3A5C',
  secondaryColor: '2E86AB',
  accentColor: 'A23B72',
  fontTitle: 'Microsoft YaHei',
  fontBody: 'Microsoft YaHei',
  backgroundColor: 'FFFFFF'
}

const defaultOutline: Outline = {
  title: '',
  subtitle: '',
  slides: []
}

export const useStore = create<AppStore>((set) => ({
  outline: defaultOutline,
  setOutline: (outline: Outline) => set({ outline }),
  updateSlide: (id: string, slide: Partial<SlideOutline>) =>
    set((state) => ({
      outline: {
        ...state.outline,
        slides: state.outline.slides.map((s) => (s.id === id ? { ...s, ...slide } : s))
      }
    })),
  addSlide: (index: number) =>
    set((state) => {
      const newSlide: SlideOutline = {
        id: `slide-${Date.now()}`,
        title: '新幻灯片',
        bulletPoints: ['要点1'],
        notes: '',
        layout: 'content'
      }
      const slides = [...state.outline.slides]
      slides.splice(index + 1, 0, newSlide)
      return { outline: { ...state.outline, slides } }
    }),
  removeSlide: (id: string) =>
    set((state) => ({
      outline: {
        ...state.outline,
        slides: state.outline.slides.filter((s) => s.id !== id)
      }
    })),
  moveSlide: (fromIndex: number, toIndex: number) =>
    set((state) => {
      const slides = [...state.outline.slides]
      const [moved] = slides.splice(fromIndex, 1)
      slides.splice(toIndex, 0, moved)
      return { outline: { ...state.outline, slides } }
    }),
  providers: [],
  setProviders: (providers: ProviderConfig[]) => set({ providers }),
  activeProvider: null,
  setActiveProvider: (provider: ProviderConfig | null) => set({ activeProvider: provider }),
  generating: false,
  setGenerating: (val: boolean) => set({ generating: val }),
  currentTemplate: defaultTemplate,
  setCurrentTemplate: (template: PptTemplate) => set({ currentTemplate: template }),
  selectedSlideId: null,
  setSelectedSlideId: (id: string | null) => set({ selectedSlideId: id }),
  pptFilePath: null,
  setPptFilePath: (path: string | null) => set({ pptFilePath: path }),
  showSettings: false,
  setShowSettings: (val: boolean) => set({ showSettings: val })
}))
