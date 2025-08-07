from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Commessa, Offerta, RegistrationToken
import pandas as pd
import os
from django.conf import settings
import requests
import json
from datetime import datetime
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
import time
import re
import traceback
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, TokenRequestForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # La validazione del token e dell'email è già avvenuta nel form.clean()

            # Recuperiamo l'istanza del token validato dal form
            registration_token = form.cleaned_data['registration_token_instance']

            try:
                # Procediamo con la creazione dell'utente
                # Impostiamo l'username uguale all'email prima di salvare
                user = form.save(commit=False) # Crea l'oggetto User ma non lo salva ancora
                user.username = form.cleaned_data['email'] # Imposta username = email
                user.email = form.cleaned_data['email'] # Assicurati che l'email sia corretta
                user.first_name = form.cleaned_data['first_name'] # Assicurati che nome/cognome siano salvati
                user.last_name = form.cleaned_data['last_name']
                user.save() # Salva l'utente nel database

                # Marchiamo il token come usato e lo associamo all'utente creato
                registration_token.is_used = True
                registration_token.user = user
                registration_token.save()

                messages.success(request, 'Registrazione completata con successo! Ora puoi effettuare il login.')
                return redirect('login') # Reindirizza alla pagina di login

            except Exception as e:
                # Gestione di errori imprevisti durante il salvataggio
                messages.error(request, f'Si è verificato un errore durante la finalizzazione della registrazione. Dettaglio: {e}')
                print(f"Errore salvataggio utente/token: {e}") # Log per debug
                # Rimanere sulla pagina di registrazione mostrando il form con i dati inseriti
                # (ma senza errori specifici del salvataggio, l'errore generale è nel messaggio)

        else:
            # Il form non è valido (errori nei campi o nella validazione clean())
            # Gli errori verranno mostrati automaticamente dal template
            messages.error(request, 'Per favore, correggi gli errori nel modulo.')

    else: # Richiesta GET
        # Mostra semplicemente un form vuoto
        form = RegisterForm()

    context = {'form': form}
    return render(request, 'register.html', context)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bentornato, {user.first_name}!')
            # Controlla se c'è un parametro 'next' nell'URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url) # Reindirizza alla pagina originariamente richiesta
            else:
                return redirect('index') # Altrimenti, vai alla index
        else:
            messages.error(request, 'Email o password non validi. Riprova.')
    else:
        form = LoginForm()

    context = {'form': form}
    return render(request, 'login.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, 'Sei stato disconnesso.')
    return redirect('login')


@login_required
def index(request):
    context = {
        'user': request.user if request.user.is_authenticated else None
    }
    return render(request, 'index.html', context)

def clean_value(val):
    """Pulisce e converte un valore in float se possibile"""
    if pd.isna(val):
        return 0
    
    if isinstance(val, (int, float)):
        return float(val)
    
    # Pulisci la stringa
    val_str = str(val).replace(',', '.').strip()
    if val_str and not val_str.startswith('Q.TA'):
        try:
            return float(val_str)
        except (ValueError, TypeError):
            pass
    
    return 0

def get_geocode_cache():
    """Carica o crea la cache per gli indirizzi geocodificati"""
    cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', 'geocode_cache.json')
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {}

def save_geocode_cache(cache):
    """Salva la cache per gli indirizzi geocodificati"""
    cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', 'geocode_cache.json')
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f)

def batch_geocode(addresses, geocode_cache=None):
    """Geocodifica batch di indirizzi con un approccio sequenziale invece che parallelo"""
    if geocode_cache is None:
        geocode_cache = {}
    
    results = {}
    missing_addresses = [addr for addr in addresses if addr not in geocode_cache]
    
    # Processiamo prima gli indirizzi già in cache
    for addr in addresses:
        if addr in geocode_cache:
            results[addr] = geocode_cache[addr]
    
    # Geocodifichiamo solo gli indirizzi mancanti - in modo sequenziale
    for addr in missing_addresses:
        try:
            coords = geocode_address(addr)
            results[addr] = coords
            geocode_cache[addr] = coords
            # Aggiungiamo un piccolo ritardo per non sovraccaricare l'API
            time.sleep(0.5)
        except Exception as e:
            print(f"Errore nella geocodifica dell'indirizzo '{addr}': {str(e)}")
            results[addr] = (None, None)
            geocode_cache[addr] = (None, None)
    
    return results, geocode_cache

