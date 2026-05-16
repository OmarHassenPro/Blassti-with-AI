<template>
  <v-dialog
    :model-value="modelValue"
    max-width="980"
    scrollable
    @update:model-value="closeDialog"
  >
    <v-card rounded="xl" class="ai-dialog">
      <v-toolbar color="primary" density="comfortable">
        <v-toolbar-title class="font-weight-bold">
          <v-icon start>mdi-robot-excited-outline</v-icon>
          AI Bundle Assistant
        </v-toolbar-title>

        <v-spacer />

        <v-btn icon variant="text" @click="closeDialog(false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text class="pa-0">
        <v-row no-gutters>
          <v-col cols="12" md="7" class="chat-panel">
            <div class="messages">
              <div
                v-for="(message, index) in messages"
                :key="index"
                class="message-row"
                :class="message.role === 'user' ? 'message-row--user' : 'message-row--assistant'"
              >
                <div class="message-bubble">
                  <div class="message-role">
                    {{ message.role === 'user' ? 'You' : 'AI Assistant' }}
                  </div>
                  <div class="message-text">
                    {{ message.content }}
                  </div>
                </div>
              </div>

              <div v-if="loading" class="message-row message-row--assistant">
                <div class="message-bubble">
                  <div class="message-role">AI Assistant</div>
                  <div class="message-text">
                    Thinking...
                  </div>
                </div>
              </div>
            </div>

            <div class="composer">
              <div class="examples mb-3">
                <v-chip
                  v-for="example in examples"
                  :key="example"
                  size="small"
                  rounded="pill"
                  variant="tonal"
                  class="mr-2 mb-2"
                  @click="prompt = example"
                >
                  {{ example }}
                </v-chip>
              </div>

              <v-textarea
                v-model="prompt"
                label="Write what you want"
                placeholder="Example: I want a fun weekend in Tunis with concerts and movies"
                variant="outlined"
                rounded="xl"
                rows="3"
                auto-grow
                hide-details
                @keydown.ctrl.enter.prevent="sendMessage"
              />

              <div class="d-flex justify-space-between align-center mt-3">
                <div class="text-caption text-medium-emphasis">
                  Ctrl + Enter to send
                </div>

                <v-btn
                  color="primary"
                  rounded="lg"
                  class="text-none"
                  :loading="loading"
                  :disabled="!prompt.trim()"
                  @click="sendMessage"
                >
                  <v-icon start>mdi-send</v-icon>
                  Send
                </v-btn>
              </div>
            </div>
          </v-col>

          <v-col cols="12" md="5" class="suggestions-panel">
            <div class="pa-4">
              <div class="text-h6 font-weight-bold mb-1">
                AI suggestions
              </div>

              <div class="text-body-2 text-medium-emphasis mb-4">
                Choose one suggestion, then you can edit it in the bundle builder.
              </div>

              <v-alert
                v-if="errorText"
                type="error"
                variant="tonal"
                rounded="xl"
                class="mb-4"
              >
                {{ errorText }}
              </v-alert>

              <v-alert
                v-if="optionsWarning"
                type="warning"
                variant="tonal"
                rounded="xl"
                class="mb-4"
              >
                {{ optionsWarning }}
              </v-alert>

              <div v-if="suggestions.length" class="suggestion-list">
                <v-card
                  v-for="bundle in suggestions"
                  :key="bundle.id"
                  rounded="xl"
                  class="suggestion-card pa-4 mb-4"
                  elevation="0"
                >
                  <div class="d-flex align-start justify-space-between ga-3 mb-2">
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">
                        {{ bundle.title }}
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        {{ bundle.description }}
                      </div>
                    </div>

                    <v-chip size="small" color="primary" variant="tonal" rounded="pill">
                      {{ bundle.summary?.total_events || bundle.selected_events?.length || 0 }} events
                    </v-chip>
                  </div>

                  <div class="d-flex flex-wrap ga-2 my-3">
                    <v-chip
                      v-for="category in bundle.summary?.categories || []"
                      :key="category"
                      size="x-small"
                      rounded="pill"
                      variant="tonal"
                    >
                      {{ category }}
                    </v-chip>

                    <v-chip
                      v-for="location in bundle.summary?.locations || []"
                      :key="location"
                      size="x-small"
                      rounded="pill"
                      variant="tonal"
                    >
                      <v-icon start size="12">mdi-map-marker-outline</v-icon>
                      {{ location }}
                    </v-chip>
                  </div>

                  <div class="event-list">
                    <div
                      v-for="event in bundle.selected_events || []"
                      :key="event.id"
                      class="event-row"
                    >
                      <v-avatar size="42" rounded="lg">
                        <v-img :src="event.image" cover />
                      </v-avatar>

                      <div class="min-w-0">
                        <div class="font-weight-bold text-truncate">
                          {{ event.title }}
                        </div>
                        <div class="text-caption text-medium-emphasis text-truncate">
                          {{ event.date }} • {{ event.time }} • {{ event.city }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <v-btn
                    block
                    color="success"
                    rounded="lg"
                    class="text-none mt-4"
                    @click="useBundle(bundle)"
                  >
                    <v-icon start>mdi-check-circle-outline</v-icon>
                    Use this bundle
                  </v-btn>
                </v-card>
              </div>

              <div v-else class="empty-state">
                <v-icon size="42" class="mb-3">mdi-robot-happy-outline</v-icon>
                <div class="font-weight-bold mb-1">No suggestion yet</div>
                <div class="text-body-2 text-medium-emphasis">
                  Tell the assistant what kind of bundle you want.
                </div>
              </div>

              <v-divider class="my-4" />

              <div class="text-caption text-medium-emphasis mb-2">
                Available categories
              </div>

              <div class="d-flex flex-wrap ga-2">
                <v-chip
                  v-for="category in availableCategories"
                  :key="category"
                  size="x-small"
                  rounded="pill"
                  variant="outlined"
                >
                  {{ category }}
                </v-chip>
              </div>

              <div class="text-caption text-medium-emphasis mt-4 mb-2">
                Available locations
              </div>

              <div class="d-flex flex-wrap ga-2">
                <v-chip
                  v-for="location in availableLocations"
                  :key="location"
                  size="x-small"
                  rounded="pill"
                  variant="outlined"
                >
                  {{ location }}
                </v-chip>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from "vue"

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["update:modelValue", "use-bundle"])

