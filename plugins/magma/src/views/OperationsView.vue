<script setup>
import {
  inject,
  ref,
  onMounted,
  onBeforeUnmount,
  computed,
  watch,
  reactive,
} from "vue";
import { storeToRefs } from "pinia";
import { toast } from "bulma-toast";

//Graph imports
import Graph from "@/components/operations/Graph.vue";

import OutputModal from "@/components/operations/OutputModal.vue";
import CreateModal from "@/components/operations/CreateModal.vue";
import EditModal from "@/components/operations/EditModal.vue";
import DeleteModal from "@/components/operations/DeleteModal.vue";
import DetailsModal from "@/components/operations/DetailsModal.vue";
import DownloadModal from "@/components/operations/DownloadModal.vue";
import AgentDetailsModal from "@/components/operations/AgentDetailsModal.vue";
import CommandPopup from "@/components/operations/CommandPopup.vue";
import OutputPopup from "@/components/operations/OutputPopup.vue";
import AddPotentialLinkModal from "@/components/operations/AddPotentialLinkModal.vue";
import ManualCommand from "@/components/operations/ManualCommand.vue";
import FiltersModal from "@/components/operations/FiltersModal.vue";
import AssignMembersModal from "@/components/operations/AssignMembersModal.vue";
import AdversaryDetailsModal from "@/components/operations/AdversaryDetailsModal.vue";
import { useOperationStore } from "@/stores/operationStore";
import { useAgentStore } from "@/stores/agentStore";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import { useCoreStore } from "@/stores/coreStore";
import {
  getHumanFriendlyTimeISO8601,
  b64DecodeUnicode,
  getReadableTime,
} from "@/utils/utils";
import { getLinkStatus } from "@/utils/operationUtil.js";

const $api = inject("$api");

const coreDisplayStore = useCoreDisplayStore();
const operationStore = useOperationStore();
const agentStore = useAgentStore();
const coreStore = useCoreStore();
const { modals } = storeToRefs(coreDisplayStore);

let updateInterval = ref();
let operationsListUpdateInterval = ref();
let showPotentialLinkModal = ref(false);
let selectedOutputLink = ref(null);
let operationSearchQuery = ref("");
const redTeamMembers = ref([]);
const showAssignModal = ref(false);
const selectedOperationForAssign = ref(null);
const showUnassigned = ref(false);
const showEmptyLinks = ref(false);
const showAdversaryModal = ref(false);
const selectedOperationForAdversary = ref(null);
const showEditModal = ref(false);
const selectedOperationForEdit = ref(null);
const showDeleteAllOpsModal = ref(false);
const isDeletingOps = ref(false);

// Resizable splitter
let topPanelHeight = ref(350);
let isResizing = ref(false);
let startY = ref(0);
let startHeight = ref(0);

