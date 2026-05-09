"""认证控制器 — 注册、登录、当前用户、登出、用户管理"""
from fastapi import APIRouter, Depends, Request, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db
from app.config.response import success, BusinessException
from app.schemas.auth import LoginRequest, RegisterRequest, AdminCreateUserRequest, UserOut, UpdateRoleRequest
from app.models.user import User
from app.utils.jwt_util import get_password_hash, verify_password, create_access_token, verify_token
from app.middlewares.auth import require_admin
from app.config.logging import get_logger

logger = get_logger("routers.auth")
auth_router = APIRouter(tags=["认证与用户管理"])


@auth_router.post("/api/auth/register", summary="用户注册")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise BusinessException(msg="用户名已存在", code=409)

    user = User(
        username=req.username,
        password_hash=get_password_hash(req.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"新用户注册: {req.username}")
    return success(datas=UserOut(id=user.id, username=user.username, role=user.role.value).model_dump())


@auth_router.post("/api/auth/login", summary="用户登录")
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise BusinessException(msg="用户名或密码错误", code=401)

    token = create_access_token({"sub": user.username, "role": user.role.value, "id": user.id})
    response.set_cookie(
        key="token", value=token, httponly=True, max_age=3600 * 24, samesite="lax",
    )
    logger.info(f"用户登录: {req.username}")
    return success(datas={
        "token": token,
        "user": UserOut(id=user.id, username=user.username, role=user.role.value).model_dump(),
    })


@auth_router.get("/api/auth/me", summary="获取当前用户")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    user_info = getattr(request.state, "user", None)
    if not user_info:
        token = request.cookies.get("token")
        if token:
            user_info = verify_token(token)
    if not user_info:
        raise BusinessException(msg="未登录", code=401)

    result = await db.execute(select(User).where(User.username == user_info["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise BusinessException(msg="用户不存在", code=404)

    return success(datas=UserOut(id=user.id, username=user.username, role=user.role.value).model_dump())


@auth_router.post("/api/auth/logout", summary="退出登录")
async def logout(response: Response):
    response.delete_cookie("token")
    return success(messages="已退出登录")


# ── Admin: user management ──

@auth_router.post("/api/users", summary="创建用户（管理员）")
async def create_user(
    req: AdminCreateUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise BusinessException(msg="用户名已存在", code=409)
    from app.models.user import UserRole
    user = User(username=req.username, password_hash=get_password_hash(req.password),
                role=UserRole(req.role))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"管理员创建用户: {req.username} (role={req.role})")
    return success(datas=UserOut(id=user.id, username=user.username, role=user.role.value).model_dump())


@auth_router.get("/api/users", summary="用户列表（管理员）")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(select(func.count()).select_from(User))
    total = result.scalar()
    result = await db.execute(
        select(User).order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()
    items = [UserOut(id=u.id, username=u.username, role=u.role.value).model_dump() for u in users]
    return success(datas={"total": total, "items": items})


@auth_router.put("/api/user/{user_id}", summary="更新用户信息（管理员）")
async def update_user(
    user_id: int,
    req: UpdateRoleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    current_user = getattr(request.state, "user", None)
    if current_user and current_user.get("id") == user_id and req.role and req.role != current_user.get("role"):
        raise BusinessException(msg="不能修改自己的角色", code=400)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise BusinessException(msg="用户不存在", code=404)
    if req.role:
        from app.models.user import UserRole
        user.role = UserRole(req.role)
    if req.username:
        existing = await db.execute(select(User).where(User.username == req.username, User.id != user_id))
        if existing.scalar_one_or_none():
            raise BusinessException(msg="用户名已存在", code=409)
        user.username = req.username
    if req.password:
        user.password_hash = get_password_hash(req.password)
    await db.commit()
    logger.info(f"管理员更新用户 id={user_id}")
    return success(messages="更新成功", datas=UserOut(id=user.id, username=user.username, role=user.role.value).model_dump())


@auth_router.delete("/api/user/{user_id}", summary="删除用户（管理员）")
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    current_user = getattr(request.state, "user", None)
    if current_user and current_user.get("id") == user_id:
        raise BusinessException(msg="不能删除自己", code=400)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise BusinessException(msg="用户不存在", code=404)
    await db.delete(user)
    await db.commit()
    logger.info(f"管理员删除用户 id={user_id}")
    return success(messages="删除成功")
