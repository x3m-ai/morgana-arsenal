<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  show: Boolean,
  operationId: String,
  members: Array
});

const emit = defineEmits(['close', 'update']);

const selectedMembers = ref([]);
const showAssignedOnly = ref(false);

watch(() => props.show, (newVal) => {
  if (newVal && props.operationId) {
    console.log('AssignMembersModal opened');
    console.log('Operation ID:', props.operationId);
    console.log('Members received:', props.members);
    console.log('Members count:', props.members?.length || 0);
    
    // Load current assignments
    const assignments = JSON.parse(localStorage.getItem('operation_assignments') || '{}');
    selectedMembers.value = assignments[props.operationId] || [];
    console.log('Current assignments for this operation:', selectedMembers.value);
  }
});

const filteredMembers = computed(() => {
  if (!showAssignedOnly.value) {
    return props.members || [];
  }
  return (props.members || []).filter(m => selectedMembers.value.includes(m.aka));
});

function toggleMember(memberAka) {
  const index = selectedMembers.value.indexOf(memberAka);
  if (index > -1) {
    selectedMembers.value.splice(index, 1);
  } else {
    selectedMembers.value.push(memberAka);
  }
}

function isMemberSelected(memberAka) {
  return selectedMembers.value.includes(memberAka);
}

function updateAssignments() {
  emit('update', selectedMembers.value);
  close();
}

function close() {
  emit('close');
  showAssignedOnly.value = false;
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': show }")
  .modal-background(@click="close")
  .modal-card(style="width: 700px;")
    header.modal-card-head
      p.modal-card-title Assign Team Members
      button.delete(aria-label="close" @click="close")
    
    section.modal-card-body
      .field.mb-4
        label.checkbox
          input(type="checkbox" v-model="showAssignedOnly")
          span.ml-2 Show assigned only
      
      .notification.is-warning(v-if="!members || members.length === 0")
        p
          strong Debug info:
        p Members prop: {{ members }}
        p Members length: {{ members?.length || 0 }}
        p Go to Red Team Members page and click "Save All" to ensure members are saved in localStorage!
      
      .content(v-else-if="filteredMembers.length === 0")
        p.has-text-grey.has-text-centered No members to display
      
      table.table.is-fullwidth.is-striped.is-hoverable(v-else)
        thead
          tr
            th(style="width: 60px;") Assign
            th Name
            th Alias
            th Role
            th Current Status
        tbody
          tr(v-for="member in filteredMembers" :key="member.aka")
            td.has-text-centered
              input(type="checkbox" :checked="isMemberSelected(member.aka)" @change="toggleMember(member.aka)")
            td {{ member.name }}
            td
              strong {{ member.aka }}
            td {{ member.role }}
            td
              span.tag.is-small(:class="{ 'is-success': member.status === 'Active', 'is-warning': member.status === 'On Assignment', 'is-info': member.status === 'Stand-by', 'is-danger': member.status === 'Inactive' }") {{ member.status }}
    
    footer.modal-card-foot.is-justify-content-space-between
      button.button(@click="close") Cancel
      button.button.is-primary(@click="updateAssignments")
        span.icon
          font-awesome-icon(icon="fas fa-save")
        span Update Assignments
</template>
