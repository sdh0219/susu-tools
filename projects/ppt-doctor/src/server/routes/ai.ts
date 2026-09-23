import { Router } from 'express'
import { AIService, ProviderManager } from '../services/aiService'
import type { ProviderConfig } from '../services/aiService'
import { providerManager } from './provider'

const router = Router()
const aiService = new AIService(providerManager)

router.post('/test-connection', async (req, res) => {
  try {
    const provider = req.body as ProviderConfig
    const result = await aiService.testConnection(provider)
    res.json({ success: result })
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

router.post('/fetch-models', async (req, res) => {
  try {
    const provider = req.body as ProviderConfig
    const models = await aiService.fetchModels(provider)
    res.json(models)
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

router.post('/generate-outline', async (req, res) => {
  try {
    const { topic } = req.body
    const result = await aiService.generateOutline(topic)
    res.json({ result })
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

router.post('/expand-content', async (req, res) => {
  try {
    const { slideTitle, bulletPoints } = req.body
    const result = await aiService.expandContent(slideTitle, bulletPoints)
    res.json({ result })
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

router.post('/refine-outline', async (req, res) => {
  try {
    const { outlineJson } = req.body
    const result = await aiService.refineOutline(outlineJson)
    res.json({ result })
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

export { router as aiRouter }
