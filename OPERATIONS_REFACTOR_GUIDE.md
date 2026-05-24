# WatermarkSeal 操作区模块重构文档

## 项目结构变更

### 原始结构
所有功能代码包含在单一文件 `watermark_seal.py` 中，包括：
- UI 布局和样式定义
- 按钮创建和绑定
- 7个操作函数实现

### 新的模块化结构

```
COMP9001-Final_project/
├── watermark_seal.py              # 主应用程序 (已重构)
├── verify_operations.py            # 模块验证脚本
└── operations/                     # 操作区功能包
    ├── __init__.py
    ├── prev_image.py              # ⏮ 上一张图片
    ├── next_image.py              # ⏭ 下一张图片
    ├── zoom_in.py                 # ➕ 放大图片
    ├── zoom_out.py                # ➖ 缩小图片
    ├── rotate.py                  # 🔄 旋转图片
    ├── fit_view.py                # 🏠 自适应/重置视图
    └── toggle_watermark.py        # 🏷️ 水印开关
```

## 各模块功能说明

### 1. prev_image.py - 上一张图片
**功能**：
- 切换到上一张图片
- 支持循环滚屏（到达第一张时返回最后一张）
- 同步左侧列表选择
- 触发显示区域更新

**函数签名**：`on_prev_image(app)`

---

### 2. next_image.py - 下一张图片
**功能**：
- 切换到下一张图片
- 支持循环滚屏（到达最后一张时返回第一张）
- 同步左侧列表选择
- 触发显示区域更新

**函数签名**：`on_next_image(app)`

---

### 3. zoom_in.py - 放大图片
**功能**：
- 将图片放大 10%（百分比值）
- 锁定自动适应模式
- 缩放范围限制在 10% - 500%
- 触发显示区域重绘

**函数签名**：`on_zoom_in(app)`

---

### 4. zoom_out.py - 缩小图片
**功能**：
- 将图片缩小 10%（百分比值）
- 锁定自动适应模式
- 缩放范围限制在 10% - 500%
- 触发显示区域重绘

**函数签名**：`on_zoom_out(app)`

---

### 5. rotate.py - 旋转图片
**功能**：
- 顺时针旋转 90 度
- 支持循环旋转（360° 后回到 0°）
- 保留旋转状态在缩放操作后
- 触发显示区域重绘

**函数签名**：`on_rotate(app)`

---

### 6. fit_view.py - 自适应/重置视图
**功能**：
- 计算最优的缩放比例使图片完全显示在窗口内
- 可选重置旋转角度（非窗口事件触发时）
- 支持从窗口大小改变事件触发
- 自动激活自动适应模式
- 动态计算考虑旋转后的包围框

**函数签名**：`on_fit_view(app, called_from_resize=False)`

**参数**：
- `app`: WatermarkSealApp 应用实例
- `called_from_resize`: 是否由窗口大小改变事件触发（默认 False）

---

### 7. toggle_watermark.py - 水印开关
**功能**：
- 开启/关闭水印印章叠加
- 弹出对话框允许用户自定义水印文字
- 将自定义文字保存到应用状态
- 触发显示区域重绘应用水印效果

**函数签名**：`on_toggle_watermark(app)`

---

## 主程序更改 (watermark_seal.py)

### 1. 导入部分
在文件顶部添加了操作模块导入：
```python
from operations.prev_image import on_prev_image
from operations.next_image import on_next_image
from operations.zoom_in import on_zoom_in
from operations.zoom_out import on_zoom_out
from operations.rotate import on_rotate
from operations.fit_view import on_fit_view
from operations.toggle_watermark import on_toggle_watermark
```

### 2. 按钮绑定修改
原来：
```python
self.btn_prev = self._create_toolbar_button(btn_container, "⏮ Prev", self.on_prev_image, ...)
```

改为：
```python
self.btn_prev = self._create_toolbar_button(btn_container, "⏮ Prev", lambda: on_prev_image(self), ...)
```

### 3. 方法移除
- ✓ 已删除 `on_prev_image()` 方法
- ✓ 已删除 `on_next_image()` 方法
- ✓ 已删除 `on_zoom_in()` 方法
- ✓ 已删除 `on_zoom_out()` 方法
- ✓ 已删除 `on_rotate()` 方法
- ✓ 已删除 `on_fit_view()` 方法（逻辑已移至 operations/fit_view.py）
- ✓ 已删除 `on_toggle_watermark()` 方法

### 4. 事件绑定调用更新
在 `on_frame_resize()` 方法中：
```python
def on_frame_resize(self, event):
    if getattr(self, 'auto_fit_enabled', False):
        on_fit_view(self, called_from_resize=True)
```

### 5. 菜单方法中的调用更新
在 `on_open_file()` 和 `on_open_folder()` 方法中将 `self.on_fit_view()` 改为 `on_fit_view(self)`

---

## 优势

✅ **模块化代码**：每个按钮功能独立成文件，易于维护和测试

✅ **代码复用**：可以在其他项目中直接导入使用这些操作模块

✅ **单一职责**：每个模块只关注一个具体功能

✅ **更好的组织**：相关功能集中在 `operations` 包中

✅ **易于扩展**：添加新功能时直接在 `operations` 中创建新模块

✅ **改进的可读性**：主文件更简洁，专注于 UI 结构

---

## 运行验证

运行验证脚本确认所有模块导入成功：
```bash
python verify_operations.py
```

运行主程序：
```bash
python watermark_seal.py
```

---

## 向后兼容性

✅ 所有功能行为与重构前完全相同

✅ 按钮点击效果相同

✅ 所有快捷键和事件绑定正常工作

✅ UI 界面和交互逻辑完全保持一致

---

## 注意事项

- 所有操作模块函数都接收 `app` 作为第一个参数
- 模块通过访问 `app` 的属性和方法来操作应用状态
- 避免在模块中添加全局状态，所有状态应通过 `app` 实例管理
- 如需添加新的操作，遵循相同的模式创建新文件

