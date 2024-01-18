import re

from fastapi import FastAPI, applications, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from starlette.responses import JSONResponse

from utils import config, my_jwt

app = None


def create_app():
    app = FastAPI(
        title="店铺推荐平台后端服务",
        version="1.0.0",
        description="全部接口",
        openapi_url="/api/api.json",
        docs_url="/docs"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # 解决无法访问Swagger的问题
    def swagger_monkey_patch(*args, **kwargs):
        return get_swagger_ui_html(
            *args, **kwargs,
            swagger_js_url='https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.10.3/swagger-ui-bundle.js',
            swagger_css_url='https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.10.3/swagger-ui.css'
        )

    applications.get_swagger_ui_html = swagger_monkey_patch
    return app


def set_route(app: FastAPI):
    import controller
    # 文件
    app.mount("/static", StaticFiles(directory="static"), name="static")
    # 子路由
    app.include_router(controller.user.router, prefix="/user", tags=["user"])
    app.include_router(controller.file.router, prefix="/file", tags=["file"])
    app.include_router(controller.admin.router, prefix="/admin", tags=["admin"])
    app.include_router(controller.merchant.router, prefix="/merchant", tags=["merchant"])
    app.include_router(controller.promotion.router, prefix="/promotion", tags=["promotion"])
    app.include_router(controller.private_message.router, prefix="/private_msg", tags=["private_message"])
    app.include_router(controller.notification.router, prefix="/notification", tags=["notification"])


def set_middleware(app: FastAPI):
    # 全局token拦截
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        allowed_paths = ["/user/login", "/user/register","/admin/login", "/file"]
        # flag = False
        # for path in allowed_paths:
        #     if request.url.path.startswith(path):
        #         flag = True
        #         break
        # if not flag:
        #     token = request.headers.get("Authorization")
        #     if token == None or my_jwt.get_user_id(token) == None:
        #         return JSONResponse(
        #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #             content=jsonable_encoder({"detail": "用户未登录"}),
        #         )
        response = await call_next(request)
        return response


if __name__ == '__main__':
    # 创建fastapi的服务和socketio的服务，并整合
    app = create_app()
    set_route(app)
    set_middleware(app)
    uvicorn.run(app, host=config.get("server.host"), port=config.get("server.port")

                )
