document.addEventListener('DOMContentLoaded', function() {
    // Inizializzazione della mappa
    const map = L.map('map').setView([41.8719, 12.5674], 6); // Centro mappa sull'Italia

    // Aggiungi layer di base OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Gruppi di marker per clustering
    const commesseCluster = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({
                html: '<div class="cluster-icon cluster-commesse">' + cluster.getChildCount() + '</div>',
                className: 'marker-cluster marker-cluster-commesse',
                iconSize: L.point(40, 40)
            });
        }
    });
    
    const offerteCluster = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({
                html: '<div class="cluster-icon cluster-offerte">' + cluster.getChildCount() + '</div>',
                className: 'marker-cluster marker-cluster-offerte',
                iconSize: L.point(40, 40)
            });
        }
    });

    // Aggiungi i cluster alla mappa
    map.addLayer(commesseCluster);
    map.addLayer(offerteCluster);

    // Carica i dati per la mappa
    loadMapData();

    // Inizializza la tabella dati
    const dataTable = $('#dataTable').DataTable({
        responsive: true,
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json'
        },
        rowCallback: function(row, data) {
            // Applica classe CSS in base al tipo (prima colonna)
            if (data[0] === 'Commessa') {
                $(row).addClass('commessa-row');
            } else if (data[0] === 'Offerta') {
                $(row).addClass('offerta-row');
            }
        }
    });

    // Carica i dati per la tabella
    loadTableData();

    // Gestione filtri solo per la mappa con i pulsanti
    document.getElementById('showAll').addEventListener('click', function() {
        // Aggiorna SOLO la mappa
        map.addLayer(commesseCluster);
        map.addLayer(offerteCluster);
        updateButtonStyles('showAll');
    });

    document.getElementById('showCommesse').addEventListener('click', function() {
        // Aggiorna SOLO la mappa
        map.addLayer(commesseCluster);
        map.removeLayer(offerteCluster);
        updateButtonStyles('showCommesse');
    });

    document.getElementById('showOfferte').addEventListener('click', function() {
        // Aggiorna SOLO la mappa
        map.removeLayer(commesseCluster);
        map.addLayer(offerteCluster);
        updateButtonStyles('showOfferte');
    });

    // Funzione per gestire lo stile dei pulsanti di filtro
    function updateButtonStyles(activeButton) {
        document.getElementById('showAll').classList.remove('btn-primary');
        document.getElementById('showAll').classList.add('btn-outline-primary');
        document.getElementById('showCommesse').classList.remove('btn-primary');
        document.getElementById('showCommesse').classList.add('btn-outline-primary');
        document.getElementById('showOfferte').classList.remove('btn-primary');
        document.getElementById('showOfferte').classList.add('btn-outline-primary');

        document.getElementById(activeButton).classList.remove('btn-outline-primary');
        document.getElementById(activeButton).classList.add('btn-primary');
    }

    // Verifica che i filtri vengano applicati correttamente
    function debugTableFilters() {
        if ($.fn.DataTable.isDataTable('#dataTable')) {
            const table = $('#dataTable').DataTable();
            const totalRows = table.rows().count();
            const visibleRows = table.rows({search:'applied'}).count();
            const firstType = table.row(0).data() ? table.row(0).data()[0] : 'N/A';
            
            console.log(`Stato tabella: ${visibleRows}/${totalRows} righe visibili`);
            console.log(`Primo tipo visibile: ${firstType}`);
        } else {
            console.log("Tabella non ancora inizializzata");
        }
    }

    // Gestione filtri tabella
    $('#yearFilter, #typeFilter').on('change', function() {
        loadTableData();
    });

    // Array per memorizzare la cronologia delle ricerche
    let searchHistory = [];
    
    // Aggiungi event listener per la ricerca nella mappa
    document.getElementById('mapSearch').addEventListener('input', function() {
        const searchText = this.value.trim();
        filterMapMarkers(searchText);
    });
    
    // Gestione tasto ENTER per la ricerca
    document.getElementById('mapSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchText = this.value.trim();
            if (searchText) {
                // Aggiungi alla cronologia solo se non è già presente e non è vuoto
                if (searchText && !searchHistory.includes(searchText)) {
                    searchHistory.unshift(searchText); // Aggiungi all'inizio
                    // Mantieni solo le ultime 5 ricerche
                    if (searchHistory.length > 5) {
                        searchHistory.pop();
                    }
                    // Aggiorna la UI della cronologia
                    updateSearchHistory();
                }
                filterMapMarkers(searchText);
            }
        }
    });
    
    // Aggiungi event listener esplicito per il bottone di reset
    document.querySelector('.btn-outline-secondary').addEventListener('click', function() {
        // Resetta l'input
        document.getElementById('mapSearch').value = '';
        // Esegui il filtro che mostra tutti i marker
        filterMapMarkers('');
    });
    
    // Funzione per aggiornare la cronologia visualizzata
    function updateSearchHistory() {
        // Trova o crea il container della cronologia
        let historyContainer = document.getElementById('searchHistoryContainer');
        if (!historyContainer) {
            historyContainer = document.createElement('div');
            historyContainer.id = 'searchHistoryContainer';
            historyContainer.className = 'mt-2';
            document.querySelector('.card-body').appendChild(historyContainer);
        }
        
        // Svuota il container
        historyContainer.innerHTML = '';
        
        // Aggiungi etichetta se ci sono ricerche
        if (searchHistory.length > 0) {
            const label = document.createElement('small');
            label.className = 'text-muted d-block mb-2';
            label.textContent = 'Ricerche recenti:';
            historyContainer.appendChild(label);
            
            // Crea badge per ogni ricerca nella cronologia
            searchHistory.forEach(function(term) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-light text-dark me-1 mb-1 search-history-item';
                badge.textContent = term;
                badge.style.cursor = 'pointer';
                badge.addEventListener('click', function() {
                    document.getElementById('mapSearch').value = term;
                    filterMapMarkers(term);
                });
                historyContainer.appendChild(badge);
            });
        }
    }

    // Funzione per filtrare i marker in base alla ricerca
    function filterMapMarkers(searchText) {
        if (!searchText) {
            // Se la ricerca è vuota, ripristina tutti i marker al loro aspetto originale
            resetMarkerStyles();
            
            // Nascondi l'informazione sui risultati della ricerca se presente
            const infoElement = document.getElementById('searchResultsInfo');
            if (infoElement) {
                infoElement.style.display = 'none';
            }
            return;
        }
        
        // Verifica se è una ricerca multipla (separata da virgole)
        const searchTerms = searchText.split(',').map(term => term.trim().toLowerCase()).filter(term => term);
        
        // Contatori per debug e risultati
        let visibleCommesse = 0;
        let visibleOfferte = 0;
        
        // Array per salvare i marker trovati (per lo zoom)
        const foundMarkers = [];
        
        // Icone evidenziate per i marker trovati
        const highlightedCommessaIcon = L.divIcon({
            html: '<i class="bi bi-geo-alt-fill marker-commessa" style="color: yellow; text-shadow: 0 0 5px black, 0 0 5px black; transform: scale(1.3);"></i>',
            className: 'custom-div-icon commessa-icon-highlighted',
            iconSize: [40, 40],
            iconAnchor: [20, 40]
        });
        
        const highlightedOffertaIcon = L.divIcon({
            html: '<i class="bi bi-pin-map-fill marker-offerta" style="color: yellow; text-shadow: 0 0 5px black, 0 0 5px black; transform: scale(1.3);"></i>',
            className: 'custom-div-icon offerta-icon-highlighted',
            iconSize: [40, 40],
            iconAnchor: [20, 40]
        });
        
        // Icone normali (da ripristinare per i marker non trovati)
        const commessaIcon = L.divIcon({
            html: '<i class="bi bi-geo-alt-fill marker-commessa"></i>',
            className: 'custom-div-icon commessa-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });
        
        const offertaIcon = L.divIcon({
            html: '<i class="bi bi-pin-map-fill marker-offerta"></i>',
            className: 'custom-div-icon offerta-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });
        
        // Resetta prima lo stile di tutti i marker a quello normale
        resetMarkerStyles();
        
        // Controlla tutti i marker delle commesse
        commesseCluster.getLayers().forEach(function(layer) {
            const commessaCode = layer.options.title.split(': ')[1];
            let found = false;
            
            // Controlla tutti i termini di ricerca
            for (const term of searchTerms) {
                // Logica di ricerca per ogni termine
                const exactMatch = commessaCode.toLowerCase() === term;
                const startsWithMatch = commessaCode.toLowerCase().startsWith(term);
                const partialMatch = term.length > 3 && commessaCode.toLowerCase().includes(term);
                
                // Se uno qualsiasi dei termini corrisponde, il marker è visibile
                if (exactMatch || startsWithMatch || partialMatch) {
                    found = true;
                    
                    // Priorità alle corrispondenze esatte per lo zoom
                    if (exactMatch) {
                        foundMarkers.unshift(layer);
                    } else {
                        foundMarkers.push(layer);
                    }
                    break;  // Un termine corrispondente è sufficiente
                }
            }
            
            if (found) {
                visibleCommesse++;
                // Cambia l'icona per evidenziare questo marker
                layer.setIcon(highlightedCommessaIcon);
                // Apri automaticamente il tooltip per evidenziare ulteriormente
                layer.openTooltip();
            } else {
                // Assicurati che l'icona sia quella standard
                layer.setIcon(commessaIcon);
                // Chiudi il tooltip se aperto
                layer.closeTooltip();
            }
        });
        
        // Controlla tutti i marker delle offerte (stessa logica)
        offerteCluster.getLayers().forEach(function(layer) {
            const offertaCode = layer.options.title.split(': ')[1];
            let found = false;
            
            // Controlla tutti i termini di ricerca
            for (const term of searchTerms) {
                const exactMatch = offertaCode.toLowerCase() === term;
                const startsWithMatch = offertaCode.toLowerCase().startsWith(term);
                const partialMatch = term.length > 3 && offertaCode.toLowerCase().includes(term);
                
                if (exactMatch || startsWithMatch || partialMatch) {
                    found = true;
                    if (exactMatch) {
                        foundMarkers.unshift(layer);
                    } else {
                        foundMarkers.push(layer);
                    }
                    break;
                }
            }
            
            if (found) {
                visibleOfferte++;
                layer.setIcon(highlightedOffertaIcon);
                layer.openTooltip();
            } else {
                layer.setIcon(offertaIcon);
                layer.closeTooltip();
            }
        });
        
        console.log(`Filtro "${searchText}": ${visibleCommesse} commesse e ${visibleOfferte} offerte trovate`);
        
        // Se abbiamo dei risultati, eventualmente possiamo fare zoom sui risultati
        if (foundMarkers.length > 0 && foundMarkers.length <= 10) {
            // Creiamo un gruppo con tutti i marker trovati
            const group = L.featureGroup(foundMarkers);
            // Facciamo zoom su questo gruppo
            map.fitBounds(group.getBounds().pad(0.2));
        }
        
        // Aggiorna l'eventuale contatore dei risultati
        updateSearchResultsInfo(visibleCommesse + visibleOfferte, searchText);
    }
    
    // Funzione per mostrare info sui risultati della ricerca
    function updateSearchResultsInfo(count, searchText) {
        let infoElement = document.getElementById('searchResultsInfo');
        
        // Se non esiste, crealo
        if (!infoElement) {
            infoElement = document.createElement('div');
            infoElement.id = 'searchResultsInfo';
            infoElement.className = 'alert alert-info mt-2';
            const searchContainer = document.querySelector('.card-body');
            searchContainer.appendChild(infoElement);
        }
        
        // Aggiorna il contenuto
        if (count === 0) {
            infoElement.innerHTML = `<i class="bi bi-exclamation-circle"></i> Nessun risultato trovato per "${searchText}"`;
            infoElement.className = 'alert alert-warning mt-2';
        } else if (count === 1) {
            infoElement.innerHTML = `<i class="bi bi-check-circle"></i> Trovato 1 risultato per "${searchText}"`;
            infoElement.className = 'alert alert-success mt-2';
        } else {
            infoElement.innerHTML = `<i class="bi bi-info-circle"></i> Trovati ${count} risultati per "${searchText}"`;
            infoElement.className = 'alert alert-info mt-2';
        }
        
        // Mostra solo se c'è una ricerca attiva
        infoElement.style.display = searchText ? 'block' : 'none';
    }

    // Nuova funzione per ripristinare tutti i marker al loro aspetto originale
    function resetMarkerStyles() {
        // Icone normali
        const commessaIcon = L.divIcon({
            html: '<i class="bi bi-geo-alt-fill marker-commessa"></i>',
            className: 'custom-div-icon commessa-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });
        
        const offertaIcon = L.divIcon({
            html: '<i class="bi bi-pin-map-fill marker-offerta"></i>',
            className: 'custom-div-icon offerta-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });
        
        // Ripristina lo stile delle commesse
        commesseCluster.getLayers().forEach(function(layer) {
            layer.setIcon(commessaIcon);
            layer.closeTooltip();
        });
        
        // Ripristina lo stile delle offerte
        offerteCluster.getLayers().forEach(function(layer) {
            layer.setIcon(offertaIcon);
            layer.closeTooltip();
        });
    }

    // Modifica alla funzione di reset dei marker per usare la nuova logica
    function resetAllMarkers() {
        resetMarkerStyles();
        
        // Nascondi l'informazione sui risultati della ricerca se presente
        const infoElement = document.getElementById('searchResultsInfo');
        if (infoElement) {
            infoElement.style.display = 'none';
        }
        
        console.log("Filtro resettato: tutti i marker sono stati ripristinati");
    }

    // NUOVA FUNZIONE: estrai la logica di popolamento dei marker in una funzione separata
    function populateMarkers(data) {
        // I dati sono separati in commesse e offerte
        const commesse = data.commesse || [];
        const offerte = data.offerte || [];
        
        console.log(`Mappa: trovate ${commesse.length} commesse e ${offerte.length} offerte con coordinate`);
        
        // Crea un oggetto per tracciare le posizioni già occupate
        const usedPositions = {};
        
        // Aggiungi marker per le commesse
        commesse.forEach(commessa => {
            if (commessa.latitudine && commessa.longitudine) {
                // Crea una chiave univoca per questa posizione
                const posKey = `${commessa.latitudine.toFixed(6)}_${commessa.longitudine.toFixed(6)}`;
                
                // Applica un leggero offset se la posizione è già occupata da un'altra commessa
                let lat = commessa.latitudine;
                let lng = commessa.longitudine;
                
                if (usedPositions[posKey]) {
                    // Incrementa il contatore per questa posizione
                    usedPositions[posKey]++;
                    
                    // Aggiungi un piccolo offset a spirale
                    const angle = usedPositions[posKey] * (Math.PI / 4); // 45 gradi in radianti
                    const radius = 0.0002 * usedPositions[posKey]; // Circa 20-30 metri
                    lat += radius * Math.cos(angle);
                    lng += radius * Math.sin(angle);
                } else {
                    // Questa è la prima volta che usiamo questa posizione
                    usedPositions[posKey] = 1;
                }
                
                // Usa un'icona personalizzata per le commesse
                const commessaIcon = L.divIcon({
                    html: '<i class="bi bi-geo-alt-fill marker-commessa"></i>',
                    className: 'custom-div-icon commessa-icon',
                    iconSize: [30, 30],
                    iconAnchor: [15, 30]
                });
                
                const marker = L.marker([lat, lng], {
                    icon: commessaIcon,
                    title: `Commessa: ${commessa.codice_commessa}`
                });
                
                // Aggiungi tooltip per visualizzazione rapida
                marker.bindTooltip(`<strong>Commessa:</strong> ${commessa.codice_commessa}<br><strong>Quantità:</strong> ${commessa.quantita} t`);
                
                marker.bindPopup(createCommessaPopupContent(commessa));
                commesseCluster.addLayer(marker);
            }
        });
        
        // Aggiungi marker per le offerte (mantenendo lo stesso sistema di offset)
        offerte.forEach(offerta => {
            if (offerta.latitudine && offerta.longitudine) {
                // Crea una chiave univoca per questa posizione
                const posKey = `${offerta.latitudine.toFixed(6)}_${offerta.longitudine.toFixed(6)}`;
                
                // Applica un leggero offset se la posizione è già occupata
                let lat = offerta.latitudine;
                let lng = offerta.longitudine;
                
                if (usedPositions[posKey]) {
                    // Incrementa il contatore per questa posizione
                    usedPositions[posKey]++;
                    
                    // Aggiungi un piccolo offset a spirale
                    const angle = usedPositions[posKey] * (Math.PI / 4); // 45 gradi in radianti
                    const radius = 0.0002 * usedPositions[posKey]; // Circa 20-30 metri
                    lat += radius * Math.cos(angle);
                    lng += radius * Math.sin(angle);
                } else {
                    // Questa è la prima volta che usiamo questa posizione
                    usedPositions[posKey] = 1;
                }
                
                // Usa un'icona personalizzata per le offerte
                const offertaIcon = L.divIcon({
                    html: '<i class="bi bi-pin-map-fill marker-offerta"></i>',
                    className: 'custom-div-icon offerta-icon',
                    iconSize: [30, 30],
                    iconAnchor: [15, 30]
                });
                
                const marker = L.marker([lat, lng], {
                    icon: offertaIcon,
                    title: `Offerta: ${offerta.codice_offerta}`
                });
                
                // Aggiungi tooltip per visualizzazione rapida
                marker.bindTooltip(`<strong>Offerta:</strong> ${offerta.codice_offerta}<br><strong>Quantità:</strong> ${offerta.quantita} `);
                
                marker.bindPopup(createOffertaPopupContent(offerta));
                offerteCluster.addLayer(marker);
            }
        });
    }

    // Funzione per caricare i dati della mappa
    function loadMapData() {
        fetch('/api/map-data/')
            .then(response => response.json())
            .then(data => {
                // Debug - Verifica i dati ricevuti
                console.log('Dati ricevuti dalla mappa:', data);
                
                // Svuota i cluster esistenti
                commesseCluster.clearLayers();
                offerteCluster.clearLayers();
                
                // Usa la funzione di popolamento marker
                populateMarkers(data);
                
                // Zoom della mappa per adattarsi a tutti i marker
                if ((data.commesse && data.commesse.length > 0) || (data.offerte && data.offerte.length > 0)) {
                    const allLayers = [...commesseCluster.getLayers(), ...offerteCluster.getLayers()];
                    if (allLayers.length > 0) {
                        const group = L.featureGroup(allLayers);
                        map.fitBounds(group.getBounds().pad(0.1));
                    }
                }
                
                // Popola il filtro delle province dopo che i dati sono caricati
                populateProvinceFilter();
            })
            .catch(error => {
                console.error('Errore nel caricamento dei dati della mappa:', error);
                showError('Errore nel caricamento dei dati della mappa. Controlla la console per dettagli.');
            });
    }

    // Funzione per creare contenuto popup per commesse
    function createCommessaPopupContent(commessa) {
        return `
            <div class="popup-content">
                <h5 class="text-danger"><i class="bi bi-geo-alt-fill"></i> Commessa: ${commessa.codice_commessa}</h5>
                <p><strong>Quantità:</strong> ${commessa.quantita} t</p>
                <p><strong>Tipologia:</strong> ${commessa.tipologia || 'N/A'}</p>
                <p><strong>Produttore:</strong> ${commessa.produttore || 'N/A'}</p>
                <p><strong>Luogo di ritiro:</strong> ${commessa.indirizzo || 'N/A'}</p>
                <p><strong>Provincia:</strong> ${commessa.provincia || 'N/A'}</p>
                <p><strong>Anno:</strong> ${commessa.anno || 'N/A'}</p>
                <hr>
                <small class="text-muted">Commessa confermata</small>
            </div>
        `;
    }

    // Funzione per creare contenuto popup per offerte
    function createOffertaPopupContent(offerta) {
        return `
            <div class="popup-content">
                <h5 class="text-primary"><i class="bi bi-pin-map-fill"></i> Offerta: ${offerta.codice_offerta}</h5>
                <p><strong>Quantità:</strong> ${offerta.quantita} </p>
                <p><strong>Tipologia:</strong> ${offerta.tipologia || 'N/A'}</p>
                <p><strong>Produttore:</strong> ${offerta.produttore || 'N/A'}</p>
                <p><strong>Luogo di ritiro:</strong> ${offerta.indirizzo || 'N/A'}</p>
                <p><strong>Provincia:</strong> ${offerta.provincia || 'N/A'}</p>
                <p><strong>Data offerta:</strong> ${offerta.data_offerta || 'N/A'}</p>
                <p><strong>Anno:</strong> ${offerta.anno || 'N/A'}</p>
                <hr>
                <small class="text-muted">Offerta in attesa di conferma</small>
            </div>
        `;
    }

    // Funzione per inizializzare la tabella dei dati
    function initDataTable() {
        // Controlla se la tabella è già stata inizializzata
        if ($.fn.DataTable.isDataTable('#dataTable')) {
            return $('#dataTable').DataTable();
        }
        
        // Inizializza DataTable con opzioni di configurazione
        const dataTable = $('#dataTable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json',
            },
            responsive: true,
            order: [[1, 'asc']], // Ordina per codice di default
            pageLength: 25,
            columnDefs: [
                { "width": "10%", "targets": 0 },  // Tipo
                { "width": "15%", "targets": 1 },  // Codice
                { "width": "15%", "targets": 2 },  // Produttore
                { "width": "8%", "targets": 3 }    // Quantità
            ]
        });

        // Imposta il filtro per l'anno
        $('#yearFilter').change(function() {
            const yearValue = $(this).val();
            dataTable.column(8).search(yearValue === 'all' ? '' : yearValue).draw();
        });
        
        // Imposta il filtro per il tipo (commessa/offerta) SOLO per la tabella
        $('#typeFilter').change(function() {
            const typeValue = $(this).val();
            
            // Aggiorna SOLO i filtri della tabella
            if (typeValue === 'commesse') {
                dataTable.column(0).search('^Commessa$', true, false).draw();
            } else if (typeValue === 'offerte') {
                dataTable.column(0).search('^Offerta$', true, false).draw();
            } else {
                dataTable.column(0).search('').draw();
            }
            
            console.log(`Filtro tabella impostato su: ${typeValue}`);
        });
        
        return dataTable;
    }

    // Funzione per caricare i dati nella tabella
    function loadTableData(dataTable = null) {
        // Se dataTable non è fornito, ottienilo
        if (!dataTable) {
            dataTable = initDataTable();
        }
        
        // Controlla se dataTable è valido
        if (!dataTable) {
            console.error('Impossibile inizializzare la tabella dati');
            return;
        }
        
        // Prima svuota la tabella
        dataTable.clear();
        
        // Carica i dati dall'API
        fetch('/api/map-data/')
            .then(response => response.json())
            .then(data => {
                console.log('Dati ricevuti per la tabella:', data);
                
                // Aggiungi le commesse alla tabella
                if (data.commesse && data.commesse.length > 0) {
                    data.commesse.forEach(commessa => {
                        dataTable.row.add([
                            'Commessa',
                            commessa.codice_commessa,
                            commessa.produttore || '',
                            commessa.quantita || '',
                            commessa.tipologia || '',
                            commessa.indirizzo || '',
                            commessa.provincia || '',
                            commessa.data_ritiro || 'DA FARE',
                            commessa.anno || ''
                        ]).node().className = 'commessa-row';
                    });
                }
                
                // Aggiungi le offerte alla tabella
                if (data.offerte && data.offerte.length > 0) {
                    data.offerte.forEach(offerta => {
                        dataTable.row.add([
                            'Offerta',
                            offerta.codice_offerta,
                            offerta.produttore || '',
                            offerta.quantita || '',
                            offerta.tipologia || '',
                            offerta.indirizzo || '',
                            offerta.provincia || '',
                            offerta.data_offerta || 'DA FARE',
                            offerta.anno || ''
                        ]).node().className = 'offerta-row';
                    });
                }
                
                // Applica i cambiamenti alla tabella
                dataTable.draw();
                
                console.log(`Tabella popolata con ${data.commesse ? data.commesse.length : 0} commesse e ${data.offerte ? data.offerte.length : 0} offerte`);
            })
            .catch(error => {
                console.error('Errore durante il caricamento dei dati della tabella:', error);
            });
    }

    // Inizializza quando il documento è pronto
    $(document).ready(function() {
        // Inizializza la tabella e carica i dati in una sola operazione
        const dataTable = initDataTable();
        loadTableData(dataTable);
        
        // Aggiungi handler per quando si cambia tab
        $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
            // Se stiamo passando alla tab della tabella, ridisegna la tabella per il corretto rendering
            if (e.target.id === 'table-tab') {
                // Assicurati che la tabella esista prima di provare a ridisegnarla
                if ($.fn.DataTable.isDataTable('#dataTable')) {
                    $('#dataTable').DataTable().columns.adjust().draw();
                }
            }
        });
    });

    // Funzione per ricaricare i dati della tabella (per essere chiamata da altre parti del codice)
    function refreshTableData() {
        if ($.fn.DataTable.isDataTable('#dataTable')) {
            loadTableData($('#dataTable').DataTable());
        } else {
            loadTableData();
        }
    }

    // Aggiungi event listener per il filtro delle province
    document.getElementById('provinceFilter').addEventListener('change', function() {
        const selectedProvince = this.value;
        filterByProvince(selectedProvince);
    });
    
    // Variabile per tenere traccia dell'ultimo filtro provincia applicato
    let currentProvinceFilter = 'all';
    
    // Funzione per filtrare i marker per provincia
    function filterByProvince(province) {
        currentProvinceFilter = province;
        
        if (province === 'all') {
            // Se "Tutte le province" è selezionato, mostra tutti i marker
            // ma rispetta gli altri filtri attivi (es. solo commesse o solo offerte)
            const activeButton = document.querySelector('.btn-group .btn-primary').id;
            if (activeButton === 'showAll') {
                map.addLayer(commesseCluster);
                map.addLayer(offerteCluster);
            } else if (activeButton === 'showCommesse') {
                map.addLayer(commesseCluster);
                map.removeLayer(offerteCluster);
            } else if (activeButton === 'showOfferte') {
                map.removeLayer(commesseCluster);
                map.addLayer(offerteCluster);
            }
            
            // Resetta stili dei marker se c'è una ricerca attiva
            const searchText = document.getElementById('mapSearch').value.trim();
            if (searchText) {
                filterMapMarkers(searchText);
            }
            return;
        }
        
        // Crea nuovi cluster filtrati per provincia
        const filteredCommesseCluster = L.markerClusterGroup({
            iconCreateFunction: function(cluster) {
                return L.divIcon({
                    html: '<div class="cluster-icon cluster-commesse">' + cluster.getChildCount() + '</div>',
                    className: 'marker-cluster marker-cluster-commesse',
                    iconSize: L.point(40, 40)
                });
            }
        });
        
        const filteredOfferteCluster = L.markerClusterGroup({
            iconCreateFunction: function(cluster) {
                return L.divIcon({
                    html: '<div class="cluster-icon cluster-offerte">' + cluster.getChildCount() + '</div>',
                    className: 'marker-cluster marker-cluster-offerte',
                    iconSize: L.point(40, 40)
                });
            }
        });
        
        // Filtra le commesse per la provincia selezionata
        commesseCluster.getLayers().forEach(function(layer) {
            const popup = layer.getPopup();
            const popupContent = popup ? popup.getContent() : '';
            
            // Estrai la provincia dal popup (adatta questo in base al tuo formato di popup)
            if (popupContent.includes(`<strong>Provincia:</strong> ${province}`)) {
                // Clona il marker con tutte le sue proprietà
                const clonedMarker = L.marker(layer.getLatLng(), {
                    icon: layer.options.icon,
                    title: layer.options.title
                });
                
                clonedMarker.bindPopup(popup.getContent());
                if (layer._tooltip) {
                    clonedMarker.bindTooltip(layer._tooltip._content);
                }
                
                filteredCommesseCluster.addLayer(clonedMarker);
            }
        });
        
        // Filtra le offerte per la provincia selezionata
        offerteCluster.getLayers().forEach(function(layer) {
            const popup = layer.getPopup();
            const popupContent = popup ? popup.getContent() : '';
            
            // Estrai la provincia dal popup
            if (popupContent.includes(`<strong>Provincia:</strong> ${province}`)) {
                // Clona il marker con tutte le sue proprietà
                const clonedMarker = L.marker(layer.getLatLng(), {
                    icon: layer.options.icon,
                    title: layer.options.title
                });
                
                clonedMarker.bindPopup(popup.getContent());
                if (layer._tooltip) {
                    clonedMarker.bindTooltip(layer._tooltip._content);
                }
                
                filteredOfferteCluster.addLayer(clonedMarker);
            }
        });
        
        // Rimuovi i cluster originali e aggiungi quelli filtrati
        map.removeLayer(commesseCluster);
        map.removeLayer(offerteCluster);
        
        // Rispetta il filtro attivo (tutti, solo commesse, solo offerte)
        const activeButton = document.querySelector('.btn-group .btn-primary').id;
        if (activeButton === 'showAll' || activeButton === 'showCommesse') {
            map.addLayer(filteredCommesseCluster);
        }
        
        if (activeButton === 'showAll' || activeButton === 'showOfferte') {
            map.addLayer(filteredOfferteCluster);
        }
        
        // Se ci sono risultati, fai lo zoom
        if (filteredCommesseCluster.getLayers().length > 0 || filteredOfferteCluster.getLayers().length > 0) {
            const allLayers = [...filteredCommesseCluster.getLayers(), ...filteredOfferteCluster.getLayers()];
            const group = L.featureGroup(allLayers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
        
        // Aggiorna il contatore dei risultati
        const totalMarkers = filteredCommesseCluster.getLayers().length + filteredOfferteCluster.getLayers().length;
        updateFilterResultsInfo(totalMarkers, province);
    }
    
    // Funzione per popolare il dropdown delle province
    function populateProvinceFilter() {
        const provinces = new Set();
        
        // Raccogli tutte le province dai marker di commesse
        commesseCluster.getLayers().forEach(function(layer) {
            const popup = layer.getPopup();
            const popupContent = popup ? popup.getContent() : '';
            
            // Usa una regex per estrarre la provincia dal popup
            const match = popupContent.match(/<strong>Provincia:<\/strong>\s*([^<]+)/);
            if (match && match[1].trim()) {
                provinces.add(match[1].trim());
            }
        });
        
        // Raccogli tutte le province dai marker di offerte
        offerteCluster.getLayers().forEach(function(layer) {
            const popup = layer.getPopup();
            const popupContent = popup ? popup.getContent() : '';
            
            // Usa una regex per estrarre la provincia dal popup
            const match = popupContent.match(/<strong>Provincia:<\/strong>\s*([^<]+)/);
            if (match && match[1].trim()) {
                provinces.add(match[1].trim());
            }
        });
        
        // Ordina le province alfabeticamente
        const sortedProvinces = Array.from(provinces).sort();
        
        // Aggiungi le opzioni al dropdown
        const selectElement = document.getElementById('provinceFilter');
        
        // Mantieni solo l'opzione "Tutte le province"
        selectElement.innerHTML = '<option value="all">Tutte le province</option>';
        
        // Aggiungi le province trovate
        sortedProvinces.forEach(function(province) {
            const option = document.createElement('option');
            option.value = province;
            option.textContent = province;
            selectElement.appendChild(option);
        });
    }
    
    // Funzione per aggiornare info sui risultati del filtro provincia
    function updateFilterResultsInfo(count, province) {
        let infoElement = document.getElementById('filterResultsInfo');
        
        // Crea l'elemento se non esiste
        if (!infoElement) {
            infoElement = document.createElement('div');
            infoElement.id = 'filterResultsInfo';
            infoElement.className = 'alert alert-info mt-2';
            document.querySelector('.filter-controls').appendChild(infoElement);
        }
        
        // Aggiorna il contenuto e rendi visibile
        infoElement.textContent = `Trovati ${count} risultati per la provincia di ${province}`;
        infoElement.style.display = count > 0 ? 'block' : 'none';
    }
});