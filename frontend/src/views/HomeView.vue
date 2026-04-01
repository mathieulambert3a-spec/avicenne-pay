<script setup>
import { ref, onMounted } from 'vue'

const userRole = ref('')
const prenomUtilisateur = ref('Utilisateur') // Valeur par défaut

// 🕵️‍♂️ On va chercher le rôle et le prénom directement dans le token stocké
onMounted(() => {
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
      
      // Si ton backend renvoie le prénom dans le JWT, on le récupère ici :
      if (decoded.prenom) {
        prenomUtilisateur.value = decoded.prenom
      }
    } catch (error) {
      console.error("Erreur de lecture du token sur l'accueil", error)
    }
  }
})
</script>

<template>
  <div class="text-start">
    <div class="mb-5">
      <h1 class="fw-bold" style="color: var(--primary-color);">
        Bonjour, {{ prenomUtilisateur }} ! 👋
      </h1>
      <p class="text-muted">
        Bienvenue sur votre espace <strong>Avicenne Pay</strong>. Vous êtes connecté avec le profil <span class="badge bg-secondary text-uppercase">{{ userRole }}</span>.
      </p>
    </div>

    <div class="row g-4">
      
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm hover-card">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title fw-bold">📝 Mes Déclarations</h5>
            <p class="card-text text-muted flex-grow-1">Saisissez vos heures de cours et vos missions du mois pour préparer votre paie.</p>
            <RouterLink to="/declarations" class="btn btn-outline-primary mt-3">Y accéder</RouterLink>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm hover-card">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title fw-bold">👤 Mon Profil</h5>
            <p class="card-text text-muted flex-grow-1">Consultez vos informations personnelles et vos contrats en cours.</p>
            <RouterLink to="/profil" class="btn btn-outline-primary mt-3">Voir mon profil</RouterLink>
          </div>
        </div>
      </div>

      <div v-if="['admin', 'coordo'].includes(userRole)" class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm border-primary hover-card">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title fw-bold text-primary">📊 Synthèse Paie</h5>
            <p class="card-text text-muted flex-grow-1">Visualisez et validez les états de paie de l'ensemble des formateurs pour ce mois-ci.</p>
            <RouterLink to="/synthese-paie" class="btn btn-primary mt-3">Gérer la paie</RouterLink>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Un petit effet au survol des cartes pour faire pro ! */
.hover-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.hover-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
}
</style>