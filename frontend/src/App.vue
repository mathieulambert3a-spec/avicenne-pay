<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import './assets/main.css'

const router = useRouter()

// --- États de l'application ---
const estConnecte = ref(false)
const userRole = ref('')
const loading = ref(false)
const errorMessage = ref('')
const reponsePython = ref('')

// --- Fonction pour lire le rôle dans le token ---
const extraireRoleDuToken = () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join(''))

      const decoded = JSON.parse(jsonPayload)
      userRole.value = decoded.role
      estConnecte.value = true
    } catch (error) {
      console.error("Erreur de lecture du token", error)
      seDeconnecter()
    }
  }
}

onMounted(() => {
  extraireRoleDuToken()
})

// --- Fonction de test Python d'origine ---
async function appelerLeBackend() {
  try {
    const response = await fetch('http://localhost:8000/') 
    const data = await response.json()
    reponsePython.value = data.message || data
  } catch (error) {
    reponsePython.value = "Erreur de connexion : " + error.message
  }
}

// --- Fonction de déconnexion ---
const seDeconnecter = () => {
  localStorage.removeItem('token')
  userRole.value = ''
  estConnecte.value = false
  
  // 🚪 3. On pousse l'utilisateur vers la page de login
  router.push('/login')
}

// --- 🔐 LOGIQUE DES ROLES ---
const peutVoirGestionUtilisateurs = computed(() => ['admin', 'coordo'].includes(userRole.value))
const peutVoirCcda = computed(() => ['admin', 'coordo'].includes(userRole.value))
const peutVoirCcdu = computed(() => userRole.value === 'admin')
const peutVoirPilotageEtPaie = computed(() => ['admin', 'coordo'].includes(userRole.value))
</script>

<template>
  <div class="container mt-4">
    
    <div v-if="$route.name === 'login'">
      <RouterView />
    </div>

    <div v-else>
      <nav class="navbar navbar-expand-lg shadow-sm mb-4">
        <div class="container-fluid d-flex justify-content-between align-items-center p-3">
          
          <div class="d-flex align-items-center gap-2">
            <span class="navbar-brand mb-0" style="color: var(--primary-color);">
              Avicenne Pay
            </span>
            <span v-if="estConnecte" class="badge bg-secondary text-uppercase" style="font-size: 0.75rem;">{{ userRole }}</span>
          </div>

          <div class="d-flex gap-2 align-items-center flex-wrap">
            <RouterLink to="/dashboard" class="hover-primary text-decoration-none fw-bold">Tableau de bord</RouterLink>
            <RouterLink to="/profil" class="hover-primary text-decoration-none fw-bold">Mon profil</RouterLink>
            <RouterLink to="/declarations" class="hover-primary text-decoration-none fw-bold">Déclarations</RouterLink>

            <RouterLink v-if="peutVoirGestionUtilisateurs" to="/utilisateurs" class="hover-primary text-decoration-none fw-bold">Utilisateurs</RouterLink>
            <RouterLink v-if="peutVoirCcda" to="/catalogue-ccda" class="hover-primary text-decoration-none fw-bold">Catalogue CCDA</RouterLink>
            <RouterLink v-if="peutVoirCcdu" to="/catalogue-ccdu" class="hover-primary text-decoration-none fw-bold">Catalogue CCDU</RouterLink>
            <RouterLink v-if="peutVoirPilotageEtPaie" to="/pilotage" class="hover-primary text-decoration-none fw-bold">Pilotage</RouterLink>
            <RouterLink v-if="peutVoirPilotageEtPaie" to="/synthese-paie" class="hover-primary text-decoration-none fw-bold">Synthèse Paie</RouterLink>

            <button class="btn btn-sm btn-outline-danger fw-bold ms-2" @click="seDeconnecter">Déconnexion</button>
          </div>
        </div>
      </nav>

      <main class="container text-center mt-5">
        
        <button @click="appelerLeBackend" class="btn btn-warning p-3 mb-4">
          Tester la connexion avec Python 🐍
        </button>

        <div v-if="reponsePython" class="alert alert-info mt-3 shadow-sm mx-auto" style="max-width: 500px;">
          <strong>Réponse du serveur :</strong> {{ reponsePython }}
        </div>

        <div class="mt-5">
          <RouterView />
        </div>
      </main>
    </div>

  </div>
</template>

<style scoped>
nav a.router-link-exact-active {
  color: var(--primary-color) !important;
  border-bottom: 2px solid var(--primary-color);
  background-color: rgba(13, 110, 253, 0.05);
  border-radius: 4px;
}
nav a {
  color: var(--gray-muted);
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}
</style>

