import os
import json
import time
import httpx
import shutil
import random
import uvicorn
import logging
import logging.handlers 
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILENAME = os.path.join(LOG_DIR, "app.log")
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
# --- 日志配置字典 ---
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # 定义一个名为 "default" 的格式化器
        "default": {
            "()": "logging.Formatter",  # 使用标准的 Formatter
            "fmt": "[%(levelname)s - %(filename)s:%(lineno)d | %(funcName)s] - %(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        # 控制台输出的 Handler
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",  # 使用上面定义的 default 格式
            "stream": "ext://sys.stderr",
        },
        # 文件输出和轮转的 Handler
        "file_rotating": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "default",  # 也使用上面定义的 default 格式
            "filename": LOG_FILENAME,  # 日志文件路径
            "when": "D",  # 按天轮转 ('D' for Day)
            "interval": 1,  # 每天轮转一次
            "backupCount": 2,  # 保留2个旧的日志文件 (加上当前文件，总共覆盖3天)
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # 根日志记录器
        "": {
            # 同时将日志发送到 console 和 file_rotating 两个 Handler
            "handlers": ["console", "file_rotating"],
            "level": log_level,
        },
        # 针对 uvicorn 的日志记录器进行配置，确保它们也使用我们的设置
        "uvicorn": {
            "handlers": ["console", "file_rotating"],
            "level": "WARNING",
            "propagate": False, # 阻止 uvicorn 日志向上传播到根 logger，避免重复记录
        },
        "uvicorn.error": {
            "level": "WARNING",
            "propagate": True, # uvicorn.error 应该传播，以便根记录器可以捕获它
        },
        "uvicorn.access": {
            "handlers": ["console", "file_rotating"],
            "level": log_level,
            "propagate": False,
        },
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
from crack import Crack
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI,Query, HTTPException
from predict import (predict_onnx,
                     predict_onnx_pdl,
                     predict_onnx_dfine,
                     predict_dino_classify_pipeline,
                     load_by,
                     unload,
                     get_models,
                     get_available_models)
from crop_image import crop_image_v3,save_path,save_fail_path,save_pass_path,validate_path

PORT = 9645

def get_available_hosts() -> set[str]:
    """获取本机所有可用的IPv4地址。"""
    import socket
    hosts = {"127.0.0.1"}
    try:
        hostname = socket.gethostname()
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
        hosts.update({info[4][0] for info in addr_info})
    except socket.gaierror:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                hosts.add(s.getsockname()[0])
        except OSError:
            pass
    return hosts

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("="*50)
    logger.info("启动服务中...")
    # 从 uvicorn 配置中获取 host 和 port
    server = app.servers[0] if app.servers else None
    host = server.config.host if server else "0.0.0.0"
    port = server.config.port if server else PORT
    if host == "0.0.0.0":
        available_hosts = get_available_hosts()
        logger.info(f"服务地址(依需求选用，docker中使用宿主机host:{port}，若使用Uvicorn运行则基于命令):")
        for h in sorted(list(available_hosts)):
            logger.info(f"  - http://{h}:{port}")
    else:
        logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"可用服务路径如下:")
    for route in app.routes:
        logger.info(f"    -{route.methods} {route.path}")
    logger.info(f"具体api使用可以查看/docs")
    logger.info("="*50)
    
    yield
    logger.info("="*50)
    logger.info("服务关闭")
    logger.info("="*50)

app = FastAPI(title="极验V3图标点选+九宫格", lifespan=lifespan)

def prepare(gt: str, challenge: str) -> tuple[Crack, bytes, str, str]:
    """获取信息。"""
    logger.info(f"开始获取:\ngt:{gt}\nchallenge:{challenge}")
    crack = Crack(gt, challenge)
    logger.debug(f"初次获得{crack.gettype()}")
    crack.get_c_s()
    time.sleep(random.uniform(0.4,0.6))
    crack.ajax()
    pic_content,pic_name,pic_type = crack.get_pic()
    return crack,pic_content,pic_name,pic_type

def do_pass_nine(pic_content: bytes, use_v3_model: bool, point: Optional[str]) -> list[str]:
    """处理九宫格验证码，返回坐标点列表。"""
    crop_image_v3(pic_content)
    if use_v3_model:
        result_list = predict_onnx_pdl(validate_path)
    else:
        with open(f"{validate_path}/cropped_9.jpg", "rb") as rb:
            icon_image = rb.read()
        with open(f"{validate_path}/nine.jpg", "rb") as rb:
            bg_image = rb.read()
        result_list = predict_onnx(icon_image, bg_image, point)
    return [f"{col}_{row}" for row, col in result_list]

def do_pass_icon(pic:Any, draw_result: bool) -> list[str]:
    """处理图标点选验证码，返回坐标点列表。"""
    result_list = predict_onnx_dfine(pic,draw_result)
    logger.debug(result_list)
    return [f"{round(x / 333 * 10000)}_{round(y / 333 * 10000)}" for x, y in result_list]

def do_pass_icon0(pic:Any, draw_result: bool) -> list[str]:
    """处理图标点选验证码，返回坐标点列表。"""
    result_list = predict_dino_classify_pipeline(pic,draw_result)
    return [f"{round(x / 333 * 10000)}_{round(y / 333 * 10000)}" for x, y in result_list]

