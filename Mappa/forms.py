from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import RegistrationToken # Importa il modello Token
from django.utils import timezone # Per gestire date e ore
import uuid # Per validare il formato UUID

class RegisterForm(UserCreationForm):
    # Aggiungiamo i campi che non sono presenti nel form base
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=150, required=True, label="Cognome")
    email = forms.EmailField(required=True, label="Email")
    # Aggiungiamo il campo per inserire il token
    token = forms.CharField(
        label="Token di Registrazione",
        required=True,
        help_text="Inserisci il token che hai ricevuto via email.",
        widget=forms.TextInput(attrs={'placeholder': 'Es: f47ac10b-58cc-4372-a567-0e02b2c3d479'})
    )

    class Meta(UserCreationForm.Meta):
        # Specifichiamo il modello utente di Django
        model = User
        # Indichiamo i campi che vogliamo nel form.
        # Useremo l'email come username, quindi non mostriamo il campo username standard.
        # I campi password1 e password2 sono gestiti da UserCreationForm.
        fields = ("first_name", "last_name", "email", "token")

    def clean_token(self):
        """Valida il formato del token (deve essere un UUID valido)."""
        token_str = self.cleaned_data.get('token')
        try:
            uuid.UUID(token_str) # Prova a convertire in UUID
        except ValueError:
            raise forms.ValidationError("Il formato del token non è valido.")
        return token_str

    def clean(self):
        """
        Validazione incrociata: controlla il token, l'email
        e la loro corrispondenza nel database.
        """
        cleaned_data = super().clean() # Esegue le validazioni standard dei campi
        token_str = cleaned_data.get("token")
        email = cleaned_data.get("email")

        if token_str and email: # Procedi solo se entrambi i campi sono presenti e validi finora
            try:
                # Cerca il token nel database
                registration_token = RegistrationToken.objects.get(token=token_str)

                # Controlla se il token è valido (non usato, non scaduto)
                if not registration_token.is_valid():
                    if registration_token.is_used:
                        raise forms.ValidationError("Questo token è già stato utilizzato.")
                    else: # Scaduto
                        raise forms.ValidationError("Questo token è scaduto. Richiedine uno nuovo.")

                # Controlla se l'email inserita corrisponde a quella associata al token
                # Usiamo lower() per un confronto case-insensitive
                if registration_token.email.lower() != email.lower():
                    raise forms.ValidationError("L'email inserita non corrisponde a quella associata al token.")

                # Se tutto ok, possiamo salvare il token trovato nel cleaned_data
                # per usarlo facilmente nella vista dopo il salvataggio dell'utente.
                # Nota: questo non salva il token nel modello User.
                cleaned_data['registration_token_instance'] = registration_token

            except RegistrationToken.DoesNotExist:
                raise forms.ValidationError("Token di registrazione non trovato o non valido.")
            except forms.ValidationError as e:
                # Rilancia le eccezioni di validazione specifiche trovate sopra
                raise e
            except Exception as e:
                # Gestisce altri errori imprevisti durante la ricerca
                print(f"Errore imprevisto validazione token: {e}") # Log per debug
                raise forms.ValidationError("Si è verificato un errore durante la validazione del token. Riprova.")

        return cleaned_data

# Nuovo Form per il Login
class LoginForm(AuthenticationForm):
    # Sovrascriviamo il campo username per cambiare l'etichetta
    username = forms.EmailField(
        label="Email", # Cambiamo l'etichetta da "Username" a "Email"
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
    # Il campo password è già gestito da AuthenticationForm

    # Puoi aggiungere qui ulteriori personalizzazioni se necessario 

# Nuovo Form per la Richiesta Token
class TokenRequestForm(forms.Form):
    email = forms.EmailField(
        label="Il tuo indirizzo Email",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'esempio@dominio.com'})
    )

    def clean_email(self):
        """Validazione custom per l'email."""
        email = self.cleaned_data.get('email')

        # 1. Controlla se esiste già un utente registrato con questa email
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un utente con questa email è già registrato.")

        # 2. Controlla se esiste già un token VALIDO (non usato, non scaduto) per questa email
        #    Questo previene richieste multiple mentre una è in attesa o valida.
        #    Se vuoi permettere nuove richieste dopo la scadenza, modifica questa logica.
        existing_valid_token = RegistrationToken.objects.filter(
            email__iexact=email,
            is_used=False,
            expires_at__gt=timezone.now() # Controlla che non sia scaduto
        ).exists()

        if existing_valid_token:
            raise forms.ValidationError("Una richiesta di registrazione per questa email è già attiva o in attesa di approvazione. Attendi l'email con il token o contatta l'amministratore.")

        return email 