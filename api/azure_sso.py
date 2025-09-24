from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from msal import ConfidentialClientApplication
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.requests import Request
from starlette.status import HTTP_400_BAD_REQUEST

from common.security import create_access_token
from config import settings
from models.user_model import Users


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True, validate_default=True)

    id: int
    oid: str
    preferred_username: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, exclude=True)


class IDTokenClaims(BaseModel):
    preferred_username: Optional[str] = None
    display_name: Optional[str] = Field(None, alias="name")
    oid: Optional[str] = None
    email: Optional[str] = Field(None,
                                 description='可能不会返回，注意azure配置合理权限,一般preferred_username和email值相同')

    @model_validator(mode="after")
    @classmethod
    def validate_claims(cls, values):
        if values.email:
            values.preferred_username = values.email
        else:
            print('未能获取email,azure权限可能未配置，或检查scope')
        return values


class AuthToken(BaseModel):
    model_config = ConfigDict(extra="allow")
    id_token: str
    id_token_claims: Optional[IDTokenClaims] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    not_before: Optional[datetime] = None
    expires_in: Optional[timedelta] = None
    client_info: Optional[str] = None
    scope: Optional[str] = None
    refresh_token: Optional[str] = None
    refresh_token_expires_in: Optional[timedelta] = None
    error: Optional[str] = None
    error_description: Optional[str] = None
    error_uri: Optional[str] = None


