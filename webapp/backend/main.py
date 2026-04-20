"""
FastAPI 后端 - 提供 API 服务
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from loguru import logger
from contextlib import asynccontextmanager

# 导入项目模块
from models.ollama_model import get_llm, get_embeddings
from database.db_manager import db_manager
from knowledge_base.knowledge_base import kb_manager
from agent.factory import create_agent, AgentFactory
from skills.registry import skill_registry, discover_skills

# ========== 生命周期管理 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化系统...")
    
    # 初始化模型
    app_state["llm"] = get_llm()
    app_state["embeddings"] = get_embeddings()
    
    # 发现技能
    discover_skills()
    
    app_state["initialized"] = True
    logger.info("系统初始化完成")
    
    yield
    
    # 关闭时清理
    logger.info("系统正在关闭...")

app = FastAPI(
    title="Offline Agent Web",
    description="AI 智能体交互式 Web 界面",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
app_state = {
    "initialized": False,
    "llm": None,
    "embeddings": None
}

# 存储 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


# ========== 数据模型 ==========

class ChatRequest(BaseModel):
    message: str
    agent_type: str = "react"
    use_knowledge_base: Optional[str] = None
    use_database: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Dict]] = None
    execution_steps: Optional[List[Dict]] = None

class DatabaseQueryRequest(BaseModel):
    db_name: str
    sql: str

class KnowledgeBaseQueryRequest(BaseModel):
    kb_name: str
    query: str

class SkillExecuteRequest(BaseModel):
    skill_name: str
    parameters: Dict[str, Any]

class AgentCreateRequest(BaseModel):
    name: str
    agent_type: str = "react"
    system_prompt: Optional[str] = None


# ========== API 路由 ==========

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "running",
        "initialized": app_state["initialized"],
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ----- 对话 API -----

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口
    支持普通对话、知识库增强、Agent 执行
    """
    try:
        if not app_state["initialized"]:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        response_text = ""
        sources = None
        execution_steps = None
        
        # 如果使用知识库
        if request.use_knowledge_base:
            kb = kb_manager.get(request.use_knowledge_base)
            if kb:
                result = kb.query(request.message)
                response_text = result.get("answer", "")
                sources = result.get("sources")
            else:
                response_text = f"知识库 '{request.use_knowledge_base}' 不存在"
        
        # 如果使用 Agent
        elif request.agent_type:
            agent = create_agent(
                agent_type=request.agent_type,
                name="web_agent",
                llm=app_state["llm"]
            )
            
            # 如果指定了数据库，添加数据库工具
            if request.use_database:
                from database.db_manager import get_db
                db = get_db(request.use_database)
                if db:
                    def query_db(sql: str):
                        return db.execute(sql)
                    agent.register_tool("query_database", query_db, "执行 SQL 查询")
            
            response_text = agent.run(request.message)
            execution_steps = agent.get_conversation_history()
        
        # 普通对话
        else:
            from langchain_core.messages import HumanMessage
            result = app_state["llm"].invoke([HumanMessage(content=request.message)])
            response_text = result.content
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            execution_steps=execution_steps
        )
    
    except Exception as e:
        logger.error(f"对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 实时对话"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # 发送思考状态
            await websocket.send_json({
                "type": "thinking",
                "content": "正在思考..."
            })
            
            # 处理消息
            from langchain_core.messages import HumanMessage
            
            # 流式输出
            for chunk in app_state["llm"].stream([HumanMessage(content=message)]):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk.content
                })
            
            await websocket.send_json({
                "type": "complete",
                "content": ""
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })
        manager.disconnect(websocket)


# ----- 数据库 API -----

@app.get("/api/databases")
async def list_databases():
    """列出所有数据库连接"""
    return {
        "databases": db_manager.list_databases()
    }


