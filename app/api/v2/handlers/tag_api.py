import aiohttp_apispec
from aiohttp import web

from app.api.v2.handlers.base_object_api import BaseObjectApi
from app.api.v2.managers.base_api_manager import BaseApiManager
from app.objects.c_tag import Tag, TagSchema


class TagApi(BaseObjectApi):
    def __init__(self, services):
        super().__init__(description='tag', obj_class=Tag, schema=TagSchema, ram_key='tags', id_property='name', auth_svc=services['auth_svc'])
        self._api_manager = BaseApiManager(data_svc=services['data_svc'], file_svc=services['file_svc'])

    def add_routes(self, app: web.Application):
        router = app.router
        router.add_get('/tags', self.get_tags)
        router.add_get('/tags/{name}', self.get_tag_by_name)
        router.add_post('/tags', self.create_tag)
        router.add_patch('/tags/{name}', self.update_tag)
        router.add_put('/tags/{name}', self.create_or_update_tag)
        router.add_delete('/tags/{name}', self.delete_tag)

    @aiohttp_apispec.docs(tags=['tags'])
    async def get_tags(self, request: web.Request):
        """
        Get all tags
        ---
        description: Retrieve all tags in the system
        """
        tags = [tag.display for tag in self._api_manager.find_objects(self.ram_key)]
        return web.json_response(tags)

    @aiohttp_apispec.docs(tags=['tags'])
    async def get_tag_by_name(self, request: web.Request):
        """
        Get a single tag by name
        ---
        description: Retrieve a specific tag by name
        """
        tag_name = request.match_info.get('name')
        tag = self._api_manager.find_object(self.ram_key, {'name': tag_name})
        if tag:
            return web.json_response(tag.display)
        return web.HTTPNotFound()

    @aiohttp_apispec.docs(tags=['tags'], summary='Create a new tag')
    @aiohttp_apispec.request_schema(TagSchema)
    @aiohttp_apispec.response_schema(TagSchema)
    async def create_tag(self, request: web.Request):
        """
        Create a new tag
        ---
        description: Create a new tag with name and value
        """
        tag_dict = await request.json()
        tag = Tag(name=tag_dict.get('name'), value=tag_dict.get('value', ''))
        stored_tag = tag.store(self._api_manager._data_svc.ram)
        return web.json_response(stored_tag.display, status=201)

    @aiohttp_apispec.docs(tags=['tags'], summary='Update an existing tag')
    @aiohttp_apispec.request_schema(TagSchema)
    @aiohttp_apispec.response_schema(TagSchema)
    async def update_tag(self, request: web.Request):
        """
        Update an existing tag
        ---
        description: Update tag value
        """
        tag_name = request.match_info.get('name')
        data = await request.json()
        
        tag = self._api_manager.find_object(self.ram_key, {'name': tag_name})
        if not tag:
            return web.HTTPNotFound()
        
        if 'value' in data:
            tag.value = data['value']
        
        return web.json_response(tag.display)

    @aiohttp_apispec.docs(tags=['tags'], summary='Create or update a tag')
    @aiohttp_apispec.request_schema(TagSchema)
    @aiohttp_apispec.response_schema(TagSchema)
    async def create_or_update_tag(self, request: web.Request):
        """
        Create or update a tag
        ---
        description: Create a new tag or update if exists
        """
        tag_name = request.match_info.get('name')
        data = await request.json()
        
        tag = self._api_manager.find_object(self.ram_key, {'name': tag_name})
        if tag:
            if 'value' in data:
                tag.value = data['value']
            return web.json_response(tag.display)
        
        new_tag = Tag(name=tag_name, value=data.get('value', ''))
        stored_tag = new_tag.store(self._api_manager._data_svc.ram)
        return web.json_response(stored_tag.display, status=201)

    @aiohttp_apispec.docs(tags=['tags'], summary='Delete a tag')
    async def delete_tag(self, request: web.Request):
        """
        Delete a tag
        ---
        description: Delete a tag by name
        """
        tag_name = request.match_info.get('name')
        tag = self._api_manager.find_object(self.ram_key, {'name': tag_name})
        if not tag:
            return web.HTTPNotFound()
        
        # Remove tag from ram
        self._api_manager._data_svc.ram[self.ram_key].remove(tag)
        return web.HTTPNoContent()
