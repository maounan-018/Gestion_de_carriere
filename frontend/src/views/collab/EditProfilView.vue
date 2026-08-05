<script setup lang="ts">
/**
 * Éditer mon profil · ÉCRAN DÉDIÉ (collaborateur).
 * Sections éditables + champs déroulants, dépôt / remplacement du CV (PDF conservé
 * côté serveur, alimente extractions & analyses, présenté au manager / à la HRBP),
 * et extraction assistée des compétences. Sauvegarde via PATCH /profils/me.
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Sparkles, FileText, UploadCloud, Check, ArrowLeft } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { MyCvStatus } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import LoadingState from '@/components/ui/LoadingState.vue'

const router = useRouter()
const { toast } = useToast()

const HORIZONS = ['6 mois', '1 an', '2-3 ans']
const TYPES = ['Management', 'Expertise', 'Mobilité géographique', 'Mission transverse']
const inputCls =
  'w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm text-ink outline-none focus:border-green-line'

const loading = ref(true)
const saving = ref(false)
const posteActuel = ref('')
const posteVise = ref('')
const horizon = ref('')
const typeEvolution = ref('')
const mobiliteGeo = ref('')
const disponibilite = ref('')
const bio = ref('')
const aspirations = ref('')

// CV conservé (Lot 4)
const cv = ref<MyCvStatus | null>(null)
const cvBusy = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const cvDate = computed(() =>
  cv.value?.uploadedAt
    ? new Date(cv.value.uploadedAt).toLocaleDateString('fr-FR', { dateStyle: 'medium' })
    : '',
)

onMounted(async () => {
  loading.value = true
  try {
    const [p, status] = await Promise.all([
      apiService.getMyProfilEditable(),
      apiService.getMyCvStatus(),
    ])
    posteActuel.value = p?.poste_actuel ?? ''
    posteVise.value = p?.poste_vise ?? ''
    horizon.value = p?.horizon ?? ''
    typeEvolution.value = p?.type_evolution ?? ''
    mobiliteGeo.value = p?.mobilite_geo ?? ''
    disponibilite.value = p?.disponibilite ?? ''
    bio.value = p?.bio ?? ''
    aspirations.value = p?.aspirations ?? ''
    cv.value = status
  } finally {
    loading.value = false
  }
})

async function save() {
  if (saving.value) return
  saving.value = true
  try {
    await apiService.updateMyProfil({
      poste_actuel: posteActuel.value.trim(),
      poste_vise: posteVise.value.trim(),
      horizon: horizon.value,
      type_evolution: typeEvolution.value,
      mobilite_geo: mobiliteGeo.value.trim(),
      disponibilite: disponibilite.value.trim(),
      bio: bio.value.trim(),
      aspirations: aspirations.value.trim(),
    })
    toast('Profil mis à jour', 'ok')
    router.push({ name: 'collab.profil' })
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la mise à jour', 'error')
  } finally {
    saving.value = false
  }
}

function pickFile() {
  fileInput.value?.click()
}

async function onCvChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // permet de re-sélectionner le même fichier
  if (!file) return
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    toast('Le CV doit être un fichier PDF.', 'error')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    toast('CV trop volumineux (max 10 Mo).', 'error')
    return
  }
  cvBusy.value = true
  try {
    cv.value = await apiService.uploaderMonCv(file)
    toast('CV enregistré · il sera présenté à votre manager et à la HRBP', 'ok')
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec du téléversement du CV', 'error')
  } finally {
    cvBusy.value = false
  }
}

// Extraction assistée (texte) : enrichit les compétences détenues depuis le CV.
const showExtract = ref(false)
const cvText = ref('')
const extractBusy = ref(false)
async function submitExtract() {
  const texte = cvText.value.trim()
  if (texte.length < 10 || extractBusy.value) return
  extractBusy.value = true
  try {
    const n = await apiService.extraireMonCv(texte)
    toast(
      n > 0
        ? `${n} compétence(s) extraite(s) et ajoutée(s) à votre profil`
        : 'Aucune compétence détectée dans ce texte',
      'ok',
    )
    showExtract.value = false
    cvText.value = ''
  } catch {
    toast('Extraction indisponible pour le moment. Réessayez.', 'error')
  } finally {
    extractBusy.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <div class="flex items-center gap-3">
      <BaseButton variant="secondary" size="sm" @click="router.push({ name: 'collab.profil' })">
        <ArrowLeft :size="15" /> Retour
      </BaseButton>
      <div>
        <h2 class="font-display text-xl font-bold text-ink">Éditer mon profil</h2>
        <p class="text-sm text-ink-3">Vos informations orientent vos recommandations et la préparation de vos entretiens.</p>
      </div>
    </div>

    <LoadingState v-if="loading" label="Chargement de votre profil…" />

    <template v-else>
      <!-- CV conservé -->
      <BaseCard title="Mon CV">
        <p class="mb-3 text-xs text-ink-3">
          Votre CV (PDF) est conservé de façon sécurisée. Il alimente vos analyses et est présenté à
          votre manager et à la HRBP lorsque vous candidatez. Un nouveau dépôt remplace l'ancien.
        </p>
        <div class="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-panel p-3.5">
          <div
            class="grid h-11 w-11 shrink-0 place-items-center rounded-xl"
            :class="cv?.filename ? 'bg-green-soft text-green-deep' : 'bg-panel-2 text-ink-3'"
          >
            <FileText :size="20" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-bold text-ink">{{ cv?.filename || 'Aucun CV déposé' }}</p>
            <p class="text-xs text-ink-3">
              <span v-if="cv?.filename" class="inline-flex items-center gap-1 text-green-deep">
                <Check :size="12" /> Conservé · déposé le {{ cvDate }}
              </span>
              <span v-else>Déposez votre CV au format PDF (max 10 Mo).</span>
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <a
              v-if="cv?.filename"
              :href="apiService.cvUrl(cv.profilId)"
              target="_blank"
              rel="noopener"
              class="text-xs font-semibold text-green-deep hover:underline"
            >Consulter</a>
            <BaseButton size="sm" :disabled="cvBusy" @click="pickFile">
              <UploadCloud :size="15" /> {{ cvBusy ? 'Envoi…' : cv?.filename ? 'Remplacer' : 'Déposer mon CV' }}
            </BaseButton>
          </div>
        </div>
        <input ref="fileInput" type="file" accept="application/pdf,.pdf" class="hidden" @change="onCvChange" />
        <button
          type="button"
          class="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-green-deep hover:underline"
          @click="showExtract = true"
        >
          <Sparkles :size="13" /> Extraire mes compétences depuis mon CV
        </button>
      </BaseCard>

      <!-- Informations générales -->
      <BaseCard title="Informations générales">
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-ink-2">Poste actuel</label>
            <input v-model="posteActuel" :class="inputCls" maxlength="200" placeholder="Ex : Analyste Risque Senior" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-ink-2">Description / à propos</label>
            <textarea v-model="bio" rows="3" :class="inputCls" placeholder="Décrivez votre parcours en quelques lignes…" />
          </div>
        </div>
      </BaseCard>

      <!-- Aspirations & poste visé -->
      <BaseCard title="Aspirations & poste visé">
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-semibold text-ink-2">Poste visé</label>
            <input v-model="posteVise" :class="inputCls" maxlength="200" placeholder="Ex : Manager d'équipe Risques" />
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-xs font-semibold text-ink-2">Horizon</label>
              <select v-model="horizon" :class="inputCls">
                <option value="">Non précisé</option>
                <option v-for="h in HORIZONS" :key="h" :value="h">{{ h }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-semibold text-ink-2">Type d'évolution souhaitée</label>
              <select v-model="typeEvolution" :class="inputCls">
                <option value="">Non précisé</option>
                <option v-for="t in TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-xs font-semibold text-ink-2">Zones géographiques</label>
              <input v-model="mobiliteGeo" :class="inputCls" maxlength="200" placeholder="Casablanca · Paris…" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-semibold text-ink-2">Disponibilité</label>
              <input v-model="disponibilite" :class="inputCls" maxlength="64" placeholder="Ex : 6 à 12 mois" />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-ink-2">Mes ambitions (texte libre)</label>
            <textarea v-model="aspirations" rows="3" :class="inputCls" placeholder="Décrivez ce que vous visez et pourquoi…" />
          </div>
        </div>
      </BaseCard>

      <div class="sticky bottom-0 flex justify-end gap-2 rounded-2xl border border-border bg-paper/95 p-3 shadow-card backdrop-blur">
        <BaseButton variant="secondary" @click="router.push({ name: 'collab.profil' })">Annuler</BaseButton>
        <BaseButton :disabled="saving" @click="save">
          <Check :size="15" /> {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
        </BaseButton>
      </div>
    </template>

    <BaseModal v-model="showExtract" title="Extraire mes compétences depuis mon CV">
      <div class="space-y-3">
        <p class="text-xs text-ink-3">
          Collez le texte de votre CV ou un résumé de votre parcours. L'IA en extrait vos compétences
          détenues et les ajoute à votre profil (source « CV »).
        </p>
        <textarea
          v-model="cvText"
          rows="8"
          placeholder="Collez ici votre CV ou un résumé de votre parcours…"
          :class="inputCls"
        />
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="extractBusy" @click="showExtract = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="extractBusy || cvText.trim().length < 10" @click="submitExtract">
          <Sparkles :size="14" /> {{ extractBusy ? 'Analyse…' : 'Extraire mes compétences' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