def geocode_address(address):
    """Funzione per convertire un indirizzo in coordinate geografiche usando Nominatim (OpenStreetMap)"""
    if not address:
        return None, None
    
    try:
        # Converti l'indirizzo in stringa se non lo è già
        address = str(address)
        
        # Aggiungi ", Italia" all'indirizzo se non è già presente
        if "italia" not in address.lower() and "italy" not in address.lower():
            address = f"{address}, Italia"
        
        # Utilizza il servizio Nominatim di OpenStreetMap
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {'User-Agent': 'MappaEcoPVTrasporti/1.0'}  # OpenStreetMap richiede un User-Agent
        
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        
        if data and len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon'])
        else:
            return None, None
    except Exception as e:
        print(f"Errore nella geocodifica dell'indirizzo: {str(e)}")
        return None, None

def upload_excel(request):
    temp_paths = []
    
    if request.method == 'POST':
        try:
            # Carica la cache di geocoding
            geocode_cache = get_geocode_cache()
            
            # Definizione del finder delle colonne
            def find_column(df, pattern, exclude_patterns=None):
                """Trova una colonna nel DataFrame basandosi su un pattern regex"""
                if exclude_patterns is None:
                    exclude_patterns = []
                
                for col in df.columns:
                    if re.search(pattern, str(col), re.IGNORECASE):
                        # Verifica che la colonna non contenga pattern da escludere
                        exclude_match = False
                        for exclude_pattern in exclude_patterns:
                            if re.search(exclude_pattern, str(col), re.IGNORECASE):
                                exclude_match = True
                                break
                        
                        if not exclude_match:
                            return col
                return None
            
            # Processa i file
            commesse_file = request.FILES.get('commesse_file')
            offerte_file = request.FILES.get('offerte_file')
            print(offerte_file)
            
            commesse_imported = 0
            offerte_imported = 0
            
            # Crea directory temporanea se non esiste
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # MODIFICA: Conta record esistenti
            commesse_prima = Commessa.objects.count()
            offerte_prima = Offerta.objects.count()
            print(f"Prima dell'importazione: {commesse_prima} commesse, {offerte_prima} offerte")
            
            # Processa file delle commesse
            if commesse_file:
                # MODIFICA: Elimina SOLO le commesse se stiamo caricando un file di commesse
                with transaction.atomic():
                    commesse_count = Commessa.objects.count()
                    Commessa.objects.all().delete()
                    print(f"Dati commesse esistenti eliminati: {commesse_count} commesse.")
                
                # Salva il file temporaneamente
                temp_commesse_path = os.path.join(temp_dir, commesse_file.name)
                temp_paths.append(temp_commesse_path)
                
                with open(temp_commesse_path, 'wb+') as destination:
                    for chunk in commesse_file.chunks():
                        destination.write(chunk)
                
                # Processa le commesse
                commesse_imported = process_commesse_file(temp_commesse_path, geocode_cache, find_column)
                print(f"Commesse importate: {commesse_imported}")
                print(f"Verifica DB - Commesse nel database: {Commessa.objects.count()}")
            
            # Processa file delle offerte
            if offerte_file:
                # MODIFICA: Elimina SOLO le offerte se stiamo caricando un file di offerte
                with transaction.atomic():
                    offerte_count = Offerta.objects.count()
                    Offerta.objects.all().delete()
                    print(f"Dati offerte esistenti eliminati: {offerte_count} offerte.")
                
                # Salva il file temporaneamente
                temp_offerte_path = os.path.join(temp_dir, offerte_file.name)
                temp_paths.append(temp_offerte_path)
                
                with open(temp_offerte_path, 'wb+') as destination:
                    for chunk in offerte_file.chunks():
                        destination.write(chunk)
                
                # Processa le offerte
                offerte_imported = process_offerte_file(temp_offerte_path, geocode_cache, find_column)
                print(f"Offerte importate: {offerte_imported}")
                print(f"Verifica DB - Offerte nel database: {Offerta.objects.count()}")
            
            # Salva la cache di geocoding aggiornata
            save_geocode_cache(geocode_cache)
            
            # Verifica finale del database
            commesse_db = Commessa.objects.count()
            offerte_db = Offerta.objects.count()
            print(f"VERIFICA FINALE DATABASE:")
            print(f"- Commesse nel DB: {commesse_db}")
            print(f"- Offerte nel DB: {offerte_db}")
            
            # Calcola i dati importati
            commesse_importate = commesse_db - (0 if commesse_file else commesse_prima)
            offerte_importate = offerte_db - (0 if offerte_file else offerte_prima)
            total_imported = commesse_importate + offerte_importate
            
            # Messaggio di successo
            if total_imported > 0:
                messages.success(request, f"Importazione completata con successo! Nel database: {commesse_db} commesse e {offerte_db} offerte.")
            else:
                messages.warning(request, "Nessun dato importato. Verifica che i file Excel contengano dati validi con 'DA FARE'.")
            
        except Exception as e:
            messages.error(request, f"Errore durante l'importazione: {str(e)}")
            traceback.print_exc()
        
        finally:
            # Gestione file temporanei (manteniamo il codice esistente)
            import time
            import gc
            gc.collect()
            time.sleep(1)
            
            for temp_path in temp_paths:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        print(f"File temporaneo rimosso: {temp_path}")
                except Exception as e:
                    print(f"Impossibile rimuovere il file temporaneo: {str(e)}")
                    pass
    
    return redirect('index')