const API_BASE_URL = "http://localhost:5000/api"

const prompt = ref("")
const loading = ref(false)
const errorText = ref("")
const optionsWarning = ref("")
const suggestions = ref([])
const availableCategories = ref([])
const availableLocations = ref([])

const examples = [
  "I want a fun weekend in Tunis with music and cinema",
  "Create a sports bundle near Ariana",
  "Je veux un bundle culturel à Tunis",
  "Give me popular events for next week",
]

const messages = ref([
  {
    role: "assistant",
    content:
      "Tell me what kind of bundle you want. You can write naturally, for example: concerts in Tunis this weekend, sports events near Ariana, or a family-friendly movie bundle.",
  },
])

watch(
  () => props.modelValue,
  isOpen => {
    if (isOpen) {
      loadOptions()
    }
  }
)

function closeDialog(value) {
  emit("update:modelValue", value)
}

async function loadOptions() {
  optionsWarning.value = ""

  try {
    const response = await fetch(`${API_BASE_URL}/ai/bundle-options`)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data?.error || "Backend options could not be loaded.")
    }

    availableCategories.value = Array.isArray(data.categories) ? data.categories : []
    availableLocations.value = Array.isArray(data.locations) ? data.locations : []
  } catch (error) {
    optionsWarning.value =
      "The backend options could not be loaded. Start the Python backend before using AI suggestions."
  }
}

function buildHistoryForBackend() {
  return messages.value
    .filter(message => ["user", "assistant"].includes(message.role))
    .slice(-8)
    .map(message => ({
      role: message.role,
      content: message.content,
    }))
}

async function sendMessage() {
  const text = prompt.value.trim()
  if (!text || loading.value) return

  errorText.value = ""
  suggestions.value = []

  messages.value.push({
    role: "user",
    content: text,
  })

  prompt.value = ""
  loading.value = true

  try {
    const response = await fetch(`${API_BASE_URL}/ai/llm-bundle-suggestions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: text,
        history: buildHistoryForBackend(),
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      const errorMessage =
        data?.errors?.[0] ||
        data?.error ||
        "The AI backend returned an error."

      throw new Error(errorMessage)
    }

    if (data.reply) {
      messages.value.push({
        role: "assistant",
        content: data.reply,
      })
    } else if (data.question) {
      messages.value.push({
        role: "assistant",
        content: data.question,
      })
    } else {
      messages.value.push({
        role: "assistant",
        content: "I finished checking your request.",
      })
    }

    suggestions.value = Array.isArray(data.bundles) ? data.bundles : []

    if (!suggestions.value.length && data.question) {
      messages.value.push({
        role: "assistant",
        content: data.question,
      })
    }

    if (Array.isArray(data.errors) && data.errors.length) {
      errorText.value = data.errors[0]
    }
  } catch (error) {
    errorText.value = error?.message || "AI request failed."

    messages.value.push({
      role: "assistant",
      content:
        "I could not connect to the AI backend. Check that Flask is running and your OpenRouter key is correct.",
    })
  } finally {
    loading.value = false
  }
}

function useBundle(bundle) {
  emit("use-bundle", bundle)
  closeDialog(false)
}
</script>

<style scoped>
.ai-dialog {
  overflow: hidden;
}

.chat-panel {
  border-right: 1px solid rgba(148, 163, 184, 0.2);
  min-height: 680px;
  display: flex;
  flex-direction: column;
}

.suggestions-panel {
  min-height: 680px;
  background: rgba(148, 163, 184, 0.06);
  overflow-y: auto;
}

.messages {
  flex: 1;
  padding: 18px;
  overflow-y: auto;
  display: grid;
  align-content: start;
  gap: 12px;
  max-height: 480px;
}

.message-row {
  display: flex;
}

.message-row--user {
  justify-content: flex-end;
}

.message-row--assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 84%;
  border-radius: 20px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.08);
}

.message-row--user .message-bubble {
  background: rgba(99, 102, 241, 0.18);
}

.message-role {
  font-size: 0.72rem;
  font-weight: 800;
  opacity: 0.7;
  margin-bottom: 4px;
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.45;
}

.composer {
  padding: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}

.suggestion-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.08);
}

.event-list {
  display: grid;
  gap: 10px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px;
  border-radius: 14px;
  background: rgba(148, 163, 184, 0.08);
}

.min-w-0 {
  min-width: 0;
}

.empty-state {
  min-height: 260px;
  display: grid;
  place-items: center;
  align-content: center;
  text-align: center;
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 24px;
  padding: 24px;
}

@media (max-width: 960px) {
  .chat-panel {
    border-right: 0;
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
    min-height: 560px;
  }

  .suggestions-panel {
    min-height: auto;
  }
}
</style>