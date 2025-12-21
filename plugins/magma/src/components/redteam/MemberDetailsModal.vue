<script setup>
import { inject, computed } from "vue";
import { useOperationStore } from "@/stores/operationStore";
import { storeToRefs } from "pinia";

const props = defineProps({
  member: Object,
  show: Boolean
});

const emit = defineEmits(['close']);

const operationStore = useOperationStore();
const { operations } = storeToRefs(operationStore);

const assignedOperations = computed(() => {
  const assignments = JSON.parse(localStorage.getItem('operation_assignments') || '{}');
  const memberOps = [];
  
  Object.keys(assignments).forEach(opId => {
    const members = assignments[opId];
    if (Array.isArray(members) && members.includes(props.member?.aka)) {
      const op = operations.value[opId];
      if (op) {
        memberOps.push(op);
      }
    }
  });
  
  return memberOps;
});

function close() {
  emit('close');
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': show }")
  .modal-background(@click="close")
  .modal-card(style="width: 600px;")
    header.modal-card-head
      p.modal-card-title Member Details
      button.delete(aria-label="close" @click="close")
    section.modal-card-body(v-if="member")
      .content
        h4 {{ member.name }} ({{ member.aka }})
        
        .field
          label.label Email
          p {{ member.email }}
        
        .field
          label.label Role
          p {{ member.role }}
        
        .field
          label.label Specialization
          p {{ member.specialization }}
        
        .field
          label.label Status
          p
            span.tag(:class="{ 'is-success': member.status === 'Active', 'is-warning': member.status === 'On Assignment', 'is-info': member.status === 'Stand-by', 'is-danger': member.status === 'Inactive' }") {{ member.status }}
        
        hr
        
        h5 Assigned Operations
        .box(v-if="assignedOperations.length === 0" style="background-color: #f5f5f5;")
          p.has-text-grey.has-text-centered Not assigned to any operations
        
        table.table.is-fullwidth.is-striped(v-else)
          thead
            tr
              th Operation Name
              th State
              th Started
          tbody
            tr(v-for="op in assignedOperations" :key="op.id")
              td {{ op.name }}
              td
                span.tag.is-info {{ op.state }}
              td.is-size-7 {{ op.start }}
    
    footer.modal-card-foot.is-justify-content-flex-end
      button.button(@click="close") Close
</template>
