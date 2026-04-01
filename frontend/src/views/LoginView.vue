<template>
  <div class="card shadow-sm mx-auto" style="max-width: 400px; margin-top: 100px; padding: 2rem;">
    <div class="card-body">
      <h2 class="navbar-brand text-center d-block mb-4" style="font-size: 1.6rem; color: var(--primary-dark);">
        Avicenne Pay
      </h2>
      
      <p class="text-center text-muted mb-4" style="font-size: 0.9rem;">
        Veuillez vous connecter pour accéder au tableau de bord.
      </p>

      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label for="email" class="form-label" style="font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: var(--gray-muted);">
            Email Professionnel
          </label>
          <input 
            type="email" 
            id="email" 
            class="form-control" 
            v-model="email" 
            required 
            placeholder="admin@avicenne.fr"
            style="border-radius: 0.5rem;"
          >
        </div>
        
        <div class="mb-4">
          <label for="password" class="form-label" style="font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: var(--gray-muted);">
            Mot de passe
          </label>
          <input 
            type="password" 
            id="password" 
            class="form-control" 
            v-model="password" 
            required 
            placeholder="••••••"
            style="border-radius: 0.5rem;"
          >
        </div>

        <button 
          type="submit" 
          class="btn btn-success w-100 py-2" 
          :disabled="loading"
          style="border-radius: 0.5rem;"
        >
          {{ loading ? 'Connexion en cours...' : 'Se connecter' }}
        </button>
        
        <div v-if="errorMessage" class="mt-3 text-center badge bg-soft-danger w-100 py-2">
          ⚠️ {{ errorMessage }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router' // 👈 On importe l'outil de navigation

const router = useRouter() // 👈 On l'initialise

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  
  try {
    // 💡 Format OAuth2 standard attendu par FastAPI
    const formData = new URLSearchParams()
    formData.append('username', email.value)
    formData.append('password', password.value)

    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Identifiants incorrects')
    }

    // Si ça marche, on stocke le Token de sécurité
    localStorage.setItem('token', data.access_token)
    
    // 🔥 Redirection magique vers le Dashboard !
    router.push('/')
    
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}
</script>