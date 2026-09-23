import OpenAI from 'openai'
import { app } from 'electron'
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

export interface ProviderConfig {
  id: string
  name: string
  apiKey: string
  baseUrl: string
  modelName: string
  enabled: boolean
  isDefault: boolean
}

const CONFIG_DIR = join(app.getPath('userData'), 'config')
const CONFIG_FILE = join(CONFIG_DIR, 'providers.json')

const BUILTIN_PROVIDERS: Omit<ProviderConfig, 'id' | 'apiKey' | 'enabled'>[] = [
  {
    name: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    modelName: 'deepseek-chat',
    isDefault: true
  },
  {
    name: '通义千问',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    modelName: 'qwen-plus',
    isDefault: false
  },
  {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    modelName: 'gpt-4o-mini',
    isDefault: false
  },
  {
    name: '智谱AI',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    modelName: 'glm-4-flash',
    isDefault: false
  },
  {
    name: '月之暗面',
    baseUrl: 'https://api.moonshot.cn/v1',
    modelName: 'moonshot-v1-8k',
    isDefault: false
  }
]

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

export class ProviderManager {
  private providers: ProviderConfig[] = []

  constructor() {
    this.load()
  }

  load(): void {
    if (!existsSync(CONFIG_DIR)) {
      mkdirSync(CONFIG_DIR, { recursive: true })
    }

    if (existsSync(CONFIG_FILE)) {
      try {
        const data = readFileSync(CONFIG_FILE, 'utf-8')
        this.providers = JSON.parse(data)
        return
      } catch {
        this.providers = []
      }
    }

    this.providers = BUILTIN_PROVIDERS.map((p) => ({
      ...p,
      id: generateId(),
      apiKey: '',
      enabled: false
    }))
    this.save()
  }

  save(): void {
    if (!existsSync(CONFIG_DIR)) {
      mkdirSync(CONFIG_DIR, { recursive: true })
    }
    writeFileSync(CONFIG_FILE, JSON.stringify(this.providers, null, 2), 'utf-8')
  }

  getAll(): ProviderConfig[] {
    return this.providers
  }

  getById(id: string): ProviderConfig | undefined {
    return this.providers.find((p) => p.id === id)
  }

  getActive(): ProviderConfig | undefined {
    return this.providers.find((p) => p.enabled && p.apiKey)
  }

  add(provider: Omit<ProviderConfig, 'id'>): ProviderConfig {
    const newProvider: ProviderConfig = {
      ...provider,
      id: generateId()
    }
    this.providers.push(newProvider)
    this.save()
    return newProvider
  }

  update(id: string, updates: Partial<ProviderConfig>): ProviderConfig | undefined {
    const index = this.providers.findIndex((p) => p.id === id)
    if (index === -1) return undefined
    this.providers[index] = { ...this.providers[index], ...updates, id }
    this.save()
    return this.providers[index]
  }

  delete(id: string): boolean {
    const index = this.providers.findIndex((p) => p.id === id)
    if (index === -1) return false
    this.providers.splice(index, 1)
    this.save()
    return true
  }

  setDefault(id: string): void {
    this.providers.forEach((p) => {
      p.isDefault = p.id === id
    })
    this.save()
  }

  getDefault(): ProviderConfig | undefined {
    return this.providers.find((p) => p.isDefault) || this.providers.find((p) => p.apiKey)
  }
}

export class AIService {
  private providerManager: ProviderManager

  constructor(providerManager: ProviderManager) {
    this.providerManager = providerManager
  }

  private createClient(provider: ProviderConfig): OpenAI {
    return new OpenAI({
      apiKey: provider.apiKey,
      baseURL: provider.baseUrl
    })
  }

  private getActiveProvider(): ProviderConfig {
    const provider = this.providerManager.getDefault()
    if (!provider || !provider.apiKey) {
      throw new Error('未配置AI模型供应商，请先在设置中配置API Key')
    }
    return provider
  }

  async testConnection(provider: ProviderConfig): Promise<boolean> {
    try {
      const client = this.createClient(provider)
      await client.chat.completions.create({
        model: provider.modelName,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1,
        temperature: 0
      })
      return true
    } catch {
      return false
    }
  }

  async fetchModels(provider: ProviderConfig): Promise<string[]> {
    try {
      const client = this.createClient(provider)
      const response = await client.models.list()
      const models: string[] = []
      for await (const model of response) {
        models.push(model.id)
      }
      return models
    } catch {
      return [provider.modelName]
    }
  }

  async generateOutline(topic: string): Promise<string> {
    const provider = this.getActiveProvider()
    const client = this.createClient(provider)

    const prompt = `你是一位专业的医学PPT制作助手。请根据以下主题，生成一份专业的医学PPT大纲。

要求：
1. 生成8-12页幻灯片的大纲
2. 第一页为标题页
3. 最后一页为总结页
4. 每页幻灯片包含标题和3-5个要点
5. 内容要专业、准确、有逻辑性
6. 严格按照JSON格式输出，不要输出其他内容

输出格式如下：
{
  "title": "PPT主标题",
  "subtitle": "副标题",
  "slides": [
    {
      "title": "幻灯片标题",
      "bulletPoints": ["要点1", "要点2", "要点3"],
      "notes": "演讲者备注",
      "layout": "title"
    }
  ]
}

layout字段可选值：title（标题页）、content（内容页）、section（章节页）、ending（结尾页）
第一页layout必须为"title"，最后一页layout为"ending"，中间可以有section页。

主题：${topic}`

    const response = await client.chat.completions.create({
      model: provider.modelName,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 4096
    })

    let content = response.choices[0]?.message?.content || ''

    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      content = jsonMatch[0]
    }

    return content
  }

  async expandContent(slideTitle: string, bulletPoints: string[]): Promise<string> {
    const provider = this.getActiveProvider()
    const client = this.createClient(provider)

    const prompt = `你是一位专业的医学PPT制作助手。请为以下幻灯片扩展内容。

幻灯片标题：${slideTitle}
当前要点：${bulletPoints.join('、')}

请为每个要点扩展2-3句详细的演讲者备注，使内容更加丰富和专业。
严格按照JSON格式输出：
{
  "expandedNotes": "扩展后的演讲者备注，可以包含多个段落",
  "additionalPoints": ["补充要点1", "补充要点2"]
}`

    const response = await client.chat.completions.create({
      model: provider.modelName,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 2048
    })

    let content = response.choices[0]?.message?.content || ''
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      content = jsonMatch[0]
    }
    return content
  }

  async refineOutline(outlineJson: string): Promise<string> {
    const provider = this.getActiveProvider()
    const client = this.createClient(provider)

    const prompt = `你是一位专业的医学PPT制作助手。请优化以下PPT大纲，使其更加专业、逻辑清晰、内容完整。

当前大纲：
${outlineJson}

请优化大纲，可以：
1. 调整幻灯片顺序使逻辑更清晰
2. 补充遗漏的重要内容
3. 精简冗余内容
4. 优化标题和要点的表述

严格按照相同的JSON格式输出，不要输出其他内容。`

    const response = await client.chat.completions.create({
      model: provider.modelName,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 4096
    })

    let content = response.choices[0]?.message?.content || ''
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      content = jsonMatch[0]
    }
    return content
  }
}
