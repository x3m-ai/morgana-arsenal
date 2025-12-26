import json
import aiohttp_apispec

from aiohttp import web

from app.api.v2.handlers.base_object_api import BaseObjectApi
from app.api.v2.managers.operation_api_manager import OperationApiManager
from app.api.v2.responses import JsonHttpNotFound
from app.api.v2.schemas.base_schemas import BaseGetAllQuerySchema, BaseGetOneQuerySchema
from app.api.v2.schemas.link_result_schema import LinkResultSchema
from app.objects.c_operation import Operation, OperationSchema, OperationSchemaAlt, OperationOutputRequestSchema
from app.objects.secondclass.c_link import LinkSchema


def decode_link_status(status_value):
    """Decode numeric link status to text representation."""
    status_map = {
        -5: 'HIGH_VIZ',
        -4: 'UNTRUSTED',
        -3: 'EXECUTE',
        -2: 'DISCARD',
        -1: 'PAUSE',
        0: 'SUCCESS',
        1: 'ERROR',
        124: 'TIMEOUT'
    }
    try:
        return status_map.get(int(status_value), f'UNKNOWN({status_value})')
    except (ValueError, TypeError):
        return 'N/A'


class OperationApi(BaseObjectApi):
    def __init__(self, services):
        super().__init__(description='operation', obj_class=Operation, schema=OperationSchema, ram_key='operations',
                         id_property='id', auth_svc=services['auth_svc'])
        self._api_manager = OperationApiManager(services)

    def add_routes(self, app: web.Application):
        router = app.router
        router.add_get('/operations', self.get_operations)
        router.add_get('/operations/summary', self.get_operations_summary)
        router.add_get('/operations/{id}', self.get_operation_by_id)
        router.add_post('/operations', self.create_operation)
        router.add_patch('/operations/{id}', self.update_operation)
        router.add_delete('/operations/{id}', self.delete_operation)
        router.add_post('/operations/{id}/report', self.get_operation_report)
        router.add_post('/operations/{id}/event-logs', self.get_operation_event_logs)
        router.add_get('/operations/{id}/links', self.get_operation_links)
        router.add_get('/operations/{id}/links/{link_id}', self.get_operation_link)
        router.add_get('/operations/{id}/links/{link_id}/result', self.get_operation_link_result)
        router.add_patch('/operations/{id}/links/{link_id}', self.update_operation_link)
        router.add_post('/operations/{id}/potential-links', self.create_potential_link)
        router.add_get('/operations/{id}/potential-links', self.get_potential_links)
        router.add_get('/operations/{id}/potential-links/{paw}', self.get_potential_links_by_paw)
        router.add_get('/merlino/operations', self.merlino_get_operations)
        router.add_post('/merlino/synchronize', self.merlino_synchronize)
        router.add_get('/merlino/dashboard/metrics', self.merlino_dashboard_metrics)
        router.add_get('/merlino/dashboard/abilities', self.merlino_dashboard_abilities)
        router.add_get('/merlino/dashboard/operations-health', self.merlino_dashboard_operations_health)
        router.add_get('/merlino/dashboard/errors', self.merlino_dashboard_errors)
        router.add_get('/merlino/dashboard/realtime', self.merlino_dashboard_realtime)
        router.add_get('/merlino/dashboard/force-graph', self.merlino_dashboard_force_graph)
        # New Merlino Ops Graph API
        router.add_post('/merlino/ops-graph', self.merlino_ops_graph)
        router.add_get('/merlino/ops-graph/problem-details', self.merlino_problem_details)
        router.add_get('/merlino/ops-graph/operation-details', self.merlino_operation_details)
        router.add_get('/merlino/ops-graph/agent-details', self.merlino_agent_details)
        router.add_post('/merlino/ops-actions', self.merlino_ops_actions)
        router.add_get('/merlino/ui-routes', self.merlino_ui_routes)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve operations',
                          description='Retrieve all Caldera operations from memory.  Use fields from the '
                                      '`BaseGetAllQuerySchema` in the request body to filter.')
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema)
    @aiohttp_apispec.response_schema(OperationSchema(many=True, partial=True),
                                     description='The response is a list of all operations.')
    async def get_operations(self, request: web.Request):
        operations = await self.get_all_objects(request)
        return web.json_response(operations)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve an operation by operation id',
                          description='Retrieve one Caldera operation from memory based on the operation id (String '
                                      'UUID).  Use fields from the `BaseGetOneQuerySchema` in the request body to add '
                                      '`include` and `exclude` filters.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the Operation object to be retrieved.'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.response_schema(OperationSchema(partial=True),
                                     description='The response is the operation with the specified id, if any.')
    async def get_operation_by_id(self, request: web.Request):
        operation = await self.get_object(request)
        return web.json_response(operation)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve operations (alternate)',
                          description='Retrieve all Caldera operations from memory, with an alternate selection'
                                      ' of properties. Use fields from the `BaseGetAllQuerySchema` in the request'
                                      ' body to filter.')
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema)
    @aiohttp_apispec.response_schema(OperationSchemaAlt(many=True, partial=True),
                                     description='The response is a list of all operations.')
    async def get_operations_summary(self, request: web.Request):
        remove_props = ['chain', 'host_group', 'source', 'visibility']
        operations = await self.get_all_objects(request)
        operations_mod = []
        for op in operations:
            op['agents'] = self._api_manager.get_agents(op)
            op['hosts'] = await self._api_manager.get_hosts(op)
            for prop in remove_props:
                op.pop(prop, None)
            operations_mod.append(op)
        return web.json_response(operations_mod)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Create a new Caldera operation record',
                          description='Create a new Caldera operation using the format provided in the '
                                      '`OperationSchema`. Required schema fields are as follows: "name", '
                                      '"adversary.adversary_id", "planner.id", and "source.id"')
    @aiohttp_apispec.request_schema(OperationSchema)
    @aiohttp_apispec.response_schema(OperationSchema,
                                     description='The response is the newly-created operation report.')
    async def create_operation(self, request: web.Request):
        operation = await self.create_object(request)
        return web.json_response(operation.display)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Update fields within an operation',
                          description='Update one Caldera operation in memory based on the operation id (String '
                                      'UUID). The `state`, `autonomous` and `obfuscator` fields in the operation '
                                      'object may be edited in the request body using the `OperationSchema`.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the Operation object to be retrieved.'
                          }])
    @aiohttp_apispec.request_schema(OperationSchema(partial=True, only=['state', 'autonomous', 'obfuscator']))
    @aiohttp_apispec.response_schema(OperationSchema(partial=True),
                                     description='The response is the updated operation, including user modifications.')
    async def update_operation(self, request: web.Request):
        operation = await self.update_object(request)
        return web.json_response(operation.display)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Delete an operation by operation id',
                          description='Delete one Caldera operation from memory based on the operation id (String '
                                      'UUID).',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the Operation object to be retrieved.'
                          }])
    @aiohttp_apispec.response_schema(OperationSchema,
                                     description='There is an empty response from a successful delete request.')
    async def delete_operation(self, request: web.Request):
        await self.delete_object(request)
        knowledge_svc_handle = self._api_manager.knowledge_svc
        await knowledge_svc_handle.delete_fact(criteria=dict(source=request.match_info.get('id')))
        await knowledge_svc_handle.delete_relationship(criteria=dict(origin=request.match_info.get('id')))
        return web.HTTPNoContent()

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Get Operation Report',
                          description='Retrieves the report for a given operation_id.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'operation_id': 'Unique ID for operation',
                              'access': 'Format for report',
                              'output': 'Boolean for Agent Output in report',
                              'schema': {'type': 'string'},
                              'required': 'true'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.request_schema(OperationOutputRequestSchema)
    @aiohttp_apispec.response_schema(OperationOutputRequestSchema)
    async def get_operation_report(self, request: web.Request):
        operation_id = request.match_info.get('id')
        access = await self.get_request_permissions(request)
        output = await self._read_output_parameter_(request)
        report = await self._api_manager.get_operation_report(operation_id, access, output)
        return web.json_response(report)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Get Operation Event Logs',
                          description='Retrieves the event logs for a given operation_id.',
                          parameters=[{
                                'in': 'path',
                                'name': 'id',
                                'operation_id': 'Unique ID for operation',
                                'access': 'Format for report',
                                'output': 'Boolean for Agent Output in report',
                                'schema': {'type': 'string'},
                                'required': 'true'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.request_schema(OperationOutputRequestSchema)
    @aiohttp_apispec.response_schema(OperationOutputRequestSchema)
    async def get_operation_event_logs(self, request: web.Request):
        operation_id = request.match_info.get('id')
        access = await self.get_request_permissions(request)
        output = await self._read_output_parameter_(request)
        report = await self._api_manager.get_operation_event_logs(operation_id, access, output)
        return web.json_response(report)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Get Links from Operation',
                          description='Retrieves all links for a given operation_id.',
                          parameters=[{
                                'in': 'path',
                                'name': 'id',
                                'operation_id': 'Unique ID for operation',
                                'schema': {'type': 'string'},
                                'required': 'true'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema)
    @aiohttp_apispec.response_schema(LinkSchema(many=True, partial=True),
                                     description='All links contained in operation with the given `id` (String UUID).')
    async def get_operation_links(self, request: web.Request):
        operation_id = request.match_info.get('id')
        access = await self.get_request_permissions(request)
        links = await self._api_manager.get_operation_links(operation_id, access)
        return web.json_response(links)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve a specified link from an operation',
                          description='Retrieve the link with the provided `link_id` (String UUID) from the operation '
                                      'with the given operation `id` (String UUID). Use fields from the '
                                      '`BaseGetOneQuerySchema` in the request body to add `include` and `exclude` '
                                      'filters.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'String UUID of the Operation containing desired link.'},
                              {
                              'in': 'path',
                              'name': 'link_id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'String UUID of the Link with the above operation.'}
                          ])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.response_schema(LinkSchema(partial=True),
                                     description='The link matching the provided `link_id` within the operation '
                                                 'matching `id`. Use fields from the `BaseGetOneQuerySchema` in the '
                                                 'request body to add `include` and `exclude` filters.')
    async def get_operation_link(self, request: web.Request):
        operation_id = request.match_info.get('id')
        link_id = request.match_info.get('link_id')
        access = await self.get_request_permissions(request)
        link = await self._api_manager.get_operation_link(operation_id, link_id, access)
        return web.json_response(link)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve the result of a link',
                          description='Retrieve a dictionary containing a link and its results dictionary based on the operation id (String '
                                      'UUID) and link id (String UUID).  Use fields from the `BaseGetOneQuerySchema` in the '
                                      'request body to add `include` and `exclude` filters.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the operation object to be retrieved.'
                          },
                          {
                              'in': 'path',
                              'name': 'link_id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the link object to retrieve results of.'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.response_schema(LinkResultSchema(),
                                     description='Contains a dictionary with the requested link and its results dictionary.')
    async def get_operation_link_result(self, request: web.Request):
        operation_id = request.match_info.get('id')
        link_id = request.match_info.get('link_id')
        access = await self.get_request_permissions(request)
        result = await self._api_manager.get_operation_link_result(operation_id, link_id, access)
        return web.json_response(result)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Update the specified link within an operation',
                          description='Update the `command` (String) or `status` (Integer) field within the link with '
                                      'the provided  `link_id` (String UUID) from the operation with the given '
                                      'operation `id` (String UUID).',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'String UUID of the Operation containing desired link.'},
                              {
                              'in': 'path',
                              'name': 'link_id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'String UUID of the Link with the above operation.'}
                          ])
    @aiohttp_apispec.request_schema(LinkSchema(partial=True, only=['command', 'status']))
    @aiohttp_apispec.response_schema(LinkSchema,
                                     description='The updated link after a successful `PATCH` request.')
    async def update_operation_link(self, request: web.Request):
        operation_id = request.match_info.get('id')
        link_id = request.match_info.get('link_id')
        access = await self.get_request_permissions(request)
        data = await request.json()
        link = await self._api_manager.update_operation_link(operation_id, link_id, data, access)
        return web.json_response(link)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Creates a potential Link',
                          description='Creates a potential link to be executed by an agent. Create a potential Link using '
                                      'the format provided in the `LinkSchema`. The request body requires `paw`, '
                                      '`executor`, and `ability`.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the operation object for the link to be created on.'
                          }])
    @aiohttp_apispec.request_schema(LinkSchema)
    @aiohttp_apispec.response_schema(LinkSchema,
                                     description='Response contains the newly assigned Link object.')
    async def create_potential_link(self, request: web.Request):
        operation_id = request.match_info.get('id')
        access = await self.get_request_permissions(request)
        data = await request.json()
        potential_link = await self._api_manager.create_potential_link(operation_id, data, access)
        return web.json_response(potential_link)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve potential links for an operation.',
                          description='Retrieve all potential links for an operation based on the operation id (String '
                                      'UUID).  Use fields from the `BaseGetAllQuerySchema` in the request body to add '
                                      '`include`, `exclude`, and `sort` filters.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the operation object to retrieve links for.'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema)
    @aiohttp_apispec.response_schema(LinkSchema(many=True, partial=True),
                                     description='Response contains a list of link objects for the requested id.')
    async def get_potential_links(self, request: web.Request):
        operation_id = request.match_info.get('id')
        access = await self.get_request_permissions(request)
        potential_links = await self._api_manager.get_potential_links(operation_id, access)
        return web.json_response(potential_links)

    @aiohttp_apispec.docs(tags=['operations'],
                          summary='Retrieve potential links for an operation filterd by agent paw (id)',
                          description='Retrieve all potential links for an operation-agent pair based on the operation id (String '
                                      'UUID) and the agent paw (id) (String).  Use fields from the `BaseGetAllQuerySchema` '
                                      'in the request body to add `include`, `exclude`, and `sort` filters.',
                          parameters=[
                              {
                                'in': 'path',
                                'name': 'id',
                                'schema': {'type': 'string'},
                                'required': 'true',
                                'description': 'String UUID of the Operation containing desired links.'},
                              {
                                'in': 'path',
                                'name': 'paw',
                                'schema': {'type': 'string'},
                                'required': 'true',
                                'description': 'Agent paw for the specified operation.'
                              }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.response_schema(LinkSchema(partial=True),
                                     description='All potential links for operation and the specified agent paw.')
    async def get_potential_links_by_paw(self, request: web.Request):
        operation_id = request.match_info.get('id')
        paw = request.match_info.get('paw')
        access = await self.get_request_permissions(request)
        potential_links = await self._api_manager.get_potential_links(operation_id, access, paw)
        return web.json_response(potential_links)

    async def create_object(self, request: web.Request):
        data = await request.json()
        await self._error_if_object_with_id_exists(data.get(self.id_property))
        access = await self.get_request_permissions(request)
        return await self._api_manager.create_object_from_schema(self.schema, data, access)

    async def update_object(self, request: web.Request):
        data, access, obj_id, query, search = await self._parse_common_data_from_request(request)
        obj = await self._api_manager.find_and_update_object(self.ram_key, data, search)
        if not obj:
            raise JsonHttpNotFound(f'{self.description.capitalize()} not found: {obj_id}')
        return obj

    async def _read_output_parameter_(self, request: web.Request):
        raw_body = await request.read()
        output = False
        if raw_body:
            output = json.loads(raw_body).get('enable_agent_output', False)
        return output

    @aiohttp_apispec.docs(tags=['merlino'],
                          summary='Retrieve all operations with detailed information',
                          description='Custom Merlino API to retrieve all operations with full details including links, abilities, and execution information.')
    @aiohttp_apispec.response_schema(OperationSchema(many=True, partial=True),
                                     description='The response is a list of all operations with detailed information.')
    async def merlino_get_operations(self, request: web.Request):
        """Custom Merlino API to get all operations with detailed information in flat format."""
        try:
            operations = list(self._api_manager.find_objects(self.ram_key))
            
            result = []
            for op in operations:
                # Base operation data
                base_data = {
                    'operation': op.name,
                    'state': op.state,
                    'adversary': op.adversary.name if op.adversary else 'N/A',
                    'agents': len(op.agents) if hasattr(op, 'agents') and op.agents else 0,
                    'tcodes': ', '.join([link.ability.technique_id for link in op.chain if link.ability and hasattr(link.ability, 'technique_id') and link.ability.technique_id]) if hasattr(op, 'chain') and op.chain else '',
                    'description': getattr(op, 'description', ''),
                    'comments': getattr(op, 'comments', ''),
                    'assigned': '',  # Will be populated from localStorage on frontend
                    'started': op.start.strftime('%Y-%m-%d %H:%M:%S') if hasattr(op, 'start') and op.start else ''
                }
                
                # IDs to be added at the end
                operation_id = op.id
                adversary_id = op.adversary.adversary_id if op.adversary and hasattr(op.adversary, 'adversary_id') else 'N/A'
                
                # If operation has links, create a flat row for each link
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        try:
                            row = base_data.copy()
                            row.update({
                                'status': decode_link_status(getattr(link, 'status', 'N/A')),
                                'ability': link.ability.name if hasattr(link, 'ability') and link.ability else 'N/A',
                                'tactic': link.ability.tactic if hasattr(link, 'ability') and link.ability and hasattr(link.ability, 'tactic') else 'N/A',
                                'technique': link.ability.technique_id if hasattr(link, 'ability') and link.ability and hasattr(link.ability, 'technique_id') else 'N/A',
                                'agent': str(getattr(link, 'paw', 'N/A')),
                                'host': str(getattr(link, 'host', 'N/A')),
                                'pid': str(getattr(link, 'pid', 'N/A')),
                                'operation_id': operation_id,
                                'adversary_id': adversary_id
                            })
                            result.append(row)
                        except Exception as link_error:
                            # Skip problematic links
                            continue
                else:
                    # If no links, add operation with empty link fields
                    row = base_data.copy()
                    row.update({
                        'status': 'N/A',
                        'ability': 'N/A',
                        'tactic': 'N/A',
                        'technique': 'N/A',
                        'agent': 'N/A',
                        'host': 'N/A',
                        'pid': 'N/A',
                        'operation_id': operation_id,
                        'adversary_id': adversary_id
                    })
                    result.append(row)
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            error_msg = f"Error in merlino_get_operations: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return web.json_response({'error': str(e)}, status=500)

    async def merlino_synchronize(self, request: web.Request):
        """
        Merlino CTI Synchronization API
        POST endpoint that receives operations data from Merlino Excel Add-in
        Creates new adversaries and operations if operation_id/adversary_id are missing
        Returns synchronized operations list in the same format as merlino_get_operations
        """
        try:
            # Get incoming data from Merlino
            data = await request.json()
            
            # Debug: log incoming payload
            import json
            print(f"[MERLINO SYNC] Received payload with {len(data) if isinstance(data, list) else 'N/A'} items")
            print(f"[MERLINO SYNC] Payload content: {json.dumps(data, indent=2)}")
            
            if not isinstance(data, list):
                return web.json_response({'error': 'Expected list of operations'}, status=400)
            
            # Access services
            data_svc = self._api_manager._data_svc
            
            # Process each operation from Merlino
            for op_data in data:
                operation_id = op_data.get('operation_id', '').strip()
                adversary_id = op_data.get('adversary_id', '').strip()
                operation_name = op_data.get('operation', '').strip()
                adversary_name = op_data.get('adversary', '').strip()
                tcodes = op_data.get('tcodes', '').strip()
                
                # Check if this is truly an existing operation by verifying the NAME matches
                is_existing = False
                if operation_id and operation_name:
                    # Look up the operation by ID and check if the name matches
                    existing_by_id = await data_svc.locate('operations', match=dict(id=operation_id))
                    if existing_by_id and len(existing_by_id) > 0:
                        existing_op = existing_by_id[0]
                        if hasattr(existing_op, 'name') and existing_op.name == operation_name:
                            is_existing = True
                            print(f"[MERLINO SYNC] Skipping existing operation '{operation_name}' (ID: {operation_id})")
                        else:
                            print(f"[MERLINO SYNC] Name mismatch! ID {operation_id} has name '{existing_op.name}' but payload says '{operation_name}' - treating as NEW")
                
                if is_existing:
                    continue
                
                # If no name, skip
                if not operation_name or not adversary_name or not tcodes:
                    print(f"[MERLINO SYNC] Skipping - missing required fields: operation='{operation_name}', adversary='{adversary_name}', tcodes='{tcodes}'")
                    continue
                
                # Check if operation with this NAME already exists (by name, not ID)
                existing_by_name = await data_svc.locate('operations', match=dict(name=operation_name))
                
                if existing_by_name and len(existing_by_name) > 0:
                    print(f"[MERLINO SYNC] Operation '{operation_name}' already exists - skipping creation")
                    continue
                
                # NEW OPERATION - Create it with adversary and abilities from tcodes
                print(f"[MERLINO SYNC] Creating NEW operation '{operation_name}' with adversary '{adversary_name}'")
                
                # Extract data from incoming operation
                description = op_data.get('description', '')
                comments = op_data.get('comments', '')
                
                # Parse technique codes (e.g., "T1082, T1027.013") and maintain order
                technique_ids = [t.strip() for t in tcodes.split(',') if t.strip()]
                print(f"[MERLINO SYNC] TCodes to process (in order): {technique_ids}")
                
                # Find ALL abilities for each technique ID, maintaining order
                ability_ids = []
                for tech_id in technique_ids:
                    matching_abilities = await data_svc.locate('abilities', match=dict(technique_id=tech_id))
                    print(f"[MERLINO SYNC] TTP {tech_id}: found {len(matching_abilities)} abilities")
                    
                    for ability in matching_abilities:
                        if ability.ability_id not in ability_ids:
                            ability_ids.append(ability.ability_id)
                            print(f"[MERLINO SYNC]   - Added ability: {ability.name} ({ability.ability_id})")
                
                print(f"[MERLINO SYNC] Total abilities for adversary: {len(ability_ids)}")
                
                if not ability_ids:
                    print(f"[MERLINO SYNC] ERROR: No abilities found for tcodes '{tcodes}' - cannot create operation")
                    continue
                
                # Create Adversary
                from app.objects.c_adversary import Adversary
                new_adversary = Adversary(
                    name=adversary_name,
                    description=description,
                    atomic_ordering=ability_ids,
                    objective='495a9828-cab1-44dd-a0ca-66e58177d8cc'  # Default objective
                )
                
                # Store adversary
                stored_adversary = await data_svc.store(new_adversary)
                print(f"[MERLINO SYNC] Created adversary '{adversary_name}' (ID: {stored_adversary.adversary_id})")
                
                # Get default planner and source
                planners = await data_svc.locate('planners')
                default_planner = planners[0] if planners else None
                
                sources = await data_svc.locate('sources')
                default_source = sources[0] if sources else None
                
                if not default_planner or not default_source:
                    print(f"[MERLINO SYNC] ERROR: Missing planner or source for operation {operation_name}")
                    continue
                
                # Create Operation (PAUSED - must be started manually)
                from app.objects.c_operation import Operation
                new_operation = Operation(
                    name=operation_name,
                    adversary=stored_adversary,
                    planner=default_planner,
                    source=default_source,
                    state='paused',  # Start PAUSED - must be started manually
                    autonomous=1,  # Run automatically when started
                    group='',  # Empty string means "All groups"
                    obfuscator='plain-text',
                    jitter='2/8',
                    visibility=50,
                    comments=comments
                )
                
                # Add description to operation
                if description:
                    new_operation.description = description
                
                # Store operation
                stored_operation = await data_svc.store(new_operation)
                
                print(f"[MERLINO SYNC] Created operation '{operation_name}' (ID: {stored_operation.id})")
            
            # Return all synchronized operations using the same format as merlino_get_operations
            operations = list(self._api_manager.find_objects(self.ram_key))
            print(f"[MERLINO SYNC] Found {len(operations)} operations in database")
            result = []
            
            for op in operations:
                print(f"[MERLINO SYNC] Processing operation: {op.name if hasattr(op, 'name') else 'NO NAME'}")
                
                # Force reload operation to get ALL links (op.chain may be filtered)
                if hasattr(op, 'id'):
                    full_op_list = await data_svc.locate('operations', match=dict(id=op.id))
                    if full_op_list and len(full_op_list) > 0:
                        full_op = full_op_list[0]
                        full_chain = full_op.chain if hasattr(full_op, 'chain') else []
                        print(f"[MERLINO SYNC] Reloaded operation from data_svc - full chain has {len(full_chain)} links")
                    else:
                        full_chain = op.chain if hasattr(op, 'chain') else []
                        print(f"[MERLINO SYNC] Could not reload, using op.chain directly - {len(full_chain)} links")
                else:
                    full_chain = op.chain if hasattr(op, 'chain') else []
                    print(f"[MERLINO SYNC] No operation ID, using op.chain directly - {len(full_chain)} links")
                operation_id = str(op.id) if hasattr(op, 'id') else 'N/A'
                adversary_id = str(op.adversary.adversary_id) if hasattr(op, 'adversary') and op.adversary else 'N/A'
                
                # Extract TTP codes from adversary abilities
                tcodes_list = []
                if hasattr(op, 'adversary') and op.adversary and hasattr(op.adversary, 'atomic_ordering'):
                    for ability_id in op.adversary.atomic_ordering:
                        abilities = await data_svc.locate('abilities', match=dict(ability_id=ability_id))
                        for ability in abilities:
                            if hasattr(ability, 'technique_id') and ability.technique_id:
                                if ability.technique_id not in tcodes_list:
                                    tcodes_list.append(ability.technique_id)
                
                tcodes = ', '.join(tcodes_list) if tcodes_list else ''
                
                # Get team assignment from localStorage (not stored in Caldera)
                assigned = ''
                
                base_data = {
                    'operation': str(getattr(op, 'name', 'N/A')),
                    'state': str(getattr(op, 'state', 'N/A')),
                    'adversary': op.adversary.name if hasattr(op, 'adversary') and op.adversary else 'N/A',
                    'agents': len(op.agents) if hasattr(op, 'agents') else 0,
                    'tcodes': tcodes,
                    'description': str(getattr(op, 'description', '')),
                    'comments': str(getattr(op, 'comments', '')),
                    'assigned': assigned,
                    'started': str(op.start.strftime('%Y-%m-%d %H:%M:%S')) if hasattr(op, 'start') and op.start else 'N/A'
                }
                
                # Use full_chain instead of op.chain
                print(f"[MERLINO SYNC] Operation has {len(full_chain)} links")
                
                if len(full_chain) > 0:
                    print(f"[MERLINO SYNC] Processing {len(full_chain)} links...")
                    for idx, link_data in enumerate(full_chain):
                        print(f"[MERLINO SYNC] Processing link {idx+1}/{len(full_chain)}")
                        try:
                            # Handle both dict (from API) and object (from chain)
                            if isinstance(link_data, dict):
                                ability_name = link_data.get('ability', {}).get('name', 'N/A') if isinstance(link_data.get('ability'), dict) else str(link_data.get('ability', 'N/A'))
                                ability_tactic = link_data.get('ability', {}).get('tactic', 'N/A') if isinstance(link_data.get('ability'), dict) else 'N/A'
                                ability_technique = link_data.get('ability', {}).get('technique_id', 'N/A') if isinstance(link_data.get('ability'), dict) else 'N/A'
                                link_status = link_data.get('status', 'N/A')
                                paw = link_data.get('paw', 'N/A')
                                host = link_data.get('host', 'N/A')
                                pid = str(link_data.get('pid', 'N/A'))
                            else:
                                ability_name = link_data.ability.name if hasattr(link_data, 'ability') and link_data.ability else 'N/A'
                                ability_tactic = link_data.ability.tactic if hasattr(link_data, 'ability') and link_data.ability and hasattr(link_data.ability, 'tactic') else 'N/A'
                                ability_technique = link_data.ability.technique_id if hasattr(link_data, 'ability') and link_data.ability and hasattr(link_data.ability, 'technique_id') else 'N/A'
                                link_status = getattr(link_data, 'status', 'N/A')
                                paw = getattr(link_data, 'paw', 'N/A')
                                host = getattr(link_data, 'host', 'N/A')
                                pid = str(getattr(link_data, 'pid', 'N/A'))
                            
                            print(f"[MERLINO SYNC] Link {idx+1} ability: {ability_name}")
                            
                            row = base_data.copy()
                            row.update({
                                'status': decode_link_status(link_status),
                                'ability': ability_name,
                                'tactic': ability_tactic,
                                'technique': ability_technique,
                                'agent': str(paw),
                                'host': str(host),
                                'pid': str(pid),
                                'operation_id': operation_id,
                                'adversary_id': adversary_id
                            })
                            result.append(row)
                            print(f"[MERLINO SYNC] Link {idx+1} added successfully")
                        except Exception as e:
                            print(f"[MERLINO SYNC] Error processing link {idx+1}: {e}")
                            import traceback
                            print(f"[MERLINO SYNC] Traceback: {traceback.format_exc()}")
                            continue
                else:
                    print(f"[MERLINO SYNC] No links, adding operation with N/A fields")
                    row = base_data.copy()
                    row.update({
                        'status': 'N/A',
                        'ability': 'N/A',
                        'tactic': 'N/A',
                        'technique': 'N/A',
                        'agent': 'N/A',
                        'host': 'N/A',
                        'pid': 'N/A',
                        'operation_id': operation_id,
                        'adversary_id': adversary_id
                    })
                    result.append(row)
            
            print(f"[MERLINO SYNC] Returning {len(result)} rows")
            if len(result) > 0:
                print(f"[MERLINO SYNC] Response preview (first item): {result[0]}")
            else:
                print(f"[MERLINO SYNC] Response is EMPTY - no operations found")
            return web.json_response(result)
        except Exception as e:
            import traceback
            error_msg = f"Error in merlino_synchronize: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return web.json_response({'error': str(e)}, status=500)

    async def merlino_dashboard_metrics(self, request: web.Request):
        """Merlino Dashboard - General Metrics"""
        try:
            operations = list(self._api_manager.find_objects('operations'))
            agents = list(self._api_manager.find_objects('agents'))
            
            # Count operation states
            running = sum(1 for op in operations if op.state == 'running')
            done = sum(1 for op in operations if op.state == 'finished')
            stopped = sum(1 for op in operations if op.state == 'paused')
            
            # Count total abilities and their status across all operations
            total_abilities = 0
            success_count = 0
            error_count = 0
            
            for op in operations:
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        total_abilities += 1
                        status = getattr(link, 'status', -1)
                        if status == 0:
                            success_count += 1
                        elif status in [1, 124]:
                            error_count += 1
            
            # Calculate success rate
            success_rate = (success_count / total_abilities * 100) if total_abilities > 0 else 0.0
            
            # Count agent platforms
            platforms = {}
            for agent in agents:
                platform = getattr(agent, 'platform', 'unknown')
                platforms[platform] = platforms.get(platform, 0) + 1
            
            result = {
                'total_operations': len(operations),
                'operations_running': running,
                'operations_done': done,
                'operations_stopped': stopped,
                'total_abilities': total_abilities if total_abilities > 0 else None,
                'abilities_success': success_count,
                'abilities_errors': error_count,
                'success_rate': round(success_rate, 2),
                'success_rate_status': 'Excellent' if success_rate >= 80 else 'Good' if success_rate >= 60 else 'Needs Attention',
                'active_agents': len(agents),
                'agent_platforms': platforms
            }
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    async def merlino_dashboard_abilities(self, request: web.Request):
        """Merlino Dashboard - Ability Success Rate Analysis"""
        try:
            operations = list(self._api_manager.find_objects('operations'))
            data_svc = self._api_manager._data_svc
            
            # Collect ability statistics
            ability_stats = {}
            
            for op in operations:
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        if not hasattr(link, 'ability') or not link.ability:
                            continue
                        
                        ability_id = link.ability.ability_id
                        status = getattr(link, 'status', -1)
                        
                        if ability_id not in ability_stats:
                            ability_stats[ability_id] = {
                                'ability_id': ability_id,
                                'name': link.ability.name if hasattr(link.ability, 'name') else 'Unknown',
                                'tactic': link.ability.tactic if hasattr(link.ability, 'tactic') else 'N/A',
                                'technique_id': link.ability.technique_id if hasattr(link.ability, 'technique_id') else 'N/A',
                                'executions': 0,
                                'success': 0,
                                'failed': 0,
                                'timeout': 0,
                                'pending': 0,
                                'total_time': 0.0,
                                'operations': set()
                            }
                        
                        ability_stats[ability_id]['executions'] += 1
                        ability_stats[ability_id]['operations'].add(op.id)
                        
                        if status == 0:
                            ability_stats[ability_id]['success'] += 1
                        elif status == 1:
                            ability_stats[ability_id]['failed'] += 1
                        elif status == 124:
                            ability_stats[ability_id]['timeout'] += 1
                        else:
                            ability_stats[ability_id]['pending'] += 1
            
            # Calculate success rates and categorize
            top_performers = []
            needs_attention = []
            needs_improvement = []
            
            for ability_id, stats in ability_stats.items():
                executions = stats['executions']
                success_rate = (stats['success'] / executions * 100) if executions > 0 else 0.0
                avg_time = stats['total_time'] / executions if executions > 0 else 0.0
                
                ability_data = {
                    'ability_id': ability_id,
                    'name': stats['name'],
                    'tactic': stats['tactic'],
                    'technique_id': stats['technique_id'],
                    'executions': executions,
                    'success_rate': round(success_rate, 2),
                    'avg_time': round(avg_time, 2),
                    'success': stats['success'],
                    'failed': stats['failed'],
                    'timeout': stats['timeout'],
                    'pending': stats['pending'],
                    'used_in_operations': len(stats['operations'])
                }
                
                if success_rate >= 80:
                    top_performers.append(ability_data)
                elif success_rate >= 50:
                    needs_attention.append(ability_data)
                else:
                    needs_improvement.append(ability_data)
            
            # Sort by success rate
            top_performers.sort(key=lambda x: x['success_rate'], reverse=True)
            needs_attention.sort(key=lambda x: x['success_rate'], reverse=True)
            needs_improvement.sort(key=lambda x: x['success_rate'])
            
            result = {
                'top_performers': top_performers,
                'needs_attention': needs_attention,
                'needs_improvement': needs_improvement,
                'total_abilities_analyzed': len(ability_stats)
            }
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    async def merlino_dashboard_operations_health(self, request: web.Request):
        """Merlino Dashboard - Operations Health Matrix"""
        try:
            operations = list(self._api_manager.find_objects('operations'))
            
            health_matrix = []
            
            for op in operations:
                total_abilities = 0
                success = 0
                errors = 0
                agents_set = set()
                
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        total_abilities += 1
                        status = getattr(link, 'status', -1)
                        paw = getattr(link, 'paw', None)
                        
                        if paw:
                            agents_set.add(paw)
                        
                        if status == 0:
                            success += 1
                        elif status in [1, 124]:
                            errors += 1
                
                success_rate = (success / total_abilities * 100) if total_abilities > 0 else 0.0
                
                # Calculate health score (0-100)
                if total_abilities == 0:
                    health_score = 0
                else:
                    health_score = success_rate
                
                # Determine health status
                if health_score >= 80:
                    health_status = 'healthy'
                elif health_score >= 50:
                    health_status = 'warning'
                else:
                    health_status = 'critical'
                
                # Map Caldera states to display states
                state_map = {
                    'running': 'RUNNING',
                    'paused': 'STOPPED',
                    'finished': 'FINISHED'
                }
                
                health_matrix.append({
                    'operation_id': op.id,
                    'operation_name': op.name,
                    'status': state_map.get(op.state, op.state.upper()),
                    'abilities': total_abilities,
                    'success': success,
                    'errors': errors,
                    'success_rate': round(success_rate, 2),
                    'agents': len(agents_set),
                    'health': health_status,
                    'health_score': round(health_score, 2),
                    'adversary': op.adversary.name if hasattr(op, 'adversary') and op.adversary else 'N/A',
                    'started': op.start.strftime('%Y-%m-%d %H:%M:%S') if hasattr(op, 'start') and op.start else None
                })
            
            # Sort by health score (worst first)
            health_matrix.sort(key=lambda x: x['health_score'])
            
            return web.json_response(health_matrix)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    async def merlino_dashboard_errors(self, request: web.Request):
        """Merlino Dashboard - Error Analytics & Troubleshooting"""
        try:
            operations = list(self._api_manager.find_objects('operations'))
            
            total_errors = 0
            operations_with_errors = 0
            error_messages = {}
            operation_errors = []
            
            for op in operations:
                op_error_count = 0
                op_error_types = set()
                
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        status = getattr(link, 'status', -1)
                        
                        if status in [1, 124]:
                            total_errors += 1
                            op_error_count += 1
                            
                            # Get error output
                            output = getattr(link, 'output', '')
                            if output:
                                try:
                                    import base64
                                    decoded = base64.b64decode(output).decode('utf-8', errors='ignore')
                                    # Extract first line as error message
                                    error_msg = decoded.split('\n')[0][:100]
                                    error_messages[error_msg] = error_messages.get(error_msg, 0) + 1
                                    op_error_types.add(error_msg)
                                except:
                                    pass
                
                if op_error_count > 0:
                    operations_with_errors += 1
                    
                    # Determine criticality
                    if hasattr(op, 'chain') and op.chain:
                        error_rate = (op_error_count / len(op.chain) * 100)
                        if error_rate >= 50:
                            criticality = 'critical'
                        elif error_rate >= 25:
                            criticality = 'high'
                        else:
                            criticality = 'medium'
                    else:
                        criticality = 'low'
                    
                    operation_errors.append({
                        'operation_id': op.id,
                        'operation_name': op.name,
                        'error_count': op_error_count,
                        'error_types': len(op_error_types),
                        'criticality': criticality
                    })
            
            # Get top 5 most common error messages
            top_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Sort operations by error count
            operation_errors.sort(key=lambda x: x['error_count'], reverse=True)
            
            # Count critical operations
            critical_ops = sum(1 for op in operation_errors if op['criticality'] == 'critical')
            
            # Calculate failure rate
            total_links = sum(len(op.chain) if hasattr(op, 'chain') and op.chain else 0 for op in operations)
            failure_rate = (total_errors / total_links * 100) if total_links > 0 else 0.0
            
            result = {
                'total_errors': total_errors,
                'operations_with_errors': operations_with_errors,
                'critical_operations': critical_ops,
                'unique_error_types': len(error_messages),
                'failure_rate': round(failure_rate, 2),
                'most_common_errors': [{'message': msg, 'count': count} for msg, count in top_errors],
                'operations_ranked': operation_errors[:20]  # Top 20
            }
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    async def merlino_dashboard_realtime(self, request: web.Request):
        """Merlino Dashboard - Real-Time Operations Metrics"""
        try:
            from datetime import datetime, timedelta
            operations = list(self._api_manager.find_objects('operations'))
            
            # Calculate execution velocity (abilities per minute in last 10 mins)
            now = datetime.now()
            ten_mins_ago = now - timedelta(minutes=10)
            
            recent_executions = 0
            total_success = 0
            total_executions = 0
            
            for op in operations:
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        total_executions += 1
                        status = getattr(link, 'status', -1)
                        
                        if status == 0:
                            total_success += 1
                        
                        # Check if executed in last 10 mins
                        if hasattr(link, 'finish') and link.finish:
                            try:
                                finish_time = datetime.fromisoformat(link.finish.replace('Z', '+00:00'))
                                if finish_time >= ten_mins_ago:
                                    recent_executions += 1
                            except:
                                pass
            
            execution_velocity = recent_executions / 10.0  # per minute
            success_rate = (total_success / total_executions * 100) if total_executions > 0 else 0.0
            
            # Count active operations
            running_ops = sum(1 for op in operations if op.state == 'running')
            stopped_ops = sum(1 for op in operations if op.state == 'paused')
            
            # Recent activity (last 10 operations sorted by ID, not start time to avoid datetime issues)
            recent_activity = []
            for op in list(operations)[-10:]:
                activity_msg = 'Operation started with undefined abilities'
                
                if hasattr(op, 'chain') and op.chain:
                    activity_msg = f'Operation has {len(op.chain)} abilities'
                
                recent_activity.append({
                    'operation_name': op.name,
                    'message': activity_msg,
                    'timestamp': op.start.strftime('%H:%M:%S') if hasattr(op, 'start') and op.start else 'N/A'
                })
            
            # Overall health gauge (based on success rate)
            health_percentage = success_rate
            
            result = {
                'execution_velocity': round(execution_velocity, 2),
                'success_rate': round(success_rate, 2),
                'success_rate_trend': 'STABLE',  # Can be improved with historical data
                'active_operations': {
                    'running': running_ops,
                    'stopped': stopped_ops
                },
                'total_abilities': total_executions if total_executions > 0 else None,
                'abilities_ok': total_success,
                'abilities_error': total_executions - total_success,
                'health_percentage': round(health_percentage, 2),
                'recent_activity': recent_activity
            }
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    async def merlino_dashboard_force_graph(self, request: web.Request):
        """Merlino Dashboard - Force Graph Data (Operations, Agents, TTPs)"""
        try:
            operations = list(self._api_manager.find_objects('operations'))
            agents = list(self._api_manager.find_objects('agents'))
            data_svc = self._api_manager._data_svc
            
            nodes = []
            links = []
            
            # Add operation nodes
            operation_ttps = {}
            for op in operations:
                # Get TTPs from adversary
                ttps = []
                if hasattr(op, 'adversary') and op.adversary and hasattr(op.adversary, 'atomic_ordering'):
                    for ability_id in op.adversary.atomic_ordering:
                        abilities = await data_svc.locate('abilities', match=dict(ability_id=ability_id))
                        for ability in abilities:
                            if hasattr(ability, 'technique_id') and ability.technique_id:
                                ttps.append(ability.technique_id)
                
                operation_ttps[op.id] = ttps
                
                # Determine node size based on number of abilities
                size = len(op.chain) if hasattr(op, 'chain') and op.chain else 5
                
                # Color based on state
                color_map = {
                    'running': '#3273dc',   # blue
                    'paused': '#ffdd57',    # yellow
                    'finished': '#48c774'   # green
                }
                
                nodes.append({
                    'id': f'op_{op.id}',
                    'label': op.name[:30],
                    'type': 'operation',
                    'size': max(size, 5),
                    'color': color_map.get(op.state, '#7957d5'),
                    'state': op.state,
                    'ttps': ttps,
                    'metadata': {
                        'full_name': op.name,
                        'adversary': op.adversary.name if hasattr(op, 'adversary') and op.adversary else 'N/A',
                        'abilities': len(op.chain) if hasattr(op, 'chain') and op.chain else 0
                    }
                })
            
            # Add agent nodes
            agent_operations = {}
            for agent in agents:
                # Find operations this agent participated in
                ops_involved = set()
                
                for op in operations:
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            if hasattr(link, 'paw') and link.paw == agent.paw:
                                ops_involved.add(op.id)
                
                agent_operations[agent.paw] = ops_involved
                
                # Color based on platform
                platform_colors = {
                    'windows': '#f14668',   # red
                    'linux': '#48c774',     # green
                    'darwin': '#3273dc'     # blue
                }
                
                nodes.append({
                    'id': f'agent_{agent.paw}',
                    'label': getattr(agent, 'host', agent.paw)[:20],
                    'type': 'agent',
                    'size': 8,
                    'color': platform_colors.get(getattr(agent, 'platform', 'unknown'), '#7957d5'),
                    'platform': getattr(agent, 'platform', 'unknown'),
                    'metadata': {
                        'paw': agent.paw,
                        'host': getattr(agent, 'host', 'unknown'),
                        'group': getattr(agent, 'group', 'unknown'),
                        'operations': len(ops_involved)
                    }
                })
            
            # Create links between operations based on shared TTPs
            op_ids = list(operation_ttps.keys())
            for i, op_id1 in enumerate(op_ids):
                for op_id2 in op_ids[i+1:]:
                    ttps1 = set(operation_ttps[op_id1])
                    ttps2 = set(operation_ttps[op_id2])
                    
                    shared_ttps = ttps1.intersection(ttps2)
                    
                    if len(shared_ttps) > 0:
                        # Strength based on number of shared TTPs
                        strength = len(shared_ttps)
                        
                        links.append({
                            'source': f'op_{op_id1}',
                            'target': f'op_{op_id2}',
                            'value': strength,
                            'type': 'shared_ttp',
                            'label': f'{len(shared_ttps)} TTPs',
                            'metadata': {
                                'shared_ttps': list(shared_ttps)
                            }
                        })
            
            # Create links between agents and operations
            for agent_paw, ops_involved in agent_operations.items():
                for op_id in ops_involved:
                    links.append({
                        'source': f'agent_{agent_paw}',
                        'target': f'op_{op_id}',
                        'value': 1,
                        'type': 'agent_operation',
                        'label': 'executes'
                    })
            
            result = {
                'nodes': nodes,
                'links': links,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_links': len(links),
                    'operations': len([n for n in nodes if n['type'] == 'operation']),
                    'agents': len([n for n in nodes if n['type'] == 'agent'])
                }
            }
            
            return web.json_response(result)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

    # ========== NEW MERLINO OPS GRAPH API (2025-12-26) ==========

    async def merlino_ops_graph(self, request: web.Request):
        """
        API 1 (CORE) — Ops Graph Aggregation
        POST /api/v2/merlino/ops-graph
        
        Return operational force-graph dataset with nodes (operations, agents, problems)
        and edges (agent-operation, operation-problem, agent-problem).
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse request body
            body = await request.json()
            window_minutes = body.get('window_minutes', 60)
            operation_ids_filter = body.get('operation_ids', [])
            agent_paws_filter = body.get('agent_paws', [])
            include_nodes = body.get('include_nodes', ['operation', 'agent', 'problem'])
            include_edges = body.get('include_edges', ['agent_operation', 'operation_problem', 'agent_problem'])
            limits = body.get('limits', {'max_nodes': 250, 'max_edges': 800})
            thresholds = body.get('thresholds', {'min_edge_weight': 1})
            grouping = body.get('grouping', 'tactic_technique')
            
            # Calculate time window
            now = datetime.datetime.utcnow()
            cutoff_time = now - datetime.timedelta(minutes=window_minutes)
            
            # Status normalization function
            def normalize_status(status_value):
                """Normalize link status to success|failed|running"""
                try:
                    status = int(status_value)
                    if status == 0:
                        return 'success'
                    elif status in [1, 124]:  # 1=ERROR, 124=TIMEOUT
                        return 'failed'
                    elif status == -1:  # PAUSE
                        return 'running'
                    else:
                        return 'running'  # Other statuses treated as running
                except (ValueError, TypeError):
                    return 'running'
            
            # Collect all events (links) from all operations
            all_operations = list(self._api_manager.find_objects('operations'))
            all_agents = list(self._api_manager.find_objects('agents'))
            
            # Build event list
            events = []
            for op in all_operations:
                # Filter by operation_ids if specified
                if operation_ids_filter and op.id not in operation_ids_filter:
                    continue
                
                op_data = op.display
                for link in op.chain:
                    link_data = link.display
                    
                    # Parse timestamp
                    try:
                        link_ts = datetime.datetime.fromisoformat(link_data.get('finish', '').replace('Z', '+00:00'))
                        if link_ts < cutoff_time:
                            continue  # Outside time window
                    except:
                        continue  # Skip if no valid timestamp
                    
                    # Get ability details
                    ability = link.ability
                    if not ability:
                        continue
                    
                    # Extract tactic and technique
                    tactic = ability.tactic if hasattr(ability, 'tactic') else 'unknown'
                    technique = 'unknown'
                    if hasattr(ability, 'technique_id'):
                        technique = ability.technique_id
                    elif hasattr(ability, 'technique') and hasattr(ability.technique, 'attack_id'):
                        technique = ability.technique['attack_id']
                    
                    # Normalize status
                    status = normalize_status(link_data.get('status', -1))
                    
                    # Filter by agent if specified
                    agent_paw = link_data.get('paw', '')
                    if agent_paws_filter and agent_paw not in agent_paws_filter:
                        continue
                    
                    # Create event
                    event = {
                        'ts': link_data.get('finish', ''),
                        'operation_id': op.id,
                        'operation': op_data.get('name', 'Unknown'),
                        'agent': agent_paw,
                        'host': link_data.get('host', ''),
                        'ability': ability.name if hasattr(ability, 'name') else 'Unknown',
                        'tactic': tactic,
                        'technique': technique,
                        'status': status
                    }
                    events.append(event)
            
            # Aggregate nodes and edges
            operation_nodes = {}
            agent_nodes = {}
            problem_nodes = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0})
            
            # Edges
            agent_operation_edges = defaultdict(lambda: {'success': 0, 'failed': 0, 'running': 0})
            operation_problem_edges = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0})
            agent_problem_edges = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0})
            
            # Process events
            for event in events:
                op_id = event['operation_id']
                agent_paw = event['agent']
                status = event['status']
                tactic = event['tactic']
                technique = event['technique']
                
                # Problem ID based on grouping
                if grouping == 'tactic_technique':
                    problem_id = f"problem:{tactic}:{technique}"
                else:
                    problem_id = f"problem:{tactic}:{technique}"
                
                # Update operation node
                if 'operation' in include_nodes:
                    if op_id not in operation_nodes:
                        op_obj = next((o for o in all_operations if o.id == op_id), None)
                        if op_obj:
                            operation_nodes[op_id] = {
                                'id': op_id,
                                'name': event['operation'],
                                'state': op_obj.state,
                                'started': op_obj.start.isoformat() if hasattr(op_obj, 'start') and op_obj.start else '',
                                'last_activity': '',
                                'counts': {'success': 0, 'failed': 0, 'running': 0},
                                'agents_count': 0,
                                'agents_set': set()
                            }
                    
                    if op_id in operation_nodes:
                        operation_nodes[op_id]['counts'][status] += 1
                        operation_nodes[op_id]['agents_set'].add(agent_paw)
                        # Update last_activity
                        if not operation_nodes[op_id]['last_activity'] or event['ts'] > operation_nodes[op_id]['last_activity']:
                            operation_nodes[op_id]['last_activity'] = event['ts']
                
                # Update agent node
                if 'agent' in include_nodes:
                    if agent_paw not in agent_nodes:
                        agent_obj = next((a for a in all_agents if a.paw == agent_paw), None)
                        if agent_obj:
                            agent_nodes[agent_paw] = {
                                'paw': agent_paw,
                                'host': event['host'],
                                'platform': agent_obj.platform if hasattr(agent_obj, 'platform') else 'unknown',
                                'last_seen': '',
                                'status': 'active',
                                'counts': {'success': 0, 'failed': 0, 'running': 0}
                            }
                        else:
                            # Agent not found in memory, create minimal node
                            agent_nodes[agent_paw] = {
                                'paw': agent_paw,
                                'host': event['host'],
                                'platform': 'unknown',
                                'last_seen': '',
                                'status': 'inactive',
                                'counts': {'success': 0, 'failed': 0, 'running': 0}
                            }
                    
                    if agent_paw in agent_nodes:
                        agent_nodes[agent_paw]['counts'][status] += 1
                        # Update last_seen
                        if not agent_nodes[agent_paw]['last_seen'] or event['ts'] > agent_nodes[agent_paw]['last_seen']:
                            agent_nodes[agent_paw]['last_seen'] = event['ts']
                
                # Update problem node
                if 'problem' in include_nodes:
                    problem_nodes[problem_id][status] += 1
                
                # Update edges
                if 'agent_operation' in include_edges:
                    edge_key = f"{agent_paw}|{op_id}"
                    agent_operation_edges[edge_key][status] += 1
                
                if 'operation_problem' in include_edges:
                    edge_key = f"{op_id}|{problem_id}"
                    operation_problem_edges[edge_key][status] += 1
                
                if 'agent_problem' in include_edges:
                    edge_key = f"{agent_paw}|{problem_id}"
                    agent_problem_edges[edge_key][status] += 1
            
            # Finalize operation nodes (agents_count)
            for op_id, op_node in operation_nodes.items():
                op_node['agents_count'] = len(op_node['agents_set'])
                del op_node['agents_set']  # Remove temporary set
            
            # Build response
            response = {
                'meta': {
                    'window_minutes': window_minutes,
                    'generated': now.isoformat() + 'Z'
                },
                'nodes': {},
                'edges': {}
            }
            
            # Add operation nodes
            if 'operation' in include_nodes:
                response['nodes']['operations'] = list(operation_nodes.values())
            
            # Add agent nodes
            if 'agent' in include_nodes:
                response['nodes']['agents'] = list(agent_nodes.values())
            
            # Add problem nodes
            if 'problem' in include_nodes:
                problems_list = []
                for problem_id, counts in problem_nodes.items():
                    parts = problem_id.split(':')
                    tactic = parts[1] if len(parts) > 1 else 'unknown'
                    technique = parts[2] if len(parts) > 2 else 'unknown'
                    
                    problems_list.append({
                        'id': problem_id,
                        'kind': grouping,
                        'tactic': tactic,
                        'technique': technique,
                        'label': f"{tactic} / {technique}",
                        'counts': counts
                    })
                response['nodes']['problems'] = problems_list
            
            # Add edges
            if 'agent_operation' in include_edges:
                edges_list = []
                for edge_key, counts in agent_operation_edges.items():
                    agent_paw, op_id = edge_key.split('|')
                    weight = sum(counts.values())
                    if weight >= thresholds.get('min_edge_weight', 1):
                        edges_list.append({
                            'source': f"agent:{agent_paw}",
                            'target': f"op:{op_id}",
                            'weight': weight,
                            'counts': counts
                        })
                # Sort by weight descending and limit
                edges_list.sort(key=lambda x: x['weight'], reverse=True)
                response['edges']['agent_operation'] = edges_list[:limits.get('max_edges', 800)]
            
            if 'operation_problem' in include_edges:
                edges_list = []
                for edge_key, counts in operation_problem_edges.items():
                    op_id, problem_id = edge_key.split('|', 1)
                    weight = counts['failed']  # Only count failures for problem edges
                    if weight >= thresholds.get('min_edge_weight', 1):
                        edges_list.append({
                            'source': f"op:{op_id}",
                            'target': problem_id,
                            'weight': weight,
                            'counts': counts
                        })
                edges_list.sort(key=lambda x: x['weight'], reverse=True)
                response['edges']['operation_problem'] = edges_list[:limits.get('max_edges', 800)]
            
            if 'agent_problem' in include_edges:
                edges_list = []
                for edge_key, counts in agent_problem_edges.items():
                    agent_paw, problem_id = edge_key.split('|', 1)
                    weight = counts['failed']  # Only count failures for problem edges
                    if weight >= thresholds.get('min_edge_weight', 1):
                        edges_list.append({
                            'source': f"agent:{agent_paw}",
                            'target': problem_id,
                            'weight': weight,
                            'counts': counts
                        })
                edges_list.sort(key=lambda x: x['weight'], reverse=True)
                response['edges']['agent_problem'] = edges_list[:limits.get('max_edges', 800)]
            
            return web.json_response(response)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    async def merlino_problem_details(self, request: web.Request):
        """
        API 2 (CORE) — Problem Drilldown
        GET /api/v2/merlino/ops-graph/problem-details?problem_id=problem:execution:T1059&window_minutes=60&limit=100
        
        Return top agents, top operations, and recent events for a specific problem.
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse query params
            problem_id = request.query.get('problem_id')
            if not problem_id:
                return web.json_response({'error': 'problem_id is required'}, status=400)
            
            window_minutes = int(request.query.get('window_minutes', 60))
            limit = int(request.query.get('limit', 100))
            
            # Parse problem_id
            parts = problem_id.split(':')
            if len(parts) < 3:
                return web.json_response({'error': 'Invalid problem_id format'}, status=400)
            
            tactic = parts[1]
            technique = parts[2]
            
            # Calculate time window
            now = datetime.datetime.utcnow()
            cutoff_time = now - datetime.timedelta(minutes=window_minutes)
            
            # Status normalization
            def normalize_status(status_value):
                try:
                    status = int(status_value)
                    if status == 0:
                        return 'success'
                    elif status in [1, 124]:
                        return 'failed'
                    else:
                        return 'running'
                except:
                    return 'running'
            
            # Collect events matching this problem
            all_operations = list(self._api_manager.find_objects('operations'))
            all_agents = list(self._api_manager.find_objects('agents'))
            
            matching_events = []
            agent_stats = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0, 'last_seen': '', 'host': ''})
            operation_stats = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0, 'state': 'unknown', 'name': ''})
            
            for op in all_operations:
                op_data = op.display
                for link in op.chain:
                    link_data = link.display
                    
                    # Parse timestamp
                    try:
                        link_ts = datetime.datetime.fromisoformat(link_data.get('finish', '').replace('Z', '+00:00'))
                        if link_ts < cutoff_time:
                            continue
                    except:
                        continue
                    
                    # Get ability details
                    ability = link.ability
                    if not ability:
                        continue
                    
                    # Check if this link matches the problem
                    link_tactic = ability.tactic if hasattr(ability, 'tactic') else 'unknown'
                    link_technique = 'unknown'
                    if hasattr(ability, 'technique_id'):
                        link_technique = ability.technique_id
                    elif hasattr(ability, 'technique') and hasattr(ability.technique, 'attack_id'):
                        link_technique = ability.technique['attack_id']
                    
                    if link_tactic != tactic or link_technique != technique:
                        continue  # Not matching this problem
                    
                    status = normalize_status(link_data.get('status', -1))
                    agent_paw = link_data.get('paw', '')
                    
                    # Add to events
                    event = {
                        'ts': link_data.get('finish', ''),
                        'operation_id': op.id,
                        'operation': op_data.get('name', 'Unknown'),
                        'agent': agent_paw,
                        'host': link_data.get('host', ''),
                        'ability': ability.name if hasattr(ability, 'name') else 'Unknown',
                        'tactic': link_tactic,
                        'technique': link_technique,
                        'status': status
                    }
                    matching_events.append(event)
                    
                    # Update agent stats
                    agent_stats[agent_paw][status] += 1
                    agent_stats[agent_paw]['host'] = link_data.get('host', '')
                    if not agent_stats[agent_paw]['last_seen'] or event['ts'] > agent_stats[agent_paw]['last_seen']:
                        agent_stats[agent_paw]['last_seen'] = event['ts']
                    
                    # Update operation stats
                    operation_stats[op.id][status] += 1
                    operation_stats[op.id]['state'] = op.state
                    operation_stats[op.id]['name'] = op_data.get('name', 'Unknown')
            
            # Build top_agents
            top_agents = []
            for paw, stats in agent_stats.items():
                top_agents.append({
                    'paw': paw,
                    'host': stats['host'],
                    'failed': stats['failed'],
                    'running': stats['running'],
                    'success': stats['success'],
                    'last_seen': stats['last_seen']
                })
            # Sort by failures descending
            top_agents.sort(key=lambda x: x['failed'], reverse=True)
            
            # Build top_operations
            top_operations = []
            for op_id, stats in operation_stats.items():
                top_operations.append({
                    'id': op_id,
                    'name': stats['name'],
                    'failed': stats['failed'],
                    'running': stats['running'],
                    'success': stats['success'],
                    'state': stats['state']
                })
            top_operations.sort(key=lambda x: x['failed'], reverse=True)
            
            # Sort events by timestamp descending and limit
            matching_events.sort(key=lambda x: x['ts'], reverse=True)
            recent_events = matching_events[:limit]
            
            response = {
                'problem': {
                    'id': problem_id,
                    'tactic': tactic,
                    'technique': technique
                },
                'top_agents': top_agents,
                'top_operations': top_operations,
                'recent_events': recent_events
            }
            
            return web.json_response(response)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    async def merlino_operation_details(self, request: web.Request):
        """
        API 3 (CORE) — Operation Drilldown
        GET /api/v2/merlino/ops-graph/operation-details?operation_id=xxx&window_minutes=60&limit=100
        
        Return per-agent involvement, top problems, and recent events for an operation.
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse query params
            operation_id = request.query.get('operation_id')
            if not operation_id:
                return web.json_response({'error': 'operation_id is required'}, status=400)
            
            window_minutes = int(request.query.get('window_minutes', 60))
            limit = int(request.query.get('limit', 100))
            
            # Calculate time window
            now = datetime.datetime.utcnow()
            cutoff_time = now - datetime.timedelta(minutes=window_minutes)
            
            # Status normalization
            def normalize_status(status_value):
                try:
                    status = int(status_value)
                    if status == 0:
                        return 'success'
                    elif status in [1, 124]:
                        return 'failed'
                    else:
                        return 'running'
                except:
                    return 'running'
            
            # Find the operation
            all_operations = list(self._api_manager.find_objects('operations'))
            operation = next((o for o in all_operations if o.id == operation_id), None)
            
            if not operation:
                return web.json_response({'error': 'Operation not found'}, status=404)
            
            op_data = operation.display
            
            # Collect events from this operation
            events = []
            agent_stats = defaultdict(lambda: {'success': 0, 'failed': 0, 'running': 0, 'host': '', 'platform': 'unknown', 'last_seen': ''})
            problem_stats = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0})
            overall_counts = {'success': 0, 'failed': 0, 'running': 0}
            last_activity = ''
            
            for link in operation.chain:
                link_data = link.display
                
                # Parse timestamp
                try:
                    link_ts = datetime.datetime.fromisoformat(link_data.get('finish', '').replace('Z', '+00:00'))
                    if link_ts < cutoff_time:
                        continue
                except:
                    continue
                
                # Get ability details
                ability = link.ability
                if not ability:
                    continue
                
                tactic = ability.tactic if hasattr(ability, 'tactic') else 'unknown'
                technique = 'unknown'
                if hasattr(ability, 'technique_id'):
                    technique = ability.technique_id
                elif hasattr(ability, 'technique') and hasattr(ability.technique, 'attack_id'):
                    technique = ability.technique['attack_id']
                
                status = normalize_status(link_data.get('status', -1))
                agent_paw = link_data.get('paw', '')
                
                # Add event
                event = {
                    'ts': link_data.get('finish', ''),
                    'agent': agent_paw,
                    'ability': ability.name if hasattr(ability, 'name') else 'Unknown',
                    'tactic': tactic,
                    'technique': technique,
                    'status': status
                }
                events.append(event)
                
                # Update stats
                overall_counts[status] += 1
                agent_stats[agent_paw][status] += 1
                agent_stats[agent_paw]['host'] = link_data.get('host', '')
                
                # Get agent platform
                all_agents = list(self._api_manager.find_objects('agents'))
                agent_obj = next((a for a in all_agents if a.paw == agent_paw), None)
                if agent_obj:
                    agent_stats[agent_paw]['platform'] = agent_obj.platform if hasattr(agent_obj, 'platform') else 'unknown'
                
                if not agent_stats[agent_paw]['last_seen'] or event['ts'] > agent_stats[agent_paw]['last_seen']:
                    agent_stats[agent_paw]['last_seen'] = event['ts']
                
                # Problem stats
                problem_id = f"problem:{tactic}:{technique}"
                problem_stats[problem_id][status] += 1
                
                # Last activity
                if not last_activity or event['ts'] > last_activity:
                    last_activity = event['ts']
            
            # Build agents list
            agents_list = []
            for paw, stats in agent_stats.items():
                agents_list.append({
                    'paw': paw,
                    'host': stats['host'],
                    'platform': stats['platform'],
                    'last_seen': stats['last_seen'],
                    'counts': {
                        'success': stats['success'],
                        'failed': stats['failed'],
                        'running': stats['running']
                    }
                })
            
            # Build top_problems (sort by failures)
            top_problems = []
            for problem_id, stats in problem_stats.items():
                if stats['failed'] > 0:  # Only include problems with failures
                    top_problems.append({
                        'problem_id': problem_id,
                        'failed': stats['failed']
                    })
            top_problems.sort(key=lambda x: x['failed'], reverse=True)
            
            # Sort events by timestamp descending
            events.sort(key=lambda x: x['ts'], reverse=True)
            recent_events = events[:limit]
            
            response = {
                'operation': {
                    'id': operation.id,
                    'name': op_data.get('name', 'Unknown'),
                    'state': operation.state,
                    'started': operation.start.isoformat() if hasattr(operation, 'start') and operation.start else '',
                    'last_activity': last_activity,
                    'counts': overall_counts
                },
                'agents': agents_list,
                'top_problems': top_problems,
                'recent_events': recent_events
            }
            
            return web.json_response(response)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    async def merlino_agent_details(self, request: web.Request):
        """
        API 4 (CORE) — Agent Drilldown
        GET /api/v2/merlino/ops-graph/agent-details?paw=xxx&window_minutes=60&limit=100
        
        Return operations, top problems, and recent events for a specific agent.
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse query params
            paw = request.query.get('paw')
            if not paw:
                return web.json_response({'error': 'paw is required'}, status=400)
            
            window_minutes = int(request.query.get('window_minutes', 60))
            limit = int(request.query.get('limit', 100))
            
            # Calculate time window
            now = datetime.datetime.utcnow()
            cutoff_time = now - datetime.timedelta(minutes=window_minutes)
            
            # Status normalization
            def normalize_status(status_value):
                try:
                    status = int(status_value)
                    if status == 0:
                        return 'success'
                    elif status in [1, 124]:
                        return 'failed'
                    else:
                        return 'running'
                except:
                    return 'running'
            
            # Find the agent
            all_agents = list(self._api_manager.find_objects('agents'))
            agent = next((a for a in all_agents if a.paw == paw), None)
            
            if not agent:
                return web.json_response({'error': 'Agent not found'}, status=404)
            
            # Collect events from all operations for this agent
            all_operations = list(self._api_manager.find_objects('operations'))
            events = []
            operation_stats = defaultdict(lambda: {'success': 0, 'failed': 0, 'running': 0, 'name': '', 'state': 'unknown'})
            problem_stats = defaultdict(lambda: {'failed': 0, 'running': 0, 'success': 0})
            last_seen = ''
            
            for op in all_operations:
                op_data = op.display
                for link in op.chain:
                    link_data = link.display
                    
                    # Only this agent
                    if link_data.get('paw', '') != paw:
                        continue
                    
                    # Parse timestamp
                    try:
                        link_ts = datetime.datetime.fromisoformat(link_data.get('finish', '').replace('Z', '+00:00'))
                        if link_ts < cutoff_time:
                            continue
                    except:
                        continue
                    
                    # Get ability details
                    ability = link.ability
                    if not ability:
                        continue
                    
                    tactic = ability.tactic if hasattr(ability, 'tactic') else 'unknown'
                    technique = 'unknown'
                    if hasattr(ability, 'technique_id'):
                        technique = ability.technique_id
                    elif hasattr(ability, 'technique') and hasattr(ability.technique, 'attack_id'):
                        technique = ability.technique['attack_id']
                    
                    status = normalize_status(link_data.get('status', -1))
                    
                    # Add event
                    event = {
                        'ts': link_data.get('finish', ''),
                        'operation_id': op.id,
                        'ability': ability.name if hasattr(ability, 'name') else 'Unknown',
                        'tactic': tactic,
                        'technique': technique,
                        'status': status
                    }
                    events.append(event)
                    
                    # Update stats
                    operation_stats[op.id][status] += 1
                    operation_stats[op.id]['name'] = op_data.get('name', 'Unknown')
                    operation_stats[op.id]['state'] = op.state
                    
                    problem_id = f"problem:{tactic}:{technique}"
                    problem_stats[problem_id][status] += 1
                    
                    if not last_seen or event['ts'] > last_seen:
                        last_seen = event['ts']
            
            # Build operations list
            operations_list = []
            for op_id, stats in operation_stats.items():
                operations_list.append({
                    'id': op_id,
                    'name': stats['name'],
                    'state': stats['state'],
                    'counts': {
                        'success': stats['success'],
                        'failed': stats['failed'],
                        'running': stats['running']
                    }
                })
            
            # Build top_problems
            top_problems = []
            for problem_id, stats in problem_stats.items():
                if stats['failed'] > 0:
                    top_problems.append({
                        'problem_id': problem_id,
                        'failed': stats['failed']
                    })
            top_problems.sort(key=lambda x: x['failed'], reverse=True)
            
            # Sort events by timestamp descending
            events.sort(key=lambda x: x['ts'], reverse=True)
            recent_events = events[:limit]
            
            response = {
                'agent': {
                    'paw': paw,
                    'host': agent.host if hasattr(agent, 'host') else 'unknown',
                    'platform': agent.platform if hasattr(agent, 'platform') else 'unknown',
                    'last_seen': last_seen,
                    'status': 'active' if agent.trusted else 'inactive'
                },
                'operations': operations_list,
                'top_problems': top_problems,
                'recent_events': recent_events
            }
            
            return web.json_response(response)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    async def merlino_ops_actions(self, request: web.Request):
        """
        API 5 (OPTIONAL) — Intervention Actions
        POST /api/v2/merlino/ops-actions
        
        Allow Merlino UI to trigger operational actions:
        - pause_operation
        - stop_operation
        - tag_agent
        """
        try:
            body = await request.json()
            action = body.get('action')
            
            if not action:
                return web.json_response({'error': 'action is required'}, status=400)
            
            if action == 'pause_operation':
                operation_id = body.get('operation_id')
                if not operation_id:
                    return web.json_response({'error': 'operation_id is required'}, status=400)
                
                # Find and pause the operation
                operations = list(self._api_manager.find_objects('operations'))
                operation = next((o for o in operations if o.id == operation_id), None)
                
                if not operation:
                    return web.json_response({'error': 'Operation not found'}, status=404)
                
                operation.state = 'paused'
                await self._api_manager.data_svc.store(operation)
                
                return web.json_response({
                    'ok': True,
                    'message': 'paused',
                    'operation_id': operation_id
                })
            
            elif action == 'stop_operation':
                operation_id = body.get('operation_id')
                if not operation_id:
                    return web.json_response({'error': 'operation_id is required'}, status=400)
                
                # Find and stop the operation
                operations = list(self._api_manager.find_objects('operations'))
                operation = next((o for o in operations if o.id == operation_id), None)
                
                if not operation:
                    return web.json_response({'error': 'Operation not found'}, status=404)
                
                operation.state = 'finished'
                await self._api_manager.data_svc.store(operation)
                
                return web.json_response({
                    'ok': True,
                    'message': 'stopped',
                    'operation_id': operation_id
                })
            
            elif action == 'tag_agent':
                paw = body.get('paw')
                tag = body.get('tag')
                
                if not paw or not tag:
                    return web.json_response({'error': 'paw and tag are required'}, status=400)
                
                # Find and tag the agent
                agents = list(self._api_manager.find_objects('agents'))
                agent = next((a for a in agents if a.paw == paw), None)
                
                if not agent:
                    return web.json_response({'error': 'Agent not found'}, status=404)
                
                # Add tag to agent (store in group field for now)
                if not hasattr(agent, 'tags'):
                    agent.tags = []
                if tag not in agent.tags:
                    agent.tags.append(tag)
                
                await self._api_manager.data_svc.store(agent)
                
                return web.json_response({
                    'ok': True,
                    'message': f'tagged as {tag}',
                    'paw': paw,
                    'tag': tag
                })
            
            else:
                return web.json_response({'error': f'Unknown action: {action}'}, status=400)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    async def merlino_ui_routes(self, request: web.Request):
        """
        API 6 (OPTIONAL) — UI Route Resolver
        GET /api/v2/merlino/ui-routes
        
        Return UI URL patterns so Merlino can open Morgana pages.
        """
        try:
            # Get base URL from request
            scheme = request.scheme
            host = request.host
            base_url = f"{scheme}://{host}"
            
            response = {
                'base_url': base_url,
                'routes': {
                    'operation': '/operations/{id}',
                    'agent': '/agents/{paw}',
                    'search': '/search?q={query}'
                }
            }
            
            return web.json_response(response)
        
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
            
        except Exception as e:
            import traceback
            error_msg = f"Error in merlino_synchronize: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
