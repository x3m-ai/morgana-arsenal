<script setup>
import { inject, reactive, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";
import { toast } from "bulma-toast";

import { useAdversaryStore } from "@/stores/adversaryStore";
import { useAbilityStore } from "@/stores/abilityStore";
import { useObjectiveStore } from "@/stores/objectiveStore";
import DetailsTable from "@/components/adversaries/DetailsTable.vue";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import ImportModal from "@/components/adversaries/ImportModal.vue";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const { adversaries, selectedAdversary } = storeToRefs(adversaryStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const abilityStore = useAbilityStore();
const { abilities } = storeToRefs(abilityStore);
const objectiveStore = useObjectiveStore();

let adversarySearchQuery = ref("");
let showOnlyEmpty = ref(false);
let showDeleteAllModal = ref(false);
let isDeleting = ref(false);

// Delete all adversaries with confirmation
async function confirmDeleteAllAdversaries() {
    if (adversaries.value.length === 0) {
        toast({
            message: "No adversaries to delete",
            type: "is-warning",
            dismissible: true,
            pauseOnHover: true,
            duration: 3000,
            position: "bottom-right",
        });
        return;
    }
    showDeleteAllModal.value = true;
}

async function executeDeleteAllAdversaries() {
    isDeleting.value = true;
    try {
        const result = await adversaryStore.deleteAllAdversaries($api);
        showDeleteAllModal.value = false;
        toast({
            message: `Deleted ${result.deleted} adversaries${result.errors > 0 ? ` (${result.errors} errors)` : ''}`,
            type: result.errors > 0 ? "is-warning" : "is-success",
            dismissible: true,
            pauseOnHover: true,
            duration: 3000,
            position: "bottom-right",
        });
    } catch (error) {
        toast({
            message: "Error deleting adversaries: " + error.message,
            type: "is-danger",
            dismissible: true,
            pauseOnHover: true,
            duration: 5000,
            position: "bottom-right",
        });
    } finally {
        isDeleting.value = false;
    }
}

// Compute TCodes (all technique IDs) for each adversary
const adversariesWithTCodes = computed(() => {
    return adversaries.value.map(adversary => {
        const tcodes = [];
        if (adversary.atomic_ordering && Array.isArray(adversary.atomic_ordering)) {
            for (const abilityId of adversary.atomic_ordering) {
                const ability = abilities.value.find(a => a.ability_id === abilityId);
                if (ability && ability.technique_id) {
                    tcodes.push(ability.technique_id);
                }
            }
        }
        return {
            ...adversary,
            tcodes: tcodes.join(', '),
            tcodesArray: tcodes
        };
    });
});

let filteredAdversaries = computed(() => {
    return adversariesWithTCodes.value.filter((adversary) => {
        try {
            // Filter by empty abilities if checkbox is checked
            if (showOnlyEmpty.value && adversary.atomic_ordering && adversary.atomic_ordering.length > 0) {
                return false;
            }
            
            // Smart search: searches in all fields
            const query = adversarySearchQuery.value.toLowerCase().trim();
            
            if (query && query.length > 0) {
                // Search in basic fields
                const nameMatch = adversary.name && adversary.name.toLowerCase().includes(query);
                const descMatch = adversary.description && adversary.description.toLowerCase().includes(query);
                const idMatch = adversary.adversary_id && adversary.adversary_id.toLowerCase().includes(query);
                const objectiveMatch = adversary.objective && adversary.objective.toLowerCase().includes(query);
                
                // Search in TCodes
                const tcodesMatch = adversary.tcodes && adversary.tcodes.toLowerCase().includes(query);
                
                // Search in associated abilities (commands, technique names, etc.)
                let abilityMatch = false;
                if (adversary.atomic_ordering && Array.isArray(adversary.atomic_ordering)) {
                    for (const abilityId of adversary.atomic_ordering) {
                        const ability = abilities.value.find(a => a.ability_id === abilityId);
                        if (!ability) continue;
                        
                        // Search in ability fields
                        if ((ability.name && ability.name.toLowerCase().includes(query)) ||
                            (ability.description && ability.description.toLowerCase().includes(query)) ||
                            (ability.tactic && ability.tactic.toLowerCase().includes(query)) ||
                            (ability.technique_name && ability.technique_name.toLowerCase().includes(query)) ||
                            (ability.technique_id && ability.technique_id.toLowerCase().includes(query))) {
                            abilityMatch = true;
                            break;
                        }
                        
                        // Search in executors (commands)
                        if (ability.executors && Array.isArray(ability.executors)) {
                            for (const executor of ability.executors) {
                                if (!executor) continue;
                                if ((executor.command && typeof executor.command === 'string' && 
                                     executor.command.toLowerCase().includes(query)) ||
                                    (executor.cleanup && typeof executor.cleanup === 'string' && 
                                     executor.cleanup.toLowerCase().includes(query)) ||
                                    (executor.platform && executor.platform.toLowerCase().includes(query)) ||
                                    (executor.name && executor.name.toLowerCase().includes(query))) {
                                    abilityMatch = true;
                                    break;
                                }
                            }
                        }
                        if (abilityMatch) break;
                    }
                }
                
                // If none of the fields match, filter it out
                if (!nameMatch && !descMatch && !idMatch && !objectiveMatch && 
                    !tcodesMatch && !abilityMatch) {
                    return false;
                }
            }
            
            return true;
        } catch (error) {
            console.error('Error filtering adversary:', error);
            return true; // Don't filter out on error
        }
    });
});

onMounted(async () => {
    await abilityStore.getAbilities($api);
    await adversaryStore.getAdversaries($api);
    await objectiveStore.getObjectives($api);
});

function selectAdversary(adversary) {
    selectedAdversary.value = adversary; 
    adversaryStore.updateSelectedAdversaryAbilities();
    adversarySearchQuery.value = "";
}
</script>

<template lang="pug">
//- Header
.content
    h2 Adversaries
    p Adversary Profiles are collections of ATT&CK TTPs, designed to create specific effects on a host or network. Profiles can be used for offensive or defensive use cases.
hr

//- Adversaries Table
.box.mb-4
    .is-flex.is-justify-content-space-between.mb-3
        .field.has-addons(style="width: 400px")
            .control.has-icons-left.is-expanded
                input.input.is-small(type="text" placeholder="Search adversaries..." v-model="adversarySearchQuery")
                span.icon.is-small.is-left
                    font-awesome-icon(icon="fas fa-search")
        .is-flex.is-align-items-center
            label.checkbox.mr-4(style="font-size: 0.875rem;")
                input(type="checkbox" v-model="showOnlyEmpty")
                span.ml-2 Show only empty (0 abilities)
            .buttons
                button.button.is-primary.is-small(type="button" @click="adversaryStore.createAdversary($api)")
                    span.icon 
                        font-awesome-icon(icon="fas fa-plus") 
                    span New Profile
                button.button.is-small(type="button" @click="modals.adversaries.showImport = true")
                    span.icon
                        font-awesome-icon(icon="fas fa-file-import") 
                    span Import
                button.button.is-danger.is-small(type="button" @click="confirmDeleteAllAdversaries" :disabled="adversaries.length === 0")
                    span.icon
                        font-awesome-icon(icon="fas fa-trash")
                    span Delete All
    
    .table-container(style="max-height: 400px; overflow-y: auto; border: 1px solid #dbdbdb; border-radius: 4px;")
        table.table.is-fullwidth.is-hoverable.is-striped(style="margin-bottom: 0;")
        thead
            tr(style="background-color: #363636; color: white;")
                th(style="color: white; min-width: 180px;") Adversary Name
                th(style="color: white; min-width: 200px;") Description
                th(style="color: white; min-width: 100px; text-align: center;") Abilities
                th(style="color: white; min-width: 250px;") TCodes
                th(style="color: white; min-width: 150px;") Objective
                th(style="color: white; min-width: 100px;" class="has-text-centered") Actions
        tbody
            tr(v-if="adversaries.length === 0")
                td(colspan="6" class="has-text-centered has-text-grey-light is-italic") No adversaries yet. Create one to get started.
            tr(
                v-for="adversary in filteredAdversaries" 
                :key="adversary.adversary_id"
                :class="{ 'is-selected': adversary.adversary_id === selectedAdversary.adversary_id }"
                style="cursor: pointer;"
                @click="selectAdversary(adversary)"
            )
                td
                    strong {{ adversary.name }}
                td.is-size-7 {{ adversary.description || 'No description' }}
                td.has-text-centered
                    span.tag.is-info.is-light {{ adversary.atomic_ordering?.length || 0 }}
                td.is-size-7(style="font-family: monospace; color: #00d1b2;") {{ adversary.tcodes || 'No TTPs' }}
                td.is-size-7 {{ adversary.objective || 'None' }}
                td.has-text-centered
                    button.button.is-small.is-info(@click.stop="selectAdversary(adversary)" title="View details")
                        span.icon.is-small
                            font-awesome-icon(icon="fas fa-search" style="color: white;")
hr

//- Adversary details table
DetailsTable(v-if="selectedAdversary.adversary_id")

//- Delete All Confirmation Modal
.modal(:class="{ 'is-active': showDeleteAllModal }")
    .modal-background(@click="showDeleteAllModal = false")
    .modal-card
        header.modal-card-head.has-background-danger
            p.modal-card-title.has-text-white
                span.icon.mr-2
                    font-awesome-icon(icon="fas fa-exclamation-triangle")
                span Delete All Adversaries
            button.delete(aria-label="close" @click="showDeleteAllModal = false")
        section.modal-card-body
            .content
                p.has-text-weight-bold.is-size-5 Are you sure you want to delete ALL adversaries?
                p This action will permanently delete 
                    strong.has-text-danger {{ adversaries.length }} adversary profiles
                    |  and cannot be undone.
                .notification.is-warning.is-light.mt-4
                    span.icon
                        font-awesome-icon(icon="fas fa-info-circle")
                    span  This will NOT delete the abilities associated with these adversaries.
        footer.modal-card-foot
            button.button.is-danger(:class="{ 'is-loading': isDeleting }" @click="executeDeleteAllAdversaries" :disabled="isDeleting")
                span.icon
                    font-awesome-icon(icon="fas fa-trash")
                span Yes, Delete All
            button.button(@click="showDeleteAllModal = false" :disabled="isDeleting") Cancel

//- Modals
ImportModal
</template>

<style scoped>
</style>
