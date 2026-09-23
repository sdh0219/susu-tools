import { Router } from 'express'
import { ProviderManager } from '../services/aiService'

const router = Router()
const providerManager = new ProviderManager()

router.get('/all', (_req, res) => {
  res.json(providerManager.getAll())
})

router.get('/active', (_req, res) => {
  const active = providerManager.getActive()
  res.json(active || null)
})

router.get('/:id', (req, res) => {
  const provider = providerManager.getById(req.params.id)
  if (!provider) {
    res.status(404).json({ error: '供应商不存在' })
    return
  }
  res.json(provider)
})

router.post('/add', (req, res) => {
  const provider = providerManager.add(req.body)
  res.json(provider)
})

router.put('/update/:id', (req, res) => {
  const provider = providerManager.update(req.params.id, req.body)
  if (!provider) {
    res.status(404).json({ error: '供应商不存在' })
    return
  }
  res.json(provider)
})

router.delete('/delete/:id', (req, res) => {
  const success = providerManager.delete(req.params.id)
  res.json({ success })
})

router.put('/set-default/:id', (req, res) => {
  providerManager.setDefault(req.params.id)
  res.json({ success: true })
})

export { providerManager, router as providerRouter }