def process_commesse_file(file_path, geocode_cache, find_column):
    """Processa il file Excel delle commesse"""
    print("\n=== INIZIO ELABORAZIONE FILE COMMESSE ===")
    righe_da_fare_trovate = 0
    righe_importate = 0
    
    try:
        # Leggi il file Excel e chiudilo subito dopo l'uso
        with pd.ExcelFile(file_path) as xlsx:
            sheet_names = xlsx.sheet_names
            
            # Processa ogni foglio
            for sheet_name in sheet_names:
                print(f"\nAnalisi foglio: {sheet_name}")
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                
                # Debug: stampa colonne
                print(f"Colonne nel foglio {sheet_name}: {df.columns.tolist()}")
                
                # Determine il codice anno dal nome del foglio o dal titolo
                anno = None
                
                # Prova a estrarre l'anno dal nome del foglio
                match = re.search(r'20(\d{2})', sheet_name)
                if match:
                    anno = int(f"20{match.group(1)}")
                
                # Se non troviamo l'anno, cerca nel titolo del file
                if not anno:
                    file_name = os.path.basename(file_path)
                    match = re.search(r'20(\d{2})', file_name)
                    if match:
                        anno = int(f"20{match.group(1)}")
                
                # Se ancora non troviamo l'anno, usa l'anno corrente
                if not anno:
                    anno = datetime.now().year
                
                print(f"Anno determinato per il foglio {sheet_name}: {anno}")
                
                # Trova le colonne rilevanti usando regex
                commessa_col = find_column(df, r'COMMESSA|CODICE')
                quantita_col = find_column(df, r'QUANTITA|PESO|Q\.TA', ['ECOLIGHT'])
                tipo_col = find_column(df, r'TIPOLOGIA|CATEGORIA|PRODOTTO')
                produttore_col = find_column(df, r'PRODUTTORE|CLIENTE')
                luogo_col = find_column(df, r'LUOGO|RITIRO')
                provincia_col = find_column(df, r'PROVINCIA')
                data_ritiro_col = find_column(df, r'DATA.*RITIRO')
                
                # Verifica colonne obbligatorie
                if not commessa_col:
                    print(f"Errore: Colonna COMMESSA non trovata nel foglio {sheet_name}")
                    continue
                
                if not quantita_col:
                    print(f"Errore: Colonna QUANTITA non trovata nel foglio {sheet_name}")
                    continue
                
                if not data_ritiro_col:
                    print(f"Errore: Colonna DATA RITIRO non trovata nel foglio {sheet_name}")
                    continue
                
                # Debug: stampa colonne trovate
                print(f"Colonne trovate: COMMESSA={commessa_col}, QUANTITA={quantita_col}, TIPO={tipo_col}, " +
                      f"PRODUTTORE={produttore_col}, LUOGO={luogo_col}, PROVINCIA={provincia_col}, " +
                      f"DATA_RITIRO={data_ritiro_col}")
                
                # Per ogni riga dei dati, processa separatamente
                processed_rows = 0
                skipped_rows = 0
                
                for _, row in df.iterrows():
                    try:
                        # Estrai il codice commessa
                        codice_commessa = str(row.get(commessa_col, "")).strip()
                        if not codice_commessa:
                            skipped_rows += 1
                            continue
                        
                        # Estrai data ritiro e verifica se è "DA FARE"
                        data_ritiro = str(row.get(data_ritiro_col, "")).strip()
                        
                        # MODIFICA: Controllo molto più flessibile per "DA FARE"
                        is_da_fare = is_da_fare_text(data_ritiro)
                        print(f"Commessa {codice_commessa}: DATA RITIRO = '{data_ritiro}', da importare: {is_da_fare}")
                        
                        # IMPORTANTE: Filtriamo solo le righe con "DA FARE" nella colonna DATA RITIRO
                        if not is_da_fare:
                            print(f"Skipping commessa {codice_commessa}: DATA RITIRO = '{data_ritiro}' (non 'DA FARE')")
                            skipped_rows += 1
                            continue
                        
                        # Estrai gli altri campi
                        quantita = clean_value(row.get(quantita_col))
                        tipologia = str(row.get(tipo_col, "")).strip() if tipo_col and pd.notna(row.get(tipo_col)) else ""
                        produttore = str(row.get(produttore_col, "")).strip() if produttore_col and pd.notna(row.get(produttore_col)) else ""
                        indirizzo = str(row.get(luogo_col, "")).strip() if luogo_col and pd.notna(row.get(luogo_col)) else ""
                        provincia = str(row.get(provincia_col, "")).strip() if provincia_col and pd.notna(row.get(provincia_col)) else ""
                        
                        # Ottieni coordinate geografiche
                        lat, lng = None, None
                        if indirizzo:
                            geocode_results = get_coordinates(indirizzo, provincia, geocode_cache)
                            if geocode_results:
                                lat, lng = geocode_results
                        
                        # Crea o aggiorna la commessa in transazioni separate
                        commessa_data = {
                            'quantita': quantita,
                            'tipologia': tipologia,
                            'produttore': produttore,
                            'indirizzo': indirizzo,
                            'provincia': provincia,
                            'data_ritiro': data_ritiro,
                            'anno': anno,
                            'latitudine': lat,
                            'longitudine': lng
                        }
                        
                        # Usa with transaction.atomic() per ogni operazione di database
                        with transaction.atomic():
                            # Crea nuova commessa (dati precedenti sono stati eliminati)
                            commessa = Commessa(
                                codice_commessa=codice_commessa,
                                **commessa_data
                            )
                            commessa.save()
                            print(f"Creata nuova commessa (DA FARE): {codice_commessa}")
                        
                        righe_importate += 1
                        processed_rows += 1
                        
                    except Exception as e:
                        print(f"Errore nell'elaborazione della riga: {str(e)}")
                        skipped_rows += 1
                        continue
                
                print(f"Foglio {sheet_name}: elaborate {processed_rows} righe, saltate {skipped_rows} righe")
        
    except Exception as e:
        print(f"Errore nell'elaborazione del file delle commesse: {str(e)}")
        traceback.print_exc()
    
    return righe_importate

