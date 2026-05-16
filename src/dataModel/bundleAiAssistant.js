const MAX_BUNDLE_DAYS = 7

const DEFAULT_CATEGORY_ALIASES = {
  Concerts: ["concert", "music", "live", "festival", "dj", "band", "rap", "singer", "vocals"],
  Sports: ["sports", "sport", "football", "basketball", "match", "derby", "game"],
  Movies: ["movies", "movie", "cinema", "film", "screening", "premiere", "anime"],
  Shows: ["show", "performance", "magic", "illusion", "stage", "nightlife", "variety"],
  Comedy: ["comedy", "funny", "laugh", "standup", "stand-up", "roast"],
  Exhibitions: ["exhibition", "expo", "market", "fair", "creator", "fashion", "showcase"],
  Education: ["education", "conference", "summit", "forum", "startup", "talk", "learning"],
  Theatre: ["theatre", "theater", "play", "drama", "stage acting"],
  Networking: ["networking", "community", "brunch", "panel", "career", "business"],
  "Food & Culture": ["food", "culture", "tasting", "culinary"],
  "Cultural Nights": ["cultural", "traditional", "spiritual", "heritage", "slaymiya"],
}

function normalizeText(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ")
}

function toIsoDateString(value) {
  if (!value) return ""
  const text = String(value).trim()

  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    return text
  }

  const parsed = new Date(text)
  if (Number.isNaN(parsed.getTime())) return ""

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, "0")
  const day = String(parsed.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function enumerateDateRange(startDateText, endDateText) {
  const startText = toIsoDateString(startDateText)
  const endText = toIsoDateString(endDateText)

  if (!startText || !endText) return []

  const start = new Date(`${startText}T00:00:00`)
  const end = new Date(`${endText}T00:00:00`)

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) {
    return []
  }

  const dates = []
  const current = new Date(start)

  while (current <= end) {
    const year = current.getFullYear()
    const month = String(current.getMonth() + 1).padStart(2, "0")
    const day = String(current.getDate()).padStart(2, "0")
    dates.push(`${year}-${month}-${day}`)
    current.setDate(current.getDate() + 1)
  }

  return dates
}

function uniqueList(values = []) {
  return [...new Set(values.filter(Boolean))]
}

function scoreOptionMatch(inputText, optionText, aliases = []) {
  const input = normalizeText(inputText)
  const option = normalizeText(optionText)

  if (!input || !option) return 0
  if (input === option) return 100
  if (input.includes(option)) return 90
  if (option.includes(input)) return 70

  let score = 0
  const inputWords = input.split(/[\s,/-]+/).filter(Boolean)

  inputWords.forEach(word => {
    if (option.includes(word)) score += 8
  })

  aliases.forEach(alias => {
    const aliasText = normalizeText(alias)
    if (aliasText && input.includes(aliasText)) {
      score += 15
    }
  })

  return score
}

export function createEmptyAiBundleForm() {
  return {
    bundle_name: "",
    note: "",
    date_mode: "",
    start_date: "",
    end_date: "",
    exact_dates: [],
    categories: [],
    location: "",
  }
}

export function buildSelectedDates(form) {
  if (form.date_mode === "range") {
    return enumerateDateRange(form.start_date, form.end_date)
  }

  if (form.date_mode === "exact") {
    return uniqueList((form.exact_dates || []).map(toIsoDateString)).sort()
  }

  return []
}

export function matchRequestedCategories(input, availableCategories = []) {
  const text = normalizeText(input)
  if (!text) return []

  const scoredMatches = availableCategories
    .map(category => {
      const aliases = DEFAULT_CATEGORY_ALIASES[category] || []
      return {
        category,
        score: scoreOptionMatch(text, category, aliases),
      }
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)

  return scoredMatches.slice(0, 3).map(item => item.category)
}

export function matchRequestedLocation(input, availableLocations = []) {
  const text = normalizeText(input)
  if (!text) return ""

  const scoredMatches = availableLocations
    .map(location => ({
      location,
      score: scoreOptionMatch(text, location),
    }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)

  return scoredMatches[0]?.location || ""
}

export function validateAiBundleForm(form) {
  const missingFields = []
  const errors = []
  const selectedDates = buildSelectedDates(form)

  if (!String(form.bundle_name || "").trim()) {
    missingFields.push("bundle_name")
  }

  if (!String(form.date_mode || "").trim()) {
    missingFields.push("date_mode")
  } else if (form.date_mode === "range") {
    if (!toIsoDateString(form.start_date) || !toIsoDateString(form.end_date)) {
      missingFields.push("date_range")
    }
  } else if (form.date_mode === "exact") {
    if (!selectedDates.length) {
      missingFields.push("exact_dates")
    }
  }

  if (!Array.isArray(form.categories) || !form.categories.length) {
    missingFields.push("categories")
  }

  if (form.date_mode === "range" && selectedDates.length === 0) {
    errors.push("The selected date range is invalid.")
  }

  if (selectedDates.length > MAX_BUNDLE_DAYS) {
    errors.push(`The bundle can include at most ${MAX_BUNDLE_DAYS} total days.`)
  }

  return {
    missingFields: uniqueList(missingFields),
    errors,
    selectedDates,
  }
}

export function buildSuggestionRequest(form) {
  const validation = validateAiBundleForm(form)

  return {
    payload: {
      bundle_name: String(form.bundle_name || "").trim(),
      note: String(form.note || "").trim(),
      date_mode: String(form.date_mode || "").trim(),
      start_date: toIsoDateString(form.start_date),
      end_date: toIsoDateString(form.end_date),
      exact_dates: buildSelectedDates(form),
      categories: uniqueList(form.categories || []),
      location: String(form.location || "").trim(),
    },
    validation,
  }
}

export function getFirstMissingStep(missingFields = []) {
  const fieldToStep = {
    bundle_name: "name",
    date_mode: "date_mode",
    date_range: "dates",
    exact_dates: "dates",
    categories: "categories",
  }

  for (const field of missingFields) {
    if (fieldToStep[field]) {
      return fieldToStep[field]
    }
  }

  return "review"
}

export function getAssistantPrompt(step) {
  const prompts = {
    name: "What should I call this bundle?",
    note: "Do you want to add an optional note for this bundle?",
    date_mode: "Do you want exact dates or a date range?",
    dates: "Choose the dates for this bundle. The total coverage must stay within 7 days.",
    categories: "What kind of events do you want? You can type a description and I will match it to the closest categories.",
    location: "Do you want a specific location? This is optional.",
    review: "Here is your current request. If it looks good, I can generate 2 or 3 bundle suggestions.",
    suggestions: "Here are the bundle suggestions I created for you.",
  }

  return prompts[step] || "Tell me what you want for this bundle."
}

export function summarizeAnswer(step, form, selectedDates = []) {
  if (step === "name") {
    return form.bundle_name || "No bundle name"
  }

  if (step === "note") {
    return form.note || "No note added"
  }

  if (step === "date_mode") {
    return form.date_mode === "exact" ? "I want exact dates." : "I want a date range."
  }

  if (step === "dates") {
    return selectedDates.length
      ? `Selected dates: ${selectedDates.join(", ")}`
      : "No dates selected"
  }

  if (step === "categories") {
    return Array.isArray(form.categories) && form.categories.length
      ? `Categories: ${form.categories.join(", ")}`
      : "No categories selected"
  }

  if (step === "location") {
    return form.location ? `Location: ${form.location}` : "No specific location"
  }

  return ""
}