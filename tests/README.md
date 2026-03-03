```bash
uv run pytest --cov=src tests/
# --cov=src：指定你要检查覆盖率的代码目录（如你的项目是 src/ 目录）
# tests/：测试目录
```

```bash
uv run pytest --cov=branchlayerflow .
```

```bash
uv run pytest --cov=branchlayerflow
```

```bash
uv run pytest --cov=branchlayerflow --cov-report=html
```