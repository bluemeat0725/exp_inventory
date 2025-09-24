import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from common.user_service import header_scheme, user_logout, get_current_user
from connector.con_redis import cacheDep
from azure_sso import AADLoginService
from config import settings
from connector.sql import SessionDep
from deps import userDep

router = APIRouter(tags=['用户登录'])
aad_service = AADLoginService()


async def get_session_data(session_id: str, redis_client: cacheDep):
    session_data = await redis_client.getdel(session_id)
    return session_data if session_data else {}


class LoginResponse(BaseModel):
    message: Optional[str] = ''
    token: Optional[str] = ''
    user_info: dict


@router.get("/auth-url",
            summary="获取AAD登录URL",
            description="获取Azure Active Directory的登录授权URL，用于启动OAuth2.0授权流程",
            response_description="返回包含授权URL和状态码的JSON对象")
async def get_auth_url(request: Request, redis_client: cacheDep):
    """获取AAD登录URL"""
    msal_state = str(uuid.uuid4())
    flow = aad_service.get_auth_uri(msal_state)
    await redis_client.set(msal_state, json.dumps(flow))
    response = JSONResponse({"auth_url": flow['auth_uri'], "state": flow['state']})
    response.set_cookie(key="msal_state", value=msal_state)
    return response


class SSOCallback(BaseModel):
    msal_state: str
    auth_response: dict


response_des_sso_token = """```json\n
{
    "token": "eyJhbGciOiJIUzI1Ni....",
        "user_info": {
        "id": 5,
        "oid": "e4b01ea5-4648-495b-8848-b2662a8ac471",
        "full_name": "Wang Renyuan",
        "role": "tour",
        "is_active": false,
        "created_at": "2025-08-24 21:14:22",
        "is_admin": false,
        "last_login": null,
        "exp": null
    },
    "access_token": "tyugjhjlk;jkjl....."
    }```
"""


@router.post("/auth/sso-token",
             summary="获取token",
             description="使用授权码和状态码从Azure Active Directory获取访问令牌",
             response_description="返回包含访问令牌和用户信息\n" + response_des_sso_token
             )
async def get_sso_token(request: Request, callbackdata: SSOCallback, db: SessionDep, redis_client: cacheDep):
    session_data = await get_session_data(callbackdata.msal_state, redis_client)
    if not session_data:
        raise HTTPException(status_code=400, detail="Invalid state or login session expired")
    flow = json.loads(session_data)
    result = await aad_service.validate_and_login(request, callbackdata.auth_response, flow, db)
    return LoginResponse(**result)


@router.get("/auth/logout",
            summary="用户登出",
            description="注销当前用户的登录状态",
            response_description="返回登出成功消息")
async def logout(
        aredis_client: cacheDep,
        current_user=Depends(get_current_user),
        token: str = Depends(header_scheme)
):
    """用户登出"""
    await user_logout(token, current_user.exp, aredis_client)
    logout_url = await aad_service.sso_log_out()
    return {'redirect': logout_url}


@router.get("/login/callback",
            response_class=HTMLResponse,
            summary="sso登录callback页面",
            description="sso登录callback页面",
            response_description="返回未授权页面的HTML内容")
async def sso_callback_page():
    with open("static/sso_callback.html", "r", encoding="utf-8") as f:
        content = f.read()
        # 动态替换API_BASE_URL为配置的FRONTEND_URL
        api_base_url = settings.FRONTEND_URL
        content = content.replace('{{API_BASE_URL}}', api_base_url)
        return HTMLResponse(content=content)


@router.get("/profile",
            summary="获取当前用户资料",
            description="获取当前已认证用户的详细资料信息，需要有效的Bearer Token",
            response_description="返回用户的完整资料信息，包括ID、用户名、角色等")
def get_profile(current_user: userDep):
    """获取用户资料（受保护的端点）"""
    return current_user.model_dump()
