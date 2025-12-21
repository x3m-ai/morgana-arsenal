<script setup>
import { ref, reactive, computed, inject, onMounted } from 'vue';
import { storeToRefs } from "pinia";

import { useAbilityStore } from "@/stores/abilityStore";
import CreateEditAbility from "@/components/abilities/CreateEditAbility.vue";
import AutoSuggest from "@/components/core/AutoSuggest.vue";

const props = defineProps({ 
    active: Boolean,
    canCreate: Boolean
});
const emit = defineEmits(['select', 'close']);

const $api = inject("$api");

const abilityStore = useAbilityStore();
const { abilities, tactics, techniqueIds, techniqueNames } = storeToRefs(abilityStore);

let filters = reactive({
    searchQuery: "",
    tactic: "",
    techniqueId: "",
    techniqueName: ""
});
let showFilters = ref(false);
let showCreateAbilityModal = ref(false);

const filteredAbilities = computed(() => {
    return abilities.value.filter((ability) => {
        try {
            // Smart search: searches in all fields of the ability
            const query = filters.searchQuery.toLowerCase().trim();
            
            if (query && query.length > 0) {
                // Search in basic fields
                const nameMatch = ability.name && ability.name.toLowerCase().includes(query);
                const descMatch = ability.description && ability.description.toLowerCase().includes(query);
                const idMatch = ability.ability_id && ability.ability_id.toLowerCase().includes(query);
                const tacticMatch = ability.tactic && ability.tactic.toLowerCase().includes(query);
                const techniqueNameMatch = ability.technique_name && ability.technique_name.toLowerCase().includes(query);
                
                // Technique ID search with smart matching (T1110 matches T1110.001, T1110.002, etc.)
                const techniqueIdMatch = ability.technique_id && ability.technique_id.toLowerCase().startsWith(query.replace(/\./g, ''));
                
                // Search in executors (commands, parsers, etc.)
                let executorMatch = false;
                if (ability.executors && Array.isArray(ability.executors)) {
                    for (const executor of ability.executors) {
                        if (!executor) continue;
                        
                        // Search in command
                        if (executor.command && typeof executor.command === 'string' && executor.command.toLowerCase().includes(query)) {
                            executorMatch = true;
                            break;
                        }
                        // Search in parser names
                        if (executor.parsers && Array.isArray(executor.parsers)) {
                            for (const parser of executor.parsers) {
                                if (!parser) continue;
                                if ((parser.module && parser.module.toLowerCase().includes(query)) || 
                                    (parser.parserconfigs && Array.isArray(parser.parserconfigs) && 
                                     parser.parserconfigs.some(pc => {
                                         try {
                                             return JSON.stringify(pc).toLowerCase().includes(query);
                                         } catch {
                                             return false;
                                         }
                                     }))) {
                                    executorMatch = true;
                                    break;
                                }
                            }
                        }
                        if (executorMatch) break;
                        
                        // Search in cleanup command
                        if (executor.cleanup && typeof executor.cleanup === 'string' && executor.cleanup.toLowerCase().includes(query)) {
                            executorMatch = true;
                            break;
                        }
                        // Search in platform and executor name
                        if ((executor.platform && executor.platform.toLowerCase().includes(query)) || 
                            (executor.name && executor.name.toLowerCase().includes(query))) {
                            executorMatch = true;
                            break;
                        }
                    }
                }
                
                // Search in requirements
                let requirementMatch = false;
                if (ability.requirements && Array.isArray(ability.requirements)) {
                    for (const req of ability.requirements) {
                        if (!req) continue;
                        try {
                            if (JSON.stringify(req).toLowerCase().includes(query)) {
                                requirementMatch = true;
                                break;
                            }
                        } catch {
                            // Skip if JSON.stringify fails
                        }
                    }
                }
                
                // Search in singleton and repeatable
                const singletonMatch = ability.singleton !== undefined && ability.singleton.toString().toLowerCase().includes(query);
                const repeatableMatch = ability.repeatable !== undefined && ability.repeatable.toString().toLowerCase().includes(query);
                
                // Search in privilege
                const privilegeMatch = ability.privilege && ability.privilege.toLowerCase().includes(query);
                
                // Search in plugin
                const pluginMatch = ability.plugin && ability.plugin.toLowerCase().includes(query);
                
                // If none of the fields match, filter it out
                if (!nameMatch && !descMatch && !idMatch && !tacticMatch && 
                    !techniqueNameMatch && !techniqueIdMatch && !executorMatch && 
                    !requirementMatch && !singletonMatch && !repeatableMatch && 
                    !privilegeMatch && !pluginMatch) {
                    return false;
                }
            }
            
            // Apply other filters
            return (!filters.tactic || ability.tactic.toLowerCase().includes(filters.tactic.toLowerCase()))
                && (!filters.techniqueId || ability.technique_id.toLowerCase().includes(filters.techniqueId.toLowerCase()))
                && (!filters.techniqueName || ability.technique_name.toLowerCase().includes(filters.techniqueName.toLowerCase()));
        } catch (error) {
            console.error('Error filtering ability:', error);
            return true; // In case of error, don't filter out the ability
        }
    });
});

