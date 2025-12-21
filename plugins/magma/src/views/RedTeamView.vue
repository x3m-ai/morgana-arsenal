<script setup>
import { ref, onMounted, inject } from "vue";
import { useOperationStore } from "@/stores/operationStore";
import { storeToRefs } from "pinia";
import MemberDetailsModal from "@/components/redteam/MemberDetailsModal.vue";

const $api = inject("$api");
const operationStore = useOperationStore();
const { operations } = storeToRefs(operationStore);

const hackers = ref([
    { name: "Thomas Anderson", aka: "Neo", email: "neo@redteam.local", role: "Red Team Lead", specialization: "Matrix Operations", status: "Active" },
    { name: "Kate Libby", aka: "Acid Burn", email: "acidburn@redteam.local", role: "Exploitation Expert", specialization: "Zero-Day Research", status: "Active" }
]);

const selectedMember = ref(null);
const showDetailsModal = ref(false);

const roles = [
    "Red Team Lead",
    "Penetration Tester",
    "Exploitation Expert",
    "Social Engineer",
    "Network Specialist",
    "Malware Developer",
    "OSINT Analyst",
    "Wireless Specialist",
    "Physical Security",
    "C2 Operator"
];

const statuses = ["Active", "On Assignment", "Stand-by", "Inactive"];

onMounted(async () => {
    await operationStore.getOperations($api);
    loadHackers();
});

function updateHacker(index) {
    const hacker = hackers.value[index];
    
    // If status is not "On Assignment", remove from all operations
    if (hacker.status !== "On Assignment") {
        const assignments = JSON.parse(localStorage.getItem('operation_assignments') || '{}');
        let updated = false;
        
        // Remove this member from all operations
        for (const opId in assignments) {
            if (Array.isArray(assignments[opId])) {
                const originalLength = assignments[opId].length;
                assignments[opId] = assignments[opId].filter(aka => aka !== hacker.aka);
                
                // If array is now empty, delete the key
                if (assignments[opId].length === 0) {
                    delete assignments[opId];
                    updated = true;
                } else if (assignments[opId].length !== originalLength) {
                    updated = true;
                }
            }
        }
        
        // Save updated assignments if changed
        if (updated) {
            localStorage.setItem('operation_assignments', JSON.stringify(assignments));
            console.log(`Removed ${hacker.aka} from all operations due to status change to ${hacker.status}`);
        }
    }
    
    localStorage.setItem('redteam_hackers', JSON.stringify(hackers.value));
    console.log(`Updated ${hacker.name} (${hacker.aka})`);
}

function loadHackers() {
    const stored = localStorage.getItem('redteam_hackers');
    if (stored) {
        try {
            const parsed = JSON.parse(stored);
            // Validate data - must be array with at least some valid members
            if (Array.isArray(parsed) && parsed.length > 0) {
                hackers.value = parsed;
                console.log('Loaded red team members from localStorage:', parsed.length, 'members');
                return;
            }
        } catch (e) {
            console.error('Error loading hackers from storage', e);
        }
    }
    // If no valid data, initialize with defaults
    const defaults = [
        { name: "Thomas Anderson", aka: "Neo", email: "neo@redteam.local", role: "Red Team Lead", specialization: "Matrix Operations", status: "Active" },
        { name: "Kate Libby", aka: "Acid Burn", email: "acidburn@redteam.local", role: "Exploitation Expert", specialization: "Zero-Day Research", status: "Active" }
    ];
    hackers.value = defaults;
    localStorage.setItem('redteam_hackers', JSON.stringify(defaults));
    console.log('Initialized red team with default members');
}

function addNewMember() {
    hackers.value.push({
        name: "",
        aka: "",
        email: "",
        role: "Penetration Tester",
        specialization: "",
        status: "Active"
    });
    // Save immediately so it persists
    localStorage.setItem('redteam_hackers', JSON.stringify(hackers.value));
}

function removeMember(index) {
    hackers.value.splice(index, 1);
    localStorage.setItem('redteam_hackers', JSON.stringify(hackers.value));
}

function viewDetails(member) {
    selectedMember.value = member;
    showDetailsModal.value = true;
}

