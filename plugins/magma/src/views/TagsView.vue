<script setup>
import { ref, inject, onMounted, computed } from "vue";

const $api = inject("$api");

const tags = ref([]);
const editingTag = ref(null);
const newTag = ref({ name: "", value: "" });
const showNewTagForm = ref(false);
const searchQuery = ref("");

// Maximum 40 tags allowed
const MAX_TAGS = 40;

onMounted(async () => {
    await loadTags();
});

async function loadTags() {
    try {
        const response = await $api.get("/api/v2/tags");
        tags.value = response.data || [];
    } catch (error) {
        console.error("Error loading tags:", error);
    }
}

async function createTag() {
    if (!newTag.value.name.trim()) {
        alert("Tag name is required");
        return;
    }
    
    if (tags.value.length >= MAX_TAGS) {
        alert(`Maximum ${MAX_TAGS} tags allowed`);
        return;
    }
    
    try {
        await $api.post("/api/v2/tags", newTag.value);
        newTag.value = { name: "", value: "" };
        showNewTagForm.value = false;
        await loadTags();
    } catch (error) {
        console.error("Error creating tag:", error);
        alert("Error creating tag: " + (error.response?.data?.error || error.message));
    }
}

async function updateTag(tag) {
    try {
        await $api.patch(`/api/v2/tags/${tag.name}`, { value: tag.value });
        editingTag.value = null;
        await loadTags();
    } catch (error) {
        console.error("Error updating tag:", error);
        alert("Error updating tag: " + (error.response?.data?.error || error.message));
    }
}

async function deleteTag(tagName) {
    if (!confirm(`Delete tag "${tagName}"?`)) {
        return;
    }
    
    try {
        await $api.delete(`/api/v2/tags/${tagName}`);
        await loadTags();
    } catch (error) {
        console.error("Error deleting tag:", error);
        alert("Error deleting tag: " + (error.response?.data?.error || error.message));
    }
}

function startEdit(tag) {
    editingTag.value = { ...tag };
}

function cancelEdit() {
    editingTag.value = null;
}

const filteredTags = computed(() => {
    if (!searchQuery.value) {
        return tags.value;
    }
    const query = searchQuery.value.toLowerCase();
    return tags.value.filter(tag => 
        tag.name.toLowerCase().includes(query) || 
        tag.value.toLowerCase().includes(query)
    );
});

const tagsRemaining = computed(() => MAX_TAGS - tags.value.length);
</script>

<template lang="pug">
.content
    .level
        .level-left
            .level-item
                h2.title Tags Configuration
                span.tag.is-info.ml-3 {{ tags.length }} / {{ MAX_TAGS }}
        .level-right
            .level-item
                .field.has-addons
                    .control
                        input.input(
                            v-model="searchQuery" 
                            type="text" 
                            placeholder="Search tags..."
                        )
                    .control
                        button.button.is-primary(
                            @click="showNewTagForm = !showNewTagForm"
                            :disabled="tags.length >= MAX_TAGS"
                        )
                            span.icon
                                font-awesome-icon(icon="fas fa-plus")
                            span New Tag

hr

.box(v-if="showNewTagForm")
    h4.title.is-5 Create New Tag
    .columns
        .column.is-4
            .field
                label.label Tag Name
                .control
                    input.input(
                        v-model="newTag.name" 
                        type="text" 
                        placeholder="e.g., environment"
                    )
        .column.is-6
            .field
                label.label Tag Value
                .control
                    input.input(
                        v-model="newTag.value" 
                        type="text" 
                        placeholder="e.g., production"
                    )
        .column.is-2
            .field
                label.label &nbsp;
                .control
                    button.button.is-success.is-fullwidth(@click="createTag") Create
                    button.button.is-light.is-fullwidth.mt-2(@click="showNewTagForm = false") Cancel

.box(v-if="tagsRemaining <= 5 && tagsRemaining > 0")
    .notification.is-warning
        strong Warning: 
        | Only {{ tagsRemaining }} tag slots remaining (max {{ MAX_TAGS }})

.box(v-if="tags.length === 0")
    .notification.is-info
        | No tags defined yet. Tags can be used to categorize and label agents and operations.

.box(v-else)
    table.table.is-fullwidth.is-striped.is-hoverable
        thead
            tr
                th(style="min-width: 200px") Tag Name
                th(style="min-width: 300px") Tag Value
                th(style="width: 150px") Created
                th(style="width: 120px; text-align: center") Actions
        tbody
            tr(v-for="tag in filteredTags" :key="tag.name")
                td
                    span.tag.is-medium.is-primary {{ tag.name }}
                td
                    template(v-if="editingTag && editingTag.name === tag.name")
                        input.input(v-model="editingTag.value" type="text")
                    template(v-else)
                        | {{ tag.value }}
                td
                    small {{ new Date(tag.created).toLocaleString() }}
                td(style="text-align: center")
                    template(v-if="editingTag && editingTag.name === tag.name")
                        button.button.is-small.is-success.mr-1(@click="updateTag(editingTag)")
                            span.icon
                                font-awesome-icon(icon="fas fa-check")
                        button.button.is-small.is-light(@click="cancelEdit")
                            span.icon
                                font-awesome-icon(icon="fas fa-times")
                    template(v-else)
                        button.button.is-small.is-info.mr-1(@click="startEdit(tag)")
                            span.icon
                                font-awesome-icon(icon="fas fa-edit")
                        button.button.is-small.is-danger(@click="deleteTag(tag.name)")
                            span.icon
                                font-awesome-icon(icon="fas fa-trash")

    .notification.is-light.mt-4(v-if="filteredTags.length === 0 && searchQuery")
        | No tags match search query "{{ searchQuery }}"
</template>

<style scoped>
.table {
    background-color: white;
}

.tag.is-medium {
    font-family: monospace;
    font-weight: bold;
}
</style>