def process_offerte_file(file_path, geocode_cache, find_column):
    """Processa il file Excel delle offerte"""
    print("\n=== INIZIO ELABORAZIONE FILE OFFERTE ===")
    offerte_salvate = 0
    
    try:
        # Leggi il file Excel
        with pd.ExcelFile(file_path) as xlsx:
            sheet_names = xlsx.sheet_names
            print(f"Fogli trovati nel file delle offerte: {sheet_names}")
            
            # Processa ogni foglio
            for sheet_name in sheet_names:
                print(f"\n=== FOGLIO: {sheet_name} ===")
                
                try:
                    df = pd.read_excel(xlsx, sheet_name=sheet_name)
                    print(f"Lette {len(df)} righe dal foglio {sheet_name}")
                    
                    # Trova le colonne rilevanti
                    offerta_col = find_column(df, r'(OFFERTA|PREVENTIVO|NUM)', ['ECOLIGHT'])
                    commessa_col = find_column(df, r'COMMESSA|CODICE', [])
                    quantita_col = find_column(df, r'QUANTITA|PESO|Q\.TA', ['ECOLIGHT'])
                    tipo_col = find_column(df, r'TIPOLOGIA|CATEGORIA|PRODOTTO|TIPO', [])
                    produttore_col = find_column(df, r'PRODUTTORE|CLIENTE', [])
                    luogo_col = find_column(df, r'LUOGO|RITIRO|INDIRIZZO', [])
                    provincia_col = find_column(df, r'PROVINCIA|PROV', [])
                    data_offerta_col = find_column(df, r'DATA', [])
                    
                    # Debug: mostra le colonne trovate
                    print(f"Colonne trovate: OFFERTA={offerta_col}, COMMESSA={commessa_col}, "
                          f"QUANTITÀ={quantita_col}, TIPO={tipo_col}, PRODUTTORE={produttore_col}, "
                          f"LUOGO={luogo_col}, PROVINCIA={provincia_col}, DATA={data_offerta_col}")
                    
                    # Verifica colonne obbligatorie
                    if not offerta_col:
                        print(f"ERRORE: Colonna OFFERTA non trovata nel foglio {sheet_name}")
                        continue
                    
                    # Estrai l'anno
                    anno = extract_year(sheet_name, file_path)
                    print(f"Anno determinato: {anno}")
                    
                    # Per ogni riga dei dati
                    offerte_nel_foglio = 0
                    for idx, row in df.iterrows():
                        try:
                            # Estrai il codice offerta
                            codice_offerta = str(row.get(offerta_col, "")).strip()
                            if not codice_offerta or codice_offerta == "nan":
                                continue
                            
                            # Estrai data offerta e verifica se è "DA FARE"
                            data_offerta = ""
                            if data_offerta_col:
                                data_offerta_value = row.get(data_offerta_col, "")
                                data_offerta = str(data_offerta_value).strip() if pd.notna(data_offerta_value) else ""
                            
                            # Usa il test semplificato per "da fare"
                            is_da_fare = False
                            if data_offerta:
                                data_offerta_lower = data_offerta.lower()
                                is_da_fare = "da" in data_offerta_lower and "fare" in data_offerta_lower
                            
                            if not is_da_fare:
                                continue
                            
                            # Estrai gli altri campi
                            codice_commessa = str(row.get(commessa_col, "")).strip() if commessa_col and pd.notna(row.get(commessa_col)) else ""
                            quantita = clean_value(row.get(quantita_col)) if quantita_col else 0
                            tipologia = str(row.get(tipo_col, "")).strip() if tipo_col and pd.notna(row.get(tipo_col)) else ""
                            produttore = str(row.get(produttore_col, "")).strip() if produttore_col and pd.notna(row.get(produttore_col)) else ""
                            indirizzo = str(row.get(luogo_col, "")).strip() if luogo_col and pd.notna(row.get(luogo_col)) else ""
                            provincia = str(row.get(provincia_col, "")).strip() if provincia_col and pd.notna(row.get(provincia_col)) else ""
                            
                            # Ottieni coordinate
                            lat, lng = None, None
                            if indirizzo:
                                indirizzo_completo = f"{indirizzo}, {provincia}, Italia" if provincia else f"{indirizzo}, Italia"
                                if indirizzo_completo in geocode_cache:
                                    lat, lng = geocode_cache[indirizzo_completo]
                                else:
                                    try:
                                        lat, lng = geocode_address(indirizzo_completo)
                                        geocode_cache[indirizzo_completo] = (lat, lng)
                                    except:
                                        pass
                            
                            # SALVATAGGIO SICURO: non usiamo transaction.atomic qui per evitare problemi
                            try:
                                offerta = Offerta(
                                    codice_offerta=codice_offerta,
                                    codice_commessa=codice_commessa,
                                    quantita=quantita,
                                    tipologia=tipologia,
                                    produttore=produttore,
                                    indirizzo=indirizzo,
                                    provincia=provincia,
                                    data_ritiro="DA FARE",  # Forza "DA FARE" per coerenza
                                    anno=anno,
                                    latitudine=lat,
                                    longitudine=lng
                                )
                                offerta.save()
                                print(f"Salvata offerta: {codice_offerta}")
                                offerte_salvate += 1
                                offerte_nel_foglio += 1
                            except Exception as save_error:
                                print(f"Errore salvataggio offerta {codice_offerta}: {str(save_error)}")
                        
                        except Exception as row_error:
                            print(f"Errore nella riga {idx+2}: {str(row_error)}")
                    
                    print(f"Offerte salvate da questo foglio: {offerte_nel_foglio}")
                
                except Exception as sheet_error:
                    print(f"Errore nel foglio {sheet_name}: {str(sheet_error)}")
            
            # Verifica dopo ogni file
            print(f"Verifica dopo elaborazione file: {Offerta.objects.count()} offerte nel DB")
    
    except Exception as file_error:
        print(f"Errore generale file offerte: {str(file_error)}")
        traceback.print_exc()
    
    return offerte_salvate