def save_image_for_train(pic_name,pic_type,passed):
    shutil.move(os.path.join(validate_path,pic_name),os.path.join(save_path,pic_name))
    if passed:
        path_2_save = os.path.join(save_pass_path,pic_name.split('.')[0])
    else:
        path_2_save = os.path.join(save_fail_path,pic_name.split('.')[0])
    os.makedirs(path_2_save,exist_ok=True)
    for pic in os.listdir(validate_path):
        if pic_type == "nine" and pic.startswith('cropped'):
            shutil.move(os.path.join(validate_path,pic),os.path.join(path_2_save,pic))
        if pic_type == "icon" and pic.startswith('icon'):
            shutil.move(os.path.join(validate_path,pic),os.path.join(path_2_save,pic))


def handle_pass_request(gt: str, challenge: str, save_result: bool, **kwargs) -> JSONResponse:
    """
    统一处理所有验证码请求的核心函数。
    """
    start_time = time.monotonic()
    try:
        # 1. 准备
        crack, pic_content, pic_name, pic_type = prepare(gt, challenge)
        
        # 2. 识别
        logger.debug(f"接收图片类型{pic_type}")
        if pic_type == "nine":
            point_list = do_pass_nine(
                pic_content,
                use_v3_model=kwargs.get("use_v3_model", True),
                point=kwargs.get("point",None)
            )
        elif pic_type == 'icon': # dino
            point_list = do_pass_icon0(pic_content, save_result)
        elif pic_type == "icon1": # d-fine
            point_list = do_pass_icon(pic_content, save_result)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown picture type: {pic_type}")

        # 3. 验证
        elapsed = time.monotonic() - start_time
        wait_time = max(0, 4.0 - elapsed)
        time.sleep(wait_time)

        response_str = crack.verify(point_list)
        result = json.loads(response_str)

        # 4. 后处理
        passed = 'validate' in result.get('data', {})
        if save_result:
            save_image_for_train(pic_name, pic_type, passed)
        else:
            os.remove(os.path.join(validate_path,pic_name))

        total_time = time.monotonic() - start_time
        logger.info(
            f"请求完成,耗时: {total_time:.2f}s (等待 {wait_time:.2f}s). "
            f"结果: {result}"
        )
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"服务错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred.", "detail": str(e)}
        )

    

@app.get("/pass_nine")
def pass_nine(gt: str = Query(...), 
            challenge: str = Query(...), 
            point: str = Query(default=None), 
            use_v3_model = Query(default=True),
            save_result = Query(default=False)
           ):
    return handle_pass_request(
        gt, challenge, save_result,
        use_v3_model=use_v3_model, point=point
    )

@app.get("/pass_icon")
def pass_icon(gt: str = Query(...), 
            challenge: str = Query(...),
            save_result = Query(default=False)
            ):
    return handle_pass_request(gt, challenge, save_result)

@app.get("/pass_uni")
def pass_uni(gt: str = Query(...), 
            challenge: str = Query(...),
            save_result = Query(default=False)
            ):
    return handle_pass_request(gt, challenge, save_result)

@app.get("/pass_hutao")
def pass_hutao(gt: str = Query(...), 
            challenge: str = Query(...),
            save_result = Query(default=False)):
    try:
        # 调用原函数获取返回值
        response = handle_pass_request(gt, challenge, save_result)
        # 获取原始状态码和内容
        original_status_code = response.status_code
        original_content = json.loads(response.body.decode("utf-8"))
        if original_status_code == 200 and original_content.get("status",False)=="success" and "validate" in original_content.get("data",{}):
            rebuild_content = {"code":0,"data":{"gt":gt,"challenge":challenge,"validate":original_content["data"]["validate"]}}
        else:
            rebuild_content = {"code":1,"data":{"gt":gt,"challenge":challenge,"validate":original_content}}
        return JSONResponse(content=rebuild_content, status_code=original_status_code)

    except Exception as e:
        logger.error(f"修改路由错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred.", "detail": str(e)}
        )

@app.get("/list_model")
def list_model():
    return JSONResponse(content = get_models())
@app.get("/list_all_model")
def list_model():
    return JSONResponse(content = get_available_models())
@app.get("/load_model")
def load_model(name: str = Query(...)):
    return JSONResponse(content = get_models())
@app.get("/unload_model")
def unload_model(name: str = Query(...)):
    return JSONResponse(content = get_models())

@app.get("/set_log_level")
def set_log_level(level: str = Query(...)):
    """
    在服务运行时动态修改所有主要 logger 的日志级别。
    例如: /set_log_level?level=DEBUG
    """
    # 将字符串级别转换为 logging 模块对应的整数值
    level_str = str(level).upper()
    numeric_level = getattr(logging, level_str, None)
    if not isinstance(numeric_level, int):
        raise HTTPException(status_code=400, detail=f"无效的日志级别: {level}")

    # 获取并修改您配置中所有关键 logger 的级别
    # 1. 修改根 logger
    logging.getLogger().setLevel(numeric_level)
    # 2. 修改 uvicorn logger
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("uvicorn.error").setLevel(numeric_level)
    logging.getLogger("uvicorn.access").setLevel(numeric_level)
    
    # 记录一条高级别的日志，确保能被看到
    logger.warning(f"所有 logger 的日志级别已被动态修改为: {level_str}")
    
    return JSONResponse(content = f"Log level successfully set to {level_str}")

if __name__ == "__main__":
    import uvicorn
    # 添加 host="0.0.0.0" 参数以允许宿主机及局域网设备访问
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_config=LOGGING_CONFIG)
    