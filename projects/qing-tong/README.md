# 千瞳 - 视角转换器

将普通2D视频转换为可交互的3D场景，支持视角自由切换。

## 项目结构（全部自包含，删除即清）

```
QianTong/
├── .local/              # 本地缓存（npm、pip），可安全删除
│   ├── npm-cache/
│   └── pip-cache/
├── frontend/            # 前端 React + Three.js
│   ├── node_modules/    # npm 依赖（本地安装）
│   └── ...
├── backend/             # 后端 Python FastAPI
│   ├── .venv/           # Python 虚拟环境（本地）
│   ├── checkpoints/     # 深度模型权重（需手动下载）
│   ├── uploads/         # 上传的视频（临时）
│   ├── tasks/           # 处理结果（临时）
│   └── ...
├── scripts/             # 启动脚本
├── .env                 # 环境变量配置
└── 需求分析.md
```

**删除整个 `QianTong` 文件夹即可完全清除，不留残余。**

## 快速开始

### 1. 初始化环境（首次运行）

```powershell
# 在项目根目录执行
.\scripts\setup.ps1
```

### 2. 启动服务

```powershell
# 启动后端 + 前端
.\scripts\start.ps1
```

- 前端：http://localhost:3000
- 后端：http://localhost:8000

### 3. 可选：下载深度模型（提升效果）

默认使用梯度估计的简易深度图。如需高质量深度估计：

1. 从 https://huggingface.co/depth-anything/Depth-Anything-V2-Large 下载 `depth_anything_v2_vitl.pth`
2. 放到 `backend/checkpoints/` 目录下
3. 重启后端即可自动加载

## 技术栈

- **前端**：Vite + React + TypeScript + Three.js
- **后端**：Python FastAPI + OpenCV + Depth Anything V2
- **3D渲染**：Three.js 深度位移网格 + 自由相机控制