# Funzione helper per estrarre l'anno
def extract_year(sheet_name, file_path):
    """Estrae l'anno dal nome del foglio o dal percorso del file"""
    # Prova dal nome del foglio
    match = re.search(r'20(\d{2})', sheet_name)
    if match:
        return int(f"20{match.group(1)}")
    
    # Prova dal nome del file
    file_name = os.path.basename(file_path)
    match = re.search(r'20(\d{2})', file_name)
    if match:
        return int(f"20{match.group(1)}")
    
    # Default: anno corrente
    return datetime.now().year

def map_data(request):
    """API per ottenere i dati per la mappa"""
    # Ottieni tutte le commesse e offerte con coordinate valide
    commesse = list(Commessa.objects.filter(
        latitudine__isnull=False, 
        longitudine__isnull=False
    ).values())
    
    offerte = list(Offerta.objects.filter(
        latitudine__isnull=False, 
        longitudine__isnull=False
    ).values())
    
    # Debug
    print(f"API map-data: trovate {len(commesse)} commesse e {len(offerte)} offerte con coordinate")
    print(f"Commesse con 'da fare': {Commessa.objects.filter(data_ritiro__icontains='da fare').count()}")
    print(f"Offerte con 'da fare': {Offerta.objects.filter(data_ritiro__icontains='da fare').count()}")
    
    # Converti date in stringhe per la serializzazione JSON
    for offerta in offerte:
        if offerta.get('data_offerta'):
            offerta['data_offerta'] = offerta['data_offerta'].strftime('%Y-%m-%d')
    
    # Nel metodo map_data, prima del return aggiungi:
    print(f"API map_data: DATI NEL DATABASE:")
    print(f"Commesse totali nel DB: {Commessa.objects.count()}")
    print(f"Offerte totali nel DB: {Offerta.objects.count()}")
    print(f"Commesse con 'DA FARE' ma senza coordinate: {Commessa.objects.filter(data_ritiro='DA FARE', latitudine__isnull=True).count()}")
    print(f"Offerte con 'DA FARE' ma senza coordinate: {Offerta.objects.filter(data_ritiro='DA FARE', latitudine__isnull=True).count()}")
    
    return JsonResponse({
        'commesse': commesse,
        'offerte': offerte
    })