function saveAll() {
    // Filter out empty members (those without aka)
    const validMembers = hackers.value.filter(h => h.aka && h.aka.trim() !== '');
    hackers.value = validMembers;
    
    localStorage.setItem('redteam_hackers', JSON.stringify(hackers.value));
    console.log('Saved all team members:', hackers.value.length);
    console.log('Members:', hackers.value.map(h => h.aka).join(', '));
    alert(`Saved ${hackers.value.length} team members!`);
}

function checkStorage() {
    const stored = localStorage.getItem('redteam_hackers');
    if (stored) {
        const parsed = JSON.parse(stored);
        alert(`localStorage has ${parsed.length} members:\n${parsed.map(h => h.aka).join(', ')}`);
    } else {
        alert('localStorage is EMPTY!');
    }
}

function resetToDefaults() {
    if (confirm('Reset to default members (Neo and Acid Burn)? This will delete all current members.')) {
        const defaults = [
            { name: "Thomas Anderson", aka: "Neo", email: "neo@redteam.local", role: "Red Team Lead", specialization: "Matrix Operations", status: "Active" },
            { name: "Kate Libby", aka: "Acid Burn", email: "acidburn@redteam.local", role: "Exploitation Expert", specialization: "Zero-Day Research", status: "Active" }
        ];
        hackers.value = defaults;
        localStorage.setItem('redteam_hackers', JSON.stringify(defaults));
        alert('Reset to default members!');
    }
}
</script>

<template lang="pug">
.content
    h2 Red Team Members
    p.subtitle Manage your offensive security team roster and track operational assignments
hr

.mb-4
    .buttons
        button.button.is-primary(@click="addNewMember")
            span.icon
                font-awesome-icon(icon="fas fa-plus")
            span Add New Member
        button.button.is-success(@click="saveAll")
            span.icon
                font-awesome-icon(icon="fas fa-save")
            span Save All
        button.button.is-warning(@click="resetToDefaults")
            span.icon
                font-awesome-icon(icon="fas fa-undo")
            span Reset Defaults
        button.button.is-info(@click="checkStorage")
            span.icon
                font-awesome-icon(icon="fas fa-info-circle")
            span Check Storage

.table-container
    table.table.is-fullwidth.is-striped.is-hoverable
        thead
            tr
                th(style="width: 15%") Name
                th(style="width: 12%") Alias
                th(style="width: 20%") Email
                th(style="width: 15%") Role
                th(style="width: 15%") Specialization
                th(style="width: 13%") Status
                th(style="width: 10%") Actions
        tbody
            tr(v-for="(hacker, idx) in hackers" :key="idx")
                td
                    input.input.is-small(v-model="hacker.name")
                td
                    input.input.is-small(v-model="hacker.aka")
                td
                    input.input.is-small(type="email" v-model="hacker.email")
                td
                    .select.is-small.is-fullwidth
                        select(v-model="hacker.role")
                            option(v-for="role in roles" :key="role" :value="role") {{ role }}
                td
                    input.input.is-small(v-model="hacker.specialization")
                td
                    .select.is-small.is-fullwidth
                        select(v-model="hacker.status" :class="{ 'has-text-success': hacker.status === 'Active', 'has-text-warning': hacker.status === 'On Assignment', 'has-text-info': hacker.status === 'Stand-by', 'has-text-danger': hacker.status === 'Inactive' }")
                            option(v-for="status in statuses" :key="status" :value="status") {{ status }}
                td
                    .buttons.is-small
                        button.button.is-small.is-info(@click="viewDetails(hacker)" v-tooltip="'View details'")
                            span.icon.is-small
                                font-awesome-icon(icon="fas fa-search")
                        button.button.is-small.is-primary(@click="updateHacker(idx)" v-tooltip="'Save changes'")
                            span.icon
                                font-awesome-icon(icon="fas fa-save")
                        button.button.is-small.is-danger(@click="removeMember(idx)" v-tooltip="'Remove member'")
                            span.icon
                                font-awesome-icon(icon="fas fa-trash")

MemberDetailsModal(:show="showDetailsModal" :member="selectedMember" @close="showDetailsModal = false")
</template>

<style scoped>
.table-container {
    max-height: 600px;
    overflow-y: auto;
}

.has-text-success {
    color: #48c774 !important;
}

.has-text-warning {
    color: #ffdd57 !important;
}

.has-text-info {
    color: #3e8ed0 !important;
}

.has-text-danger {
    color: #f14668 !important;
}
</style>
