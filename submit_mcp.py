#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import asyncio
import httpx  # 使用httpx替代requests，支持异步
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

LEADERBOARD_URL = "http://acm.q.opensii.ai:37029/submit"
EXCLUDE_NAMES = ("data", "testcases")
TIMEOUT_SECONDS = 60  # 设置超时时间

def filter_and_copy_source(src_dir: str, exclude_names=EXCLUDE_NAMES) -> str:
    """
    复制目录内容到临时目录中，排除特定目录或文件。
    """
    temp_dst = tempfile.mkdtemp()
    dst_repo = os.path.join(temp_dst, "repo")

    def ignore_func(dir, names):
        return [name for name in names if name in exclude_names]

    shutil.copytree(src_dir, dst_repo, ignore=ignore_func, dirs_exist_ok=True)
    return dst_repo

def zip_directory(src_dir: str) -> str:
    """
    将目录打包为 zip 文件，返回 zip 路径。
    """
    zip_base = tempfile.mktemp()
    zip_path = shutil.make_archive(zip_base, 'zip', root_dir=src_dir)
    return zip_path

async def submit_zip_async(zip_path: str, model_id: int = 1) -> str:
    """
    异步提交 zip 文件到 leaderboard 接口。
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        with open(zip_path, 'rb') as f:
            files = {
                'model_id': str(model_id),
                'zip_file': ('repositories.zip', f, 'application/zip'),
            }
            response = await client.post(LEADERBOARD_URL, files=files)
            response.raise_for_status()
            return response.text

# 创建MCP服务器
server = Server("oj-submit-tool")

@server.list_tools()
async def list_tools():
    """列出可用的工具"""
    return [
        Tool(
            name="submit",
            description="将指定目录打包成zip文件并提交到OJ系统",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "要提交的目录路径"
                    },
                    "model_id": {
                        "type": "integer",
                        "description": "模型ID (默认为1)",
                        "default": 1
                    }
                },
                "required": ["directory_path"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具调用"""
    if name == "submit":
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
            
            # 异步提交到OJ
            result = await submit_zip_async(zip_path, model_id)
            
            return [TextContent(
                type="text", 
                text=f"✅ 提交成功！\n📁 处理目录：{directory_path}\n📦 排除目录：{EXCLUDE_NAMES}\n🔢 模型ID：{model_id}\n📦 文件大小：{zip_size} 字节\n📡 服务器响应：\n{result}"
            )]
            
        except asyncio.TimeoutError:
            return [TextContent(type="text", text=f"❌ 提交超时（超过{TIMEOUT_SECONDS}秒）")]
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"❌ 网络请求失败：{str(e)}")]
        except httpx.HTTPStatusError as e:
            return [TextContent(type="text", text=f"❌ HTTP错误：{e.response.status_code} - {str(e)}")]
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
    
    else:
        return [TextContent(type="text", text=f"❌ 未知工具：{name}")]

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