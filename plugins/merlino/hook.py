from plugins.merlino.app.sand_gui_api import SandGuiApi
from plugins.merlino.app.sand_svc import SandService

name = 'Merlino'
description = 'Sandcat with advanced obfuscation and anti-detection features'
address = '/plugin/merlino/gui'


async def enable(services):
    app = services.get('app_svc').application
    file_svc = services.get('file_svc')
    sand_svc = SandService(services)
    await file_svc.add_special_payload('merlino.go', sand_svc.dynamically_compile_executable)
    await file_svc.add_special_payload('merlino-shared.go', sand_svc.dynamically_compile_library)
    cat_gui_api = SandGuiApi(services=services)
    app.router.add_static('/merlino', 'plugins/merlino/static', append_version=True)
    app.router.add_route('GET', '/plugin/merlino/gui', cat_gui_api.splash)
    await sand_svc.load_sandcat_extension_modules()
