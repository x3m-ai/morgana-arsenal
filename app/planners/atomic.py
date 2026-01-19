class LogicalPlanner:

    def __init__(self, operation, planning_svc, stopping_conditions=()):
        self.operation = operation
        self.planning_svc = planning_svc
        self.stopping_conditions = stopping_conditions
        self.stopping_condition_met = False
        self.state_machine = ['atomic']
        self.next_bucket = 'atomic'   # repeat this bucket until we run out of links.

    async def execute(self):
        await self.planning_svc.execute_planner(self)

    async def atomic(self):
        links_to_use = []

        self.planning_svc.log.debug('[ATOMIC] Operation %s: starting atomic planner for %d agents' % (self.operation.name, len(self.operation.agents)))
        
        # Get the first available link for each agent (make sure we maintain the order).
        for agent in self.operation.agents:
            possible_agent_links = await self._get_links(agent=agent)
            self.planning_svc.log.debug('[ATOMIC] Agent %s: found %d possible links' % (agent.paw, len(possible_agent_links)))
            next_link = await self._get_next_atomic_link(possible_agent_links)
            if next_link:
                self.planning_svc.log.debug('[ATOMIC] Agent %s: selected link with ability %s (status will be %d)' % (agent.paw, next_link.ability.name, self.operation.link_status()))
                links_to_use.append(await self.operation.apply(next_link))
            else:
                self.planning_svc.log.debug('[ATOMIC] Agent %s: no next link available' % agent.paw)

        if links_to_use:
            self.planning_svc.log.debug('[ATOMIC] Operation %s: applying %d links' % (self.operation.name, len(links_to_use)))
            # Each agent will run the next available step.
            await self.operation.wait_for_links_completion(links_to_use)
        else:
            # No more links to run.
            self.planning_svc.log.debug('[ATOMIC] Operation %s: no more links, stopping planner' % self.operation.name)
            self.next_bucket = None

    async def _get_links(self, agent=None):
        return await self.planning_svc.get_links(operation=self.operation, agent=agent)

    # Given list of links, returns the link that appears first in the adversary's atomic ordering.
    async def _get_next_atomic_link(self, links):
        abil_id_to_link = dict()
        for link in links:
            abil_id_to_link[link.ability.ability_id] = link
        candidate_ids = set(abil_id_to_link.keys())
        for ab_id in self.operation.adversary.atomic_ordering:
            if ab_id in candidate_ids:
                return abil_id_to_link[ab_id]
