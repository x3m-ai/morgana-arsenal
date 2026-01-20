<script setup>
import { ref, inject, onMounted, computed, watch } from "vue";
import { storeToRefs } from "pinia";
import { toast } from 'bulma-toast';
import { sanitizeInput, validateInput } from "@/utils/sanitize";

import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import { useOperationStore } from '@/stores/operationStore';
import { useAdversaryStore } from "@/stores/adversaryStore";
import { useCoreStore } from "@/stores/coreStore";
import { useAgentStore } from "@/stores/agentStore";
import { useSourceStore } from "@/stores/sourceStore";

const $api = inject("$api");

const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const adversaryStore = useAdversaryStore();
const operationStore = useOperationStore();
const coreStore = useCoreStore();
const agentStore = useAgentStore();
const sourceStore = useSourceStore();
const { sources } = storeToRefs(sourceStore);

const props = defineProps({
    operation: {
        type: Object,
        required: true
    },
    selectInterval: {
        type: Function,
    },
});

const emit = defineEmits(['close']);

let operationName = ref("");
let operationDescription = ref("");
let operationComments = ref("");
let selectedAdversary = ref("");
let selectedSource = ref("")
let selectedGroup = ref("");
let selectedObfuscator = ref({ name: "plain-text" });
let selectedPlanner = ref();
let isAuto = ref(true);
let isDefParser = ref(true);
let isAutoClose = ref(false);
let minJitter = ref(2);
let maxJitter = ref(8);
let visibility = ref(51);
let validation = ref({
    name: "",
});

// Available groups with 'red' always included
const availableGroups = computed(() => {
    const groups = new Set(['red', ...agentStore.agentGroups]);
    return Array.from(groups).sort();
});

// Check for duplicate operation name (excluding current operation)
const isDuplicateName = computed(() => {
    if (!operationName.value) return false;
    const currentName = operationName.value.trim().toLowerCase();
    return Object.values(operationStore.operations).some(op => 
        op.id !== props.operation.id && op.name.trim().toLowerCase() === currentName
    );
});

// Watch for name changes to show validation
watch(operationName, (newName) => {
    if (newName && isDuplicateName.value) {
        validation.value.name = "An operation with this name already exists";
    } else if (!validation.value.name.includes("empty") && !validation.value.name.includes("invalid")) {
        validation.value.name = "";
    }
});

// Load operation data when modal opens
watch(() => props.operation, (newOp) => {
    if (newOp) {
        loadOperationData();
    }
}, { immediate: true });

onMounted(async () => {
    await agentStore.getAgents($api);
    agentStore.updateAgentGroups();
    await adversaryStore.getAdversaries($api);
    await getSources();
    await coreStore.getObfuscators($api);
    await getPlanners();
    loadOperationData();
});

function loadOperationData() {
    if (!props.operation) return;
    
    operationName.value = props.operation.name || "";
    operationDescription.value = props.operation.description || "";
    operationComments.value = props.operation.comments || "";
    // Force group to 'red' if not set or empty
    selectedGroup.value = (props.operation.group && props.operation.group !== '') ? props.operation.group : "red";
    isAuto.value = props.operation.autonomous === 1 || props.operation.autonomous === true;
    isDefParser.value = props.operation.use_learning_parsers !== false;
    isAutoClose.value = props.operation.auto_close === true;
    visibility.value = props.operation.visibility || 51;
    
    // Parse jitter
    if (props.operation.jitter) {
        const jitterParts = props.operation.jitter.split('/');
        minJitter.value = parseInt(jitterParts[0]) || 2;
        maxJitter.value = parseInt(jitterParts[1]) || 8;
    }
    
    // Find adversary
    if (props.operation.adversary) {
        const adv = adversaryStore.adversaries.find(a => 
            a.adversary_id === props.operation.adversary.adversary_id
        );
        selectedAdversary.value = adv || props.operation.adversary;
    }
    
    // Find source
    if (props.operation.source) {
        const src = sources.value.find(s => s.id === props.operation.source.id);
        selectedSource.value = src || props.operation.source;
    }
    
    // Find planner
    if (props.operation.planner) {
        const plan = coreStore.planners.find(p => p.id === props.operation.planner.id);
        selectedPlanner.value = plan || props.operation.planner;
    }
    
    // Find obfuscator
    if (props.operation.obfuscator) {
        const obf = coreStore.obfuscators.find(o => o.name === props.operation.obfuscator);
        selectedObfuscator.value = obf || { name: props.operation.obfuscator };
    }
}

async function getSources() {
    try {
        await sourceStore.getSources($api);
    } catch(error) {
        console.error("Error getting sources", error);
    }
}

async function getPlanners() {
    try {
        await coreStore.getPlanners($api);
    } catch(error) {
        console.error("Error getting planners", error);
    }
}

