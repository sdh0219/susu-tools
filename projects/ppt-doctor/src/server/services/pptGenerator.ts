import PptxGenJS from 'pptxgenjs'

interface SlideOutline {
  id: string
  title: string
  bulletPoints: string[]
  notes: string
  layout: 'title' | 'content' | 'section' | 'ending'
}

interface Outline {
  title: string
  subtitle: string
  slides: SlideOutline[]
}

interface PptTemplate {
  name: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  fontTitle: string
  fontBody: string
  backgroundColor: string
}

const MEDICAL_TEMPLATES: Record<string, PptTemplate> = {
  professional: {
    name: '专业蓝',
    primaryColor: '1B3A5C',
    secondaryColor: '2E86AB',
    accentColor: 'A23B72',
    fontTitle: 'Microsoft YaHei',
    fontBody: 'Microsoft YaHei',
    backgroundColor: 'FFFFFF'
  },
  fresh: {
    name: '清新绿',
    primaryColor: '2D6A4F',
    secondaryColor: '40916C',
    accentColor: '74C69D',
    fontTitle: 'Microsoft YaHei',
    fontBody: 'Microsoft YaHei',
    backgroundColor: 'FFFFFF'
  },
  elegant: {
    name: '优雅紫',
    primaryColor: '4A1A6B',
    secondaryColor: '7B2D8E',
    accentColor: 'C77DFF',
    fontTitle: 'Microsoft YaHei',
    fontBody: 'Microsoft YaHei',
    backgroundColor: 'FFFFFF'
  }
}

export class PptGenerator {
  generate(outline: Outline, template?: PptTemplate): PptxGenJS {
    const tpl = template || MEDICAL_TEMPLATES.professional
    const pptx = new PptxGenJS()

    pptx.layout = 'LAYOUT_WIDE'
    pptx.author = 'PPT医生'
    pptx.title = outline.title

    outline.slides.forEach((slide) => {
      switch (slide.layout) {
        case 'title':
          this.addTitleSlide(pptx, slide, outline, tpl)
          break
        case 'section':
          this.addSectionSlide(pptx, slide, tpl)
          break
        case 'ending':
          this.addEndingSlide(pptx, slide, tpl)
          break
        default:
          this.addContentSlide(pptx, slide, tpl)
          break
      }
    })

    return pptx
  }

  async saveToBuffer(outline: Outline, template?: PptTemplate): Promise<Buffer> {
    const pptx = this.generate(outline, template)
    const buffer = await pptx.write({ outputType: 'nodebuffer' }) as Buffer
    return buffer
  }

  private addTitleSlide(
    pptx: PptxGenJS,
    slide: SlideOutline,
    outline: Outline,
    tpl: PptTemplate
  ): void {
    const pptSlide = pptx.addSlide()

    pptSlide.background = { color: tpl.primaryColor }

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 0,
      w: '100%',
      h: '100%',
      fill: { color: tpl.primaryColor }
    })

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: '70%',
      w: '100%',
      h: '30%',
      fill: { color: tpl.secondaryColor }
    })

    pptSlide.addText(outline.title, {
      x: 1,
      y: 1.5,
      w: 11.33,
      h: 2,
      fontSize: 40,
      fontFace: tpl.fontTitle,
      color: 'FFFFFF',
      bold: true,
      align: 'center',
      valign: 'middle'
    })

    pptSlide.addText(outline.subtitle || '', {
      x: 1,
      y: 3.5,
      w: 11.33,
      h: 1,
      fontSize: 20,
      fontFace: tpl.fontBody,
      color: 'D0D0D0',
      align: 'center',
      valign: 'middle'
    })

    const date = new Date().toLocaleDateString('zh-CN')
    pptSlide.addText(date, {
      x: 1,
      y: 6,
      w: 11.33,
      h: 0.6,
      fontSize: 14,
      fontFace: tpl.fontBody,
      color: 'FFFFFF',
      align: 'center'
    })

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 4.5,
      y: 4.8,
      w: 4.33,
      h: 0.05,
      fill: { color: tpl.accentColor }
    })
  }

  private addContentSlide(pptx: PptxGenJS, slide: SlideOutline, tpl: PptTemplate): void {
    const pptSlide = pptx.addSlide()

    pptSlide.background = { color: tpl.backgroundColor }

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 0,
      w: '100%',
      h: 1.2,
      fill: { color: tpl.primaryColor }
    })

    pptSlide.addText(slide.title, {
      x: 0.8,
      y: 0.15,
      w: 11.73,
      h: 0.9,
      fontSize: 28,
      fontFace: tpl.fontTitle,
      color: 'FFFFFF',
      bold: true,
      valign: 'middle'
    })

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0.8,
      y: 1.5,
      w: 0.08,
      h: 4.5,
      fill: { color: tpl.accentColor }
    })

    const bulletRows = slide.bulletPoints.map((point) => ({
      text: point,
      options: {
        fontSize: 18,
        fontFace: tpl.fontBody,
        color: '333333',
        bullet: { code: '25CF', color: tpl.accentColor },
        paraSpaceAfter: 12,
        indentLevel: 0
      }
    }))

    pptSlide.addText(bulletRows, {
      x: 1.2,
      y: 1.8,
      w: 10.93,
      h: 4.5,
      valign: 'top',
      lineSpacingMultiple: 1.5
    })

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 7.2,
      w: '100%',
      h: 0.3,
      fill: { color: tpl.secondaryColor }
    })

    if (slide.notes) {
      pptSlide.addNotes(slide.notes)
    }
  }

  private addSectionSlide(pptx: PptxGenJS, slide: SlideOutline, tpl: PptTemplate): void {
    const pptSlide = pptx.addSlide()

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 0,
      w: '100%',
      h: '100%',
      fill: { color: tpl.secondaryColor }
    })

    pptSlide.addText(slide.title, {
      x: 1,
      y: 2,
      w: 11.33,
      h: 3,
      fontSize: 36,
      fontFace: tpl.fontTitle,
      color: 'FFFFFF',
      bold: true,
      align: 'center',
      valign: 'middle'
    })

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 4.5,
      y: 4.5,
      w: 4.33,
      h: 0.05,
      fill: { color: tpl.accentColor }
    })
  }

  private addEndingSlide(pptx: PptxGenJS, slide: SlideOutline, tpl: PptTemplate): void {
    const pptSlide = pptx.addSlide()

    pptSlide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 0,
      w: '100%',
      h: '100%',
      fill: { color: tpl.primaryColor }
    })

    pptSlide.addText(slide.title || '谢谢！', {
      x: 1,
      y: 2,
      w: 11.33,
      h: 2.5,
      fontSize: 44,
      fontFace: tpl.fontTitle,
      color: 'FFFFFF',
      bold: true,
      align: 'center',
      valign: 'middle'
    })

    if (slide.bulletPoints.filter(Boolean).length > 0) {
      pptSlide.addText(slide.bulletPoints.filter(Boolean).join(' · '), {
        x: 1,
        y: 4.5,
        w: 11.33,
        h: 1,
        fontSize: 16,
        fontFace: tpl.fontBody,
        color: 'D0D0D0',
        align: 'center',
        valign: 'middle'
      })
    }
  }
}

export { MEDICAL_TEMPLATES }