def table_data(request):
    """API per ottenere i dati per la tabella"""
    year = request.GET.get('year', 'all')
    type_filter = request.GET.get('type', 'all')
    
    # Debugging - Stampa filtri
    print(f"API table-data: filtri year={year}, type={type_filter}")
    
    # Filtra solo per anno, senza il vincolo di data_ritiro="DA FARE"
    commesse_query = Commessa.objects.all()
    offerte_query = Offerta.objects.all()
    
    if year != 'all':
        commesse_query = commesse_query.filter(anno=int(year))
        offerte_query = offerte_query.filter(anno=int(year))
    
    # Converti QuerySet in lista di dizionari
    commesse = list(commesse_query.values()) if type_filter in ['all', 'commesse'] else []
    offerte = list(offerte_query.values()) if type_filter in ['all', 'offerte'] else []
    
    # Debugging - Stampa numeri nel server
    print(f"API table-data: restituite {len(commesse)} commesse e {len(offerte)} offerte")
    
    # Converti date in stringhe per la serializzazione JSON
    for offerta in offerte:
        if offerta.get('data_offerta'):
            offerta['data_offerta'] = offerta['data_offerta'].strftime('%Y-%m-%d')
    
    return JsonResponse({
        'commesse': commesse,
        'offerte': offerte
    })