class AADLoginService:
    def __init__(self):
        if not settings.AAD_SECRETKEY:
            try:
                with open(settings.AAD_PRIVATE_KEY_FILE, "r") as key_file:
                    private_key = key_file.read()
            except FileNotFoundError:
                raise ValueError(f"Private key file not found at path: '{settings.AAD_PRIVATE_KEY_FILE}'")

            client_credential = {
                "private_key": private_key,
                "thumbprint": settings.AAD_CERTIFICATE_THUMBPRINT,
            }
        else:
            client_credential = settings.AAD_SECRETKEY

        self.app = ConfidentialClientApplication(
            client_id=settings.AAD_CLIENT_ID,
            authority=f'https://login.microsoftonline.com/{settings.AAD_TENANT_ID}',
            client_credential=client_credential
        )

    def get_auth_uri(self, sid: str):
        """生成AAD登录URL"""
        flow = self.app.initiate_auth_code_flow(
            scopes=["email"],
            redirect_uri=f'{settings.FRONTEND_URL}{settings.AAD_REDIRECT_END_POINT}',
            state=sid
        )
        return flow

    async def create_user(self, db: AsyncSession, oid, preferred_username, display_name):
        user = Users(oid=oid, preferred_username=preferred_username, display_name=display_name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def get_or_create_user(self, db: AsyncSession, oid, preferred_username, display_name=None):
        user = (await db.execute(select(Users).where(Users.oid == oid))).scalar_one_or_none()
        if not display_name:
            display_name = preferred_username
        if not user:
            user = await self.create_user(db, oid, preferred_username, display_name)
        else:
            user.preferred_username = preferred_username
            user.display_name = display_name
            await db.commit()
        return user

    async def validate_and_login(self, request: Request, auth_response: dict, flow: dict, db: AsyncSession):
        """验证AAD回调并登录用户"""
        state = auth_response.get("state")

        if not flow:
            raise HTTPException(status_code=400, detail="Session expired or invalid. Please try logging in again.")

        if flow.get("state") != state:
            raise HTTPException(status_code=400,
                                detail=f"State mismatch. Expected: {flow.get('state')}, Received: {state}")

        # 使用授权码获取令牌
        result = self.app.acquire_token_by_auth_code_flow(flow, auth_response)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error_description", "Failed to acquire token."))

        auth_token = AuthToken(**result)

        # 从Microsoft Graph API获取用户信息
        access_token = auth_token.access_token
        user_token_info = auth_token.id_token_claims
        user = await self.get_or_create_user(db, user_token_info.oid, user_token_info.preferred_username,
                                             user_token_info.display_name)
        user.last_login = datetime.now()
        await db.commit()
        await db.refresh(user)
        user_info = UserInfo.model_validate(user)
        await db.refresh(user)
        # 生成应用内部JWT
        internal_token = create_access_token(user_info.model_dump())
        return {"token": internal_token, 'user_info': user_info.model_dump(), 'access_token': access_token}

    async def _is_user_authorized(self, oid: str, db: AsyncSession) -> bool:
        """检查用户是否在数据库中"""
        query = select(Users).where(Users.oid == oid)
        user = (await db.execute(query)).scalar_one_or_none()
        return bool(user)

    async def sso_log_out(self):
        redirect_uri = f"{settings.FRONTEND_URL}"
        redirect_param = urlencode({'post_logout_redirect_uri': redirect_uri})
        logout_url = f'https://login.microsoftonline.com/{settings.AAD_TENANT_ID}/oauth2/v2.0/logout?{redirect_param}'
        return logout_url

    async def get_user_list(self):
        """
        从Microsoft Graph API获取用户列表
        需要应用程序有User.Read.All权限
        """
        try:
            # 获取访问令牌，使用客户端凭据流程
            result = self.app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

            if "access_token" not in result:
                # 获取令牌失败
                return {"error": "获取访问令牌失败", "details": result.get("error_description", "未知错误")}

            # 使用访问令牌调用Microsoft Graph API
            access_token = result["access_token"]
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # 调用Microsoft Graph API获取用户列表
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/users",
                    headers=headers,
                    params={
                        "$select": "id,displayName,userPrincipalName,mail",  # 只获取需要的字段
                        "$top": 999  # 限制返回的用户数量
                    }
                )
                if response.status_code == 403:
                    raise Exception('用户认证平台缺乏必要权限，请联系管理员开通')

                if response.status_code == 200:
                    data = response.json()
                    # 返回用户列表
                    return {
                        "users": [{
                            "oid": user.get("id"),
                            "displayName": user.get("displayName"),
                            "email": user.get("mail")
                        } for user in data.get("value", [])]
                    }
                else:
                    # API调用失败
                    return {
                        "error": "获取用户列表失败",
                        "status_code": response.status_code,
                        "details": response.text
                    }
        except Exception as e:
            # 捕获所有异常
            return {"error": "获取用户列表时发生异常", "details": str(e)}

    async def get_user_by_email(self, email: str, fuzzy_search: bool = False):
        """
        根据邮箱搜索用户信息
        需要应用程序有User.Read.All权限
        
        Args:
            email: 用户邮箱地址
            fuzzy_search: 是否启用模糊搜索，默认为False（精确匹配）
            
        Returns:
            用户信息或错误信息
        """
        try:
            # 获取访问令牌，使用客户端凭据流程
            result = self.app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

            if "access_token" not in result:
                # 获取令牌失败
                return {"error": "获取访问令牌失败", "details": result.get("error_description", "未知错误")}

            # 使用访问令牌调用Microsoft Graph API
            access_token = result["access_token"]
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # 构建过滤条件
            if fuzzy_search:
                # 模糊搜索：使用startswith函数（Graph API不支持contains函数用于用户搜索）
                # 从@符号分割邮箱，获取用户名部分用于模糊匹配
                if '@' in email:
                    username = email.split('@')[0]
                    domain = email.split('@')[1]
                    # 构建模糊搜索条件：匹配用户名开头或域名开头
                    filter_query = f"startswith(mail, '{username}') or startswith(userPrincipalName, '{username}')"
                else:
                    # 如果没有@符号，直接使用整个输入进行模糊匹配
                    filter_query = f"startswith(mail, '{email}') or startswith(userPrincipalName, '{email}')"
            else:
                # 精确匹配：使用eq操作符
                filter_query = f"mail eq '{email}' or userPrincipalName eq '{email}' or otherMails/any(e:e eq '{email}')"

            # 调用Microsoft Graph API搜索用户
            async with (httpx.AsyncClient() as client):
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/users",
                    headers=headers,
                    params={
                        "$filter": filter_query,
                        "$select": "id,displayName,userPrincipalName,mail,jobTitle,department",  # 获取更详细的用户信息
                        "$top": 10  # 限制返回结果数量，模糊搜索可能返回多个结果
                    }
                )
                if response.status_code == 403:
                    raise HTTPException(
                        status_code=403,
                        detail="无法搜索用户，认证平台缺乏必要权限，请联系管理员开通"
                    )

                if response.status_code == 200:
                    data = response.json()
                    users = data.get("value", [])

                    if not users:
                        return {"error": "未找到匹配的用户", "email": email}
                    # 返回所有匹配的用户信息
                    return [
                        {
                            "oid": user.get("id"),
                            "displayName": user.get("displayName"),
                            "email": user.get("mail"),
                        } for user in users
                    ]


                else:
                    # API调用失败
                    return {
                        "error": "搜索用户失败",
                        "status_code": response.status_code,
                        "details": response.text
                    }
        except HTTPException as e:
            raise e
        except Exception as e:
            # 捕获所有异常
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"{str(e)}")
