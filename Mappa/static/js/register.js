document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('register-form');
    // Django assegna ID come 'id_nomecampo'
    const passwordInput = document.getElementById('id_password1');
    const confirmPasswordInput = document.getElementById('id_password2');
    const emailInput = document.getElementById('id_email');

    if (form && passwordInput && confirmPasswordInput) {
        // Funzione per mostrare un messaggio di errore sotto un campo
        const showError = (inputElement, message) => {
            // Rimuovi eventuali errori precedenti
            removeError(inputElement);
            // Crea l'elemento per l'errore
            const errorElement = document.createElement('div');
            errorElement.className = 'field-errors js-error'; // Aggiungi una classe per identificarlo
            errorElement.innerHTML = `<small>${message}</small>`;
            // Inserisci l'errore dopo l'input
            inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
            inputElement.classList.add('is-invalid'); // Opzionale: aggiungi classe per stile
        };

        // Funzione per rimuovere un messaggio di errore
        const removeError = (inputElement) => {
            const errorElement = inputElement.parentNode.querySelector('.js-error');
            if (errorElement) {
                errorElement.remove();
            }
            inputElement.classList.remove('is-invalid'); // Opzionale: rimuovi classe stile
        };

        // Validazione in tempo reale della conferma password
        confirmPasswordInput.addEventListener('input', () => {
            if (passwordInput.value !== confirmPasswordInput.value) {
                showError(confirmPasswordInput, 'Le password non coincidono.');
            } else {
                removeError(confirmPasswordInput);
            }
        });

        // Assicurati che la validazione avvenga anche quando si cambia la prima password
        passwordInput.addEventListener('input', () => {
            if (confirmPasswordInput.value && passwordInput.value !== confirmPasswordInput.value) {
                showError(confirmPasswordInput, 'Le password non coincidono.');
            } else if (confirmPasswordInput.value) {
                // Se le password ora coincidono, rimuovi l'errore
                removeError(confirmPasswordInput);
            }
        });

        // Validazione al momento dell'invio del form (aggiuntiva a quella del server)
        form.addEventListener('submit', function(event) {
            let isValid = true;

            // 1. Controllo corrispondenza password
            if (passwordInput.value !== confirmPasswordInput.value) {
                showError(confirmPasswordInput, 'Le password non coincidono.');
                isValid = false; // Impedisce l'invio se non coincidono
            } else {
                removeError(confirmPasswordInput); // Rimuovi l'errore se coincidono
            }

            // 2. Aggiungi qui altre validazioni JavaScript se necessario
            // Esempio: controllo complessità password (più avanzato)
            // if (passwordInput.value.length < 8) {
            //     showError(passwordInput, 'La password deve essere lunga almeno 8 caratteri.');
            //     isValid = false;
            // } else {
            //     removeError(passwordInput);
            // }


            // Se qualcosa non è valido, impedisci l'invio del form
            if (!isValid) {
                event.preventDefault(); // Blocca l'invio del form
                // Trova il primo campo con errore e scorri fino ad esso (opzionale)
                const firstError = form.querySelector('.js-error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            // Se tutto è valido in JS, il form viene inviato al server Django per la validazione finale e il salvataggio.
        });
    }

    // Aggiungi qui eventuali altre logiche JS, come mostrare/nascondere password, ecc.
});
