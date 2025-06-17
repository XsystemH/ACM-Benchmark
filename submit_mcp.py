#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import asyncio
import httpx
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# API配置
BASE_URL = "http://acm.q.opensii.ai:37029"
SUBMIT_URL = f"{BASE_URL}/api/submit"
QUERY_URL = f"{BASE_URL}/api/task_detail"
EXCLUDE_NAMES = ("data", "testcases", "Test")
TIMEOUT_SECONDS = 60

# 已知的repository名称（用于识别单个repo还是多个repo的父目录）
KNOWN_REPOS = {"Basic", "Book", "ICPC", "Minesweeper", "Python", "Ticket"}

def filter_and_copy_source(src_dir: str, exclude_names=EXCLUDE_NAMES) -> str:
    """
    智能复制目录结构：
    - 如果是单个repository（如Basic），将整个目录作为一个repo放在临时目录中
    - 如果是包含多个repository的目录，复制所有repository子目录
    """
    temp_dst = tempfile.mkdtemp()
    dst_repo = os.path.join(temp_dst, "repo")
    os.makedirs(dst_repo)

    def ignore_func(dir, names):
        return [name for name in names if name in exclude_names]

    # 获取源目录的名称
    src_dir_name = os.path.basename(src_dir)
    
    # 检查是否是单个repository
    if src_dir_name in KNOWN_REPOS:
        # 单个repository：将整个目录作为一个repo放在临时目录中
        dst_path = os.path.join(dst_repo, src_dir_name)
        shutil.copytree(src_dir, dst_path, ignore=ignore_func, dirs_exist_ok=True)
        print(f"📁 单个repository模式：复制 {src_dir_name} 到 {dst_path}")
    else:
        # 多个repository的父目录：复制所有子目录
        for item in os.listdir(src_dir):
            item_path = os.path.join(src_dir, item)
            if os.path.isdir(item_path) and item not in exclude_names:
                dst_path = os.path.join(dst_repo, item)
                shutil.copytree(item_path, dst_path, ignore=ignore_func, dirs_exist_ok=True)
                print(f"📁 多repository模式：复制 {item} 到 {dst_path}")
    
    return dst_repo

def zip_directory(src_dir: str) -> str:
    """
    将目录打包为 zip 文件，返回 zip 路径。
    修正：确保zip文件中包含repo目录作为根目录
    """
    zip_base = tempfile.mktemp()
    parent_dir = os.path.dirname(src_dir)
    base_name = os.path.basename(src_dir)  # 这应该是 "repo"
    zip_path = shutil.make_archive(zip_base, 'zip', root_dir=parent_dir, base_dir=base_name)
    return zip_path

async def submit_to_api(zip_path: str, model_id: int = 1) -> dict:
    """
    异步提交 zip 文件到新的 API 接口。
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        with open(zip_path, 'rb') as f:
            files = {
                'zip_file': ('submission.zip', f, 'application/zip'),
            }
            data = {
                'model_id': str(model_id)
            }
            response = await client.post(SUBMIT_URL, files=files, data=data)
            response.raise_for_status()
            return response.json()

async def query_task_detail(task_id: int) -> dict:
    """
    异步查询指定任务的评测结果。
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(f"{QUERY_URL}/{task_id}")
        response.raise_for_status()
        return response.json()

# 创建MCP服务器
server = Server("oj-api-tool")