@app.post("/api/database/query")
async def query_database(request: DatabaseQueryRequest):
    """执行数据库查询"""
    try:
        db = db_manager.get(request.db_name)
        if not db:
            raise HTTPException(status_code=404, detail=f"数据库 '{request.db_name}' 不存在")
        
        result = db.execute(request.sql)
        return {
            "success": True,
            "data": result,
            "count": len(result)
        }
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database/{db_name}/tables")
async def get_database_tables(db_name: str):
    """获取数据库表列表"""
    try:
        db = db_manager.get(db_name)
        if not db:
            raise HTTPException(status_code=404, detail=f"数据库 '{db_name}' 不存在")
        
        tables = db.get_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database/{db_name}/schema/{table_name}")
async def get_table_schema(db_name: str, table_name: str):
    """获取表结构"""
    try:
        db = db_manager.get(db_name)
        if not db:
            raise HTTPException(status_code=404, detail=f"数据库 '{db_name}' 不存在")
        
        schema = db.get_table_schema(table_name)
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 知识库 API -----

@app.get("/api/knowledge-bases")
async def list_knowledge_bases():
    """列出所有知识库"""
    kb_list = kb_manager.list_knowledge_bases()
    result = []
    for name in kb_list:
        kb = kb_manager.get(name)
        if kb:
            stats = kb.get_stats()
            result.append(stats)
    return {"knowledge_bases": result}


@app.post("/api/knowledge-base/query")
async def query_knowledge_base(request: KnowledgeBaseQueryRequest):
    """查询知识库"""
    try:
        kb = kb_manager.get(request.kb_name)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库 '{request.kb_name}' 不存在")
        
        result = kb.query(request.query)
        return result
    except Exception as e:
        logger.error(f"知识库查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge-base/{kb_name}/documents")
async def add_document_to_kb(kb_name: str, file_path: str):
    """添加文档到知识库"""
    try:
        kb = kb_manager.get(kb_name)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库 '{kb_name}' 不存在")
        
        doc_ids = kb.add_document(file_path)
        return {
            "success": True,
            "document_ids": doc_ids,
            "count": len(doc_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- Agent API -----

@app.get("/api/agents/types")
async def list_agent_types():
    """列出支持的 Agent 类型"""
    return {
        "types": AgentFactory.list_agent_types()
    }


@app.post("/api/agent/create")
async def create_new_agent(request: AgentCreateRequest):
    """创建新 Agent"""
    try:
        agent = create_agent(
            agent_type=request.agent_type,
            name=request.name,
            llm=app_state["llm"],
            system_prompt=request.system_prompt
        )
        return {
            "success": True,
            "agent_name": agent.name,
            "agent_type": request.agent_type,
            "tools": agent.list_tools()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/{agent_name}/run")
async def run_agent(agent_name: str, message: str):
    """运行 Agent"""
    try:
        agent = AgentFactory.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
        
        result = agent.run(message)
        return {
            "response": result,
            "execution_steps": agent.get_conversation_history()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 技能 API -----

@app.get("/api/skills")
async def list_skills():
    """列出所有技能"""
    return {
        "skills": skill_registry.list_skill_info()
    }


@app.post("/api/skill/execute")
async def execute_skill(request: SkillExecuteRequest):
    """执行技能"""
    try:
        from skills.registry import execute_skill
        result = execute_skill(request.skill_name, **request.parameters)
        return {
            "success": result.success,
            "data": result.data,
            "message": result.message,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 模型 API -----

@app.get("/api/models")
async def list_models():
    """列出可用模型"""
    try:
        llm = app_state["llm"]
        models = llm.list_models() if hasattr(llm, 'list_models') else []
        return {
            "current_model": llm.model if hasattr(llm, 'model') else "unknown",
            "available_models": models
        }
    except Exception as e:
        return {
            "current_model": "unknown",
            "available_models": [],
            "error": str(e)
        }


@app.post("/api/model/pull")
async def pull_model(model_name: str):
    """拉取模型"""
    try:
        llm = app_state["llm"]
        if hasattr(llm, 'pull_model'):
            success = llm.pull_model(model_name)
            return {"success": success}
        else:
            raise HTTPException(status_code=400, detail="当前模型不支持拉取操作")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 静态文件服务 ==========

# 前端构建后的文件路径
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """服务前端页面"""
        file_path = os.path.join(frontend_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
