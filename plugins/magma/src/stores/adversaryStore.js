import { defineStore } from "pinia";
import { useAbilityStore as abilityStore } from "./abilityStore";

export const useAdversaryStore = defineStore("adversaryStore", {
  state: () => {
    return {
      adversaries: [],
      selectedAdversary: {},
      selectedAdversaryAbilities: [],
      objectives: [],
      selectedObjective: "",
    };
  },
  actions: {
    async getAdversaries($api) {
      try {
        const response = await $api.get("/api/v2/adversaries");
        this.adversaries = response.data;
      } catch (error) {
        console.error("Error fetching adversaries", error);
      }
    },
    async getObjectives($api) {
      try {
        const response = await $api.get("/api/v2/objectives");
        this.objectives = response.data;
      } catch (error) {
        console.error("Error fetching objectives", error);
      }
    },
    async createObjective($api) {
      try {
        const response = await $api.post("/api/v2/objectives", {
          name: "New objective",
          description: "Enter a description",
        });
        this.objectives.push(response.data);
        this.selectedObjective = this.objectives[this.objectives.length - 1];
      } catch (error) {
        console.error("Error creating objective", error);
      }
    },
    async saveObjective($api) {
      try {
        await $api.put(
          `/api/v2/objectives/${this.selectedObjective.id}`,
          this.selectedObjective
        );
      } catch (error) {
        console.error("Error saving objective", error);
      }
    },
    async createAdversary($api, adversary = null) {
      try {
        const response = await $api.post(
          "/api/v2/adversaries",
          adversary || {
            name: "New adversary",
            description: "---",
            atomic_ordering: [],
          }
        );
        this.adversaries.push(response.data);
        this.adversaries.sort((a, b) => a.name > b.name);
        this.selectedAdversary = response.data;
        this.updateSelectedAdversaryAbilities();
      } catch (error) {
        console.error("Error creating an adversary", error);
      }
    },
    async saveSelectedAdversary($api) {
      const reqBody = {
        name: this.selectedAdversary.name,
        description: this.selectedAdversary.description,
        objective: this.selectedAdversary.objective,
        atomic_ordering: this.selectedAdversaryAbilities.map(
          (ability) => ability.ability_id
        ),
      };

      try {
        const response = await $api.patch(
          `/api/v2/adversaries/${this.selectedAdversary.adversary_id}`,
          reqBody
        );
        if (response.status != 200) {
          throw new Error(`Non-200 HTTP response code from /api/v2/adversaries/${this.selectedAdversary.adversary_id}: ${response.status}`);
        }
        // Refresh the entire adversaries list to ensure UI is in sync
        await this.getAdversaries($api);
        // Re-select the adversary with updated data
        const updatedAdversary = this.adversaries.find(
          (adv) => adv.adversary_id === response.data.adversary_id
        );
        if (updatedAdversary) {
          this.selectedAdversary = updatedAdversary;
          this.updateSelectedAdversaryAbilities();
        }
        return response.data;
      } catch (error) {
        console.error("Error saving adversary", error);
      }
    },
    async deleteAdversary($api) {
      try {
        await $api.delete(
          `/api/v2/adversaries/${this.selectedAdversary.adversary_id}`
        );
        // Clear selection first
        this.selectedAdversary = {};
        this.selectedAdversaryAbilities = [];
        // Refresh the entire list to ensure UI is in sync
        await this.getAdversaries($api);
        return true;
      } catch (error) {
        console.error("Error deleting adversary", error);
        return false;
      }
    },
    async deleteAllAdversaries($api) {
      try {
        const adversariesToDelete = [...this.adversaries];
        let deletedCount = 0;
        let errorCount = 0;
        
        for (const adversary of adversariesToDelete) {
          try {
            await $api.delete(`/api/v2/adversaries/${adversary.adversary_id}`);
            deletedCount++;
          } catch (err) {
            console.error(`Error deleting adversary ${adversary.name}:`, err);
            errorCount++;
          }
        }
        
        // Refresh the list
        this.selectedAdversary = {};
        this.selectedAdversaryAbilities = [];
        await this.getAdversaries($api);
        
        return { deleted: deletedCount, errors: errorCount };
      } catch (error) {
        console.error("Error deleting all adversaries", error);
        throw error;
      }
    },
    updateSelectedAdversaryAbilities() {
      if (!this.selectedAdversary.atomic_ordering) {
        this.selectedAdversaryAbilities = [];
      } else {
        this.selectedAdversaryAbilities =
          this.selectedAdversary.atomic_ordering.map((ability_id) => {
            return {
              ...abilityStore().abilities.find(
                (ability) => ability.ability_id === ability_id
              ),
            };
          });
      }
    },
  },
});
