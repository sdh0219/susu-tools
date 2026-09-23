import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import { providerRouter } from './routes/provider'
import { aiRouter } from './routes/ai'
import { pptRouter } from './routes/ppt'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = 3000

app.use(cors())
app.use(express.json({ limit: '10mb' }))

app.use('/api/provider', providerRouter)
app.use('/api/ai', aiRouter)
app.use('/api/ppt', pptRouter)

const staticDir = path.join(__dirname, '..', 'dist', 'renderer')
app.use(express.static(staticDir))

app.get('*', (_req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'))
})

app.listen(PORT, () => {
  console.log(`\n  🏥 PPT医生服务已启动`)
  console.log(`  访问地址: http://localhost:${PORT}\n`)
})
