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


def build_ops_graph_recent_link(link, operation, output_max_chars=4000, output_format='raw'):
    """
    Build OpsGraphRecentLink object from Caldera link.
    
    Args:
        link: Caldera link object
        operation: Caldera operation object
        output_max_chars: Maximum characters for output (0 = omit output)
        output_format: 'raw' or 'base64'
    
    Returns:
        dict with OpsGraphRecentLink structure
    """
    import base64
    import datetime
    
    link_data = link.display
    
    # Normalize status
    def normalize_status(status_value):
        try:
            status = int(status_value)
            if status == 0:
                return 'success'
            elif status == 1:
                return 'failed'
            elif status == 124:
                return 'timeout'
            elif status == -1:
                return 'running'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    # Extract command (prefer plaintext)
    command = link_data.get('plaintext_command', '')
    command_is_plaintext = bool(command)
    if not command:
        command = link_data.get('command', '')
        command_is_plaintext = False
    
    # Extract and truncate output
    output_raw = ''
    output_truncated = False
    if output_max_chars > 0:
        # Get output from link (may be base64 encoded or boolean string)
        output_field = link_data.get('output', '')
        if output_field and output_field not in ['True', 'False']:
            output_raw = str(output_field)
            if len(output_raw) > output_max_chars:
                output_raw = output_raw[:output_max_chars]
                output_truncated = True
    
    # Encode output if requested
    if output_format == 'base64' and output_raw:
        output_raw = base64.b64encode(output_raw.encode('utf-8')).decode('ascii')
    
    # Get ability details
    ability = link.ability if hasattr(link, 'ability') else None
    ability_id = ability.ability_id if ability and hasattr(ability, 'ability_id') else ''
    ability_name = ability.name if ability and hasattr(ability, 'name') else ''
    tactic = ability.tactic if ability and hasattr(ability, 'tactic') else 'unknown'
    
    # Extract technique
    technique = 'unknown'
    if ability:
        if hasattr(ability, 'technique_id'):
            technique = ability.technique_id
        elif hasattr(ability, 'technique') and isinstance(ability.technique, dict):
            technique = ability.technique.get('attack_id', 'unknown')
    
    # Get timestamps
    executed_at = link_data.get('decide', '')
    finished_at = link_data.get('finish', '')
    
    # Get agent details
    agent_paw = link_data.get('paw', '')
    host = link_data.get('host', '')
    
    # Find agent for platform
    platform = 'unknown'
    if hasattr(operation, 'agents'):
        for agent in operation.agents:
            if agent.paw == agent_paw:
                platform = agent.platform
                break
    
    # Get operation details
    op_data = operation.display if hasattr(operation, 'display') else {}
    operation_id = op_data.get('id', '')
    operation_name = op_data.get('name', '')
    
    return {
        'link_id': link_data.get('id', ''),
        'operation_id': operation_id,
        'operation_name': operation_name,
        'agent_paw': agent_paw,
        'host': host,
        'platform': platform,
        'ability_id': ability_id,
        'ability_name': ability_name,
        'tactic': tactic,
        'technique': technique,
        'status': normalize_status(link_data.get('status', -1)),
        'command': command,
        'command_is_plaintext': command_is_plaintext,
        'output': output_raw if output_max_chars > 0 else '',
        'output_truncated': output_truncated,
        'executed_at': executed_at,
        'finished_at': finished_at
    }


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
        router.add_get('/merlino/analytics/ability-success-rate', self.merlino_analytics_ability_success_rate)
        router.add_get('/merlino/analytics/operations-health-matrix', self.merlino_analytics_operations_health_matrix)
        router.add_get('/merlino/analytics/operations-health-matrix/operation/{operation_id}', self.merlino_analytics_operation_health_details)
        # Error Analytics API
        router.add_get('/merlino/analytics/error-analytics/overview', self.merlino_error_analytics_overview)
        router.add_get('/merlino/analytics/error-analytics/breakdown', self.merlino_error_analytics_breakdown)
        router.add_get('/merlino/analytics/error-analytics/top-offenders', self.merlino_error_analytics_top_offenders)
        router.add_get('/merlino/analytics/error-analytics/events/search', self.merlino_error_analytics_events_search)
        router.add_get('/merlino/analytics/error-analytics/operation/{operation_id}', self.merlino_error_analytics_operation_drilldown)
        router.add_get('/merlino/analytics/error-analytics/signatures', self.merlino_error_analytics_signatures)
        router.add_get('/merlino/analytics/error-analytics/signature/{signature_id}', self.merlino_error_analytics_signature_drilldown)
        router.add_get('/merlino/analytics/error-analytics/hints', self.merlino_error_analytics_hints)
        # Realtime Operations Metrics API
        router.add_get('/merlino/realtime/operations/metrics', self.merlino_realtime_operations_metrics)
        router.add_get('/merlino/realtime/operations', self.merlino_realtime_operations)
        router.add_get('/merlino/realtime/agents', self.merlino_realtime_agents)
        router.add_get('/merlino/realtime/timeline', self.merlino_realtime_timeline)
        router.add_get('/merlino/dashboard/realtime', self.merlino_dashboard_realtime)
        router.add_get('/merlino/dashboard/force-graph', self.merlino_dashboard_force_graph)
        # Agents Intelligence API
        router.add_get('/merlino/agents/intelligence/overview', self.merlino_agents_intelligence_overview)
        router.add_get('/merlino/agents/intelligence/agent/{paw}', self.merlino_agents_intelligence_agent_detail)
        router.add_get('/merlino/agents/intelligence/graph', self.merlino_agents_intelligence_graph)
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
                                      'UUID). The `state`, `autonomous`, `obfuscator` and `group` fields in the operation '
                                      'object may be edited in the request body using the `OperationSchema`.',
                          parameters=[{
                              'in': 'path',
                              'name': 'id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the Operation object to be retrieved.'
                          }])
    @aiohttp_apispec.request_schema(OperationSchema(partial=True, only=['state', 'autonomous', 'obfuscator', 'group']))
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
                            # Extract command (prefer plaintext) and encode to base64
                            import base64
                            link_command_raw = getattr(link, 'plaintext_command', '')
                            if not link_command_raw:
                                link_command_raw = getattr(link, 'command', '')
                            
                            # Always encode command to base64
                            link_command = ''
                            if link_command_raw:
                                # If already base64, keep it; otherwise encode it
                                try:
                                    # Try to decode - if it fails, it's plaintext
                                    base64.b64decode(link_command_raw, validate=True)
                                    link_command = link_command_raw  # Already base64
                                except:
                                    # It's plaintext, encode it
                                    link_command = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                            
                            # Extract output from result file (encrypted)
                            link_output = ''
                            try:
                                link_id = getattr(link, 'id', '')
                                if link_id:
                                    # Use file_svc to read and decrypt the result file
                                    file_svc = self._api_manager._file_svc
                                    output_content = file_svc.read_result_file(link_id)
                                    if output_content:
                                        link_output = output_content
                            except FileNotFoundError:
                                # No result file exists
                                pass
                            except Exception as e:
                                # Log but don't crash
                                self.log.warning(f'Failed to read result file for link {link_id}: {e}')
                            
                            row = base_data.copy()
                            row.update({
                                'status': decode_link_status(getattr(link, 'status', 'N/A')),
                                'ability': link.ability.name if hasattr(link, 'ability') and link.ability else 'N/A',
                                'tactic': link.ability.tactic if hasattr(link, 'ability') and link.ability and hasattr(link.ability, 'tactic') else 'N/A',
                                'technique': link.ability.technique_id if hasattr(link, 'ability') and link.ability and hasattr(link.ability, 'technique_id') else 'N/A',
                                'agent': str(getattr(link, 'paw', 'N/A')),
                                'host': str(getattr(link, 'host', 'N/A')),
                                'pid': str(getattr(link, 'pid', 'N/A')),
                                'link_command': link_command,
                                'link_output': link_output,
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
                        'link_command': '',
                        'link_output': '',
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
                            
                            # Extract command (prefer plaintext) and encode to base64
                            import base64
                            link_command_raw = ''
                            if isinstance(link_data, dict):
                                link_command_raw = link_data.get('plaintext_command', '')
                                if not link_command_raw:
                                    link_command_raw = link_data.get('command', '')
                            else:
                                link_command_raw = getattr(link_data, 'plaintext_command', '')
                                if not link_command_raw:
                                    link_command_raw = getattr(link_data, 'command', '')
                            
                            # Always encode command to base64
                            link_command = ''
                            if link_command_raw:
                                # If already base64, keep it; otherwise encode it
                                try:
                                    # Try to decode - if it fails, it's plaintext
                                    base64.b64decode(link_command_raw, validate=True)
                                    link_command = link_command_raw  # Already base64
                                except:
                                    # It's plaintext, encode it
                                    link_command = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                            
                            # Extract output from result file (encrypted)
                            link_output = ''
                            link_id = ''
                            try:
                                if isinstance(link_data, dict):
                                    link_id = link_data.get('id', '')
                                else:
                                    link_id = getattr(link_data, 'id', '')
                                
                                if link_id:
                                    # Use file_svc to read and decrypt the result file
                                    file_svc = self._api_manager._file_svc
                                    output_content = file_svc.read_result_file(link_id)
                                    if output_content:
                                        link_output = output_content
                            except FileNotFoundError:
                                # No result file exists
                                pass
                            except Exception as e:
                                # Log but don't crash
                                self.log.warning(f'Failed to read result file for link {link_id}: {e}')
                            
                            
                            row = base_data.copy()
                            row.update({
                                'status': decode_link_status(link_status),
                                'ability': ability_name,
                                'tactic': ability_tactic,
                                'technique': ability_technique,
                                'agent': str(paw),
                                'host': str(host),
                                'pid': str(pid),
                                'link_command': link_command,
                                'link_output': link_output,
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
                        'link_command': '',
                        'link_output': '',
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
        
        Supports two body formats:
        1. Spec format: window_minutes, include_nodes, etc.
        2. Frontend format: options.includeAgents, options.includeProblems, etc.
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse request body (support both formats)
            body = await request.json()
            
            # Check if using frontend format (options object)
            if 'options' in body:
                options = body.get('options', {})
                window_minutes = options.get('windowMinutes', 10080)  # Default 7 days for frontend
                operation_ids_filter = []
                agent_paws_filter = []
                
                # Determine which nodes to include
                include_nodes = ['operation']  # Always include operations
                if options.get('includeAgents', True):
                    include_nodes.append('agent')
                if options.get('includeProblems', True):
                    include_nodes.append('problem')
                
                include_edges = ['agent_operation', 'operation_problem', 'agent_problem']
                limits = {
                    'max_nodes': options.get('maxNodes', 400),
                    'max_edges': options.get('maxEdges', 1200)
                }
                thresholds = {'min_edge_weight': 1}
                grouping = 'tactic_technique'
            else:
                # Spec format
                window_minutes = body.get('window_minutes', 60)
                operation_ids_filter = body.get('operation_ids', [])
                agent_paws_filter = body.get('agent_paws', [])
                include_nodes = body.get('include_nodes', ['operation', 'agent', 'problem'])
                include_edges = body.get('include_edges', ['agent_operation', 'operation_problem', 'agent_problem'])
                limits = body.get('limits', {'max_nodes': 250, 'max_edges': 800})
                thresholds = body.get('thresholds', {'min_edge_weight': 1})
                grouping = body.get('grouping', 'tactic_technique')
            
            # Calculate time window
            now = datetime.datetime.now(datetime.timezone.utc)  # Timezone-aware
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
                        # Check for finish timestamp
                        if 'finish' not in link_data:
                            continue
                        
                        finish_value = link_data['finish']
                        if not finish_value or finish_value is None:
                            continue
                        
                        # Parse and check time window
                        link_ts = datetime.datetime.fromisoformat(str(finish_value).replace('Z', '+00:00'))
                        if link_ts < cutoff_time:
                            continue  # Outside time window
                    except Exception as e:
                        continue  # Skip if timestamp parsing fails
                    
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
            
            # Check if frontend wants flat format
            if 'options' in body:
                # Convert to frontend format: flat nodes and edges arrays
                flat_nodes = []
                flat_edges = []
                edge_id_counter = 0
                
                # Convert operation nodes
                for op_node in response['nodes'].get('operations', []):
                    flat_nodes.append({
                        'id': f"op:{op_node['id']}",
                        'type': 'operation',
                        'label': op_node['name'],
                        'state': op_node['state'],
                        'counts': op_node['counts']
                    })
                
                # Convert agent nodes
                for agent_node in response['nodes'].get('agents', []):
                    flat_nodes.append({
                        'id': f"agent:{agent_node['paw']}",
                        'type': 'agent',
                        'label': f"{agent_node['host']} ({agent_node['paw'][:6]})",
                        'paw': agent_node['paw'],
                        'host': agent_node['host'],
                        'platform': agent_node['platform'],
                        'status': agent_node['status'],
                        'counts': agent_node['counts']
                    })
                
                # Convert problem nodes
                for prob_node in response['nodes'].get('problems', []):
                    flat_nodes.append({
                        'id': prob_node['id'],
                        'type': 'problem',
                        'label': prob_node['label'],
                        'tactic': prob_node['tactic'],
                        'technique': prob_node['technique'],
                        'counts': prob_node['counts']
                    })
                
                # Convert edges
                for edge in response['edges'].get('agent_operation', []):
                    flat_edges.append({
                        'id': f"edge_{edge_id_counter}",
                        'source': edge['source'],
                        'target': edge['target'],
                        'type': 'agent_in_operation',
                        'weight': edge['weight']
                    })
                    edge_id_counter += 1
                
                for edge in response['edges'].get('operation_problem', []):
                    flat_edges.append({
                        'id': f"edge_{edge_id_counter}",
                        'source': edge['source'],
                        'target': edge['target'],
                        'type': 'operation_has_problem',
                        'weight': edge['weight']
                    })
                    edge_id_counter += 1
                
                for edge in response['edges'].get('agent_problem', []):
                    flat_edges.append({
                        'id': f"edge_{edge_id_counter}",
                        'source': edge['source'],
                        'target': edge['target'],
                        'type': 'agent_has_problem',
                        'weight': edge['weight']
                    })
                    edge_id_counter += 1
                
                # Return flat format
                return web.json_response({
                    'nodes': flat_nodes,
                    'edges': flat_edges
                })
            
            # Return spec format (nested)
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
            
            # New query params for link details
            include_links = request.query.get('include_links', 'false').lower() == 'true'
            output_max_chars = int(request.query.get('output_max_chars', 4000))
            output_format = request.query.get('output_format', 'raw')
            
            # Enforce caps
            limit = min(limit, 200)
            output_max_chars = max(0, min(output_max_chars, 50000))
            if output_format not in ['raw', 'base64']:
                output_format = 'raw'
            
            # Parse problem_id
            parts = problem_id.split(':')
            if len(parts) < 3:
                return web.json_response({'error': 'Invalid problem_id format'}, status=400)
            
            tactic = parts[1]
            technique = parts[2]
            
            # Calculate time window
            now = datetime.datetime.now(datetime.timezone.utc)
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
            recent_links_data = []  # For include_links
            
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
                    
                    # Build link detail if requested
                    if include_links:
                        link_detail = build_ops_graph_recent_link(link, op, output_max_chars, output_format)
                        recent_links_data.append(link_detail)
                    
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
            
            # Limit and sort recent_links
            if include_links:
                recent_links_data.sort(key=lambda x: x['finished_at'], reverse=True)
                recent_links_data = recent_links_data[:limit]
            
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
            
            # Add link details if requested
            if include_links:
                response['recent_links'] = recent_links_data
                response['links_meta'] = {
                    'include_links': True,
                    'output_max_chars': output_max_chars,
                    'output_format': output_format
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
            
            # New query params for link details
            include_links = request.query.get('include_links', 'false').lower() == 'true'
            output_max_chars = int(request.query.get('output_max_chars', 4000))
            output_format = request.query.get('output_format', 'raw')
            
            # Enforce caps
            limit = min(limit, 200)
            output_max_chars = max(0, min(output_max_chars, 50000))
            if output_format not in ['raw', 'base64']:
                output_format = 'raw'
            
            # Calculate time window
            now = datetime.datetime.now(datetime.timezone.utc)
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
            recent_links_data = []  # For include_links
            
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
                
                # Build link detail if requested
                if include_links:
                    link_detail = build_ops_graph_recent_link(link, operation, output_max_chars, output_format)
                    recent_links_data.append(link_detail)
                
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
            
            # Limit and sort recent_links
            if include_links:
                recent_links_data.sort(key=lambda x: x['finished_at'], reverse=True)
                recent_links_data = recent_links_data[:limit]
            
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
            
            # Add link details if requested
            if include_links:
                response['recent_links'] = recent_links_data
                response['links_meta'] = {
                    'include_links': True,
                    'output_max_chars': output_max_chars,
                    'output_format': output_format
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
        GET /api/v2/merlino/ops-graph/agent-details?agent_paw=xxx&window_minutes=60&limit=100
        
        Return operations, top problems, and recent events for a specific agent.
        Supports both 'agent_paw' (frontend) and 'paw' (spec) query parameters.
        """
        try:
            import datetime
            from collections import defaultdict
            
            # Parse query params (support both agent_paw and paw)
            paw = request.query.get('agent_paw') or request.query.get('paw')
            if not paw:
                return web.json_response({'error': 'agent_paw or paw is required'}, status=400)
            
            window_minutes = int(request.query.get('window_minutes', 60))
            limit = int(request.query.get('limit', 100))
            
            # New query params for link details
            include_links = request.query.get('include_links', 'false').lower() == 'true'
            output_max_chars = int(request.query.get('output_max_chars', 4000))
            output_format = request.query.get('output_format', 'raw')
            
            # Enforce caps
            limit = min(limit, 200)
            output_max_chars = max(0, min(output_max_chars, 50000))
            if output_format not in ['raw', 'base64']:
                output_format = 'raw'
            
            # Calculate time window
            now = datetime.datetime.now(datetime.timezone.utc)
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
            recent_links_data = []  # For include_links
            
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
                    
                    # Build link detail if requested
                    if include_links:
                        link_detail = build_ops_graph_recent_link(link, op, output_max_chars, output_format)
                        recent_links_data.append(link_detail)
                    
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
            
            # Limit and sort recent_links
            if include_links:
                recent_links_data.sort(key=lambda x: x['finished_at'], reverse=True)
                recent_links_data = recent_links_data[:limit]
            
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
            
            # Add link details if requested
            if include_links:
                response['recent_links'] = recent_links_data
                response['links_meta'] = {
                    'include_links': True,
                    'output_max_chars': output_max_chars,
                    'output_format': output_format
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
    
    async def merlino_analytics_ability_success_rate(self, request: web.Request):
        """
        Merlino Analytics - Ability Success Rate Analysis
        
        Provides aggregate statistics on ability execution success rates, execution times,
        and recent failures for troubleshooting.
        
        Query params:
        - since_hours (int, default 72): time window in hours
        - from (ISO-8601): window start time
        - to (ISO-8601): window end time  
        - operation_id (str): filter to specific operation
        - agent_paw (str): filter to specific agent
        - group (str): filter to agent group
        - limit (int, default 250, max 2000): max abilities returned
        - min_executions (int, default 1): minimum executions to include ability
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict
            import base64
            import json as json_lib
            
            # Parse query parameters
            params = request.rel_url.query
            since_hours = int(params.get('since_hours', 72))
            from_str = params.get('from')
            to_str = params.get('to')
            operation_id_filter = params.get('operation_id')
            agent_paw_filter = params.get('agent_paw')
            group_filter = params.get('group')
            limit = min(int(params.get('limit', 250)), 2000)
            min_executions = int(params.get('min_executions', 1))
            
            # Determine time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(hours=since_hours)
                window_to = now
            
            # Get all operations
            operations = list(self._api_manager.find_objects('operations'))
            agents = list(self._api_manager.find_objects('agents'))
            
            # Build agent lookup for group filtering
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Aggregate data by ability_id
            ability_data = defaultdict(lambda: {
                'ability_id': None,
                'ability_name': None,
                'plugin': None,
                'tactics': set(),
                'techniques': set(),
                'total_executions': 0,
                'success_count': 0,
                'failure_count': 0,
                'timeout_count': 0,
                'running_count': 0,
                'execution_times': [],
                'operations': defaultdict(lambda: {
                    'operation_id': None,
                    'operation_name': None,
                    'executions': 0,
                    'success': 0,
                    'failed': 0,
                    'timeout': 0,
                    'running': 0
                }),
                'recent_failures': []
            })
            
            # Process operations and links
            for op in operations:
                # Filter by operation_id
                if operation_id_filter and op.id != operation_id_filter:
                    continue
                
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    # Get link properties
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_ability = getattr(link, 'ability', None)
                    
                    if not link_ability:
                        continue
                    
                    # Filter by agent_paw
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    # Filter by group
                    if group_filter:
                        agent = agent_lookup.get(link_paw)
                        if not agent or getattr(agent, 'group', None) != group_filter:
                            continue
                    
                    # Get ability details
                    ability_id = getattr(link_ability, 'ability_id', None)
                    if not ability_id:
                        continue
                    
                    ability_name = getattr(link_ability, 'name', 'Unknown')
                    ability_tactic = getattr(link_ability, 'tactic', None)
                    ability_technique = getattr(link_ability, 'technique_id', None)
                    ability_plugin = getattr(link_ability, 'plugin', None)
                    
                    # Get execution time (if available)
                    exec_time_ms = None
                    if hasattr(link, 'finish') and hasattr(link, 'decide'):
                        finish = getattr(link, 'finish', None)
                        decide = getattr(link, 'decide', None)
                        if finish and decide:
                            try:
                                if isinstance(finish, str):
                                    finish = datetime.fromisoformat(finish.replace('Z', '+00:00'))
                                if isinstance(decide, str):
                                    decide = datetime.fromisoformat(decide.replace('Z', '+00:00'))
                                exec_time_ms = int((finish - decide).total_seconds() * 1000)
                            except:
                                pass
                    
                    # Normalize status
                    if link_status == 0:
                        status_bucket = 'success'
                    elif link_status == 1:
                        status_bucket = 'failed'
                    elif link_status == 124:
                        status_bucket = 'timeout'
                    elif link_status == -1:
                        status_bucket = 'running'
                    else:
                        status_bucket = 'running'  # Unknown = running
                    
                    # Update ability aggregate data
                    data = ability_data[ability_id]
                    if not data['ability_id']:
                        data['ability_id'] = ability_id
                        data['ability_name'] = ability_name
                        data['plugin'] = ability_plugin or 'unknown'
                        if ability_tactic:
                            data['tactics'].add(ability_tactic)
                        if ability_technique:
                            data['techniques'].add(ability_technique)
                    
                    data['total_executions'] += 1
                    
                    if status_bucket == 'success':
                        data['success_count'] += 1
                    elif status_bucket == 'failed':
                        data['failure_count'] += 1
                    elif status_bucket == 'timeout':
                        data['timeout_count'] += 1
                    elif status_bucket == 'running':
                        data['running_count'] += 1
                    
                    if exec_time_ms:
                        data['execution_times'].append(exec_time_ms)
                    
                    # Update per-operation stats
                    op_stats = data['operations'][op.id]
                    if not op_stats['operation_id']:
                        op_stats['operation_id'] = op.id
                        op_stats['operation_name'] = op.name
                    op_stats['executions'] += 1
                    if status_bucket == 'success':
                        op_stats['success'] += 1
                    elif status_bucket == 'failed':
                        op_stats['failed'] += 1
                    elif status_bucket == 'timeout':
                        op_stats['timeout'] += 1
                    elif status_bucket == 'running':
                        op_stats['running'] += 1
                    
                    # Track recent failures (up to 5 per ability)
                    if status_bucket in ['failed', 'timeout'] and len(data['recent_failures']) < 5:
                        # Read output for error context
                        stdout_preview = ''
                        stderr_preview = ''
                        exit_code = None
                        
                        try:
                            link_id = getattr(link, 'id', '')
                            if link_id:
                                file_svc = self._api_manager._file_svc
                                output_content = file_svc.read_result_file(link_id)
                                if output_content:
                                    decoded_output = base64.b64decode(output_content).decode('utf-8')
                                    output_json = json_lib.loads(decoded_output)
                                    stdout_preview = output_json.get('stdout', '')[:200]
                                    stderr_preview = output_json.get('stderr', '')[:200]
                                    exit_code = output_json.get('exit_code')
                        except:
                            pass
                        
                        # Get timestamp (prefer finish, fallback to now)
                        when = now
                        if hasattr(link, 'finish'):
                            finish = getattr(link, 'finish', None)
                            if finish:
                                try:
                                    if isinstance(finish, str):
                                        when = datetime.fromisoformat(finish.replace('Z', '+00:00'))
                                    else:
                                        when = finish
                                except:
                                    pass
                        
                        # Build problem_id for drilldown
                        problem_id = None
                        if ability_tactic and ability_technique:
                            problem_id = f"{ability_tactic}/{ability_technique}"
                        
                        data['recent_failures'].append({
                            'when': when.isoformat(),
                            'operation_id': op.id,
                            'operation_name': op.name,
                            'agent_paw': link_paw or 'unknown',
                            'agent_host': getattr(link, 'host', 'unknown'),
                            'exit_code': exit_code,
                            'stderr_preview': stderr_preview,
                            'stdout_preview': stdout_preview,
                            'problem_id': problem_id
                        })
            
            # Compute final metrics and filter by min_executions
            abilities_list = []
            for ability_id, data in ability_data.items():
                if data['total_executions'] < min_executions:
                    continue
                
                # Calculate success rate
                if data['total_executions'] > 0:
                    success_rate = (data['success_count'] / data['total_executions']) * 100
                else:
                    success_rate = 0.0
                
                # Calculate execution time stats
                avg_execution_time_ms = None
                p95_execution_time_ms = None
                if data['execution_times']:
                    avg_execution_time_ms = int(sum(data['execution_times']) / len(data['execution_times']))
                    sorted_times = sorted(data['execution_times'])
                    p95_index = int(len(sorted_times) * 0.95)
                    p95_execution_time_ms = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
                
                # Convert operations dict to list
                operations_list = list(data['operations'].values())
                
                abilities_list.append({
                    'ability_id': data['ability_id'],
                    'ability_name': data['ability_name'],
                    'plugin': data['plugin'],
                    'tactics': sorted(list(data['tactics'])),
                    'techniques': sorted(list(data['techniques'])),
                    'total_executions': data['total_executions'],
                    'success_count': data['success_count'],
                    'failure_count': data['failure_count'],
                    'timeout_count': data['timeout_count'],
                    'running_count': data['running_count'],
                    'success_rate': round(success_rate, 2),
                    'avg_execution_time_ms': avg_execution_time_ms,
                    'p95_execution_time_ms': p95_execution_time_ms,
                    'operations': operations_list,
                    'recent_failures': data['recent_failures']
                })
            
            # Sort by total_executions descending, then by success_rate ascending
            abilities_list.sort(key=lambda x: (-x['total_executions'], x['success_rate']))
            
            # Apply limit
            abilities_list = abilities_list[:limit]
            
            # Calculate global stats
            unique_abilities = len(abilities_list)
            total_executions = sum(a['total_executions'] for a in abilities_list)
            success_total = sum(a['success_count'] for a in abilities_list)
            failed_total = sum(a['failure_count'] for a in abilities_list)
            timeout_total = sum(a['timeout_count'] for a in abilities_list)
            running_total = sum(a['running_count'] for a in abilities_list)
            
            # Build response
            response = {
                'generated_at': now.isoformat(),
                'window': {
                    'from': window_from.isoformat(),
                    'to': window_to.isoformat(),
                    'since_hours': since_hours
                },
                'filters': {
                    'operation_id': operation_id_filter,
                    'agent_paw': agent_paw_filter,
                    'group': group_filter,
                    'min_executions': min_executions
                },
                'stats': {
                    'unique_abilities': unique_abilities,
                    'total_executions': total_executions,
                    'success': success_total,
                    'failed': failed_total,
                    'timeout': timeout_total,
                    'running': running_total
                },
                'abilities': abilities_list
            }
            
            return web.json_response(response)
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid query parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    async def merlino_analytics_operations_health_matrix(self, request: web.Request):
        """
        Merlino Analytics - Operations Health Matrix
        
        Provides a complete matrix (rows/columns/cells) with operation health metrics,
        already classified and render-ready for the frontend.
        
        Query params:
        - from (ISO-8601): start of time window (default: now - 7d)
        - to (ISO-8601): end of time window (default: now)
        - groupBy (str): operation|operation_agent|operation_group (default: operation)
        - scope (str): all|picked (default: all)
        - include (CSV str): cells,operationSummaries,topIssues (default: cells,operationSummaries)
        - limit (int): max rows (default: 200)
        - minSamples (int): min executions to include (default: 1)
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict
            import base64
            import json as json_lib
            
            # Parse query parameters
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            group_by = params.get('groupBy', 'operation')
            scope = params.get('scope', 'all')
            include_str = params.get('include', 'cells,operationSummaries')
            limit = int(params.get('limit', 200))
            min_samples = int(params.get('minSamples', 1))
            
            # Parse include flags
            include_parts = [p.strip() for p in include_str.split(',')]
            include_cells = 'cells' in include_parts
            include_summaries = 'operationSummaries' in include_parts
            include_top_issues = 'topIssues' in include_parts
            
            # Determine time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Thresholds (configurable)
            thresholds = {
                'stale_minutes': 30,
                'warn_error_rate': 0.05,
                'bad_error_rate': 0.2,
                'warn_timeout_rate': 0.05,
                'bad_timeout_rate': 0.2,
                'min_samples': min_samples
            }
            
            # Get all operations and agents
            operations = list(self._api_manager.find_objects('operations'))
            agents = list(self._api_manager.find_objects('agents'))
            
            # Build agent lookup
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Data structures
            rows = []
            cells = []
            operation_summaries = []
            
            # Define columns (fixed structure)
            columns = [
                {'column_id': 'health_score', 'label': 'Health', 'kind': 'score', 'description': '0..100 score'},
                {'column_id': 'success_rate', 'label': 'Success Rate', 'kind': 'score'},
                {'column_id': 'error_rate', 'label': 'Error Rate', 'kind': 'score'},
                {'column_id': 'timeout_rate', 'label': 'Timeout Rate', 'kind': 'score'},
                {'column_id': 'last_event_at', 'label': 'Last Event', 'kind': 'time'},
                {'column_id': 'freshness_minutes', 'label': 'Freshness (min)', 'kind': 'count'}
            ]
            
            # Process operations
            for op in operations[:limit]:
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                # Aggregate data based on groupBy
                if group_by == 'operation':
                    # One row per operation
                    row_data = self._compute_operation_health_row(
                        op, agent_lookup, thresholds, now, window_from, window_to, group_by
                    )
                    if row_data and row_data['counts']['total'] >= min_samples:
                        rows.append(row_data['row'])
                        if include_cells:
                            cells.extend(row_data['cells'])
                        if include_summaries:
                            operation_summaries.append(row_data['summary'])
                
                elif group_by in ['operation_agent', 'operation_group']:
                    # Group by agent or agent_group
                    agent_groups = defaultdict(list)
                    for link in op.chain:
                        link_paw = getattr(link, 'paw', None)
                        if group_by == 'operation_agent':
                            key = link_paw or 'unknown'
                        else:  # operation_group
                            agent = agent_lookup.get(link_paw)
                            key = getattr(agent, 'group', 'unknown') if agent else 'unknown'
                        agent_groups[key].append(link)
                    
                    for group_key, links in agent_groups.items():
                        row_data = self._compute_operation_health_row_grouped(
                            op, group_key, links, agent_lookup, thresholds, now, window_from, window_to, group_by
                        )
                        if row_data and row_data['counts']['total'] >= min_samples:
                            rows.append(row_data['row'])
                            if include_cells:
                                cells.extend(row_data['cells'])
                            if include_summaries:
                                operation_summaries.append(row_data['summary'])
            
            # Build response
            response = {
                'version': '1.0',
                'generated_at': now.isoformat(),
                'time_window': {
                    'from': window_from.isoformat(),
                    'to': window_to.isoformat()
                },
                'groupBy': group_by,
                'thresholds': thresholds,
                'rows': rows if include_cells else [],
                'columns': columns if include_cells else [],
                'cells': cells if include_cells else [],
                'operationSummaries': operation_summaries if include_summaries else []
            }
            
            if include_top_issues:
                response['topIssues'] = []
            
            return web.json_response(response)
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid query parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    def _compute_operation_health_row(self, op, agent_lookup, thresholds, now, window_from, window_to, group_by):
        """Compute health metrics for a single operation row"""
        from datetime import datetime, timezone
        
        # Initialize counters
        counts = {'success': 0, 'fail': 0, 'timeout': 0, 'pending': 0, 'total': 0}
        last_event_at = None
        agent_paws = set()
        
        # Process links
        for link in op.chain:
            link_status = getattr(link, 'status', -1)
            link_paw = getattr(link, 'paw', None)
            
            if link_paw:
                agent_paws.add(link_paw)
            
            # Normalize status
            if link_status == 0:
                counts['success'] += 1
            elif link_status == 1:
                counts['fail'] += 1
            elif link_status == 124:
                counts['timeout'] += 1
            elif link_status == -1:
                counts['pending'] += 1
            else:
                counts['pending'] += 1
            
            counts['total'] += 1
            
            # Track last event
            link_finish = getattr(link, 'finish', None)
            if link_finish:
                try:
                    if isinstance(link_finish, str):
                        link_finish = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                    if not last_event_at or link_finish > last_event_at:
                        last_event_at = link_finish
                except:
                    pass
        
        # Calculate rates
        denominator = counts['success'] + counts['fail'] + counts['timeout']
        if denominator > 0:
            success_rate = counts['success'] / denominator
            error_rate = counts['fail'] / denominator
            timeout_rate = counts['timeout'] / denominator
        else:
            success_rate = None
            error_rate = None
            timeout_rate = None
        
        # Calculate freshness
        freshness_minutes = None
        stale = False
        if last_event_at:
            freshness_minutes = int((now - last_event_at).total_seconds() / 60)
            stale = freshness_minutes > thresholds['stale_minutes']
        
        # Calculate health score and severity
        if counts['total'] < thresholds['min_samples']:
            severity = 'nodata'
            health_score = None
            reasons = ['insufficient data']
        else:
            health_score = 100.0
            reasons = []
            
            # Apply penalties
            if error_rate is not None:
                penalty = error_rate * 100 * 1.0
                health_score -= penalty
                if error_rate >= thresholds['bad_error_rate']:
                    reasons.append(f'error_rate={error_rate:.2f}')
                elif error_rate >= thresholds['warn_error_rate']:
                    reasons.append(f'error_rate={error_rate:.2f}')
            
            if timeout_rate is not None:
                penalty = timeout_rate * 100 * 0.7
                health_score -= penalty
                if timeout_rate >= thresholds['bad_timeout_rate']:
                    reasons.append(f'timeout_rate={timeout_rate:.2f}')
                elif timeout_rate >= thresholds['warn_timeout_rate']:
                    reasons.append(f'timeout_rate={timeout_rate:.2f}')
            
            if stale:
                health_score -= 20
                reasons.append('stale')
            
            health_score = max(0, min(100, health_score))
            
            # Determine severity
            if error_rate is not None and error_rate >= thresholds['bad_error_rate']:
                severity = 'bad'
            elif timeout_rate is not None and timeout_rate >= thresholds['bad_timeout_rate']:
                severity = 'bad'
            elif stale:
                severity = 'bad'
            elif error_rate is not None and error_rate >= thresholds['warn_error_rate']:
                severity = 'warn'
            elif timeout_rate is not None and timeout_rate >= thresholds['warn_timeout_rate']:
                severity = 'warn'
            else:
                severity = 'good'
        
        # Build row
        row_id = f"op:{op.id}"
        row = {
            'row_id': row_id,
            'operation_id': op.id,
            'operation_name': op.name,
            'agent_paw': None,
            'agent_host': None,
            'agent_group': None,
            'last_seen': last_event_at.isoformat() if last_event_at else None
        }
        
        # Build cells
        cells_data = [
            {
                'row_id': row_id,
                'column_id': 'health_score',
                'value': int(health_score) if health_score is not None else None,
                'severity': severity,
                'details': {
                    'sample_size': counts['total'],
                    'success': counts['success'],
                    'fail': counts['fail'],
                    'timeout': counts['timeout'],
                    'pending': counts['pending'],
                    'success_rate': success_rate,
                    'error_rate': error_rate,
                    'timeout_rate': timeout_rate,
                    'last_event_at': last_event_at.isoformat() if last_event_at else None,
                    'stale': stale,
                    'top_reasons': reasons
                }
            },
            {
                'row_id': row_id,
                'column_id': 'success_rate',
                'value': round(success_rate * 100, 1) if success_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'error_rate',
                'value': round(error_rate * 100, 1) if error_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'timeout_rate',
                'value': round(timeout_rate * 100, 1) if timeout_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'last_event_at',
                'value': last_event_at.isoformat() if last_event_at else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'freshness_minutes',
                'value': freshness_minutes,
                'severity': severity
            }
        ]
        
        # Build summary
        summary = {
            'operation_id': op.id,
            'operation_name': op.name,
            'state': op.state,
            'group': getattr(op, 'group', ''),
            'agent_count': len(agent_paws),
            'counts': counts,
            'rates': {
                'success_rate': success_rate,
                'error_rate': error_rate,
                'timeout_rate': timeout_rate
            },
            'last_event_at': last_event_at.isoformat() if last_event_at else None,
            'freshness_minutes': freshness_minutes,
            'health': {
                'severity': severity,
                'score': int(health_score) if health_score is not None else None,
                'reasons': reasons
            }
        }
        
        return {
            'row': row,
            'cells': cells_data,
            'summary': summary,
            'counts': counts
        }
    
    def _compute_operation_health_row_grouped(self, op, group_key, links, agent_lookup, thresholds, now, window_from, window_to, group_by):
        """Compute health metrics for a grouped row (by agent or group)"""
        from datetime import datetime, timezone
        
        # Initialize counters
        counts = {'success': 0, 'fail': 0, 'timeout': 0, 'pending': 0, 'total': 0}
        last_event_at = None
        
        # Process links
        for link in links:
            link_status = getattr(link, 'status', -1)
            
            # Normalize status
            if link_status == 0:
                counts['success'] += 1
            elif link_status == 1:
                counts['fail'] += 1
            elif link_status == 124:
                counts['timeout'] += 1
            elif link_status == -1:
                counts['pending'] += 1
            else:
                counts['pending'] += 1
            
            counts['total'] += 1
            
            # Track last event
            link_finish = getattr(link, 'finish', None)
            if link_finish:
                try:
                    if isinstance(link_finish, str):
                        link_finish = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                    if not last_event_at or link_finish > last_event_at:
                        last_event_at = link_finish
                except:
                    pass
        
        # Calculate rates (same logic as _compute_operation_health_row)
        denominator = counts['success'] + counts['fail'] + counts['timeout']
        if denominator > 0:
            success_rate = counts['success'] / denominator
            error_rate = counts['fail'] / denominator
            timeout_rate = counts['timeout'] / denominator
        else:
            success_rate = None
            error_rate = None
            timeout_rate = None
        
        # Calculate freshness
        freshness_minutes = None
        stale = False
        if last_event_at:
            freshness_minutes = int((now - last_event_at).total_seconds() / 60)
            stale = freshness_minutes > thresholds['stale_minutes']
        
        # Calculate health score and severity (same logic)
        if counts['total'] < thresholds['min_samples']:
            severity = 'nodata'
            health_score = None
            reasons = ['insufficient data']
        else:
            health_score = 100.0
            reasons = []
            
            if error_rate is not None:
                penalty = error_rate * 100 * 1.0
                health_score -= penalty
                if error_rate >= thresholds['bad_error_rate']:
                    reasons.append(f'error_rate={error_rate:.2f}')
                elif error_rate >= thresholds['warn_error_rate']:
                    reasons.append(f'error_rate={error_rate:.2f}')
            
            if timeout_rate is not None:
                penalty = timeout_rate * 100 * 0.7
                health_score -= penalty
                if timeout_rate >= thresholds['bad_timeout_rate']:
                    reasons.append(f'timeout_rate={timeout_rate:.2f}')
                elif timeout_rate >= thresholds['warn_timeout_rate']:
                    reasons.append(f'timeout_rate={timeout_rate:.2f}')
            
            if stale:
                health_score -= 20
                reasons.append('stale')
            
            health_score = max(0, min(100, health_score))
            
            # Determine severity
            if error_rate is not None and error_rate >= thresholds['bad_error_rate']:
                severity = 'bad'
            elif timeout_rate is not None and timeout_rate >= thresholds['bad_timeout_rate']:
                severity = 'bad'
            elif stale:
                severity = 'bad'
            elif error_rate is not None and error_rate >= thresholds['warn_error_rate']:
                severity = 'warn'
            elif timeout_rate is not None and timeout_rate >= thresholds['warn_timeout_rate']:
                severity = 'warn'
            else:
                severity = 'good'
        
        # Build row
        row_id = f"op:{op.id}:{group_by}:{group_key}"
        row = {
            'row_id': row_id,
            'operation_id': op.id,
            'operation_name': op.name,
            'agent_paw': group_key if group_by == 'operation_agent' else None,
            'agent_host': None,
            'agent_group': group_key if group_by == 'operation_group' else None,
            'last_seen': last_event_at.isoformat() if last_event_at else None
        }
        
        # Build cells (same structure as ungrouped)
        cells_data = [
            {
                'row_id': row_id,
                'column_id': 'health_score',
                'value': int(health_score) if health_score is not None else None,
                'severity': severity,
                'details': {
                    'sample_size': counts['total'],
                    'success': counts['success'],
                    'fail': counts['fail'],
                    'timeout': counts['timeout'],
                    'pending': counts['pending'],
                    'success_rate': success_rate,
                    'error_rate': error_rate,
                    'timeout_rate': timeout_rate,
                    'last_event_at': last_event_at.isoformat() if last_event_at else None,
                    'stale': stale,
                    'top_reasons': reasons
                }
            },
            {
                'row_id': row_id,
                'column_id': 'success_rate',
                'value': round(success_rate * 100, 1) if success_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'error_rate',
                'value': round(error_rate * 100, 1) if error_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'timeout_rate',
                'value': round(timeout_rate * 100, 1) if timeout_rate is not None else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'last_event_at',
                'value': last_event_at.isoformat() if last_event_at else None,
                'severity': severity
            },
            {
                'row_id': row_id,
                'column_id': 'freshness_minutes',
                'value': freshness_minutes,
                'severity': severity
            }
        ]
        
        # Build summary
        summary = {
            'operation_id': op.id,
            'operation_name': op.name,
            'state': op.state,
            'group': group_key if group_by == 'operation_group' else getattr(op, 'group', ''),
            'agent_count': 1 if group_by == 'operation_agent' else None,
            'counts': counts,
            'rates': {
                'success_rate': success_rate,
                'error_rate': error_rate,
                'timeout_rate': timeout_rate
            },
            'last_event_at': last_event_at.isoformat() if last_event_at else None,
            'freshness_minutes': freshness_minutes,
            'health': {
                'severity': severity,
                'score': int(health_score) if health_score is not None else None,
                'reasons': reasons
            }
        }
        
        return {
            'row': row,
            'cells': cells_data,
            'summary': summary,
            'counts': counts
        }
    
    async def merlino_analytics_operation_health_details(self, request: web.Request):
        """
        Merlino Analytics - Operation Health Details (Drilldown)
        
        Returns detailed items for a specific operation with optional decoded output and command.
        
        Path params:
        - operation_id (str): UUID of the operation
        
        Query params:
        - from (ISO-8601): start of time window
        - to (ISO-8601): end of time window
        - limit (int): max items (default 500)
        - offset (int): pagination offset (default 0)
        - status (CSV str): filter by status (success,fail,timeout,pending,unknown)
        - agent_paw (str): filter by agent PAW
        - includeOutput (bool): include output field (default false)
        - outputFormat (str): decoded|raw (default decoded)
        - includeCommand (bool): include command field (default false)
        - commandFormat (str): decoded|raw (default decoded)
        """
        try:
            from datetime import datetime, timezone, timedelta
            import base64
            import json as json_lib
            
            # Get operation_id from path
            operation_id = request.match_info['operation_id']
            
            # Parse query parameters
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            limit = int(params.get('limit', 500))
            offset = int(params.get('offset', 0))
            status_filter = params.get('status', '').split(',') if params.get('status') else []
            agent_paw_filter = params.get('agent_paw')
            include_output = params.get('includeOutput', 'false').lower() == 'true'
            output_format = params.get('outputFormat', 'decoded')
            include_command = params.get('includeCommand', 'false').lower() == 'true'
            command_format = params.get('commandFormat', 'decoded')
            
            # Determine time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Find operation
            all_operations = list(self._api_manager.find_objects(self.ram_key))
            operations = [op for op in all_operations if op.id == operation_id]
            if not operations:
                return web.json_response({'error': f'Operation {operation_id} not found'}, status=404)
            
            op = operations[0]
            
            # Initialize counters and items
            counts = {'success': 0, 'fail': 0, 'timeout': 0, 'pending': 0, 'total': 0}
            last_event_at = None
            items = []
            
            # Get agents for lookup
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Process links
            if hasattr(op, 'chain') and op.chain:
                all_links = []
                
                for link in op.chain:
                    link_status = getattr(link, 'status', -1)
                    link_paw = getattr(link, 'paw', None)
                    
                    # Normalize status to string
                    if link_status == 0:
                        status_str = 'success'
                        counts['success'] += 1
                    elif link_status == 1:
                        status_str = 'fail'
                        counts['fail'] += 1
                    elif link_status == 124:
                        status_str = 'timeout'
                        counts['timeout'] += 1
                    elif link_status == -1:
                        status_str = 'pending'
                        counts['pending'] += 1
                    else:
                        status_str = 'unknown'
                        counts['pending'] += 1
                    
                    counts['total'] += 1
                    
                    # Apply filters
                    if status_filter and status_str not in status_filter:
                        continue
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    # Track last event
                    link_finish = getattr(link, 'finish', None)
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                link_finish = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            if not last_event_at or link_finish > last_event_at:
                                last_event_at = link_finish
                        except:
                            pass
                    
                    # Build item
                    link_ability = getattr(link, 'ability', None)
                    agent = agent_lookup.get(link_paw)
                    
                    # Extract executor name if it's an Executor object
                    executor_obj = getattr(link, 'executor', None)
                    executor_name = getattr(executor_obj, 'name', None) if executor_obj else None
                    
                    item = {
                        'item_id': f"link:{getattr(link, 'id', 'unknown')}",
                        'occurred_at': link_finish if link_finish else None,
                        'status': status_str,
                        'ability_id': getattr(link_ability, 'ability_id', None) if link_ability else None,
                        'ability_name': getattr(link_ability, 'name', None) if link_ability else None,
                        'technique_id': getattr(link_ability, 'technique_id', None) if link_ability else None,
                        'tactic': getattr(link_ability, 'tactic', None) if link_ability else None,
                        'agent_paw': link_paw,
                        'agent_host': getattr(link, 'host', None),
                        'agent_group': getattr(agent, 'group', None) if agent else None,
                        'executor': executor_name,
                        'platform': getattr(link, 'platform', None),
                        'source': 'caldera'
                    }
                    
                    # Add command if requested
                    if include_command:
                        link_command_raw = getattr(link, 'plaintext_command', '') or getattr(link, 'command', '')
                        if link_command_raw:
                            try:
                                # Check if already base64
                                base64.b64decode(link_command_raw, validate=True)
                                is_base64 = True
                            except:
                                is_base64 = False
                            
                            if command_format == 'decoded':
                                if is_base64:
                                    decoded_cmd = base64.b64decode(link_command_raw).decode('utf-8', errors='ignore')
                                    item['command'] = {'encoding': 'plain', 'value': decoded_cmd}
                                else:
                                    item['command'] = {'encoding': 'plain', 'value': link_command_raw}
                            else:  # raw
                                if is_base64:
                                    item['command'] = {'encoding': 'base64', 'value': link_command_raw}
                                else:
                                    encoded_cmd = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                                    item['command'] = {'encoding': 'base64', 'value': encoded_cmd}
                    
                    # Add output if requested
                    if include_output:
                        try:
                            link_id = getattr(link, 'id', '')
                            if link_id:
                                file_svc = self._api_manager._file_svc
                                output_content = file_svc.read_result_file(link_id)
                                
                                if output_content:
                                    if output_format == 'decoded':
                                        # Decode base64 and parse JSON if possible
                                        try:
                                            decoded_output = base64.b64decode(output_content).decode('utf-8')
                                            output_json = json_lib.loads(decoded_output)
                                            item['output'] = {
                                                'encoding': 'json-base64',
                                                'value': output_content,
                                                'parsed': output_json
                                            }
                                            
                                            # Add error hint
                                            if output_json.get('exit_code', 0) != 0:
                                                item['error_hint'] = f"exit_code={output_json['exit_code']}"
                                        except:
                                            # Not JSON, just decoded text
                                            item['output'] = {
                                                'encoding': 'plain',
                                                'value': decoded_output
                                            }
                                    else:  # raw
                                        item['output'] = {
                                            'encoding': 'base64',
                                            'value': output_content
                                        }
                        except FileNotFoundError:
                            pass
                        except Exception as e:
                            self.log.warning(f'Failed to read output for link {link_id}: {e}')
                    
                    all_links.append(item)
                
                # Apply pagination
                total_filtered = len(all_links)
                items = all_links[offset:offset + limit]
            else:
                total_filtered = 0
            
            # Calculate rates
            denominator = counts['success'] + counts['fail'] + counts['timeout']
            if denominator > 0:
                success_rate = counts['success'] / denominator
                error_rate = counts['fail'] / denominator
                timeout_rate = counts['timeout'] / denominator
            else:
                success_rate = None
                error_rate = None
                timeout_rate = None
            
            # Build response
            response = {
                'operation_id': op.id,
                'operation_name': op.name,
                'time_window': {
                    'from': window_from.isoformat(),
                    'to': window_to.isoformat()
                },
                'summary': {
                    'counts': counts,
                    'rates': {
                        'success_rate': success_rate,
                        'error_rate': error_rate,
                        'timeout_rate': timeout_rate
                    },
                    'last_event_at': last_event_at.isoformat() if last_event_at else None
                },
                'items': items,
                'paging': {
                    'limit': limit,
                    'offset': offset,
                    'total': total_filtered
                }
            }
            
            return web.json_response(response)
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    # ============================================================================
    # ERROR ANALYTICS API - Helper Methods
    # ============================================================================
    
    def _normalize_error_reason(self, link, output_content=None):
        """
        Normalize error reasons for clustering and analytics.
        
        Returns: tuple (reason: str, error_hint: str | None)
        """
        import re
        
        # Default
        reason = 'unknown'
        hint = None
        
        # Check status first
        link_status = getattr(link, 'status', -1)
        
        if link_status == 124:
            return ('timeout', 'Execution timed out - consider increasing timeout or optimizing command')
        
        if link_status == -1:
            return ('pending', None)
        
        if link_status == 0:
            return ('success', None)
        
        # For failures (status=1), analyze output
        if output_content:
            try:
                import base64
                import json as json_lib
                
                decoded = base64.b64decode(output_content).decode('utf-8', errors='ignore')
                output_json = json_lib.loads(decoded)
                
                stdout = output_json.get('stdout', '').lower()
                stderr = output_json.get('stderr', '').lower()
                combined = stdout + stderr
                
                # Access denied
                if any(x in combined for x in ['access is denied', 'access denied', 'permission denied', 'unauthorized', 'sedebugprivilege']):
                    reason = 'access_denied'
                    hint = 'Run as elevated or enable required privileges'
                
                # Command not found
                elif any(x in combined for x in ['not recognized as', 'command not found', 'is not recognized', 'cmdlet does not exist']):
                    reason = 'command_not_found'
                    hint = 'Verify command exists or install required dependencies'
                
                # File not found
                elif any(x in combined for x in ['file not found', 'cannot find', 'no such file', 'path not found']):
                    reason = 'file_not_found'
                    hint = 'Check file path and verify file exists'
                
                # Network errors
                elif any(x in combined for x in ['network', 'connection', 'unreachable', 'timeout', 'timed out']):
                    reason = 'network_unreachable'
                    hint = 'Check network connectivity and firewall rules'
                
                # AMSI/EDR blocks
                elif any(x in combined for x in ['amsi', 'antimalware', 'windows defender', 'blocked', 'quarantine']):
                    reason = 'amsi_block'
                    hint = 'Content blocked by endpoint protection - adjust detection rules'
                
                # Invalid arguments
                elif any(x in combined for x in ['invalid argument', 'invalid parameter', 'syntax error', 'unexpected token']):
                    reason = 'invalid_argument'
                    hint = 'Check command syntax and parameter values'
                
                # Dependency missing
                elif any(x in combined for x in ['module', 'assembly', 'dll not found', 'import error']):
                    reason = 'dependency_missing'
                    hint = 'Install required modules or dependencies'
                
                # Parser error (server-side)
                elif 'parser' in combined or 'decode' in combined:
                    reason = 'parser_error'
                    hint = 'Server failed to parse output - check output format'
                    
            except:
                pass
        
        return (reason, hint)
    
    # ============================================================================
    # ERROR ANALYTICS API - Endpoints
    # ============================================================================
    
    async def merlino_error_analytics_overview(self, request: web.Request):
        """
        Error Analytics - Overview with KPIs and trend.
        
        GET /api/v2/merlino/analytics/error-analytics/overview
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict, Counter
            
            # Parse query parameters
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            group_by = params.get('groupBy', 'day')
            operation_id_filter = params.get('operation_id')
            agent_paw_filter = params.get('agent_paw')
            group_filter = params.get('group')
            
            # Determine time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get operations and agents
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Counters
            totals = {'events': 0, 'errors': 0, 'timeouts': 0, 'success': 0, 'unknown': 0}
            reason_counter = Counter()
            trend_buckets = defaultdict(lambda: {'events': 0, 'errors': 0, 'timeouts': 0, 'success': 0})
            
            # Process operations
            for op in operations:
                if operation_id_filter and op.id != operation_id_filter:
                    continue
                
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    
                    # Apply filters
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    if group_filter:
                        agent = agent_lookup.get(link_paw)
                        agent_group = getattr(agent, 'group', None) if agent else None
                        if agent_group != group_filter:
                            continue
                    
                    # Check timestamp
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                            
                            # Bucket key
                            if group_by == 'hour':
                                bucket_key = finish_dt.strftime('%Y-%m-%dT%H:00:00Z')
                            elif group_by == 'week':
                                bucket_key = finish_dt.strftime('%Y-W%U')
                            else:
                                bucket_key = finish_dt.strftime('%Y-%m-%d')
                        except:
                            continue
                    else:
                        continue
                    
                    # Count
                    totals['events'] += 1
                    trend_buckets[bucket_key]['events'] += 1
                    
                    if link_status == 0:
                        totals['success'] += 1
                        trend_buckets[bucket_key]['success'] += 1
                    elif link_status == 1:
                        totals['errors'] += 1
                        trend_buckets[bucket_key]['errors'] += 1
                        try:
                            link_id = getattr(link, 'id', '')
                            file_svc = self._api_manager._file_svc
                            output_content = file_svc.read_result_file(link_id)
                            reason, _ = self._normalize_error_reason(link, output_content)
                            reason_counter[reason] += 1
                        except:
                            reason_counter['unknown'] += 1
                    elif link_status == 124:
                        totals['timeouts'] += 1
                        trend_buckets[bucket_key]['timeouts'] += 1
                        reason_counter['timeout'] += 1
                    else:
                        totals['unknown'] += 1
            
            # Calculate rates
            denominator = totals['events'] or 1
            rates = {
                'error_rate': totals['errors'] / denominator,
                'timeout_rate': totals['timeouts'] / denominator,
                'success_rate': totals['success'] / denominator
            }
            
            # Build trend
            trend = [
                {'bucket': bucket, 'events': data['events'], 'errors': data['errors'], 
                 'timeouts': data['timeouts'], 'success': data['success']}
                for bucket, data in sorted(trend_buckets.items())
            ]
            
            # Top reasons
            top_reasons = [{'reason': reason, 'count': count} for reason, count in reason_counter.most_common(10)]
            
            return web.json_response({
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'totals': totals,
                'rates': rates,
                'trend': trend,
                'top_reasons': top_reasons
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_breakdown(self, request: web.Request):
        """
        Error Analytics - Breakdown by dimension.
        
        GET /api/v2/merlino/analytics/error-analytics/breakdown
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict, Counter
            
            params = request.rel_url.query
            dimension = params.get('dimension')
            if not dimension:
                return web.json_response({'error': 'Missing required parameter: dimension'}, status=422)
            
            valid_dimensions = ['status', 'operation', 'agent', 'group', 'ability', 'executor', 'platform', 'plugin', 'reason']
            if dimension not in valid_dimensions:
                return web.json_response({'error': f'Invalid dimension. Must be one of: {", ".join(valid_dimensions)}'}, status=400)
            
            # Parse other params
            from_str = params.get('from')
            to_str = params.get('to')
            metric = params.get('metric', 'count')
            operation_id_filter = params.get('operation_id')
            agent_paw_filter = params.get('agent_paw')
            group_filter = params.get('group')
            ability_id_filter = params.get('ability_id')
            status_filter = params.get('status', '').split(',') if params.get('status') else []
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get data
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Aggregate by dimension
            dimension_counter = Counter()
            total_events = 0
            
            for op in operations:
                if operation_id_filter and op.id != operation_id_filter:
                    continue
                
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    
                    # Apply filters
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    if group_filter:
                        agent = agent_lookup.get(link_paw)
                        agent_group = getattr(agent, 'group', None) if agent else None
                        if agent_group != group_filter:
                            continue
                    
                    if ability_id_filter and (not link_ability or getattr(link_ability, 'ability_id', None) != ability_id_filter):
                        continue
                    
                    # Status filter
                    if status_filter:
                        status_str = 'success' if link_status == 0 else 'fail' if link_status == 1 else 'timeout' if link_status == 124 else 'pending' if link_status == -1 else 'unknown'
                        if status_str not in status_filter:
                            continue
                    
                    # Time window check
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                        except:
                            continue
                    else:
                        continue
                    
                    total_events += 1
                    
                    # Extract dimension value
                    if dimension == 'status':
                        key = 'success' if link_status == 0 else 'fail' if link_status == 1 else 'timeout' if link_status == 124 else 'pending' if link_status == -1 else 'unknown'
                    elif dimension == 'operation':
                        key = op.name
                    elif dimension == 'agent':
                        key = link_paw or 'unknown'
                    elif dimension == 'group':
                        agent = agent_lookup.get(link_paw)
                        key = getattr(agent, 'group', 'unknown') if agent else 'unknown'
                    elif dimension == 'ability':
                        key = getattr(link_ability, 'name', 'unknown') if link_ability else 'unknown'
                    elif dimension == 'executor':
                        executor_obj = getattr(link, 'executor', None)
                        key = getattr(executor_obj, 'name', 'unknown') if executor_obj else 'unknown'
                    elif dimension == 'platform':
                        key = getattr(link, 'platform', 'unknown') or 'unknown'
                    elif dimension == 'plugin':
                        key = getattr(link_ability, 'plugin', 'unknown') if link_ability and hasattr(link_ability, 'plugin') else 'unknown'
                    elif dimension == 'reason':
                        try:
                            link_id = getattr(link, 'id', '')
                            file_svc = self._api_manager._file_svc
                            output_content = file_svc.read_result_file(link_id)
                            key, _ = self._normalize_error_reason(link, output_content)
                        except:
                            key = 'unknown'
                    else:
                        key = 'unknown'
                    
                    dimension_counter[key] += 1
            
            # Build items
            items = []
            for key, count in dimension_counter.most_common():
                rate = count / total_events if total_events > 0 else 0
                items.append({
                    'key': key,
                    'label': key.replace('_', ' ').title(),
                    'count': count,
                    'rate': rate
                })
            
            return web.json_response({
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'dimension': dimension,
                'metric': metric,
                'items': items
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_top_offenders(self, request: web.Request):
        """
        Error Analytics - Top Offenders (entities with most errors).
        
        GET /api/v2/merlino/analytics/error-analytics/top-offenders
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict, Counter
            
            params = request.rel_url.query
            entity_type = params.get('entity')
            if not entity_type:
                return web.json_response({'error': 'Missing required parameter: entity'}, status=422)
            
            valid_entities = ['operation', 'agent', 'ability', 'group']
            if entity_type not in valid_entities:
                return web.json_response({'error': f'Invalid entity. Must be one of: {", ".join(valid_entities)}'}, status=400)
            
            # Parse params
            from_str = params.get('from')
            to_str = params.get('to')
            metric = params.get('metric', 'error_rate')
            limit = int(params.get('limit', 50))
            min_samples = int(params.get('minSamples', 25))
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get data
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Aggregate by entity
            entity_stats = defaultdict(lambda: {'success': 0, 'fail': 0, 'timeout': 0, 'pending': 0, 'total': 0, 'reasons': Counter(), 'name': ''})
            
            for op in operations:
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    
                    # Time window check
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                        except:
                            continue
                    else:
                        continue
                    
                    # Determine entity key
                    if entity_type == 'operation':
                        entity_key = op.id
                        entity_name = op.name
                    elif entity_type == 'agent':
                        entity_key = link_paw or 'unknown'
                        agent = agent_lookup.get(link_paw)
                        entity_name = getattr(agent, 'host', link_paw) if agent else link_paw
                    elif entity_type == 'ability':
                        entity_key = getattr(link_ability, 'ability_id', 'unknown') if link_ability else 'unknown'
                        entity_name = getattr(link_ability, 'name', entity_key) if link_ability else entity_key
                    elif entity_type == 'group':
                        agent = agent_lookup.get(link_paw)
                        entity_key = getattr(agent, 'group', 'unknown') if agent else 'unknown'
                        entity_name = entity_key
                    else:
                        entity_key = 'unknown'
                        entity_name = 'unknown'
                    
                    # Update stats
                    entity_stats[entity_key]['name'] = entity_name
                    entity_stats[entity_key]['total'] += 1
                    
                    if link_status == 0:
                        entity_stats[entity_key]['success'] += 1
                    elif link_status == 1:
                        entity_stats[entity_key]['fail'] += 1
                        try:
                            link_id = getattr(link, 'id', '')
                            file_svc = self._api_manager._file_svc
                            output_content = file_svc.read_result_file(link_id)
                            reason, _ = self._normalize_error_reason(link, output_content)
                            entity_stats[entity_key]['reasons'][reason] += 1
                        except:
                            entity_stats[entity_key]['reasons']['unknown'] += 1
                    elif link_status == 124:
                        entity_stats[entity_key]['timeout'] += 1
                        entity_stats[entity_key]['reasons']['timeout'] += 1
                    else:
                        entity_stats[entity_key]['pending'] += 1
            
            # Build items list
            items = []
            for entity_id, stats in entity_stats.items():
                if stats['total'] < min_samples:
                    continue
                
                denominator = stats['success'] + stats['fail'] + stats['timeout']
                if denominator > 0:
                    success_rate = stats['success'] / denominator
                    error_rate = stats['fail'] / denominator
                    timeout_rate = stats['timeout'] / denominator
                else:
                    success_rate = None
                    error_rate = None
                    timeout_rate = None
                
                # Determine severity
                if error_rate is not None and error_rate >= 0.2:
                    severity = 'bad'
                elif timeout_rate is not None and timeout_rate >= 0.2:
                    severity = 'bad'
                elif error_rate is not None and error_rate >= 0.05:
                    severity = 'warn'
                elif timeout_rate is not None and timeout_rate >= 0.05:
                    severity = 'warn'
                else:
                    severity = 'good'
                
                top_reasons = [r for r, _ in stats['reasons'].most_common(3)]
                
                items.append({
                    'entity_id': entity_id,
                    'entity_name': stats['name'],
                    'sample_size': stats['total'],
                    'counts': {
                        'success': stats['success'],
                        'fail': stats['fail'],
                        'timeout': stats['timeout'],
                        'pending': stats['pending'],
                        'total': stats['total']
                    },
                    'rates': {
                        'success_rate': success_rate,
                        'error_rate': error_rate,
                        'timeout_rate': timeout_rate
                    },
                    'severity': severity,
                    'top_reasons': top_reasons
                })
            
            # Sort by metric
            if metric == 'error_count':
                items.sort(key=lambda x: x['counts']['fail'], reverse=True)
            elif metric == 'timeout_count':
                items.sort(key=lambda x: x['counts']['timeout'], reverse=True)
            elif metric == 'error_rate':
                items.sort(key=lambda x: x['rates']['error_rate'] or 0, reverse=True)
            elif metric == 'combined_bad_rate':
                items.sort(key=lambda x: (x['rates']['error_rate'] or 0) + (x['rates']['timeout_rate'] or 0), reverse=True)
            
            items = items[:limit]
            
            return web.json_response({
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'entity': entity_type,
                'metric': metric,
                'items': items
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_events_search(self, request: web.Request):
        """
        Error Analytics - Events Search with filters.
        
        GET /api/v2/merlino/analytics/error-analytics/events/search
        """
        try:
            from datetime import datetime, timezone, timedelta
            import base64
            import json as json_lib
            
            params = request.rel_url.query
            
            # Parse params
            from_str = params.get('from')
            to_str = params.get('to')
            limit = int(params.get('limit', 250))
            offset = int(params.get('offset', 0))
            
            # Filters
            status_filter = params.get('status', '').split(',') if params.get('status') else []
            operation_id_filter = params.get('operation_id')
            agent_paw_filter = params.get('agent_paw')
            group_filter = params.get('group')
            ability_id_filter = params.get('ability_id')
            executor_filter = params.get('executor')
            platform_filter = params.get('platform')
            plugin_filter = params.get('plugin')
            reason_filter = params.get('reason')
            q_filter = params.get('q', '')[:200]  # Cap at 200 chars
            
            # Include flags
            include_command = params.get('includeCommand', 'false').lower() == 'true'
            include_output = params.get('includeOutput', 'false').lower() == 'true'
            command_format = params.get('commandFormat', 'decoded')
            output_format = params.get('outputFormat', 'decoded')
            
            # Validate limit
            if limit > 1000:
                return web.json_response({'error': 'limit cannot exceed 1000'}, status=400)
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get data
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Collect matching events
            all_events = []
            
            for op in operations:
                if operation_id_filter and op.id != operation_id_filter:
                    continue
                
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    link_id = getattr(link, 'id', '')
                    
                    # Status normalization
                    if link_status == 0:
                        status_str = 'success'
                    elif link_status == 1:
                        status_str = 'fail'
                    elif link_status == 124:
                        status_str = 'timeout'
                    elif link_status == -1:
                        status_str = 'pending'
                    else:
                        status_str = 'unknown'
                    
                    # Apply filters
                    if status_filter and status_str not in status_filter:
                        continue
                    
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    if group_filter:
                        agent = agent_lookup.get(link_paw)
                        agent_group = getattr(agent, 'group', None) if agent else None
                        if agent_group != group_filter:
                            continue
                    
                    if ability_id_filter and (not link_ability or getattr(link_ability, 'ability_id', None) != ability_id_filter):
                        continue
                    
                    if executor_filter:
                        executor_obj = getattr(link, 'executor', None)
                        executor_name = getattr(executor_obj, 'name', None) if executor_obj else None
                        if executor_name != executor_filter:
                            continue
                    
                    if platform_filter:
                        platform = getattr(link, 'platform', None)
                        if platform != platform_filter:
                            continue
                    
                    if plugin_filter and link_ability:
                        plugin = getattr(link_ability, 'plugin', None) if hasattr(link_ability, 'plugin') else None
                        if plugin != plugin_filter:
                            continue
                    
                    # Time window
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                        except:
                            continue
                    else:
                        continue
                    
                    # Get reason and hint
                    try:
                        file_svc = self._api_manager._file_svc
                        output_content = file_svc.read_result_file(link_id)
                        reason, hint = self._normalize_error_reason(link, output_content)
                    except:
                        reason = 'unknown'
                        hint = None
                        output_content = None
                    
                    # Reason filter
                    if reason_filter and reason != reason_filter:
                        continue
                    
                    # Free text search (q filter)
                    if q_filter:
                        search_text = ''
                        try:
                            link_command_raw = getattr(link, 'plaintext_command', '') or getattr(link, 'command', '')
                            search_text += link_command_raw.lower() + ' '
                            if output_content:
                                decoded_output = base64.b64decode(output_content).decode('utf-8', errors='ignore')
                                search_text += decoded_output.lower()
                        except:
                            pass
                        
                        if q_filter.lower() not in search_text:
                            continue
                    
                    # Build event item
                    agent = agent_lookup.get(link_paw)
                    executor_obj = getattr(link, 'executor', None)
                    executor_name = getattr(executor_obj, 'name', None) if executor_obj else None
                    
                    item = {
                        'item_id': f"link:{link_id}",
                        'occurred_at': link_finish if link_finish else None,
                        'status': status_str,
                        'reason': reason,
                        'severity': 'bad' if status_str in ['fail', 'timeout'] else 'good',
                        'operation_id': op.id,
                        'operation_name': op.name,
                        'ability_id': getattr(link_ability, 'ability_id', None) if link_ability else None,
                        'ability_name': getattr(link_ability, 'name', None) if link_ability else None,
                        'tactic': getattr(link_ability, 'tactic', None) if link_ability else None,
                        'technique_id': getattr(link_ability, 'technique_id', None) if link_ability else None,
                        'agent_paw': link_paw,
                        'agent_host': getattr(agent, 'host', None) if agent else None,
                        'agent_group': getattr(agent, 'group', None) if agent else None,
                        'executor': executor_name,
                        'platform': getattr(link, 'platform', None),
                        'plugin': getattr(link_ability, 'plugin', None) if link_ability and hasattr(link_ability, 'plugin') else None,
                        'error_hint': hint,
                        'source': 'caldera'
                    }
                    
                    # Add command if requested
                    if include_command:
                        link_command_raw = getattr(link, 'plaintext_command', '') or getattr(link, 'command', '')
                        if link_command_raw:
                            try:
                                base64.b64decode(link_command_raw, validate=True)
                                is_base64 = True
                            except:
                                is_base64 = False
                            
                            if command_format == 'decoded':
                                if is_base64:
                                    decoded_cmd = base64.b64decode(link_command_raw).decode('utf-8', errors='ignore')
                                    item['command'] = {'encoding': 'plain', 'value': decoded_cmd}
                                else:
                                    item['command'] = {'encoding': 'plain', 'value': link_command_raw}
                            else:
                                if is_base64:
                                    item['command'] = {'encoding': 'base64', 'value': link_command_raw}
                                else:
                                    encoded_cmd = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                                    item['command'] = {'encoding': 'base64', 'value': encoded_cmd}
                    
                    # Add output if requested
                    if include_output and output_content:
                        if output_format == 'decoded':
                            try:
                                decoded_output = base64.b64decode(output_content).decode('utf-8')
                                output_json = json_lib.loads(decoded_output)
                                item['output'] = {
                                    'encoding': 'json-base64',
                                    'value': output_content,
                                    'parsed': output_json
                                }
                            except:
                                item['output'] = {'encoding': 'plain', 'value': decoded_output}
                        else:
                            item['output'] = {'encoding': 'base64', 'value': output_content}
                    
                    all_events.append(item)
            
            # Sort by occurred_at descending
            all_events.sort(key=lambda x: x['occurred_at'] or '', reverse=True)
            
            # Paginate
            total_events = len(all_events)
            paginated_events = all_events[offset:offset + limit]
            
            return web.json_response({
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'paging': {'limit': limit, 'offset': offset, 'total': total_events},
                'items': paginated_events
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_operation_drilldown(self, request: web.Request):
        """
        Error Analytics - Operation Drilldown (shortcut endpoint).
        
        GET /api/v2/merlino/analytics/error-analytics/operation/{operation_id}
        """
        try:
            from datetime import datetime, timezone, timedelta
            import base64
            import json as json_lib
            
            # Get operation_id from path
            operation_id = request.match_info['operation_id']
            
            # Parse query parameters
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            limit = int(params.get('limit', 250))
            offset = int(params.get('offset', 0))
            status_filter = params.get('status', 'fail,timeout').split(',')  # Default to errors
            agent_paw_filter = params.get('agent_paw')
            
            # Include flags
            include_command = params.get('includeCommand', 'false').lower() == 'true'
            include_output = params.get('includeOutput', 'false').lower() == 'true'
            command_format = params.get('commandFormat', 'decoded')
            output_format = params.get('outputFormat', 'decoded')
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Find operation
            all_operations = list(self._api_manager.find_objects(self.ram_key))
            operations = [op for op in all_operations if op.id == operation_id]
            if not operations:
                return web.json_response({'error': f'Operation {operation_id} not found'}, status=404)
            
            op = operations[0]
            
            # Get agents
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Collect stats and items
            counts = {'success': 0, 'fail': 0, 'timeout': 0, 'pending': 0, 'total': 0}
            last_event_at = None
            all_items = []
            
            if hasattr(op, 'chain') and op.chain:
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    link_id = getattr(link, 'id', '')
                    
                    # Status normalization
                    if link_status == 0:
                        status_str = 'success'
                        counts['success'] += 1
                    elif link_status == 1:
                        status_str = 'fail'
                        counts['fail'] += 1
                    elif link_status == 124:
                        status_str = 'timeout'
                        counts['timeout'] += 1
                    elif link_status == -1:
                        status_str = 'pending'
                        counts['pending'] += 1
                    else:
                        status_str = 'unknown'
                    
                    counts['total'] += 1
                    
                    # Apply filters
                    if status_filter and status_str not in status_filter:
                        continue
                    
                    if agent_paw_filter and link_paw != agent_paw_filter:
                        continue
                    
                    # Time window
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                            
                            if not last_event_at or finish_dt > last_event_at:
                                last_event_at = finish_dt
                        except:
                            continue
                    else:
                        continue
                    
                    # Get reason and hint
                    try:
                        file_svc = self._api_manager._file_svc
                        output_content = file_svc.read_result_file(link_id)
                        reason, hint = self._normalize_error_reason(link, output_content)
                    except:
                        reason = 'unknown'
                        hint = None
                        output_content = None
                    
                    # Build item (same as events/search)
                    agent = agent_lookup.get(link_paw)
                    executor_obj = getattr(link, 'executor', None)
                    executor_name = getattr(executor_obj, 'name', None) if executor_obj else None
                    
                    item = {
                        'item_id': f"link:{link_id}",
                        'occurred_at': link_finish if link_finish else None,
                        'status': status_str,
                        'reason': reason,
                        'severity': 'bad' if status_str in ['fail', 'timeout'] else 'good',
                        'operation_id': op.id,
                        'operation_name': op.name,
                        'ability_id': getattr(link_ability, 'ability_id', None) if link_ability else None,
                        'ability_name': getattr(link_ability, 'name', None) if link_ability else None,
                        'tactic': getattr(link_ability, 'tactic', None) if link_ability else None,
                        'technique_id': getattr(link_ability, 'technique_id', None) if link_ability else None,
                        'agent_paw': link_paw,
                        'agent_host': getattr(agent, 'host', None) if agent else None,
                        'agent_group': getattr(agent, 'group', None) if agent else None,
                        'executor': executor_name,
                        'platform': getattr(link, 'platform', None),
                        'plugin': getattr(link_ability, 'plugin', None) if link_ability and hasattr(link_ability, 'plugin') else None,
                        'error_hint': hint,
                        'source': 'caldera'
                    }
                    
                    # Add command if requested
                    if include_command:
                        link_command_raw = getattr(link, 'plaintext_command', '') or getattr(link, 'command', '')
                        if link_command_raw:
                            try:
                                base64.b64decode(link_command_raw, validate=True)
                                is_base64 = True
                            except:
                                is_base64 = False
                            
                            if command_format == 'decoded':
                                if is_base64:
                                    decoded_cmd = base64.b64decode(link_command_raw).decode('utf-8', errors='ignore')
                                    item['command'] = {'encoding': 'plain', 'value': decoded_cmd}
                                else:
                                    item['command'] = {'encoding': 'plain', 'value': link_command_raw}
                            else:
                                if is_base64:
                                    item['command'] = {'encoding': 'base64', 'value': link_command_raw}
                                else:
                                    encoded_cmd = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                                    item['command'] = {'encoding': 'base64', 'value': encoded_cmd}
                    
                    # Add output if requested
                    if include_output and output_content:
                        if output_format == 'decoded':
                            try:
                                decoded_output = base64.b64decode(output_content).decode('utf-8')
                                output_json = json_lib.loads(decoded_output)
                                item['output'] = {
                                    'encoding': 'json-base64',
                                    'value': output_content,
                                    'parsed': output_json
                                }
                            except:
                                item['output'] = {'encoding': 'plain', 'value': decoded_output}
                        else:
                            item['output'] = {'encoding': 'base64', 'value': output_content}
                    
                    all_items.append(item)
            
            # Sort and paginate
            all_items.sort(key=lambda x: x['occurred_at'] or '', reverse=True)
            total_items = len(all_items)
            paginated_items = all_items[offset:offset + limit]
            
            # Calculate rates
            denominator = counts['success'] + counts['fail'] + counts['timeout']
            if denominator > 0:
                success_rate = counts['success'] / denominator
                error_rate = counts['fail'] / denominator
                timeout_rate = counts['timeout'] / denominator
            else:
                success_rate = None
                error_rate = None
                timeout_rate = None
            
            return web.json_response({
                'operation_id': op.id,
                'operation_name': op.name,
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'summary': {
                    'counts': counts,
                    'rates': {
                        'success_rate': success_rate,
                        'error_rate': error_rate,
                        'timeout_rate': timeout_rate
                    },
                    'last_event_at': last_event_at.isoformat() if last_event_at else None
                },
                'items': paginated_items,
                'paging': {'limit': limit, 'offset': offset, 'total': total_items}
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_signatures(self, request: web.Request):
        """
        Error Analytics - Signatures (error clustering).
        
        GET /api/v2/merlino/analytics/error-analytics/signatures
        """
        try:
            from datetime import datetime, timezone, timedelta
            from collections import defaultdict, Counter
            import hashlib
            
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            limit = int(params.get('limit', 100))
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get data
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Collect signatures
            signatures = defaultdict(lambda: {
                'reason': '',
                'title': '',
                'count': 0,
                'abilities': Counter(),
                'agents': Counter(),
                'example_item_id': '',
                'first_seen': None,
                'last_seen': None,
                'hint': ''
            })
            
            for op in operations:
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    link_id = getattr(link, 'id', '')
                    
                    # Only process errors and timeouts
                    if link_status not in [1, 124]:
                        continue
                    
                    # Time window
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                        except:
                            continue
                    else:
                        continue
                    
                    # Get reason
                    try:
                        file_svc = self._api_manager._file_svc
                        output_content = file_svc.read_result_file(link_id)
                        reason, hint = self._normalize_error_reason(link, output_content)
                    except:
                        reason = 'unknown'
                        hint = None
                    
                    # Create signature ID based on reason
                    signature_id = f"sig-{hashlib.md5(reason.encode()).hexdigest()[:8]}"
                    
                    # Update signature
                    sig = signatures[signature_id]
                    sig['reason'] = reason
                    sig['title'] = reason.replace('_', ' ').title()
                    sig['count'] += 1
                    sig['hint'] = hint or sig['hint']
                    
                    if not sig['example_item_id']:
                        sig['example_item_id'] = f"link:{link_id}"
                    
                    if not sig['first_seen'] or finish_dt < sig['first_seen']:
                        sig['first_seen'] = finish_dt
                    
                    if not sig['last_seen'] or finish_dt > sig['last_seen']:
                        sig['last_seen'] = finish_dt
                    
                    # Track top entities
                    if link_ability:
                        ability_id = getattr(link_ability, 'ability_id', 'unknown')
                        ability_name = getattr(link_ability, 'name', ability_id)
                        sig['abilities'][(ability_id, ability_name)] += 1
                    
                    if link_paw:
                        agent = agent_lookup.get(link_paw)
                        agent_host = getattr(agent, 'host', link_paw) if agent else link_paw
                        sig['agents'][(link_paw, agent_host)] += 1
            
            # Build items
            items = []
            for signature_id, sig in signatures.items():
                top_abilities = [
                    {'ability_id': aid, 'name': name, 'count': count}
                    for (aid, name), count in sig['abilities'].most_common(3)
                ]
                
                top_agents = [
                    {'agent_paw': paw, 'host': host, 'count': count}
                    for (paw, host), count in sig['agents'].most_common(3)
                ]
                
                items.append({
                    'signature_id': signature_id,
                    'reason': sig['reason'],
                    'title': sig['title'],
                    'count': sig['count'],
                    'top_entities': {
                        'abilities': top_abilities,
                        'agents': top_agents
                    },
                    'example_item_id': sig['example_item_id'],
                    'first_seen_at': sig['first_seen'].isoformat() if sig['first_seen'] else None,
                    'last_seen_at': sig['last_seen'].isoformat() if sig['last_seen'] else None,
                    'hint': sig['hint']
                })
            
            # Sort by count descending
            items.sort(key=lambda x: x['count'], reverse=True)
            items = items[:limit]
            
            return web.json_response({
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'items': items
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_signature_drilldown(self, request: web.Request):
        """
        Error Analytics - Signature Drilldown.
        
        GET /api/v2/merlino/analytics/error-analytics/signature/{signature_id}
        """
        try:
            from datetime import datetime, timezone, timedelta
            import hashlib
            import base64
            import json as json_lib
            
            # Get signature_id from path
            signature_id = request.match_info['signature_id']
            
            # Extract reason from signature_id (reverse of signature generation)
            # This is a simplified approach - in production you'd store signatures persistently
            
            params = request.rel_url.query
            from_str = params.get('from')
            to_str = params.get('to')
            limit = int(params.get('limit', 250))
            offset = int(params.get('offset', 0))
            
            # Include flags
            include_command = params.get('includeCommand', 'false').lower() == 'true'
            include_output = params.get('includeOutput', 'false').lower() == 'true'
            command_format = params.get('commandFormat', 'decoded')
            output_format = params.get('outputFormat', 'decoded')
            
            # Time window
            now = datetime.now(timezone.utc)
            if from_str and to_str:
                window_from = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
                window_to = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
            else:
                window_from = now - timedelta(days=7)
                window_to = now
            
            # Get data
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            agent_lookup = {agent.paw: agent for agent in agents}
            
            # Find matching events
            all_items = []
            summary_reason = ''
            summary_title = ''
            
            for op in operations:
                if not hasattr(op, 'chain') or not op.chain:
                    continue
                
                for link in op.chain:
                    link_paw = getattr(link, 'paw', None)
                    link_status = getattr(link, 'status', -1)
                    link_finish = getattr(link, 'finish', None)
                    link_ability = getattr(link, 'ability', None)
                    link_id = getattr(link, 'id', '')
                    
                    if link_status not in [1, 124]:
                        continue
                    
                    # Time window
                    if link_finish:
                        try:
                            if isinstance(link_finish, str):
                                finish_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                            else:
                                finish_dt = link_finish
                            if finish_dt < window_from or finish_dt > window_to:
                                continue
                        except:
                            continue
                    else:
                        continue
                    
                    # Get reason
                    try:
                        file_svc = self._api_manager._file_svc
                        output_content = file_svc.read_result_file(link_id)
                        reason, hint = self._normalize_error_reason(link, output_content)
                    except:
                        reason = 'unknown'
                        hint = None
                        output_content = None
                    
                    # Check if matches signature
                    event_signature_id = f"sig-{hashlib.md5(reason.encode()).hexdigest()[:8]}"
                    if event_signature_id != signature_id:
                        continue
                    
                    summary_reason = reason
                    summary_title = reason.replace('_', ' ').title()
                    
                    # Build item (same structure as events/search)
                    status_str = 'fail' if link_status == 1 else 'timeout'
                    agent = agent_lookup.get(link_paw)
                    executor_obj = getattr(link, 'executor', None)
                    executor_name = getattr(executor_obj, 'name', None) if executor_obj else None
                    
                    item = {
                        'item_id': f"link:{link_id}",
                        'occurred_at': link_finish if link_finish else None,
                        'status': status_str,
                        'reason': reason,
                        'severity': 'bad',
                        'operation_id': op.id,
                        'operation_name': op.name,
                        'ability_id': getattr(link_ability, 'ability_id', None) if link_ability else None,
                        'ability_name': getattr(link_ability, 'name', None) if link_ability else None,
                        'tactic': getattr(link_ability, 'tactic', None) if link_ability else None,
                        'technique_id': getattr(link_ability, 'technique_id', None) if link_ability else None,
                        'agent_paw': link_paw,
                        'agent_host': getattr(agent, 'host', None) if agent else None,
                        'agent_group': getattr(agent, 'group', None) if agent else None,
                        'executor': executor_name,
                        'platform': getattr(link, 'platform', None),
                        'plugin': getattr(link_ability, 'plugin', None) if link_ability and hasattr(link_ability, 'plugin') else None,
                        'error_hint': hint,
                        'source': 'caldera'
                    }
                    
                    # Add command/output if requested (same logic as before)
                    if include_command:
                        link_command_raw = getattr(link, 'plaintext_command', '') or getattr(link, 'command', '')
                        if link_command_raw:
                            try:
                                base64.b64decode(link_command_raw, validate=True)
                                is_base64 = True
                            except:
                                is_base64 = False
                            
                            if command_format == 'decoded':
                                if is_base64:
                                    decoded_cmd = base64.b64decode(link_command_raw).decode('utf-8', errors='ignore')
                                    item['command'] = {'encoding': 'plain', 'value': decoded_cmd}
                                else:
                                    item['command'] = {'encoding': 'plain', 'value': link_command_raw}
                            else:
                                if is_base64:
                                    item['command'] = {'encoding': 'base64', 'value': link_command_raw}
                                else:
                                    encoded_cmd = base64.b64encode(link_command_raw.encode('utf-8')).decode('ascii')
                                    item['command'] = {'encoding': 'base64', 'value': encoded_cmd}
                    
                    if include_output and output_content:
                        if output_format == 'decoded':
                            try:
                                decoded_output = base64.b64decode(output_content).decode('utf-8')
                                output_json = json_lib.loads(decoded_output)
                                item['output'] = {
                                    'encoding': 'json-base64',
                                    'value': output_content,
                                    'parsed': output_json
                                }
                            except:
                                item['output'] = {'encoding': 'plain', 'value': decoded_output}
                        else:
                            item['output'] = {'encoding': 'base64', 'value': output_content}
                    
                    all_items.append(item)
            
            # Sort and paginate
            all_items.sort(key=lambda x: x['occurred_at'] or '', reverse=True)
            total_items = len(all_items)
            paginated_items = all_items[offset:offset + limit]
            
            return web.json_response({
                'signature_id': signature_id,
                'time_window': {'from': window_from.isoformat(), 'to': window_to.isoformat()},
                'summary': {
                    'reason': summary_reason,
                    'title': summary_title,
                    'count': total_items
                },
                'items': paginated_items,
                'paging': {'limit': limit, 'offset': offset, 'total': total_items}
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_error_analytics_hints(self, request: web.Request):
        """
        Error Analytics - Hints Knowledge Base.
        
        GET /api/v2/merlino/analytics/error-analytics/hints
        """
        try:
            params = request.rel_url.query
            reason_filter = params.get('reason')
            signature_filter = params.get('signature_id')
            
            # Static knowledge base of hints
            hints_db = [
                {
                    'id': 'hint-access-denied-1',
                    'reason': 'access_denied',
                    'title': 'Access Denied',
                    'steps': [
                        'Verify agent privilege level (check if running as admin/root)',
                        'Try running ability with elevated executor (e.g., use "psh" with "Run as Administrator")',
                        'Check endpoint protection logs for access denials',
                        'Enable required privileges (e.g., SeDebugPrivilege for LSASS dump)',
                        'Review User Account Control (UAC) settings'
                    ],
                    'links': [
                        {'label': 'Windows Privilege Escalation Guide', 'url': 'https://docs.microsoft.com/windows/security/threat-protection/'},
                        {'label': 'Linux Privilege Escalation', 'url': 'https://blog.g0tmi1k.com/2011/08/basic-linux-privilege-escalation/'}
                    ]
                },
                {
                    'id': 'hint-command-not-found-1',
                    'reason': 'command_not_found',
                    'title': 'Command Not Found',
                    'steps': [
                        'Verify command exists on target system (check PATH)',
                        'Install required dependencies or tools',
                        'Use absolute path to command binary',
                        'Check for typos in command name',
                        'Verify correct shell/executor is being used (cmd vs psh vs sh)'
                    ],
                    'links': [
                        {'label': 'PowerShell cmdlet reference', 'url': 'https://docs.microsoft.com/powershell/'},
                        {'label': 'Linux command reference', 'url': 'https://man7.org/'}
                    ]
                },
                {
                    'id': 'hint-timeout-1',
                    'reason': 'timeout',
                    'title': 'Execution Timeout',
                    'steps': [
                        'Increase timeout value in ability configuration',
                        'Optimize command to reduce execution time',
                        'Check network latency between server and agent',
                        'Verify target system is not overloaded (CPU/memory)',
                        'Consider breaking long-running tasks into smaller steps'
                    ],
                    'links': []
                },
                {
                    'id': 'hint-network-unreachable-1',
                    'reason': 'network_unreachable',
                    'title': 'Network Unreachable',
                    'steps': [
                        'Verify network connectivity between agent and target',
                        'Check firewall rules (both host and network firewalls)',
                        'Verify DNS resolution for target hostnames',
                        'Test connectivity with ping or telnet',
                        'Check proxy settings if applicable'
                    ],
                    'links': []
                },
                {
                    'id': 'hint-amsi-block-1',
                    'reason': 'amsi_block',
                    'title': 'AMSI/EDR Block',
                    'steps': [
                        'Content detected by endpoint protection (AMSI, Windows Defender, EDR)',
                        'Consider obfuscating payload or command',
                        'Test ability in controlled environment first',
                        'Adjust detection rules if this is expected behavior',
                        'Use alternative techniques that avoid AMSI inspection',
                        'Review Morgana Arsenal AMSI bypass techniques'
                    ],
                    'links': [
                        {'label': 'AMSI Bypass Guide', 'url': 'https://github.com/S3cur3Th1sSh1t/Amsi-Bypass-Powershell'}
                    ]
                },
                {
                    'id': 'hint-file-not-found-1',
                    'reason': 'file_not_found',
                    'title': 'File Not Found',
                    'steps': [
                        'Verify file path exists on target system',
                        'Check for typos in file path',
                        'Use absolute paths instead of relative paths',
                        'Ensure file was created by previous ability',
                        'Check file permissions'
                    ],
                    'links': []
                },
                {
                    'id': 'hint-dependency-missing-1',
                    'reason': 'dependency_missing',
                    'title': 'Missing Dependency',
                    'steps': [
                        'Install required PowerShell modules or Python packages',
                        'Verify .NET framework version (for PowerShell cmdlets)',
                        'Install missing system libraries',
                        'Check ability requirements in ability YAML',
                        'Use payload deployment to stage required files'
                    ],
                    'links': []
                },
                {
                    'id': 'hint-invalid-argument-1',
                    'reason': 'invalid_argument',
                    'title': 'Invalid Argument',
                    'steps': [
                        'Review command syntax for errors',
                        'Verify parameter values match expected format',
                        'Check for missing required parameters',
                        'Validate fact substitution (#{fact.name}) resolved correctly',
                        'Test command manually on target system'
                    ],
                    'links': []
                }
            ]
            
            # Filter hints
            filtered_hints = hints_db
            if reason_filter:
                filtered_hints = [h for h in filtered_hints if h['reason'] == reason_filter]
            
            # Note: signature_filter would require looking up signature->reason mapping
            # For now, we only filter by reason
            
            return web.json_response({'items': filtered_hints})
        
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_realtime_operations_metrics(self, request: web.Request):
        """Realtime Operations Metrics - Snapshot completo."""
        try:
            from datetime import datetime, timezone, timedelta
            
            params = request.rel_url.query
            window_minutes = int(params.get('windowMinutes', 60))
            include_timeline = params.get('includeTimeline', 'true').lower() == 'true'
            timeline_limit = int(params.get('timelineLimit', 20))
            
            generated_at = datetime.now(timezone.utc)
            window_start = generated_at - timedelta(minutes=window_minutes)
            
            operations = list(self._api_manager.find_objects(self.ram_key))
            agents = list(self._api_manager.find_objects('agents'))
            
            operations_realtime = []
            total_abilities = 0
            total_success = 0
            total_errors = 0
            running_ops = 0
            completed_ops = 0
            failed_ops = 0
            
            for op in operations:
                state = getattr(op, 'state', 'unknown')
                if state == 'running':
                    running_ops += 1
                elif state == 'finished':
                    completed_ops += 1
                elif state in ['stopped', 'paused']:
                    failed_ops += 1
                
                op_total = 0
                op_success = 0
                op_error = 0
                op_running = 0
                tcodes = set()
                abilities_list = []
                
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        op_total += 1
                        link_status = getattr(link, 'status', -1)
                        link_ability = getattr(link, 'ability', None)
                        
                        if link_status == 0:
                            op_success += 1
                            ability_status = 'success'
                        elif link_status in [1, 124]:
                            op_error += 1
                            ability_status = 'error'
                        elif link_status == -1:
                            op_running += 1
                            ability_status = 'running'
                        else:
                            ability_status = 'unknown'
                        
                        if link_ability:
                            abilities_list.append({
                                'name': getattr(link_ability, 'name', 'Unknown'),
                                'tactic': getattr(link_ability, 'tactic', None),
                                'technique': getattr(link_ability, 'technique_id', None),
                                'status': ability_status
                            })
                            technique_id = getattr(link_ability, 'technique_id', None)
                            if technique_id:
                                tcodes.add(technique_id)
                
                total_abilities += op_total
                total_success += op_success
                total_errors += op_error
                
                agent_paws = set()
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        paw = getattr(link, 'paw', None)
                        if paw:
                            agent_paws.add(paw)
                
                started = getattr(op, 'start', None)
                start_time = getattr(op, 'start', None)
                finish_time = getattr(op, 'finish', None)
                
                if started and hasattr(started, 'isoformat'):
                    started = started.isoformat()
                if start_time and hasattr(start_time, 'isoformat'):
                    start_time = start_time.isoformat()
                if finish_time and hasattr(finish_time, 'isoformat'):
                    finish_time = finish_time.isoformat()
                
                operations_realtime.append({
                    'id': op.id,
                    'name': op.name,
                    'adversary': getattr(op.adversary, 'adversary_id', None) if hasattr(op, 'adversary') and op.adversary else None,
                    'state': state,
                    'started': started,
                    'start_time': start_time,
                    'finish_time': finish_time,
                    'total_abilities': op_total,
                    'success_count': op_success,
                    'error_count': op_error,
                    'running_count': op_running,
                    'agents_count': len(agent_paws),
                    'techniques_count': len(tcodes),
                    'tcodes': sorted(list(tcodes)),
                    'abilities': abilities_list[:10]
                })
            
            success_rate = (total_success / total_abilities * 100) if total_abilities > 0 else 0.0
            global_stats = {
                'totalOps': len(operations),
                'totalAbilities': total_abilities,
                'totalSuccess': total_success,
                'totalErrors': total_errors,
                'successRate': round(success_rate, 3),
                'runningOps': running_ops,
                'completedOps': completed_ops,
                'failedOps': failed_ops,
                'totalAgents': len(agents)
            }
            
            agents_realtime = []
            for agent in agents:
                last_seen = getattr(agent, 'last_seen', None)
                if last_seen and hasattr(last_seen, 'isoformat'):
                    last_seen = last_seen.isoformat()
                agents_realtime.append({
                    'paw': agent.paw,
                    'host': getattr(agent, 'host', None),
                    'platform': getattr(agent, 'platform', None),
                    'last_seen': last_seen
                })
            
            timeline = []
            if include_timeline:
                # Generate timeline events from operations and abilities
                for op in operations:
                    op_id = op.id
                    op_name = op.name
                    op_state = getattr(op, 'state', 'unknown')
                    
                    # Event 1: Operation started
                    start_time = getattr(op, 'start', None)
                    if start_time:
                        try:
                            if isinstance(start_time, str):
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                start_ts = start_time if start_time.endswith('Z') or '+' in start_time else start_time + 'Z'
                            else:
                                start_dt = start_time
                                start_ts = start_time.isoformat()
                            
                            timeline.append({
                                'ts': start_ts,
                                'type': 'operation_started',
                                'operation_id': op_id,
                                'operation_name': op_name,
                                'details': f'Operation "{op_name}" started'
                            })
                        except Exception as e:
                            pass
                    
                    # Event 2: Operation finished (if completed)
                    finish_time = getattr(op, 'finish', None)
                    if finish_time and op_state == 'finished':
                        try:
                            if isinstance(finish_time, str):
                                finish_dt = datetime.fromisoformat(finish_time.replace('Z', '+00:00'))
                                finish_ts = finish_time if finish_time.endswith('Z') or '+' in finish_time else finish_time + 'Z'
                            else:
                                finish_dt = finish_time
                                finish_ts = finish_time.isoformat()
                            
                            timeline.append({
                                'ts': finish_ts,
                                'type': 'operation_finished',
                                'operation_id': op_id,
                                'operation_name': op_name,
                                'details': f'Operation "{op_name}" finished'
                            })
                        except Exception as e:
                            pass
                    
                    # Event 3: Abilities executed
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            # Use display to get all fields including finish
                            link_dict = link.display if hasattr(link, 'display') else {}
                            
                            link_finish = link_dict.get('finish') or getattr(link, 'finish', None)
                            link_status = link_dict.get('status', getattr(link, 'status', -1))
                            link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                            
                            if link_finish:
                                ability_name = 'Unknown'
                                ability_id = None
                                
                                # Try to get ability from link
                                if 'ability' in link_dict and link_dict['ability']:
                                    ability_dict = link_dict['ability']
                                    ability_name = ability_dict.get('name', 'Unknown')
                                    ability_id = ability_dict.get('ability_id', ability_dict.get('id', None))
                                elif hasattr(link, 'ability') and link.ability:
                                    ability_name = getattr(link.ability, 'name', 'Unknown')
                                    ability_id = getattr(link.ability, 'ability_id', None)
                                
                                try:
                                    if isinstance(link_finish, str):
                                        link_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                    else:
                                        link_ts = link_finish.isoformat()
                                    
                                    # Map status to human-readable
                                    if link_status == 0:
                                        status_str = 'success'
                                    elif link_status in [1, 124]:
                                        status_str = 'failed'
                                    elif link_status == -1:
                                        status_str = 'running'
                                    else:
                                        status_str = 'unknown'
                                    
                                    # Get command output if available (truncated)
                                    link_output = link_dict.get('output', getattr(link, 'output', ''))
                                    details = f'Status: {status_str}'
                                    if link_output and len(link_output) > 0:
                                        output_preview = link_output[:100] + '...' if len(link_output) > 100 else link_output
                                        details += f' | Output: {output_preview}'
                                    
                                    timeline.append({
                                        'ts': link_ts,
                                        'type': 'ability_executed',
                                        'operation_id': op_id,
                                        'operation_name': op_name,
                                        'agent_paw': link_paw,
                                        'ability_id': ability_id,
                                        'ability_name': ability_name,
                                        'status': status_str,
                                        'details': details
                                    })
                                except Exception as e:
                                    pass
                
                # Sort timeline by timestamp descending (most recent first)
                timeline.sort(key=lambda x: x.get('ts', ''), reverse=True)
                
                # Apply limit
                timeline = timeline[:timeline_limit]
            
            return web.json_response({
                'generatedAt': generated_at.isoformat(),
                'window': f'{window_minutes}m',
                'globalStats': global_stats,
                'operations': operations_realtime,
                'agents': agents_realtime,
                'timeline': timeline
            })
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_realtime_operations(self, request: web.Request):
        """Realtime Operations - Solo lista operazioni."""
        try:
            from datetime import datetime, timezone
            generated_at = datetime.now(timezone.utc)
            operations = list(self._api_manager.find_objects(self.ram_key))
            operations_realtime = []
            for op in operations:
                operations_realtime.append({
                    'id': op.id,
                    'name': op.name,
                    'state': getattr(op, 'state', 'unknown')
                })
            return web.json_response({'meta': {'generatedAt': generated_at.isoformat()}, 'operations': operations_realtime})
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_realtime_agents(self, request: web.Request):
        """Realtime Agents - Solo lista agents."""
        try:
            from datetime import datetime, timezone
            generated_at = datetime.now(timezone.utc)
            agents = list(self._api_manager.find_objects('agents'))
            agents_realtime = []
            for a in agents:
                last_seen = getattr(a, 'last_seen', None)
                if last_seen and hasattr(last_seen, 'isoformat'):
                    last_seen = last_seen.isoformat()
                agents_realtime.append({'paw': a.paw, 'host': getattr(a, 'host', None), 'platform': getattr(a, 'platform', None), 'last_seen': last_seen})
            return web.json_response({'meta': {'generatedAt': generated_at.isoformat()}, 'agents': agents_realtime})
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_realtime_timeline(self, request: web.Request):
        """Realtime Timeline - Solo eventi timeline."""
        try:
            from datetime import datetime, timezone, timedelta
            params = request.rel_url.query
            window_minutes = int(params.get('windowMinutes', 60))
            limit = int(params.get('limit', 20))
            generated_at = datetime.now(timezone.utc)
            window_start = generated_at - timedelta(minutes=window_minutes)
            operations = list(self._api_manager.find_objects(self.ram_key))
            
            timeline = []
            for op in operations:
                op_id = op.id
                op_name = op.name
                
                # Operation started events
                start_time = getattr(op, 'start', None)
                if start_time:
                    try:
                        if isinstance(start_time, str):
                            start_ts = start_time if start_time.endswith('Z') or '+' in start_time else start_time + 'Z'
                        else:
                            start_ts = start_time.isoformat()
                        timeline.append({
                            'ts': start_ts,
                            'type': 'operation_started',
                            'operation_id': op_id,
                            'operation_name': op_name,
                            'details': f'Operation "{op_name}" started'
                        })
                    except:
                        pass
                
                # Ability executed events
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        # Use display to get all fields including finish
                        link_dict = link.display if hasattr(link, 'display') else {}
                        
                        link_finish = link_dict.get('finish') or getattr(link, 'finish', None)
                        link_status = link_dict.get('status', getattr(link, 'status', -1))
                        link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                        
                        if link_finish:
                            ability_name = 'Unknown'
                            ability_id = None
                            
                            # Try to get ability from link
                            if 'ability' in link_dict and link_dict['ability']:
                                ability_dict = link_dict['ability']
                                ability_name = ability_dict.get('name', 'Unknown')
                                ability_id = ability_dict.get('ability_id', ability_dict.get('id', None))
                            elif hasattr(link, 'ability') and link.ability:
                                ability_name = getattr(link.ability, 'name', 'Unknown')
                                ability_id = getattr(link.ability, 'ability_id', None)
                            
                            try:
                                if isinstance(link_finish, str):
                                    link_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                else:
                                    link_ts = link_finish.isoformat()
                                
                                status_str = 'success' if link_status == 0 else ('failed' if link_status in [1, 124] else 'running')
                                
                                # Get command output if available (truncated)
                                link_output = link_dict.get('output', getattr(link, 'output', ''))
                                details = f'Status: {status_str}'
                                if link_output and len(link_output) > 0:
                                    output_preview = link_output[:100] + '...' if len(link_output) > 100 else link_output
                                    details += f' | Output: {output_preview}'
                                
                                timeline.append({
                                    'ts': link_ts,
                                    'type': 'ability_executed',
                                    'operation_id': op_id,
                                    'operation_name': op_name,
                                    'agent_paw': link_paw,
                                    'ability_id': ability_id,
                                    'ability_name': ability_name,
                                    'status': status_str,
                                    'details': details
                                })
                            except:
                                pass
            
            timeline.sort(key=lambda x: x.get('ts', ''), reverse=True)
            return web.json_response({
                'generatedAt': generated_at.isoformat(),
                'window': f'{window_minutes}m',
                'timeline': timeline[:limit]
            })
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    # ========================================================================
    # AGENTS INTELLIGENCE APIs (Merlino v2)
    # ========================================================================
    
    async def merlino_agents_intelligence_overview(self, request: web.Request):
        """
        Agents Intelligence Overview - Main endpoint for Agents Intelligence taskpane.
        Returns agents stats, timeline, graph, and insights.
        """
        try:
            from datetime import datetime, timezone, timedelta
            
            params = request.rel_url.query
            window_str = params.get('window', '15m')
            include_timeline = params.get('includeTimeline', 'true').lower() == 'true'
            timeline_limit = int(params.get('timelineLimit', 250))
            include_graph = params.get('includeGraph', 'true').lower() == 'true'
            graph_depth = int(params.get('graphDepth', 2))
            include_insights = params.get('includeTopInsights', 'true').lower() == 'true'
            
            # Parse window
            window_minutes = self._parse_window_string(window_str)
            generated_at = datetime.now(timezone.utc)
            window_start = generated_at - timedelta(minutes=window_minutes)
            
            # Get all agents
            agents = list(self._api_manager.find_objects('agents'))
            operations = list(self._api_manager.find_objects(self.ram_key))
            
            # Activity window for active/inactive determination (5 minutes default)
            activity_window_seconds = 300
            activity_threshold = generated_at - timedelta(seconds=activity_window_seconds)
            
            # Calculate agent stats
            total_agents = len(agents)
            active_agents = 0
            inactive_agents = 0
            platform_dist = {}
            privilege_dist = {}
            group_dist = {}
            
            for agent in agents:
                # Activity status
                last_seen = getattr(agent, 'last_seen', None)
                if last_seen:
                    if isinstance(last_seen, str):
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    else:
                        last_seen_dt = last_seen
                    
                    if last_seen_dt >= activity_threshold:
                        active_agents += 1
                    else:
                        inactive_agents += 1
                else:
                    inactive_agents += 1
                
                # Platform distribution
                platform = getattr(agent, 'platform', 'unknown')
                platform_dist[platform] = platform_dist.get(platform, 0) + 1
                
                # Privilege distribution
                privilege = getattr(agent, 'privilege', 'unknown')
                privilege_dist[privilege] = privilege_dist.get(privilege, 0) + 1
                
                # Group distribution
                group = getattr(agent, 'group', '')
                group_dist[group] = group_dist.get(group, 0) + 1
            
            agent_stats = {
                'totalAgents': total_agents,
                'activeAgents': active_agents,
                'inactiveAgents': inactive_agents,
                'activityWindowSeconds': activity_window_seconds,
                'platformDistribution': platform_dist,
                'privilegeDistribution': privilege_dist,
                'groupDistribution': group_dist
            }
            
            # Build agents list with rich metadata
            agents_list = []
            for agent in agents:
                paw = agent.paw
                host = getattr(agent, 'host', 'unknown')
                platform = getattr(agent, 'platform', 'unknown')
                group = getattr(agent, 'group', '')
                privilege = getattr(agent, 'privilege', 'User')
                trusted = getattr(agent, 'trusted', True)
                
                last_seen = getattr(agent, 'last_seen', None)
                last_seen_ts = None
                seconds_since_last_seen = None
                status = 'inactive'
                
                if last_seen:
                    if isinstance(last_seen, str):
                        last_seen_ts = last_seen if last_seen.endswith('Z') or '+' in last_seen else last_seen + 'Z'
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    else:
                        last_seen_ts = last_seen.isoformat()
                        last_seen_dt = last_seen
                    
                    seconds_since_last_seen = int((generated_at - last_seen_dt).total_seconds())
                    status = 'active' if seconds_since_last_seen <= activity_window_seconds else 'inactive'
                
                # Calculate agent activity in window
                ops_in_window = 0
                abilities_in_window = 0
                success_in_window = 0
                failed_in_window = 0
                pending_in_window = 0
                tcodes_set = set()
                tactics_set = set()
                
                for op in operations:
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            link_dict = link.display if hasattr(link, 'display') else {}
                            link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                            
                            if link_paw == paw:
                                link_finish = link_dict.get('finish') or getattr(link, 'finish', None)
                                if link_finish:
                                    try:
                                        if isinstance(link_finish, str):
                                            link_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                                        else:
                                            link_dt = link_finish
                                        
                                        if link_dt >= window_start:
                                            abilities_in_window += 1
                                            
                                            link_status = link_dict.get('status', getattr(link, 'status', -1))
                                            if link_status == 0:
                                                success_in_window += 1
                                            elif link_status in [1, 124]:
                                                failed_in_window += 1
                                            else:
                                                pending_in_window += 1
                                            
                                            # Get technique/tactic
                                            if 'ability' in link_dict and link_dict['ability']:
                                                ability_dict = link_dict['ability']
                                                if 'technique_id' in ability_dict:
                                                    tcodes_set.add(ability_dict['technique_id'])
                                                if 'tactic' in ability_dict:
                                                    tactics_set.add(ability_dict['tactic'])
                                    except:
                                        pass
                
                # Calculate risk score (simple heuristic)
                risk_score = 30  # Base score
                risk_reasons = []
                
                if privilege in ['Elevated', 'Administrator']:
                    risk_score += 20
                    risk_reasons.append('Elevated privilege')
                
                if failed_in_window > 0:
                    risk_score += min(failed_in_window * 5, 30)
                    risk_reasons.append(f'{failed_in_window} failed abilities')
                
                if any('credential' in t.lower() or 'T1003' in t for t in tcodes_set):
                    risk_score += 20
                    risk_reasons.append('Credential access technique observed')
                
                risk_score = min(risk_score, 100)
                risk_level = 'low' if risk_score < 40 else ('medium' if risk_score < 70 else 'high')
                
                agents_list.append({
                    'paw': paw,
                    'host': host,
                    'display_name': host,
                    'platform': platform,
                    'architecture': getattr(agent, 'architecture', 'unknown'),
                    'group': group,
                    'privilege': privilege,
                    'trusted': trusted,
                    'last_seen': last_seen_ts,
                    'first_seen': getattr(agent, 'created', generated_at).isoformat() if hasattr(getattr(agent, 'created', None), 'isoformat') else None,
                    'health': {
                        'status': status,
                        'secondsSinceLastSeen': seconds_since_last_seen,
                        'confidence': 'high' if seconds_since_last_seen and seconds_since_last_seen < 60 else 'medium'
                    },
                    'tcodes': sorted(list(tcodes_set)),
                    'tactics': sorted(list(tactics_set)),
                    'activity': {
                        'operationsInWindow': ops_in_window,
                        'abilitiesInWindow': abilities_in_window,
                        'successInWindow': success_in_window,
                        'failedInWindow': failed_in_window,
                        'pendingInWindow': pending_in_window
                    },
                    'risk': {
                        'score': risk_score,
                        'level': risk_level,
                        'reasons': risk_reasons
                    }
                })
            
            # Build timeline (if requested)
            timeline = []
            if include_timeline:
                # Agent seen events
                for agent in agents:
                    last_seen = getattr(agent, 'last_seen', None)
                    if last_seen:
                        try:
                            if isinstance(last_seen, str):
                                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                                last_seen_ts = last_seen if last_seen.endswith('Z') or '+' in last_seen else last_seen + 'Z'
                            else:
                                last_seen_dt = last_seen
                                last_seen_ts = last_seen.isoformat()
                            
                            if last_seen_dt >= window_start:
                                timeline.append({
                                    'ts': last_seen_ts,
                                    'type': 'agent_seen',
                                    'severity': 'info',
                                    'agent_paw': agent.paw,
                                    'agent_host': getattr(agent, 'host', 'unknown'),
                                    'details': f'Agent {getattr(agent, "host", "unknown")} checked in'
                                })
                        except:
                            pass
                
                # Operation events
                for op in operations:
                    op_id = op.id
                    op_name = op.name
                    
                    # Operation started
                    start_time = getattr(op, 'start', None)
                    if start_time:
                        try:
                            if isinstance(start_time, str):
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                start_ts = start_time if start_time.endswith('Z') or '+' in start_time else start_time + 'Z'
                            else:
                                start_dt = start_time
                                start_ts = start_time.isoformat()
                            
                            if start_dt >= window_start:
                                timeline.append({
                                    'ts': start_ts,
                                    'type': 'operation_started',
                                    'severity': 'info',
                                    'operation_id': op_id,
                                    'operation_name': op_name,
                                    'details': f'Operation "{op_name}" started'
                                })
                        except:
                            pass
                    
                    # Ability executed events
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            link_dict = link.display if hasattr(link, 'display') else {}
                            link_finish = link_dict.get('finish') or getattr(link, 'finish', None)
                            
                            if link_finish:
                                try:
                                    if isinstance(link_finish, str):
                                        link_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                                        link_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                    else:
                                        link_dt = link_finish
                                        link_ts = link_finish.isoformat()
                                    
                                    if link_dt >= window_start:
                                        link_status = link_dict.get('status', getattr(link, 'status', -1))
                                        link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                                        
                                        ability_name = 'Unknown'
                                        ability_id = None
                                        technique = None
                                        tactic = None
                                        
                                        if 'ability' in link_dict and link_dict['ability']:
                                            ability_dict = link_dict['ability']
                                            ability_name = ability_dict.get('name', 'Unknown')
                                            ability_id = ability_dict.get('ability_id', ability_dict.get('id', None))
                                            technique = ability_dict.get('technique_id', None)
                                            tactic = ability_dict.get('tactic', None)
                                        
                                        status_str = 'success' if link_status == 0 else ('failed' if link_status in [1, 124] else 'running')
                                        severity = 'warning' if link_status in [1, 124] else 'info'
                                        
                                        # Find agent host
                                        agent_host = 'unknown'
                                        for a in agents:
                                            if a.paw == link_paw:
                                                agent_host = getattr(a, 'host', 'unknown')
                                                break
                                        
                                        link_output = link_dict.get('output', '')
                                        details = f'Status: {status_str}'
                                        if link_output:
                                            details = link_output[:100]
                                        
                                        timeline.append({
                                            'ts': link_ts,
                                            'type': 'ability_executed',
                                            'severity': severity,
                                            'agent_paw': link_paw,
                                            'agent_host': agent_host,
                                            'operation_id': op_id,
                                            'operation_name': op_name,
                                            'ability_name': ability_name,
                                            'ability_id': ability_id,
                                            'status': status_str,
                                            'technique': technique,
                                            'tactic': tactic,
                                            'details': details
                                        })
                                except:
                                    pass
                
                timeline.sort(key=lambda x: x.get('ts', ''), reverse=True)
                timeline = timeline[:timeline_limit]
            
            # Build graph (if requested)
            graph = {'nodes': [], 'edges': [], 'legend': {'nodeTypes': [], 'edgeTypes': []}}
            if include_graph:
                # Add agent nodes
                for agent_data in agents_list[:50]:  # Limit to 50 agents for performance
                    paw = agent_data['paw']
                    status = agent_data['health']['status']
                    color = '#4ec9b0' if status == 'active' else '#808080'
                    
                    graph['nodes'].append({
                        'id': f'agent:{paw}',
                        'type': 'agent',
                        'label': agent_data['display_name'],
                        'subtitle': f"{agent_data['platform']} | {agent_data['group']}",
                        'metrics': {
                            'last_seen': agent_data['last_seen'],
                            'risk': agent_data['risk']['score']
                        },
                        'style': {
                            'status': status,
                            'color': color
                        }
                    })
                
                # Add technique nodes and edges
                technique_counts = {}
                agent_technique_edges = {}
                
                for op in operations:
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            link_dict = link.display if hasattr(link, 'display') else {}
                            link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                            
                            if 'ability' in link_dict and link_dict['ability']:
                                ability_dict = link_dict['ability']
                                technique_id = ability_dict.get('technique_id', None)
                                
                                if technique_id and link_paw:
                                    technique_counts[technique_id] = technique_counts.get(technique_id, 0) + 1
                                    
                                    edge_key = f'{link_paw}:{technique_id}'
                                    if edge_key not in agent_technique_edges:
                                        agent_technique_edges[edge_key] = {
                                            'agent': link_paw,
                                            'technique': technique_id,
                                            'count': 0,
                                            'last_ts': None
                                        }
                                    
                                    agent_technique_edges[edge_key]['count'] += 1
                                    
                                    link_finish = link_dict.get('finish')
                                    if link_finish:
                                        if isinstance(link_finish, str):
                                            link_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                        else:
                                            link_ts = link_finish.isoformat()
                                        
                                        if not agent_technique_edges[edge_key]['last_ts'] or link_ts > agent_technique_edges[edge_key]['last_ts']:
                                            agent_technique_edges[edge_key]['last_ts'] = link_ts
                
                # Add top techniques as nodes
                top_techniques = sorted(technique_counts.items(), key=lambda x: x[1], reverse=True)[:20]
                for technique_id, count in top_techniques:
                    graph['nodes'].append({
                        'id': f'technique:{technique_id}',
                        'type': 'technique',
                        'label': technique_id,
                        'subtitle': 'MITRE ATT&CK',
                        'metrics': {
                            'observed_count': count
                        },
                        'style': {
                            'color': '#ff9800'
                        }
                    })
                
                # Add edges
                edge_id = 0
                for edge_key, edge_data in agent_technique_edges.items():
                    if f"technique:{edge_data['technique']}" in [n['id'] for n in graph['nodes']]:
                        edge_id += 1
                        graph['edges'].append({
                            'id': f'e{edge_id}',
                            'source': f"agent:{edge_data['agent']}",
                            'target': f"technique:{edge_data['technique']}",
                            'type': 'observed',
                            'weight': edge_data['count'],
                            'label': f"{edge_data['count']} events",
                            'meta': {
                                'window': window_str,
                                'last_ts': edge_data['last_ts']
                            }
                        })
                
                graph['legend'] = {
                    'nodeTypes': ['agent', 'technique', 'operation', 'ability', 'tactic', 'host', 'group'],
                    'edgeTypes': ['observed', 'belongs_to', 'executed_in', 'related_to']
                }
            
            # Build insights (if requested)
            insights = {'topTechniques': [], 'topAgents': [], 'alerts': []}
            if include_insights:
                # Top techniques
                technique_counts = {}
                for agent_data in agents_list:
                    for tcode in agent_data['tcodes']:
                        technique_counts[tcode] = technique_counts.get(tcode, 0) + 1
                
                insights['topTechniques'] = [
                    {'technique': t, 'count': c}
                    for t, c in sorted(technique_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
                
                # Top agents by risk
                insights['topAgents'] = [
                    {'paw': a['paw'], 'host': a['host'], 'risk': a['risk']['score']}
                    for a in sorted(agents_list, key=lambda x: x['risk']['score'], reverse=True)[:5]
                ]
                
                # Generate alerts
                alert_id = 0
                for agent_data in agents_list:
                    if agent_data['risk']['level'] == 'high':
                        alert_id += 1
                        insights['alerts'].append({
                            'id': f'a{alert_id}',
                            'ts': generated_at.isoformat(),
                            'severity': 'warning',
                            'title': 'High-risk activity detected',
                            'details': f"Agent {agent_data['host']} has risk score {agent_data['risk']['score']}",
                            'agent_paw': agent_data['paw']
                        })
            
            return web.json_response({
                'generatedAt': generated_at.isoformat(),
                'window': window_str,
                'agentStats': agent_stats,
                'agents': agents_list,
                'timeline': timeline,
                'graph': graph,
                'insights': insights
            })
            
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_agents_intelligence_agent_detail(self, request: web.Request):
        """
        Agent Details - Deep drill-down for a specific agent.
        """
        try:
            from datetime import datetime, timezone, timedelta
            
            paw = request.match_info.get('paw')
            if not paw:
                return web.json_response({'error': 'Missing paw parameter'}, status=400)
            
            params = request.rel_url.query
            window_str = params.get('window', '24h')
            include_timeline = params.get('includeTimeline', 'true').lower() == 'true'
            timeline_limit = int(params.get('timelineLimit', 500))
            include_graph = params.get('includeGraph', 'true').lower() == 'true'
            
            window_minutes = self._parse_window_string(window_str)
            generated_at = datetime.now(timezone.utc)
            window_start = generated_at - timedelta(minutes=window_minutes)
            
            # Find agent
            agents = list(self._api_manager.find_objects('agents'))
            agent = None
            for a in agents:
                if a.paw == paw:
                    agent = a
                    break
            
            if not agent:
                return web.json_response({'error': f'Agent {paw} not found'}, status=404)
            
            # Get operations
            operations = list(self._api_manager.find_objects(self.ram_key))
            
            # Build agent data
            host = getattr(agent, 'host', 'unknown')
            platform = getattr(agent, 'platform', 'unknown')
            group = getattr(agent, 'group', '')
            privilege = getattr(agent, 'privilege', 'User')
            
            last_seen = getattr(agent, 'last_seen', None)
            last_seen_ts = None
            if last_seen:
                if isinstance(last_seen, str):
                    last_seen_ts = last_seen if last_seen.endswith('Z') or '+' in last_seen else last_seen + 'Z'
                else:
                    last_seen_ts = last_seen.isoformat()
            
            # Collect tcodes and tactics
            tcodes_set = set()
            tactics_set = set()
            
            for op in operations:
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        link_dict = link.display if hasattr(link, 'display') else {}
                        link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                        
                        if link_paw == paw:
                            if 'ability' in link_dict and link_dict['ability']:
                                ability_dict = link_dict['ability']
                                if 'technique_id' in ability_dict:
                                    tcodes_set.add(ability_dict['technique_id'])
                                if 'tactic' in ability_dict:
                                    tactics_set.add(ability_dict['tactic'])
            
            # Calculate risk
            risk_score = 30
            risk_reasons = []
            if privilege in ['Elevated', 'Administrator']:
                risk_score += 20
                risk_reasons.append('Elevated privilege')
            risk_score = min(risk_score, 100)
            risk_level = 'low' if risk_score < 40 else ('medium' if risk_score < 70 else 'high')
            
            agent_data = {
                'paw': paw,
                'host': host,
                'display_name': host,
                'platform': platform,
                'architecture': getattr(agent, 'architecture', 'unknown'),
                'group': group,
                'privilege': privilege,
                'trusted': getattr(agent, 'trusted', True),
                'first_seen': getattr(agent, 'created', generated_at).isoformat() if hasattr(getattr(agent, 'created', None), 'isoformat') else None,
                'last_seen': last_seen_ts,
                'tcodes': sorted(list(tcodes_set)),
                'tactics': sorted(list(tactics_set)),
                'risk': {
                    'score': risk_score,
                    'level': risk_level,
                    'reasons': risk_reasons
                }
            }
            
            # Build timeline
            timeline = []
            if include_timeline:
                for op in operations:
                    op_id = op.id
                    op_name = op.name
                    
                    if hasattr(op, 'chain') and op.chain:
                        for link in op.chain:
                            link_dict = link.display if hasattr(link, 'display') else {}
                            link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                            
                            if link_paw == paw:
                                link_finish = link_dict.get('finish') or getattr(link, 'finish', None)
                                
                                if link_finish:
                                    try:
                                        if isinstance(link_finish, str):
                                            link_dt = datetime.fromisoformat(link_finish.replace('Z', '+00:00'))
                                            link_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                        else:
                                            link_dt = link_finish
                                            link_ts = link_finish.isoformat()
                                        
                                        if link_dt >= window_start:
                                            link_status = link_dict.get('status', getattr(link, 'status', -1))
                                            
                                            ability_name = 'Unknown'
                                            technique = None
                                            tactic = None
                                            
                                            if 'ability' in link_dict and link_dict['ability']:
                                                ability_dict = link_dict['ability']
                                                ability_name = ability_dict.get('name', 'Unknown')
                                                technique = ability_dict.get('technique_id', None)
                                                tactic = ability_dict.get('tactic', None)
                                            
                                            status_str = 'success' if link_status == 0 else ('failed' if link_status in [1, 124] else 'running')
                                            severity = 'warning' if link_status in [1, 124] else 'info'
                                            
                                            link_output = link_dict.get('output', '')
                                            details = link_output[:200] if link_output else f'Status: {status_str}'
                                            
                                            timeline.append({
                                                'ts': link_ts,
                                                'type': 'ability_executed',
                                                'severity': severity,
                                                'operation_id': op_id,
                                                'operation_name': op_name,
                                                'ability_name': ability_name,
                                                'status': status_str,
                                                'technique': technique,
                                                'tactic': tactic,
                                                'details': details
                                            })
                                    except:
                                        pass
                
                timeline.sort(key=lambda x: x.get('ts', ''), reverse=True)
                timeline = timeline[:timeline_limit]
            
            # Build relationships
            ops_set = {}
            techniques_count = {}
            
            for op in operations:
                if hasattr(op, 'chain') and op.chain:
                    for link in op.chain:
                        link_dict = link.display if hasattr(link, 'display') else {}
                        link_paw = link_dict.get('paw', getattr(link, 'paw', None))
                        
                        if link_paw == paw:
                            if op.id not in ops_set:
                                link_finish = link_dict.get('finish')
                                if link_finish:
                                    if isinstance(link_finish, str):
                                        last_ts = link_finish if link_finish.endswith('Z') or '+' in link_finish else link_finish + 'Z'
                                    else:
                                        last_ts = link_finish.isoformat()
                                else:
                                    last_ts = None
                                
                                ops_set[op.id] = {
                                    'id': op.id,
                                    'name': op.name,
                                    'state': getattr(op, 'state', 'unknown'),
                                    'last_ts': last_ts
                                }
                            
                            if 'ability' in link_dict and link_dict['ability']:
                                ability_dict = link_dict['ability']
                                technique_id = ability_dict.get('technique_id', None)
                                technique_name = ability_dict.get('technique_name', technique_id)
                                
                                if technique_id:
                                    if technique_id not in techniques_count:
                                        techniques_count[technique_id] = {
                                            'technique': technique_id,
                                            'name': technique_name,
                                            'count': 0
                                        }
                                    techniques_count[technique_id]['count'] += 1
            
            relationships = {
                'operations': list(ops_set.values()),
                'techniques': sorted(list(techniques_count.values()), key=lambda x: x['count'], reverse=True)
            }
            
            # Build graph (simplified for single agent)
            graph = {'nodes': [], 'edges': [], 'legend': {'nodeTypes': [], 'edgeTypes': []}}
            if include_graph:
                # Agent node
                graph['nodes'].append({
                    'id': f'agent:{paw}',
                    'type': 'agent',
                    'label': host,
                    'subtitle': f'{platform} | {group}',
                    'metrics': {
                        'last_seen': last_seen_ts,
                        'risk': risk_score
                    },
                    'style': {
                        'status': 'active',
                        'color': '#4ec9b0'
                    }
                })
                
                # Technique nodes
                for tech_data in relationships['techniques'][:10]:
                    graph['nodes'].append({
                        'id': f"technique:{tech_data['technique']}",
                        'type': 'technique',
                        'label': tech_data['technique'],
                        'subtitle': tech_data['name'],
                        'metrics': {
                            'observed_count': tech_data['count']
                        },
                        'style': {
                            'color': '#ff9800'
                        }
                    })
                    
                    graph['edges'].append({
                        'id': f"e{tech_data['technique']}",
                        'source': f'agent:{paw}',
                        'target': f"technique:{tech_data['technique']}",
                        'type': 'observed',
                        'weight': tech_data['count'],
                        'label': f"{tech_data['count']} events"
                    })
                
                graph['legend'] = {
                    'nodeTypes': ['agent', 'technique'],
                    'edgeTypes': ['observed']
                }
            
            return web.json_response({
                'generatedAt': generated_at.isoformat(),
                'window': window_str,
                'agent': agent_data,
                'timeline': timeline,
                'relationships': relationships,
                'graph': graph
            })
            
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    async def merlino_agents_intelligence_graph(self, request: web.Request):
        """
        Agents Intelligence Graph - Standalone graph endpoint (optional, returns same as overview).
        """
        try:
            import json
            # Delegate to overview and extract graph only
            overview_response = await self.merlino_agents_intelligence_overview(request)
            
            if overview_response.status != 200:
                return overview_response
            
            # Parse the response body
            response_text = overview_response.body.decode('utf-8')
            data = json.loads(response_text)
            
            return web.json_response({
                'generatedAt': data.get('generatedAt'),
                'window': data.get('window'),
                'graph': data.get('graph', {'nodes': [], 'edges': [], 'legend': {}})
            })
            
        except Exception as e:
            import traceback
            return web.json_response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    def _parse_window_string(self, window_str):
        """Parse window string (5m, 15m, 1h, 6h, 24h, 7d) to minutes."""
        window_map = {
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '6h': 360,
            '24h': 1440,
            '7d': 10080
        }
        return window_map.get(window_str, 15)

