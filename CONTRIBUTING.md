# 共建指南

这个仓库既是网站源码，也是一个长期生长的自习室与作品集。欢迎任何形式的参与——不需要是程序员。

## 四种受欢迎的贡献

| 类型 | 怎么做 | 适合谁 |
|------|--------|--------|
| 📝 笔记纠错 | 提 [Issue](https://github.com/sdh0219/susu-tools/issues/new?template=note-fix.yml) | 任何看到错误的人 |
| 📚 补充资料 | 提 Issue（选「我想投稿一篇新资料」），附上你的整理 | 有现成笔记的人 |
| 💡 功能建议 | 提 [Issue](https://github.com/sdh0219/susu-tools/issues/new?template=feature.yml) 或去 [Discussions](https://github.com/sdh0219/susu-tools/discussions) | 使用者 |
| 🐛 站点修复 | 直接 Fork → 改 → 提 PR | 会写前端的人 |

## 笔记为什么优先提 Issue 而不是 PR

站内笔记页（`web/notes/*.html` / `*.md`）是**生成产物**：由 `scripts/build_notes.py` 从仓库外的课程源稿渲染而来。直接改生成物会在下一次构建时被覆盖。

所以笔记类改动走 Issue → 维护者改源稿并重新构建 → 你的名字出现在修复记录里。
**代码、样式、页面结构（`web/*.html`、`web/assets/`、`scripts/`）可以直接 PR。**

## PR 约定

1. 一个 PR 只做一件事（修一个 bug / 加一个功能），方便审阅和回滚。
2. 跑一遍门禁再提交：`python scripts/check_site.py`（检查全站本地引用是否可达）。
3. 涉及页面的改动请顺手看一眼手机宽度（375–390px）是否溢出。
4. 提交信息用一句话说清「做了什么 + 为什么」。

## 两条红线（违反必关）

- **不上传老师的课件、教材 PDF、真题原卷**——只收自己整理的笔记与本人作业。
- **不提交任何人的个人信息**（学号、姓名、电话、教师评语）。公开版本一律脱敏，这条不会松。

## 内容与代码的权利

- 站内原创笔记、文章、图片：著作权归作者，**转载/引用请注明出处并附原文链接**，不得用于商业用途。
- 代码（`scripts/`、`web/assets/js/`、`web/assets/css/`）：欢迎取用与二次开发，同样请保留出处。
- 完整许可协议尚在选定中；在此之前按上述约定执行。如你需要明确的法律条款用于商业场景，请先开 Issue 沟通。

## 贡献者

被采纳的贡献会出现在网站的[共建页](https://susu-2x9.pages.dev/contribute.html)贡献者墙上。