async function updateOperation() {
    operationName.value = sanitizeInput(operationName.value);
    selectedGroup.value = sanitizeInput(selectedGroup.value);

    if (!validateInput(operationName.value, "string")) {
        validation.value.name = "Name cannot be empty or invalid";
        return;
    }
    if (isDuplicateName.value) {
        validation.value.name = "An operation with this name already exists";
        return;
    }
    validation.value.name = "";
    
    if(!selectedAdversary.value.adversary_id){
        selectedAdversary.value = {adversary_id: "ad-hoc"};
    }
    
    const updatedOperation = {
        name: operationName.value,
        description: operationDescription.value || "",
        comments: operationComments.value || "",
        autonomous: Number(isAuto.value),
        use_learning_parsers: isDefParser.value,
        auto_close: isAutoClose.value,
        jitter: `${minJitter.value}/${maxJitter.value}`,
        visibility: visibility.value,
        obfuscator: selectedObfuscator.value.name,
        source: { id: sanitizeInput(selectedSource.value.id) },
        planner: { id: sanitizeInput(selectedPlanner.value.id) },
        adversary: { adversary_id: sanitizeInput(selectedAdversary.value.adversary_id) },
        group: sanitizeInput(selectedGroup.value),
    };
    
    try {
        await $api.patch(`/api/v2/operations/${props.operation.id}`, updatedOperation);
        
        // Force refresh operations list
        await operationStore.getOperations($api);
        
        toast({
            message: `Operation ${operationName.value} updated successfully`,
            type: 'is-success',
            dismissible: true,
            pauseOnHover: true,
            duration: 2000,
            position: "bottom-right",
        });
        
        // Close modal and refresh interval
        closeModal();
    } catch(error) {
        console.error("Error updating operation", error);
        toast({
            message: `Error updating operation: ${error.message || 'Unknown error'}`,
            type: 'is-danger',
            dismissible: true,
            pauseOnHover: true,
            duration: 3000,
            position: "bottom-right",
        });
    }
}

async function closeModal() {
    // Force refresh operations before closing
    await operationStore.getOperations($api);
    if (props.selectInterval) {
        props.selectInterval();
    }
    emit('close');
}

</script>

<template lang="pug">
.modal.is-active
    .modal-background(@click="closeModal()")
    .modal-card
        header.modal-card-head 
            p.modal-card-title Edit Operation: {{ operation.name }}
        .modal-card-body
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Operation Name
                .field-body 
                    input.input(placeholder="Operation Name" v-model="operationName")
                    label.label.ml-3.mt-1.has-text-danger {{ `${validation.name}` }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Description
                .field-body 
                    textarea.textarea(placeholder="Describe the purpose and scope of this operation" v-model="operationDescription" rows="3")
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Comments
                .field-body 
                    textarea.textarea(placeholder="Add comments or notes about this operation" v-model="operationComments" rows="3")
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Adversary
                .field-body
                    .control
                        .select
                            select(v-model="selectedAdversary")
                                option(selected value="") No Adversary (manual)
                                option(v-for="adversary in adversaryStore.adversaries" :key="adversary.adversary_id" :value="adversary") {{ `${adversary.name}` }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Fact Source
                .field-body
                    .control
                        .select
                            select(v-model="selectedSource")
                                option(disabled selected value="") Choose a Fact Source 
                                option(v-for="source in sources" :key="source.id" :value="source") {{ `${source.name}` }}
            .field.is-horizontal 
                .field-label.is-normal 
                    label.label Group
                .field-body
                    button.button.mx-2(v-for="group in availableGroups" :key="group" :class="{ 'is-primary': selectedGroup === group }", @click="selectedGroup = group") {{`${group}`}}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label Planner 
                .field-body
                    .control
                        .select 
                            select(v-model="selectedPlanner")
                                option(v-for="planner in coreStore.planners" :key="planner.id" :value="planner") {{ `${planner.name}` }}
            .field.is-horizontal
                .field-label
                    label.label Obfuscators 
                .field-body
                    .field.is-grouped-multiline
                        button.button.my-1.mr-2(v-for="obf in coreStore.obfuscators" :key="obf.id" :value="obf" :class="{ 'is-primary': selectedObfuscator.name === obf.name }" @click="selectedObfuscator = obf") {{ `${obf.name}` }}
            .field.is-horizontal
                .field-label
                    label.label Autonomous
                .field-body
                    .field.is-grouped
                        input.is-checkradio(type="radio" id="auto-edit" :checked="isAuto" @click="isAuto = true")
                        label.label.ml-3.mt-1(for="auto-edit") Run autonomously
                        input.is-checkradio.ml-3(type="radio" id="manual-edit" :checked="!isAuto" @click="isAuto = false")
                        label.label.ml-3.mt-1(for="manual-edit") Require manual approval
            .field.is-horizontal
                .field-label
                    label.label Parser
                .field-body
                    .field.is-grouped 
                        input.is-checkradio(type="radio" id="defaultparser-edit" :checked="isDefParser" @click="isDefParser = true")
                        label.label.ml-3.mt-1(for="defaultparser-edit") Use Default Parser
                        input.is-checkradio.ml-3(type="radio" id="nondefaultparser-edit" :checked="!isDefParser" @click="isDefParser = false")
                        label.label.ml-3.mt-1(for="nondefaultparser-edit") Don't use default learning parsers
            .field.is-horizontal
                .field-label 
                    label.label Auto Close
                .field-body.is-grouped
                    input.is-checkradio(type="radio" id="keepopen-edit" :checked="!isAutoClose" @click="isAutoClose = false")
                    label.label.ml-3.mt-1(for="keepopen-edit") Keep open forever
                    input.is-checkradio.ml-3(type="radio" id="autoclose-edit" :checked="isAutoClose" @click="isAutoClose = true")
                    label.label.ml-3.mt-1(for="autoclose-edit") Auto close operation
            .field.is-horizontal 
                .field-label 
                    label.label Jitter (sec/sec)
                .field-body
                    input.input.is-small(v-model="minJitter" type="number")
                    span /
                    input.input.is-small(v-model="maxJitter" type="number")
        footer.modal-card-foot.is-justify-content-space-between
            button.button(@click="closeModal()") Cancel
            button.button.is-primary(@click="updateOperation()" :disabled="isDuplicateName") Update Operation
</template>

<style scoped>
.modal {
    z-index: 1001;
}

.modal-card {
    width: 800px;
}

.field-label label{
    font-size: 0.9rem;
}
</style>
