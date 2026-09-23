import { Router } from 'express'
import { PptGenerator, MEDICAL_TEMPLATES } from '../services/pptGenerator'

const router = Router()
const pptGenerator = new PptGenerator()

router.post('/export', async (req, res) => {
  try {
    const outline = req.body
    const template = MEDICAL_TEMPLATES.professional
    const buffer = await pptGenerator.saveToBuffer(outline, template)

    const filename = `${outline.title || '医学演示文稿'}.pptx`
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
    res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(filename)}"`)
    res.send(buffer)
  } catch (err: any) {
    res.status(500).json({ error: err.message })
  }
})

export { router as pptRouter }