const hasFiltersApplied = computed(() => {
    return filters.searchQuery || filters.tactic || filters.techniqueId || filters.techniqueName;
});

onMounted(async () => {
    await abilityStore.getAbilities($api);
});

function clearFilters() {
    filters.searchQuery = "";
    filters.tactic = "";
    filters.techniqueId = "";
    filters.techniqueName = "";
}

function createAbility() {
    showCreateAbilityModal.value = true;
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': props.active }")
    .modal-background(@click="emit('close')")
    .modal-card
        header.modal-card-head
            p.modal-card-title Select Ability
        .modal-card-body
            form
                .field
                    .control.has-icons-left
                        input.input(v-model="filters.searchQuery" type="text" placeholder="Search for an ability...")
                        span.icon.is-left
                            font-awesome-icon(icon="fas fa-search")
                .field(v-if="showFilters")
                    label.label Tactic
                    .control
                        AutoSuggest(v-model="filters.tactic" :items="tactics" placeholder="Tactic")
                .field(v-if="showFilters")
                    label.label Technique ID
                    .control
                        AutoSuggest(v-model="filters.techniqueId" :items="techniqueIds" placeholder="Technique ID")
                .field(v-if="showFilters")
                    label.label Technique Name
                    .control
                        AutoSuggest(v-model="filters.techniqueName" :items="techniqueNames" placeholder="Technique Name")
            .is-flex.is-justify-content-space-between.mt-2
                a(@click="showFilters = !showFilters") {{ showFilters ? "Hide" : "Show" }} filters
                a(v-if="hasFiltersApplied" @click="clearFilters()") Clear filters
            hr.mt-3
            .card.p-3.mb-2.pointer(v-for="ability in filteredAbilities" @click="emit('select', ability)")
                .is-flex.is-justify-content-space-between.is-align-items-center
                    span.tag.is-small {{ ability.tactic }} 
                    p.help.mt-0 {{ ability.technique_id }} - {{ ability.technique_name }}
                p.mt-1 {{ ability.name }}
                p.help {{ ability.description }}
        footer.modal-card-foot.is-flex.is-justify-content-space-between
            button.button(v-if="props.canCreate" @click="createAbility()")
                span.icon
                    font-awesome-icon(icon="fas fa-plus")
                span Create an Ability
            button.button(@click="emit('close')") Close

//- Modals
CreateEditAbility(v-if="props.canCreate" :ability="{}" :active="showCreateAbilityModal" :creating="true" @close="showCreateAbilityModal = false")
</template>

<style scoped>
.card {
    border: 1px solid transparent;
    user-select: none;
}
.card:hover {
    border: 1px solid white;
}

.modal-card {
    width: 800px;
}
</style> 
    