function startResize(e) {
    isResizing.value = true;
    startY.value = e.clientY;
    startHeight.value = topPanelHeight.value;
    document.addEventListener('mousemove', onResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
}

function onResize(e) {
    if (!isResizing.value) return;
    const delta = e.clientY - startY.value;
    const newHeight = startHeight.value + delta;
    // Min 150px, max 600px
    topPanelHeight.value = Math.max(150, Math.min(600, newHeight));
}

function stopResize() {
    isResizing.value = false;
    document.removeEventListener('mousemove', onResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
}

// Delete all operations with confirmation
async function confirmDeleteAllOperations() {
    const opCount = Object.keys(operationStore.operations).length;
    if (opCount === 0) {
        toast({
            message: "No operations to delete",
            type: "is-warning",
            dismissible: true,
            pauseOnHover: true,
            duration: 3000,
            position: "bottom-right",
        });
        return;
    }
    showDeleteAllOpsModal.value = true;
}

async function executeDeleteAllOperations() {
    isDeletingOps.value = true;
    try {
        const result = await operationStore.deleteAllOperations($api);
        showDeleteAllOpsModal.value = false;
        toast({
            message: `Deleted ${result.deleted} operations${result.errors > 0 ? ` (${result.errors} errors)` : ''}`,
            type: result.errors > 0 ? "is-warning" : "is-success",
            dismissible: true,
            pauseOnHover: true,
            duration: 3000,
            position: "bottom-right",
        });
    } catch (error) {
        toast({
            message: "Error deleting operations: " + error.message,
            type: "is-danger",
            dismissible: true,
            pauseOnHover: true,
            duration: 5000,
            position: "bottom-right",
        });
    } finally {
        isDeletingOps.value = false;
    }
}

const operationAssignments = computed(() => {
  return JSON.parse(localStorage.getItem('operation_assignments') || '{}');
});

// Compute TCodes (all technique IDs) for each operation from its links
const operationsWithTCodes = computed(() => {
  let ops = Object.values(operationStore.operations);
  
  // Apply filters
  if (showUnassigned.value) {
    ops = ops.filter(op => {
      const assigned = operationAssignments.value[op.id];
      return !assigned || (Array.isArray(assigned) && assigned.length === 0);
    });
  }
  if (showEmptyLinks.value) {
    ops = ops.filter(op => !op.chain || op.chain.length === 0);
  }
  
  return ops.map(operation => {
    const tcodes = [];
    if (operation.chain && Array.isArray(operation.chain)) {
      for (const link of operation.chain) {
        if (link.ability && link.ability.technique_id) {
          tcodes.push(link.ability.technique_id);
        }
      }
    }
    return {
      ...operation,
      tcodes: tcodes.join(', '),
      tcodesArray: tcodes
    };
  });
});

// START SORTING AND FILTERING
const tableFilter = reactive({
  sortBy: "",
  sortOrder: "",
  filters: {
    decide: [],
    status: [],
    abilityName: [],
    paw: [],
    tactic: [],
    pid: [],
    host: [],
  },
});
const possibleFilters = reactive({
  abilityName: [],
  tactic: [],
  pid: [],
  paw: [],
  host: [],
});
const updatePossibleFilters = (chain) => {
  possibleFilters.abilityName.splice(0);
  possibleFilters.tactic.splice(0);
  possibleFilters.pid.splice(0);
  possibleFilters.paw.splice(0);
  possibleFilters.host.splice(0);

  chain.forEach((chain) => {
    if (!possibleFilters.abilityName.includes(chain.ability.name)) {
      possibleFilters.abilityName.push(chain.ability.name);
    }
    if (!possibleFilters.tactic.includes(chain.ability.tactic)) {
      possibleFilters.tactic.push(chain.ability.tactic);
    }
    if (!possibleFilters.paw.includes(chain.paw)) {
      possibleFilters.paw.push(chain.paw);
    }
    if (!possibleFilters.pid.includes(chain.pid)) {
      possibleFilters.pid.push(chain.pid);
    }
    if (!possibleFilters.host.includes(chain.host)) {
      possibleFilters.host.push(chain.host);
    }
  });
};

const filteredChain = computed(() => {
  let result = [...operationStore.currentOperation.chain];
  updatePossibleFilters(result);
  // Filter the data
  if (tableFilter.filters) {
    for (let property in tableFilter.filters) {
      if (tableFilter.filters[property].length === 0) {
        continue;
      }
      const filterValues = tableFilter.filters[property];
      if (filterValues && filterValues.length > 0) {
        result = result.filter((row) => {
          if (property === "abilityName") {
            return filterValues.includes(row.ability.name);
          } else if (property === "tactic") {
            return filterValues.includes(row.ability.tactic);
          }
          return filterValues.includes(row[property].toString());
        });
      }
    }
  }

  // Sort the data
  if (tableFilter.sortBy) {
    const sortOrder = tableFilter.sortOrder === "ASC" ? 1 : -1;
    if (tableFilter.sortBy == "abilityName") {
      result.sort((a, b) => {
        if (a.ability.name < b.ability.name) return -1 * sortOrder;
        if (a.ability.name > b.ability.name) return 1 * sortOrder;
        return 0;
      });
      return result;
    } else if (tableFilter.sortBy == "tactic") {
      result.sort((a, b) => {
        if (a.ability.tactic < b.ability.tactic) return -1 * sortOrder;
        if (a.ability.tactic > b.ability.tactic) return 1 * sortOrder;
        return 0;
      });
      return result;
    }
    result.sort((a, b) => {
      if (a[tableFilter.sortBy] < b[tableFilter.sortBy]) return -1 * sortOrder;
      if (a[tableFilter.sortBy] > b[tableFilter.sortBy]) return 1 * sortOrder;
      return 0;
    });
  }
  return result;
});

const handleTableSort = (property) => {
  if (tableFilter.sortBy === property) {
    if (tableFilter.sortOrder == "ASC") {
      tableFilter.sortOrder = "DESC";
    } else {
      tableFilter.sortOrder = "";
      tableFilter.sortBy = "";
    }
  } else {
    tableFilter.sortBy = property;
    tableFilter.sortOrder = "ASC";
  }
};

const getSortIconColor = (property, direction) => {
  if (tableFilter.sortBy === property) {
    if (tableFilter.sortOrder == "ASC" && direction === "up") {
      return "#fff";
    } else if (tableFilter.sortOrder == "DESC" && direction === "down") {
      return "#fff";
    }
  }
  return "grey";
};
//END SORTING AND FILTERING

onMounted(async () => {
  await operationStore.getOperations($api);
  await operationStore.getAdversaries($api);
  await agentStore.updateAgents($api);
  agentStore.updateAgentGroups();
  selectOperation();
  
  // Load red team members from localStorage
  const stored = localStorage.getItem('redteam_hackers');
  if (stored) {
    try {
      redTeamMembers.value = JSON.parse(stored);
      console.log('Loaded red team members:', redTeamMembers.value);
    } catch (e) {
      console.error('Error loading team members', e);
    }
  } else {
    console.warn('No red team members found in localStorage');
  }
  
  operationsListUpdateInterval.value = setInterval(async () => {
    await operationStore.getOperations($api);
    // Reload team members periodically to catch updates
    const freshStored = localStorage.getItem('redteam_hackers');
    if (freshStored) {
      try {
        redTeamMembers.value = JSON.parse(freshStored);
      } catch (e) {
        // Silent fail on periodic refresh
      }
    }
  }, 3000);
});

onBeforeUnmount(() => {
  if (updateInterval) clearInterval(updateInterval);
  if (operationsListUpdateInterval.value) clearInterval(operationsListUpdateInterval.value);
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
});

const resetFilter = () => {
  tableFilter.sortBy = "";
  tableFilter.sortOrder = "";
  tableFilter.filters.decide = [];
  tableFilter.filters.status = [];
  tableFilter.filters.abilityName = [];
  tableFilter.filters.paw = [];
  tableFilter.filters.tactic = [];
  tableFilter.filters.host = [];
  tableFilter.filters.pid = [];
};

function selectOperation() {
  if (updateInterval) clearInterval(updateInterval);
  if (operationStore.selectedOperationID === "") return;
  resetFilter();
  updateInterval = setInterval(async () => {
    if (operationStore.selectedOperationID !== "" &&
        operationStore.operations[operationStore.selectedOperationID].state !== "finished")
    {
      await operationStore.getOperation($api, operationStore.selectedOperationID);
    } else {
      clearInterval(updateInterval);
    }
  }, "3000");
}

async function updateAuto(event) {
  // operationStore.operations[operationStore.selectedOperationID].autonomous = event.target.checked ? 1 : 0;
  await operationStore.updateOperation(
    $api,
    "autonomous",
    event.target.checked ? 1 : 0
  );
}

function isRerun() {
  return (
    operationStore.operations[operationStore.selectedOperationID].state ===
      "cleanup" ||
    operationStore.operations[operationStore.selectedOperationID].state ===
      "finished"
  );
}

function assignTeamMember(operationId, memberAka) {
  tempAssignments.value[operationId] = memberAka;
}

function saveAssignment(operationId) {
  const memberAka = tempAssignments.value[operationId];
  const assignments = JSON.parse(localStorage.getItem('operation_assignments') || '{}');
  
  // Remove this operation from any previous assignments
  Object.keys(assignments).forEach(opId => {
    if (opId === operationId) delete assignments[opId];
  });
  
  if (memberAka && memberAka !== '') {
    assignments[operationId] = memberAka;
    const hackers = JSON.parse(localStorage.getItem('redteam_hackers') || '[]');
    const hacker = hackers.find(h => h.aka === memberAka);
    if (hacker) {
      hacker.status = 'On Assignment';
      hacker.operationId = operationId;
      localStorage.setItem('redteam_hackers', JSON.stringify(hackers));
    }
  } else {
    // Unassign - reset hacker status
    const hackers = JSON.parse(localStorage.getItem('redteam_hackers') || '[]');
    const hacker = hackers.find(h => h.operationId === operationId);
    if (hacker) {
      hacker.status = 'Active';
      hacker.operationId = '';
      localStorage.setItem('redteam_hackers', JSON.stringify(hackers));
    }
  }
  
  localStorage.setItem('operation_assignments', JSON.stringify(assignments));
  delete tempAssignments.value[operationId];
}

function openAssignModal(operation) {
  selectedOperationForAssign.value = operation.id;
  
  // Reload team members from localStorage before opening modal
  const stored = localStorage.getItem('redteam_hackers');
  if (stored) {
    try {
      redTeamMembers.value = JSON.parse(stored);
      console.log('Reloaded members for assignment:', redTeamMembers.value);
    } catch (e) {
      console.error('Error reloading team members', e);
      redTeamMembers.value = [];
    }
  } else {
    console.warn('No members found in localStorage');
    redTeamMembers.value = [];
  }
  
  showAssignModal.value = true;
}

function openAdversaryModal(operation) {
  selectedOperationForAdversary.value = operation;
  showAdversaryModal.value = true;
}

function openEditModal(operation) {
  selectedOperationForEdit.value = operation;
  showEditModal.value = true;
}

// Force all paused links in operation to EXECUTE status
async function forceExecutePausedLinks(operation) {
  if (!operation || !operation.chain) return;
  
  // Find all paused links (status=-1)
  const pausedLinks = operation.chain.filter(link => link.status === -1);
  
  if (pausedLinks.length === 0) {
    toast({
      message: `No paused links to execute in operation "${operation.name}"`,
      type: "is-info",
      dismissible: true,
      pauseOnHover: true,
      duration: 3000,
      position: "bottom-right",
    });
    return;
  }
  
  try {
    let successCount = 0;
    let errorCount = 0;
    
    // Force each paused link to EXECUTE status (-3)
    for (const link of pausedLinks) {
      try {
        await $api.patch(`/api/v2/operations/${operation.id}/links/${link.id}`, {
          status: -3  // EXECUTE
        });
        successCount++;
      } catch (error) {
        console.error(`Failed to force execute link ${link.id}:`, error);
        errorCount++;
      }
    }
    
    if (successCount > 0) {
      // Refresh operation to show updated links
      await operationStore.getOperations($api);
      
      toast({
        message: `Forced ${successCount} paused link(s) to EXECUTE${errorCount > 0 ? ` (${errorCount} errors)` : ''}`,
        type: errorCount > 0 ? "is-warning" : "is-success",
        dismissible: true,
        pauseOnHover: true,
        duration: 4000,
        position: "bottom-right",
      });
    }
  } catch (error) {
    toast({
      message: `Error forcing links: ${error.message}`,
      type: "is-danger",
      dismissible: true,
      pauseOnHover: true,
      duration: 4000,
      position: "bottom-right",
    });
  }
}

async function updateOperationComments(operation) {
  try {
    await $api.patch(`/api/v2/operations/${operation.id}`, {
      comments: operation.comments || ''
    });
    console.log('Updated comments for operation:', operation.name);
  } catch (error) {
    console.error('Error updating operation comments:', error);
  }
}

function updateOperationAssignments(selectedAkas) {
  const assignments = JSON.parse(localStorage.getItem('operation_assignments') || '{}');
  
  if (selectedAkas.length > 0) {
    assignments[selectedOperationForAssign.value] = selectedAkas;
  } else {
    delete assignments[selectedOperationForAssign.value];
  }
  
  // Update member statuses
  const hackers = JSON.parse(localStorage.getItem('redteam_hackers') || '[]');
  hackers.forEach(hacker => {
    const isAssignedToAnyOp = Object.values(assignments).some(akas => 
      Array.isArray(akas) && akas.includes(hacker.aka)
    );
    if (isAssignedToAnyOp && hacker.status === 'Active') {
      hacker.status = 'On Assignment';
    } else if (!isAssignedToAnyOp && hacker.status === 'On Assignment') {
      hacker.status = 'Active';
    }
  });
  
  localStorage.setItem('operation_assignments', JSON.stringify(assignments));
  localStorage.setItem('redteam_hackers', JSON.stringify(hackers));
}

function displayManualCommand() {
  modals.value.operations.showAddManualCommand = true;
  setTimeout(() => {
    document.getElementById("manual-input-command").scrollIntoView({
      behavior: "smooth",
    });
  }, 2);
}

async function addPotentialLinks(links) {
  try {
    if (operationStore.currentOperation.state !== "running") {
      toast({
        message:
          "Operation is currently paused, and new links might not be added.",
        type: "is-warning",
        dismissible: true,
        pauseOnHover: true,
        duration: 2000,
        position: "bottom-right",
      });
    }
    await operationStore.addPotentialLinks($api, links);
    showPotentialLinkModal.value = false;
  } catch (error) {
    console.error("Error adding potential links", error);
  }
}

function highlightLink(linkElement) {
  linkElement.classList.add("highlight-link");
  setTimeout(() => {
    linkElement.classList.remove("highlight-link");
  }, 2000);
}

function handleViewOutput(link) {
  selectedOutputLink.value = link;
  modals.value.operations.showOutput = true;
}

function getOperationDisplayState(op) {
  if (!op || !op.chain) return op?.state || 'unknown';
  
  // Check if operation has any links
  if (op.chain.length === 0) return op.state;
  
  // Count link statuses
  let hasErrors = false;
  let hasRunning = false;
  let completedCount = 0;
  let totalCount = op.chain.length;
  
  for (const link of op.chain) {
    const status = link.status;
    
    // Status: 0=success, 1=failed, -1=paused, -2=discarded, -3=collect, -4=untrusted, -5=visible, 124=timeout
    if (status === 1 || status === 124) {
      hasErrors = true;
    } else if (status === 0) {
      completedCount++;
    } else if (status === -1 || status === undefined || status === null) {
      hasRunning = true;
    }
  }
  
  // Determine display state
  if (hasErrors) {
    return 'with errors';
  } else if (completedCount === totalCount) {
    return 'completed';
  } else if (hasRunning || completedCount < totalCount) {
    return 'running';
  }
  
  return op.state;
}

function getStateClass(state) {
  const normalizedState = state?.toLowerCase();
  if (normalizedState === 'completed') return 'is-success';
  if (normalizedState === 'running') return 'is-info';
  if (normalizedState === 'with errors') return 'is-danger';
  if (normalizedState === 'paused') return 'is-warning';
  if (normalizedState === 'cleanup') return 'is-warning';
  return 'is-light';
}
</script>

<template lang="pug">
//- Operations Header
.columns.mb-0
    .column.m-0.content
        .is-flex.is-align-items-center
            h2.m-0.mr-3 Operations
            span.tag.is-dark.is-medium {{ Object.keys(operationStore.operations).length }} total
            span.tag.is-info.is-medium.ml-2(v-if="operationsWithTCodes.length !== Object.keys(operationStore.operations).length") {{ operationsWithTCodes.length }} filtered
hr.mt-2

//- Operations Table
.box.mb-4
    .is-flex.is-justify-content-space-between.mb-3
        .field.has-addons(style="width: 400px")
            .control.has-icons-left.is-expanded
                input.input.is-small(type="text" placeholder="Search operations..." v-model="operationSearchQuery")
                span.icon.is-small.is-left
                    font-awesome-icon(icon="fas fa-search")
        .field.is-grouped
            .control
                label.checkbox.mr-3
                    input(type="checkbox" v-model="showUnassigned")
                    span.ml-1 Unassigned
            .control
                label.checkbox.mr-3
                    input(type="checkbox" v-model="showEmptyLinks")
                    span.ml-1 No Links
        button.button.is-primary.is-small(@click="modals.operations.showCreate = true" type="button")
            span.icon
                font-awesome-icon(icon="fas fa-plus")
            span New Operation
        button.button.is-danger.is-small.ml-2(@click="confirmDeleteAllOperations" type="button" :disabled="Object.keys(operationStore.operations).length === 0")
            span.icon
                font-awesome-icon(icon="fas fa-trash")
            span Delete All
    
    .table-container(:style="{ maxHeight: topPanelHeight + 'px', overflowY: 'auto', border: '1px solid #dbdbdb', borderRadius: '4px' }")
        table.table.is-fullwidth.is-hoverable.is-striped(style="margin-bottom: 0;")
        thead
            tr(style="background-color: #363636; color: white;")
                th(style="color: white; min-width: 140px;") Operation Name
                th(style="color: white; min-width: 90px;") State
                th(style="color: white; min-width: 160px;") Adversary
                th(style="color: white; min-width: 70px; text-align: center;") Agents
                th(style="color: white; min-width: 70px; text-align: center;") Links
                th(style="color: white; min-width: 200px;") TCodes
                th(style="color: white; min-width: 200px;") Comments
                th(style="color: white; min-width: 280px;") Assigned Team
                th(style="color: white; min-width: 120px; padding-left: 20px;") Started
                th(style="color: white; min-width: 200px;" class="has-text-centered") Actions
        tbody
            tr(v-if="Object.keys(operationStore.operations).length === 0")
                td(colspan="10" class="has-text-centered has-text-grey-light is-italic") No operations yet. Create one to get started.
            tr(
                v-for="op in operationsWithTCodes.filter(o => !operationSearchQuery || o.name.toLowerCase().includes(operationSearchQuery.toLowerCase()))" 
                :key="op.id"
                :class="{ 'is-selected': operationStore.selectedOperationID === op.id }"
                style="cursor: pointer;"
                @click="operationStore.selectedOperationID = op.id; selectOperation();"
            )
                td
                    strong {{ op.name }}
                td
                    span.tag(:class="getStateClass(getOperationDisplayState(op))") {{ getOperationDisplayState(op) }}
                td {{ op.adversary?.name || 'N/A' }}
                td
                    span.tag.is-info.is-light {{ op.host_group?.length || 0 }}
                td
                    span.tag.is-link.is-light {{ op.chain?.length || 0 }}
                td.is-size-7(style="font-family: monospace; color: #00d1b2;") {{ op.tcodes || 'No TTPs' }}
                td.is-size-7(style="color: #555; max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="op.comments") {{ op.comments || '-' }}
                td(@click.stop)
                    .is-flex.is-align-items-center.is-justify-content-space-between
                        div(v-if="operationAssignments[op.id] && operationAssignments[op.id].length > 0" style="flex: 1;")
                            span.tag.is-info.is-light.mr-1(v-for="aka in operationAssignments[op.id]" :key="aka" style="margin-bottom: 2px;") {{ aka }}
                        span(v-else style="color: #999; font-style: italic;") No members
                        button.button.is-small.is-primary(@click="openAssignModal(op)" title="Assign members") Assign
                td.is-size-7(style="padding-left: 20px;") {{ getHumanFriendlyTimeISO8601(op.start) }}
                td.has-text-centered
                    .buttons.is-centered
                        button.button.is-small.is-warning(@click.stop="openEditModal(op)" title="Edit Operation")
                            span.icon.is-small
                                font-awesome-icon(icon="pencil-alt" style="color: white;")
                        button.button.is-small.is-link(@click.stop="openAdversaryModal(op)" title="Show Adversary")
                            span Adversary
                        button.button.is-small.is-primary(v-if="op.chain && op.chain.some(l => l.status === -1)" @click.stop="forceExecutePausedLinks(op)" title="Force execute paused links")
                            span.icon.is-small
                                font-awesome-icon(icon="fas fa-bolt" style="color: white;")
                            span.is-hidden-mobile Execute
                        button.button.is-small.is-info(@click.stop="operationStore.selectedOperationID = op.id; selectOperation();" title="View Details")
                            span.icon.is-small
                                font-awesome-icon(icon="fas fa-search" style="color: white;")
                        button.button.is-small.is-success(@click.stop="operationStore.selectedOperationID = op.id; modals.operations.showDownload = true" type="button" title="Download Report")
                            span.icon.is-small
                                font-awesome-icon(icon="fas fa-download" style="color: white;")
                        button.button.is-small.is-danger(@click.stop="operationStore.selectedOperationID = op.id; modals.operations.showDelete = true" type="button" title="Delete Operation")
                            span.icon.is-small
                                font-awesome-icon(icon="fas fa-trash" style="color: white;")

//- Resizable Divider
.resizable-divider(@mousedown="startResize" :class="{ 'is-resizing': isResizing }")
    .divider-line
    .divider-handle
        font-awesome-icon(icon="fas fa-grip-lines")

Graph(@scroll="highlightLink")
//- Control Panel
.control-panel.p-0.mb-4(v-if="operationStore.selectedOperationID")
    .columns.m-0.p-1
        .column.is-4.pt-0.pb-0.is-flex
            .buttons
                button.button(v-if="operationStore.isOperationRunning()" @click="displayManualCommand()")
                    span.icon
                        font-awesome-icon.fa(icon="fas fa-plus")
                    span Manual Command
                button.button(v-if="operationStore.isOperationRunning()" @click="showPotentialLinkModal = true")
                    span.icon
                        font-awesome-icon.fa(icon="fas fa-plus")
                    span Potential Link
                button.button(@click="modals.operations.showDetails = true" type="button") Operation Details
                button.button(@click="modals.operations.showFilters = true" type="button")
                  span.icon
                    font-awesome-icon(icon="fas fa-filter")
                  span Filters
        .column.is-4.pt-0.pb-0
            span.has-text-success.is-flex.is-justify-content-center {{ operationStore.operations[operationStore.selectedOperationID].state }}
            .is-flex.is-justify-content-center.is-align-items-center.pb-2
                a.icon.is-medium.ml-3.mr-3(v-if="!isRerun()" @click="operationStore.updateOperation($api, 'state', 'cleanup')" v-tooltip="'Stop'")
                    font-awesome-icon.fa-2x(icon="fas fa-stop")
                a.icon.is-medium.ml-3.mr-3(v-if="!isRerun() && operationStore.operations[operationStore.selectedOperationID].state === 'paused' || operationStore.operations[operationStore.selectedOperationID].state === 'run_one_link'" @click="operationStore.updateOperation($api, 'state', 'running')" v-tooltip="'Play'")
                    font-awesome-icon.fa-2x(icon="fas fa-play")
                a.icon.is-medium.ml-3.mr-3(v-else v-if="!isRerun()" @click="operationStore.updateOperation($api, 'state', 'paused')" v-tooltip="'Pause'")
                    font-awesome-icon.fa-2x(icon="fas fa-pause")
                a.icon.is-medium.ml-3.mr-3(v-if ="!isRerun()" @click="operationStore.updateOperation($api, 'state', 'run_one_link')" v-tooltip="'Run one link'")
                    font-awesome-icon.fa-2x(icon="fas fa-play")
                    span.mt-5 1
                a.icon.is-medium.ml-3.mr-3(v-if="isRerun()" @click="operationStore.rerunOperation($api)" v-tooltip="'Re-run Operation'")
                    font-awesome-icon.fa-2x(icon="fas fa-redo")
        .column.is-4.is-flex.is-justify-content-right.is-align-items-center.is-flex-wrap-wrap.pt-0.pb-0
            span.is-size-6 Obfuscator: 
            .control(v-if="operationStore.isOperationRunning()")
                .select.ml-1.mr-4
                    select(v-model="operationStore.operations[operationStore.selectedOperationID].obfuscator" @change="operationStore.updateOperation($api, 'obfuscator', operationStore.operations[operationStore.selectedOperationID].obfuscator)")
                        option(v-for="(obf, idx) in coreStore.obfuscators" :key="idx" :value="obf.name") {{ `${obf.name}` }}
            .control(v-else)
                .select.ml-1.mr-4
                    select(v-model="operationStore.operations[operationStore.selectedOperationID].obfuscator" :disabled="true")
                        option(v-for="(obf, idx) in coreStore.obfuscators" :key="idx" :value="obf.name") {{ `${obf.name}` }}
            .control(v-if="operationStore.isOperationRunning()")
                input.switch(
                    :checked="operationStore.operations[operationStore.selectedOperationID].autonomous === 1" 
                    id="switchManual" 
                    type="checkbox" 
                    @change="updateAuto($event)"
                )
                label.label(for="switchManual") {{ operationStore.operations[operationStore.selectedOperationID].autonomous ? 'Autonomous' : 'Manual' }} 
            .control(v-else)
                input.switch(
                    :checked="operationStore.operations[operationStore.selectedOperationID].autonomous === 1" 
                    :disabled="true"
                    id="switchManual" 
                    type="checkbox" 
                )
                label.label(for="switchManual") {{ operationStore.operations[operationStore.selectedOperationID].autonomous ? 'Autonomous' : 'Manual' }}
        
//- Table
table.table.is-fullwidth.is-narrow.is-striped.mb-8#link-table(v-if="operationStore.selectedOperationID")
    thead
        tr
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('decide')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Time Ran 
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('decide', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('decide', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('status')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Status
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('status', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('status', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('abilityName')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Ability Name
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('abilityName', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('abilityName', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('tactic')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Tactic
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('tactic', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('tactic', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-column.is-justify-content-center
              span.mt-2 Technique
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('agent')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Agent
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('agent', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('agent', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('host')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span Host
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('host', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('host', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-row.is-align-items-center.gap-5(@click="handleTableSort('pid')" :style="{ cursor: 'pointer', width: 'fit-content' }")
              span pid
              div.is-flex.is-flex-direction-column.is-justify-content-center
                span.icon.m-n5(:style="{ color: getSortIconColor('pid', 'up') }")
                  font-awesome-icon(icon="fas fa-angle-up")
                span.icon(:style="{ color: getSortIconColor('pid', 'down') }")
                  font-awesome-icon(icon="fas fa-angle-down")
          th
            div.is-flex.is-flex-direction-column.is-justify-content-center
              span.mt-2 Link Command 
          th
            div.is-flex.is-flex-direction-column.is-justify-content-center
              span.mt-2 Link Output 
          th
    tbody
        tr(v-for="(link, idx) in filteredChain" :key="link.id" :id="`link-${idx}`")
            td {{ getReadableTime(link.decide) }}
            td
                .is-flex.is-align-items-center(style="border-bottom-width: 0px !important")
                    .link-status.mr-2(:style="{ color: getLinkStatus(link).color}") 
                    span(:style="{ color: getLinkStatus(link).color}") {{ getLinkStatus(link).text }}
            td {{ link.ability.name }}
            td {{ link.ability.tactic }}
            td.is-size-7(style="font-family: monospace; color: #00d1b2;") {{ link.ability.technique_id || 'N/A' }}
            td {{ link.paw }}
            td {{ link.host }}
            td {{ link.pid ? link.pid : "N/A" }}
            td
                //- button.button(v-tooltip="b64DecodeUnicode(link.command)" @click="handleViewCommand(link)") View Command
                .dropdown.is-hoverable
                    .dropdown-trigger
                        button.button(aria-haspopup="true" aria-controls="dropdown-menu")
                          span View Command
                          span.icon.is-small(v-if="link.cleanup != 0")
                            font-awesome-icon(icon="fas fa-broom")
                    .dropdown-menu.command-popup(role="menu")
                        .dropdown-content
                            CommandPopup(:link="link")
            td
                //- button.button(v-if="link.output === 'True'" @click="handleViewOutput(link)") View Output
                .dropdown.is-hoverable(v-if="link.output === 'True'")
                    .dropdown-trigger
                        button.button(aria-haspopup="true" aria-controls="dropdown-menu" @click="handleViewOutput(link)") View Output
                    .dropdown-menu.command-popup(role="menu")
                        .dropdown-content
                            OutputPopup(:link="link")
                span(v-else) No output
            td(v-if="operationStore.currentOperation.state === 'running'")
                a.icon(@click="operationStore.rerunLink($api, link)" v-tooltip="'Re-run Link'")
                    font-awesome-icon(icon="fas fa-redo")
                a.icon.ml-2(@click="operationStore.skipLink($api, link)" v-tooltip="'Skip Link'" style="color: #f39c12;")
                    font-awesome-icon(icon="fas fa-forward")
        ManualCommand(v-if="modals.operations.showAddManualCommand")
                
//- Modals
CreateModal(:selectInterval="selectOperation")
EditModal(
    v-if="showEditModal && selectedOperationForEdit"
    :operation="selectedOperationForEdit"
    :selectInterval="selectOperation"
    @close="showEditModal = false; selectedOperationForEdit = null")
DeleteModal
DetailsModal
DownloadModal
AgentDetailsModal
AddPotentialLinkModal(
    :active="showPotentialLinkModal" 
    :operation="operationStore.operations[operationStore.selectedOperationID]"
    @select="addPotentialLinks" 
    @close="showPotentialLinkModal = false")
FiltersModal(:filters="tableFilter.filters" :possibleFilters="possibleFilters")
OutputModal(v-if="selectedOutputLink" :link="selectedOutputLink")
AssignMembersModal(
    :show="showAssignModal"
    :operationId="selectedOperationForAssign"
    :members="redTeamMembers"
    @close="showAssignModal = false"
    @update="updateOperationAssignments")

AdversaryDetailsModal(
    v-if="showAdversaryModal && selectedOperationForAdversary"
    :operation="selectedOperationForAdversary"
    @close="showAdversaryModal = false; selectedOperationForAdversary = null")

//- Delete All Operations Confirmation Modal
.modal(:class="{ 'is-active': showDeleteAllOpsModal }")
    .modal-background(@click="showDeleteAllOpsModal = false")
    .modal-card
        header.modal-card-head.has-background-danger
            p.modal-card-title.has-text-white
                span.icon.mr-2
                    font-awesome-icon(icon="fas fa-exclamation-triangle")
                span Delete All Operations
            button.delete(aria-label="close" @click="showDeleteAllOpsModal = false")
        section.modal-card-body
            .content
                p.has-text-weight-bold.is-size-5 Are you sure you want to delete ALL operations?
                p This action will permanently delete 
                    strong.has-text-danger {{ Object.keys(operationStore.operations).length }} operations
                    |  including all their links, results, and history.
                .notification.is-danger.is-light.mt-4
                    span.icon
                        font-awesome-icon(icon="fas fa-exclamation-circle")
                    span  This action is IRREVERSIBLE. All operation data will be lost permanently.
        footer.modal-card-foot
            button.button.is-danger(:class="{ 'is-loading': isDeletingOps }" @click="executeDeleteAllOperations" :disabled="isDeletingOps")
                span.icon
                    font-awesome-icon(icon="fas fa-trash")
                span Yes, Delete All
            button.button(@click="showDeleteAllOpsModal = false" :disabled="isDeletingOps") Cancel
</template>

<style>
.node-text {
  white-space: nowrap;
  overflow: hidden;
}

.control-panel {
  position: sticky;
  top: 70px;
  z-index: 10;
  border-radius: 8px;
  background-color: #383838;
  border: 1px solid #121212;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 1);
}

#link-table {
  border-radius: 10px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 1);
  padding: 5rem;
  margin-bottom: 15rem !important;
}

.gap-5 {
  gap: 0.4rem;
}

.m-n5 {
  margin-bottom: -0.5rem;
}

.link-status {
  background-color: #242424;
  border: 0.2em solid;
  border-radius: 50%;
  height: 1em;
  width: 1em;
  z-index: 1;
}

.dropdown-menu.command-popup {
  top: 0;
  left: initial;
  right: 90%;
  max-width: 75vw;
  max-height: 300px;
  border-radius: 8px;
  padding: 0;
}
.dropdown-menu.command-popup > .dropdown-content {
  padding: 10px;
  margin-right: 10px;
  border: 1px solid hsl(0deg, 0%, 71%);
  overflow-y: auto;
  max-width: 85vw;
  max-height: 300px;
}

a.icon {
  text-decoration: none !important;
}

.table td {
  vertical-align: middle !important;
}

.highlight-link {
  border: 2px solid #8B0000;
}

/* Ensure modals are always on top */
.modal {
  z-index: 9999 !important;
}

.modal-card, .modal-content {
  z-index: 10000 !important;
}

/* Resizable splitter styles */
.resizable-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 16px;
    cursor: row-resize;
    background: transparent;
    position: relative;
    margin: 4px 0;
    transition: background-color 0.2s;
}

.resizable-divider:hover,
.resizable-divider.is-resizing {
    background-color: rgba(0, 209, 178, 0.1);
}

.divider-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    background-color: #4a4a4a;
    transition: background-color 0.2s;
}

.resizable-divider:hover .divider-line,
.resizable-divider.is-resizing .divider-line {
    background-color: #00d1b2;
    height: 3px;
}

.divider-handle {
    z-index: 1;
    padding: 2px 16px;
    background-color: #363636;
    border-radius: 4px;
    color: #7a7a7a;
    font-size: 10px;
    transition: all 0.2s;
}

.resizable-divider:hover .divider-handle,
.resizable-divider.is-resizing .divider-handle {
    background-color: #00d1b2;
    color: white;
}
</style>
