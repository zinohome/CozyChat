# 静态文件目录

本目录存放 Swagger UI 和 ReDoc 的静态资源文件，用于在生产内网环境中使用，避免依赖外部 CDN。

## 文件说明

### Swagger UI
- `swagger-ui/swagger-ui-bundle.js` - Swagger UI 核心 JS 文件
- `swagger-ui/swagger-ui.css` - Swagger UI 样式文件

**来源**: https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/

### ReDoc
- `redoc/redoc.standalone.js` - ReDoc 核心 JS 文件

**来源**: https://cdn.jsdelivr.net/npm/redoc@2/bundles/

## 更新方法

如果需要更新这些文件，可以运行以下命令：

```bash
# 更新 Swagger UI
cd backend/app/static/swagger-ui
curl -L -o swagger-ui-bundle.js "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
curl -L -o swagger-ui.css "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"

# 更新 ReDoc
cd backend/app/static/redoc
curl -L -o redoc.standalone.js "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"
```

## 注意事项

- 这些文件已提交到 Git，确保所有环境都能正常使用
- 在生产内网环境中，这些文件将从本地提供，不依赖外部 CDN
- 如果文件损坏或需要更新，请按照上述方法重新下载

