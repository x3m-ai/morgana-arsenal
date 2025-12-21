<script setup>
import { storeToRefs } from "pinia";
import { reactive, ref, inject, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useAbilityStore } from "@/stores/abilityStore";
import { getAbilityPlatforms } from "@/utils/abilityUtil.js";
import CreateEditAbility from "@/components/abilities/CreateEditAbility.vue";

const $api = inject("$api");
const route = useRoute();

const abilityStore = useAbilityStore();
const { abilities, tactics, techniques, plugins, platforms } = storeToRefs(abilityStore);

let filters = reactive({
    searchQuery: "",
    tactic: "",
    technique: "",
    plugin: "",
    platform: ""
});

let isCreatingAbility = ref(false);
let showAbilityModal = ref(false);
let selectedAbility = ref({});

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
            return (!filters.tactic || ability.tactic === filters.tactic)
                && (!filters.technique || `${ability.technique_id} | ${ability.technique_name}` === filters.technique)
                && (!filters.plugin || ability.plugin === filters.plugin)
                && (!filters.platform || getAbilityPlatforms(ability).indexOf(filters.platform) >= 0);
        } catch (error) {
            console.error('Error filtering ability:', error);
            return true; // In case of error, don't filter out the ability
        }
    });
});

onMounted(async () => {
    await abilityStore.getAbilities($api);
    filters.plugin = route.query.plugin || "";
});

function clearFilters() {
    Object.keys(filters).forEach((k) => filters[k] = "");
}


function selectAbility(ability, creating) {
    selectedAbility.value = ability;
    isCreatingAbility.value = creating;
    showAbilityModal.value = true;
}
</script>

<template lang="pug">
//- Header
.content
    h2 Abilities
    p An ability is a specific ATT&CK tactic/technique implementation which can be executed on running agents. Abilities will include the command(s) to run, the platforms / executors the commands can run on (ex: Windows / PowerShell), payloads to include, and a reference to a module to parse the output on the Caldera server.
hr

.columns
    .column.is-2.m-0
        button.button.is-primary.is-fullwidth.mb-4(@click="selectAbility({}, true)")
            span.icon
                font-awesome-icon(icon="fas fa-plus")
            span Create an Ability
        form
            .field
                .control.has-icons-left
                    input.input.is-small(v-model="filters.searchQuery" type="text" placeholder="Find an ability...")
                    span.icon.is-left
                        font-awesome-icon(icon="fas fa-search")
            .field
                label.label Tactic 
                .control
                    .select.is-fullwidth
                        select(v-model="filters.tactic")
                            option(value="") All 
                            option(v-for="tactic in tactics" :value="tactic") {{ tactic }}    
            .field
                label.label Technique 
                .control
                    .select.is-fullwidth
                        select(v-model="filters.technique")
                            option(value="") All 
                            option(v-for="technique in techniques" :value="technique") {{ technique }}   
            .field
                label.label Plugin 
                .control
                    .select.is-fullwidth
                        select(v-model="filters.plugin")
                            option(value="") All 
                            option(v-for="plugin in plugins" :value="plugin") {{ plugin }}   
            .field
                label.label Platform 
                .control
                    .select.is-fullwidth
                        select(v-model="filters.platform")
                            option(value="") All 
                            option(v-for="platform in Object.keys(platforms)" :value="platform") {{ platform }}   
        button.button.is-fullwidth.mt-4(@click="clearFilters()") Clear Filters
        p.mt-2.has-text-centered
            strong {{ filteredAbilities.length }}&nbsp;
            | / {{ abilities.length }} abilities
    .column.is-10.m-0.is-flex.is-flex-wrap-wrap.is-align-content-flex-start
        .box.mb-2.mr-2.p-3.ability(v-for="ability in filteredAbilities" @click="selectAbility(ability, false)" :key="ability.ability_id")
            .is-flex.is-justify-content-space-between.is-align-items-center.mb-1
                .is-flex
                    span.tag.is-small.mr-3 {{ ability.tactic }} 
                p.help.mt-0 {{ ability.technique_id }} - {{ ability.technique_name }}
            strong {{ ability.name }}
            p.help.mb-0 {{ ability.description }}   

//- Modals
CreateEditAbility(:ability="selectedAbility" :active="showAbilityModal" :creating="isCreatingAbility" @close="showAbilityModal = false")
</template>

<style scoped>
@media(max-width: 1200px) {
    .box.ability {
        width: 98%;
    }
}
@media(min-width: 1200px) {
    .box.ability {
        width: 48%;
    }
}
.box.ability {
    position: relative;
    cursor: pointer;
    border: 1px solid transparent;
    background-color: #272727;
}
.box.ability:hover {
    border: 1px solid #474747;
}

.abilities {
    overflow-x: hidden;
}
</style>
