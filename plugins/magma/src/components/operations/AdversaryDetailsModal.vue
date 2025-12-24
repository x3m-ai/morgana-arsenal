<script setup>
import { ref, computed, onMounted } from 'vue';
import { inject } from 'vue';

const props = defineProps({
  operation: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['close']);

const $api = inject('$api');
const adversaryDetails = ref(null);
const abilities = ref([]);
const loading = ref(true);

onMounted(async () => {
  await loadAdversaryDetails();
});

async function loadAdversaryDetails() {
  try {
    loading.value = true;
    
    console.log('Loading adversary for operation:', props.operation);
    console.log('Operation has adversary?', !!props.operation.adversary);
    console.log('Adversary value:', props.operation.adversary);
    
    // Check if operation has adversary
    if (!props.operation.adversary) {
      console.error('No adversary in operation:', props.operation);
      loading.value = false;
      return;
    }
    
    // Get adversary ID
    let adversaryId = null;
    if (typeof props.operation.adversary === 'string') {
      adversaryId = props.operation.adversary;
    } else if (props.operation.adversary.adversary_id) {
      adversaryId = props.operation.adversary.adversary_id;
    } else if (props.operation.adversary.id) {
      adversaryId = props.operation.adversary.id;
    }
    
    if (!adversaryId) {
      console.error('Could not find adversary ID in:', props.operation.adversary);
      loading.value = false;
      return;
    }
    
    console.log('Loading adversary with ID:', adversaryId);
    
    // Get full adversary details
    const adversaryResponse = await $api.get(`/api/v2/adversaries/${adversaryId}`);
    console.log('Adversary loaded:', adversaryResponse);
    adversaryDetails.value = adversaryResponse.data;
    
    // Load all abilities that are part of this adversary
    if (adversaryDetails.value.atomic_ordering && adversaryDetails.value.atomic_ordering.length > 0) {
      const abilitiesResponse = await $api.get('/api/v2/abilities');
      const allAbilities = abilitiesResponse.data;
      
      // Sort abilities according to atomic_ordering to preserve the original order
      abilities.value = adversaryDetails.value.atomic_ordering
        .map(abilityId => allAbilities.find(ab => ab.ability_id === abilityId))
        .filter(ab => ab !== undefined);
      
      console.log('Abilities sorted by atomic_ordering:', abilities.value.map(a => a.name));
    }
    
  } catch (error) {
    console.error('Error loading adversary details:', error);
  } finally {
    loading.value = false;
  }
}

const groupedByTactic = computed(() => {
  if (!abilities.value || abilities.value.length === 0) return {};
  
  const grouped = {};
  abilities.value.forEach(ability => {
    const tactic = ability.tactic || 'other';
    if (!grouped[tactic]) {
      grouped[tactic] = [];
    }
    grouped[tactic].push(ability);
  });
  
  return grouped;
});

const sortedTactics = computed(() => {
  // Preserve the order of tactics as they appear in the abilities array
  const tacticsInOrder = [];
  abilities.value.forEach(ability => {
    const tactic = ability.tactic || 'other';
    if (!tacticsInOrder.includes(tactic)) {
      tacticsInOrder.push(tactic);
    }
  });
  return tacticsInOrder;
});

function getTacticColor(tactic) {
  const colors = {
    'reconnaissance': 'is-info',
    'resource-development': 'is-primary',
    'initial-access': 'is-link',
    'execution': 'is-success',
    'persistence': 'is-warning',
    'privilege-escalation': 'is-danger',
    'defense-evasion': 'is-info',
    'credential-access': 'is-warning',
    'discovery': 'is-success',
    'lateral-movement': 'is-link',
    'collection': 'is-primary',
    'command-and-control': 'is-danger',
    'exfiltration': 'is-warning',
    'impact': 'is-danger',
    'other': 'is-light'
  };
  return colors[tactic] || 'is-light';
}
</script>

<template lang="pug">
.modal.is-active(style="z-index: 9999 !important;")
  .modal-background(@click="emit('close')")
  .modal-card(style="width: 90%; max-width: 1200px; z-index: 10000 !important;")
    header.modal-card-head
      p.modal-card-title
        span.icon.mr-2
          font-awesome-icon(icon="fas fa-mask")
        | Adversary Details
      button.delete(aria-label="close" @click="emit('close')")
    
    section.modal-card-body(v-if="loading" style="text-align: center; padding: 3rem;")
      span.icon.is-large
        font-awesome-icon(icon="fas fa-spinner" spin style="font-size: 3rem;")
      p.mt-3 Loading adversary details...
    
    section.modal-card-body(v-else-if="!adversaryDetails")
      .notification.is-warning
        | No adversary associated with this operation
    
    section.modal-card-body(v-else style="max-height: 70vh; overflow-y: auto;")
      //- Adversary Header
      .box.has-background-dark.has-text-white.mb-4
        .columns.is-vcentered
          .column
            h3.title.is-4.has-text-white.mb-2
              span.icon.mr-2
                font-awesome-icon(icon="fas fa-user-secret")
              | {{ adversaryDetails.name }}
            p.subtitle.is-6.has-text-grey-lighter(v-if="adversaryDetails.description") {{ adversaryDetails.description }}
            p.subtitle.is-6.has-text-grey-lighter(v-else style="font-style: italic;") No description available
          .column.is-narrow
            .tags
              span.tag.is-large.is-primary
                span.icon
                  font-awesome-icon(icon="fas fa-crosshairs")
                span {{ abilities.length }} Abilities
              span.tag.is-large.is-info
                span.icon
                  font-awesome-icon(icon="fas fa-layer-group")
                span {{ Object.keys(groupedByTactic).length }} Tactics
      
      //- Operation Context
      .box.mb-4(style="background-color: #363636; color: #f5f5f5;")
        .is-flex.is-align-items-center.is-justify-content-space-between
          div
            strong.mr-2 Used in Operation:
            span.tag.is-medium.is-link {{ operation.name }}
          div
            strong.mr-2 State:
            span.tag.is-medium(:class="operation.state === 'running' ? 'is-success' : 'is-warning'") {{ operation.state }}
      
      //- No Abilities Message
      .notification.is-info(v-if="abilities.length === 0")
        p
          span.icon
            font-awesome-icon(icon="fas fa-info-circle")
          | This adversary has no abilities configured yet
      
      //- Abilities grouped by Tactic
      div(v-else)
        .mb-5(v-for="tactic in sortedTactics" :key="tactic")
          h4.title.is-5.mb-3
            span.tag.is-medium.mr-2(:class="getTacticColor(tactic)")
              span.icon.is-small
                font-awesome-icon(icon="fas fa-chess-knight")
              span {{ tactic.toUpperCase() }}
            span.has-text-grey ({{ groupedByTactic[tactic].length }} abilities)
          
          .table-container
            table.table.is-fullwidth.is-hoverable.is-striped
              thead
                tr
                  th(style="width: 120px;") Technique ID
                  th Ability Name
                  th(style="width: 150px;") Platforms
                  th(style="width: 100px; text-align: center;") Executors
              tbody
                tr(v-for="ability in groupedByTactic[tactic]" :key="ability.ability_id")
                  td
                    span.tag.is-link.is-light(style="font-family: monospace;") {{ ability.technique_id || 'N/A' }}
                  td
                    strong {{ ability.name }}
                    p.is-size-7(v-if="ability.description" style="margin-top: 4px; color: #666;") {{ ability.description.substring(0, 120) }}{{ ability.description.length > 120 ? '...' : '' }}
                  td
                    span.tag.is-small.is-info.mr-1(v-for="executor in ability.executors" :key="executor.platform") {{ executor.platform }}
                  td.has-text-centered
                    span.tag.is-small {{ ability.executors?.length || 0 }}
    
    footer.modal-card-foot.is-justify-content-flex-end
      button.button(@click="emit('close')") Close
</template>

<style scoped>
.modal-card-body {
  background-color: #2b2b2b;
  color: #f5f5f5;
}

.modal-card-head {
  background-color: #363636;
  color: white;
}

.modal-card-foot {
  background-color: #363636;
  border-top: 1px solid #4a4a4a;
}

.table-container {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.table {
  background-color: #363636;
}

.table thead th {
  background-color: #1a1a1a;
  color: white;
  border: none;
  font-weight: 600;
}

.table tbody tr {
  background-color: #2b2b2b;
}

.table tbody tr:hover {
  background-color: #404040;
}

.table tbody td {
  color: #f5f5f5;
  border-color: #4a4a4a;
}

.table tbody td strong {
  color: #ffffff;
}

.table tbody td p {
  color: #b5b5b5 !important;
}

.notification.is-info {
  background-color: #2b5278;
  color: #ffffff;
}
</style>
