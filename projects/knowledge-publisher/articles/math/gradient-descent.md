---
title: 梯度下降到底是什么？
subtitle: 机器学习中最常用的优化算法，一篇讲透它的思想与实现
series: 机器学习基础
author: 芝士土豆
tags: [机器学习, 优化]
---

# 梯度下降到底是什么？

梯度下降是机器学习中最常用的优化算法之一。本文用最直观的方式，讲清楚它为什么存在、怎么工作，以及一个完整的 Python 实现。

## 1. 为什么需要梯度下降？

机器学习中，我们通常需要最小化一个损失函数：

$$
J(\theta)
=
\frac{1}{n}
\sum_{i=1}^{n}
(f_\theta(x_i)-y_i)^2
$$

**损失函数**衡量模型预测与真实值之间的差距，我们希望它越小越好。

### 核心思想

沿着梯度下降的方向不断更新参数：

$$
\theta_{t+1}
=
\theta_t-\eta\nabla J(\theta_t)
$$

其中：

- $\theta$ 是模型参数
- $\eta$ 是学习率，控制每步迈多大
- $\nabla J(\theta_t)$ 是损失函数在 $\theta_t$ 处的梯度

## 2. 一个直观的例子

想象你在山谷中，目标是走到最低点。你看不到全局地图，只能感受脚下的坡度：

> 坡度告诉你哪个方向下降最快，迈出的步子大小就是学习率。

![梯度下降示意图](assets/images/gradient.png)

## 3. Python 实现

```python
import numpy as np

def gradient_descent(grad, start, lr=0.1, steps=100):
    theta = start
    history = [theta]
    for _ in range(steps):
        theta = theta - lr * grad(theta)
        history.append(theta)
    return theta, history
```

## 4. 关键要点

| 名称 | 含义 | 常见问题 |
| ---- | ---- | -------- |
| 学习率 $\eta$ | 每次更新的步长 | 太大发散，太小收敛慢 |
| 梯度 $\nabla J$ | 上升最快的方向 | 更新时要取反方向 |
| 局部最优 | 非凸问题的陷阱 | 可用动量来缓解 |

## 5. 小结

1. 梯度下降通过反复迭代来最小化损失函数。
2. 核心公式只有一条：$\theta_{t+1}=\theta_t-\eta\nabla J(\theta_t)$。
3. 多试试不同的学习率，你会对它有更直观的感觉。
