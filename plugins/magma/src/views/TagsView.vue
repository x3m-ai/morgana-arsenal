<script setup>
import { ref, inject, onMounted, computed } from "vue";

const $api = inject("$api");

const tags = ref([]);
const editingTag = ref(null);
const newTag = ref({ name: "", value: "" });
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
        return;
    }
    
    if (tags.value.length >= MAX_TAGS) {
        alert(`Maximum ${MAX_TAGS} tags allowed`);
        return;
    }
    
    try {
        await $api.post("/api/v2/tags", newTag.value);
        newTag.value = { name: "", value: "" };
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
                .field
                    .control
                        input.input(
                            v-model="searchQuery" 
                            type="text" 
                            placeholder="Search tags..."
                        )

    hr

    .notification.is-warning(v-if="tagsRemaining <= 5 && tagsRemaining > 0")
        strong Warning: 
        | Only {{ tagsRemaining }} tag slots remaining (max {{ MAX_TAGS }})

    .notification.is-info(v-if="tags.length === 0")
        | No tags defined yet. Tags can be used to categorize and label agents and operations.

    .box(v-if="filteredTags.length > 0")
        .table-container(style="max-height: 600px; overflow-y: auto;")
            table.table.is-fullwidth.is-hoverable(style="background: transparent;")
                tbody
                    tr(v-for="tag in filteredTags" :key="tag.name" style="border-bottom: 1px solid #dbdbdb;")
                        td(style="width: 30%; padding: 20px; text-align: right; vertical-align: middle; font-weight: 500;")
                            | {{ tag.name }}
                        td(style="width: 50%; padding: 20px; vertical-align: middle;")
                            template(v-if="editingTag && editingTag.name === tag.name")
                                input.input(v-model="editingTag.value" type="text" style="max-width: 500px;")
                            template(v-else)
                                | {{ tag.value || '(empty)' }}
                        td(style="width: 20%; padding: 20px; text-align: center; vertical-align: middle;")
                            template(v-if="editingTag && editingTag.name === tag.name")
                                button.button.is-small.is-success.mr-2(
                                    @click="updateTag(editingTag)"
                                    title="Save"
                                )
                                    span.icon
                                        font-awesome-icon(icon="fas fa-check")
                                button.button.is-small.is-light(
                                    @click="cancelEdit"
                                    title="Cancel"
                                )
                                    span.icon
                                        font-awesome-icon(icon="fas fa-times")
                            template(v-else)
                                button.button.is-small.is-info.mr-2(
                                    @click="startEdit(tag)"
                                    title="Edit"
                                    style="border-radius: 4px;"
                                )
                                    span.icon
                                        font-awesome-icon(icon="fas fa-edit")
                                button.button.is-small.is-danger(
                                    @click="deleteTag(tag.name)"
                                    title="Delete"
                                    style="border-radius: 4px;"
                                )
                                    span.icon
                                        font-awesome-icon(icon="fas fa-trash")
                    
                    // New tag row (always at bottom)
                    tr(v-if="tags.length < MAX_TAGS" style="border-bottom: 1px solid #dbdbdb; background: #f9f9f9;")
                        td(style="width: 30%; padding: 20px; text-align: right; vertical-align: middle;")
                            input.input(
                                v-model="newTag.name"
                                type="text"
                                placeholder="new_tag_name"
                                style="max-width: 300px;"
                                @keyup.enter="createTag"
                            )
                        td(style="width: 50%; padding: 20px; vertical-align: middle;")
                            input.input(
                                v-model="newTag.value"
                                type="text"
                                placeholder="tag value"
                                style="max-width: 500px;"
                                @keyup.enter="createTag"
                            )
                        td(style="width: 20%; padding: 20px; text-align: center; vertical-align: middle;")
                            button.button.is-small.is-success(
                                @click="createTag"
                                :disabled="!newTag.name.trim()"
                                title="Create Tag"
                                style="border-radius: 4px;"
                            )
                                span.icon
                                    font-awesome-icon(icon="fas fa-plus")
                                span Create

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