def is_da_fare_text(text):
    """Verifica in modo più flessibile se un testo è 'da fare'"""
    if not text or not isinstance(text, str):
        return False
    
    # Debug: stampa il valore esatto che stiamo esaminando
    print(f"Verifica 'da fare' per valore: '{text}'")
    
    # Normalizza il testo: rimuovi spazi extra, converti in minuscolo
    normalized = text.lower().strip()
    
    # Verifica esatta per "da fare" (con o senza spazi)
    if normalized == "da fare" or normalized == "dafare":
        print(f"  ✓ Match esatto per 'da fare'")
        return True
    
    # Verifica per substring "da fare" o "dafare"
    if "da fare" in normalized or "dafare" in normalized:
        print(f"  ✓ Contiene 'da fare'")
        return True
        
    # Altre possibili varianti
    variants = ["da_fare", "da-fare", "da.fare", "dfare"]
    for variant in variants:
        if variant in normalized:
            print(f"  ✓ Contiene variante '{variant}'")
            return True
    
    print(f"  ✗ Non è 'da fare'")
    return False

def get_coordinates(indirizzo, provincia, geocode_cache):
    """Ottiene le coordinate geografiche per un indirizzo"""
    # Aggiungi provincia all'indirizzo se presente
    if provincia and provincia.strip():
        indirizzo_completo = f"{indirizzo}, {provincia}, Italia"
    else:
        indirizzo_completo = f"{indirizzo}, Italia"
    
    # Verifica se l'indirizzo è nella cache
    if indirizzo_completo in geocode_cache:
        return geocode_cache[indirizzo_completo]
    
    # Altrimenti geocodifica l'indirizzo
    return geocode_address(indirizzo_completo)

def verifica_db_stato():
    """Funzione per verificare lo stato del database"""
    commesse_totali = Commessa.objects.count()
    offerte_totali = Offerta.objects.count()
    
    commesse_da_fare = Commessa.objects.filter(data_ritiro__icontains='da fare').count()
    offerte_da_fare = Offerta.objects.filter(data_ritiro__icontains='da fare').count()
    
    print("\n=== STATO ATTUALE DATABASE ===")
    print(f"Commesse totali: {commesse_totali}")
    print(f"Offerte totali: {offerte_totali}")
    print(f"Commesse con 'da fare': {commesse_da_fare}")
    print(f"Offerte con 'da fare': {offerte_da_fare}")
    print("==============================\n")

# Nuova Vista per la Richiesta Token
def request_token_view(request):
    if request.method == 'POST':
        form = TokenRequestForm(request.POST)
        if form.is_valid():
            email_richiedente = form.cleaned_data['email']
            try:
                subject = 'Nuova Richiesta di Registrazione Ricevuta'
                admin_email = settings.ADMIN_EMAIL
                # Aggiorna il template email se necessario per non menzionare link speciali
                html_message = render_to_string('emails/admin_request_notification.html', {
                    'email_richiedente': email_richiedente,
                })
                plain_message = f"L'utente con email {email_richiedente} ha richiesto l'accesso per la registrazione. Genera un token dall'admin e comunicalo all'utente."

                send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [admin_email], html_message=html_message, fail_silently=False)
                messages.success(request, 'La tua richiesta è stata inviata. Riceverai un token via email una volta approvata.')
            except Exception as e:
                messages.error(request, f'Si è verificato un errore durante l\'invio della notifica. Riprova più tardi. Dettaglio: {e}')
                print(f"Errore invio email notifica admin: {e}")
            return redirect('request_token')
        else:
            messages.error(request, 'Per favore, correggi gli errori nel modulo.')
    else:
        form = TokenRequestForm()
    context = {'form': form}
    return render(request, 'request_token.html', context)