@server.list_tools()
async def list_tools():
    """列出可用的工具"""
    return [
        Tool(
            name="submit",
            description="将指定目录打包成zip文件并通过新API提交到OJ系统",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "要提交的目录绝对路径"
                    },
                    "model_id": {
                        "type": "integer",
                        "description": "模型ID (默认为1)",
                        "default": 1
                    }
                },
                "required": ["directory_path"]
            }
        ),
        Tool(
            name="query",
            description="查询指定任务ID的评测结果",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "要查询的任务ID"
                    }
                },
                "required": ["task_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具调用"""
    if name == "submit":
        return await handle_submit(arguments)
    elif name == "query":
        return await handle_query(arguments)
    else:
        return [TextContent(type="text", text=f"❌ 未知工具：{name}")]

async def handle_submit(arguments: dict):
    """处理提交请求"""
    directory_path = arguments.get("directory_path")
    model_id = arguments.get("model_id", 1)
    
    if not directory_path:
        return [TextContent(type="text", text="❌ 错误: 必须提供directory_path参数")]
    
    if not os.path.isdir(directory_path):
        return [TextContent(type="text", text=f"❌ 错误：路径无效：{directory_path}")]
    
    cleaned_path = None
    zip_path = None
    
    try:
        # 处理目录 - 在executor中运行以避免阻塞
        loop = asyncio.get_event_loop()
        cleaned_path = await loop.run_in_executor(None, filter_and_copy_source, directory_path)
        
        # 打包为zip - 在executor中运行以避免阻塞
        zip_path = await loop.run_in_executor(None, zip_directory, cleaned_path)
        
        # 获取文件大小
        zip_size = os.path.getsize(zip_path)
        
        # 异步提交到新API
        result = await submit_to_api(zip_path, model_id)
        
        # 格式化返回结果
        if result.get("success"):
            response_text = f"""✅ 提交成功！
📁 处理目录：{directory_path}
📦 排除目录：{EXCLUDE_NAMES}
🔢 模型ID：{model_id}
📦 文件大小：{zip_size} 字节
🎯 总提交ID：{result.get('submission_id')}

📋 各任务提交ID："""
            
            submission_ids = result.get('submission_ids', {})
            for task, task_id in submission_ids.items():
                if task_id != -1:
                    response_text += f"\n  • {task}: {task_id}"
                else:
                    response_text += f"\n  • {task}: 失败"
                    
            response_text += f"\n\n💡 使用 query 工具查询各任务评测结果"
        else:
            response_text = f"""❌ 提交失败！
📁 处理目录：{directory_path}
🔢 模型ID：{model_id}
📦 文件大小：{zip_size} 字节
❌ 错误信息：{result.get('error', '未知错误')}
🎯 总提交ID：{result.get('submission_id', '无')}"""
        
        return [TextContent(type="text", text=response_text)]
        
    except asyncio.TimeoutError:
        return [TextContent(type="text", text=f"❌ 提交超时（超过{TIMEOUT_SECONDS}秒）")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"❌ 网络请求失败：{str(e)}")]
    except httpx.HTTPStatusError as e:
        error_text = f"❌ HTTP错误：{e.response.status_code} - {str(e)}"
        try:
            error_response = e.response.json()
            error_text += f"\n📋 服务器响应：{error_response}"
        except:
            error_text += f"\n📋 服务器响应：{e.response.text}"
        return [TextContent(type="text", text=error_text)]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 提交失败：{str(e)}")]
    finally:
        # 确保清理临时文件
        try:
            if cleaned_path and os.path.exists(cleaned_path):
                shutil.rmtree(os.path.dirname(cleaned_path))
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as cleanup_error:
            print(f"清理临时文件时出错：{cleanup_error}")

async def handle_query(arguments: dict):
    """处理查询请求"""
    task_id = arguments.get("task_id")
    
    if not task_id:
        return [TextContent(type="text", text="❌ 错误: 必须提供task_id参数")]
    
    try:
        # 异步查询任务详情
        result = await query_task_detail(task_id)
        
        # 格式化查询结果
        response_text = f"📊 任务 {task_id} 评测结果：\n"
        response_text += f"🏷️  原始数据：\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        
        # 如果有特定字段，可以进行格式化显示
        if "data" in result:
            data = result["data"]
            response_text = f"""任务 {task_id} 评测结果：

🏷️  状态：{data.get('result', '未知')}
📝 题目：{data.get('problem', {}).get('title', '未知')}
💯 分数：{data.get('score', '未知')} 分
⏱️  时间：{data.get('time_cost', '未知')} ms
💾 内存：{data.get('memory_cost', '未知')} KB
📅 提交时间：{data.get('create_time', '未知')}

🔗 详细信息：{json.dumps(data, indent=2, ensure_ascii=False)}"""
        
        return [TextContent(type="text", text=response_text)]
        
    except asyncio.TimeoutError:
        return [TextContent(type="text", text=f"❌ 查询超时（超过{TIMEOUT_SECONDS}秒）")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"❌ 网络请求失败：{str(e)}")]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(type="text", text=f"❌ 任务ID {task_id} 不存在")]
        else:
            return [TextContent(type="text", text=f"❌ HTTP错误：{e.response.status_code} - {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 查询失败：{str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 