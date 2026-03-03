/**
 * Avicenne Pay - Scripts globaux
 */

// 1. Gestion de la visibilité des mots de passe
// Utilisé dans profile.html, login.html et admin/user_form.html
function toggleVisibility(fieldId, btn) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    if (field.type === 'password') {
        field.type = 'text';
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
        field.type = 'password';
        btn.innerHTML = '<i class="bi bi-eye"></i>';
    }
}

// 2. Initialisations au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-fermeture des alertes (ex: message "profil incomplet") après 8 secondes
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 8000);
    });

    // Activation des tooltips Bootstrap (si tu en utilises)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    console.log("Avicenne Pay JS : Initialisé avec succès");
});

// 3. Utilitaires pour l'administration
function confirmAction(message) {
    return confirm(message || "Êtes-vous sûr de vouloir effectuer cette action ?");
}

// 4. Formatage des nombres pour l'affichage (ex: 1250.5 -> 1 250,50 €)
function formatMoney(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
    }).format(amount);
}