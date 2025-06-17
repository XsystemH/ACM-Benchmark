# ACM-Benchmark

| Project | Code Framework | Open Test Points | Hidden Test Points | Evaluation Mode | Problem_id |
|---------|----------------|------------------|--------------------|-----------------|------------|
| Mine | ✅ | ✅ | ✅ | Single Header File | 1983 |
| ICPC | ❌ | ✅ | ✅ | Whole Repository | 1987 |
| Basic | ✅ | ✅ | ❌ | Whole Repository | 2510 |
| Python | ✅ | ✅ | ✅ | Whole Repository | 2515 |
| Book | ❌ | ✅ | ✅ | Whole Repository | 1075(open) 1775(close) | 
| Ticket | ❌ | ✅ | ❌ | Whole Repository | 1867 |

## Instruction

```
根据`README.md`中的要求完成仓库。

在完成并利用提供的测试用例验证无误后，请使用已启用的 `submit` 工具将你的代码打包并提交到 Leaderboard。

提交后mcp工具将会返回Submission ID，你可以通过`query`工具查询提交结果。
```

## Environment

```
pip install -r requirements.txt
```

```
# requirements
requests>=2.28.0
mcp>=1.0.0
httpx>=0.24.0 
```

## Agent Settings

以`Cursor`为例，其他Agent类似

在Settings->Tools&Integrations->MCP Tools中添加以下配置：

```json
// mcp.json
{
  "mcpServers": {
    // you need to add these lines
    "oj-api-tool": {
      "command": "python",
      "args": ["/home/xhsystem/Code/Term5/Cursor/submit_mcp.py"],
      "env": {}
    }
    // you need to add these lines
  }
}
```

并重启MCP tools，你将可以在MCP tools中看到`oj-api-tool`

![alt text](image-1.png)

## Leader Board

| Agent | Mine | ICPC | Basic | Python | Book | Ticket |
|-------|------|------|-------|--------|------|--------|
| Cursor(Claude-4-sonnet) | 100 | 0 | 100 | - | 61 | - |
| Cursor(GPT) | || | | |