import fastapi

# 延迟导入，避免在模块加载时就导入所有app
# 这样可以避免不必要的依赖加载（如CTP模块）

def get_td_app():
    """延迟导入td_app"""
    from .td_app import app as _td_app
    return _td_app

def get_md_app():
    """延迟导入md_app"""
    from .md_app import app as _md_app
    return _md_app

# 组合应用（仅在需要时创建）
def create_td_app():
    """创建交易应用"""
    td_app = fastapi.FastAPI()
    td_app.mount("/td", get_td_app())
    return td_app

def create_md_app():
    """创建行情应用"""
    md_app = fastapi.FastAPI()
    md_app.mount("/md", get_md_app())
    return md_app

def create_dev_app():
    """创建开发应用（包含交易和行情）"""
    dev_app = fastapi.FastAPI()
    dev_app.mount("/td", get_td_app())
    dev_app.mount("/md", get_md_app())
    return dev_app

# 为了向后兼容，保留原有的变量名
# 但使用延迟加载
td_app = None
md_app = None
dev_app = None

def __getattr__(name):
    """动态属性访问，实现延迟加载"""
    global td_app, md_app, dev_app
    
    if name == 'td_app':
        if td_app is None:
            td_app = create_td_app()
        return td_app
    elif name == 'md_app':
        if md_app is None:
            md_app = create_md_app()
        return md_app
    elif name == 'dev_app':
        if dev_app is None:
            dev_app = create_dev_app()
        return dev_app
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
