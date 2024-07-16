import streamlit as st  # Importa Streamlit per la creazione dell'applicazione web
import requests  # Per effettuare richieste HTTP alle pagine web
from bs4 import BeautifulSoup  # Per il parsing dell'HTML
from PyPDF2 import PdfReader  # Per lavorare con i file PDF
import io  # Per la gestione dei dati in memoria
import re  # Per l'uso delle espressioni regolari
import nltk  # Libreria per il processamento del linguaggio naturale
from nltk.tokenize import sent_tokenize  # Per la tokenizzazione delle frasi

nltk.download('punkt')  # Download dei dati necessari per NLTK (tokenizzazione)

# Funzione per estrarre il testo da un PDF dato l'URL
def extract_text_from_pdf(url):
    try:
        response = requests.get(url)  # Effettua la richiesta GET all'URL del PDF
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            # Verifica se la risposta è valida e se il tipo di contenuto è PDF
            pdf_data = io.BytesIO(response.content)  # Ottiene i dati del PDF
            reader = PdfReader(pdf_data)  # Crea un oggetto PdfReader
            text = ''
            for page in reader.pages:  # Itera tra tutte le pagine del PDF
                text += page.extract_text()  # Estrae il testo dalla pagina corrente
            return text  # Ritorna il testo estratto dal PDF
        else:
            st.write("PDF non apribile, errore")  # Se il PDF non è valido, mostra un messaggio di errore
            return None
    except Exception as e:
        st.write(f"Errore durante l'estrazione del testo dal PDF: {e}")  # Gestisce le eccezioni mostrando l'errore
        return None

# Funzione per cercare frasi contenenti il termine specificato (NOAEL o LD50) nei PDF
def search_terms_in_pdf(url, term):
    text = extract_text_from_pdf(url)  # Ottiene il testo dal PDF tramite la funzione sopra
    results = []  # Lista per memorizzare i risultati delle frasi trovate
    if text:  # Se il testo è stato estratto correttamente
        if term == 'NOAEL':
            matches = list(re.finditer(r'(\.|\s)(NOAEL[^\.]+)\.', text, re.IGNORECASE))
            # Trova tutte le corrispondenze di NOAEL nel testo ignorando maiuscole/minuscole
        elif term == 'LD50':
            matches = list(re.finditer(r'(\.|\s)(LD\s*50[^\.]+)\.', text, re.IGNORECASE))
            # Trova tutte le corrispondenze di LD50 nel testo ignorando maiuscole/minuscole
        else:
            matches = []  # Se il termine non è né NOAEL né LD50, inizializza vuoto

        for match in matches:  # Itera tra tutte le corrispondenze trovate
            phrase = match.group(2)  # Ottiene la frase corrispondente al gruppo 2 (escluso il punto finale)
            sentences = sent_tokenize(phrase)  # Tokenizza la frase in frasi più piccole
            for sentence in sentences:  # Itera tra tutte le frasi tokenizzate
                if len(sentence.split()) <= 50:  # Controlla che la frase non superi le 50 parole
                    results.append(sentence.strip())  # Aggiunge la frase trovata ai risultati

    return results  # Ritorna tutte le frasi contenenti il termine cercato

# Funzione per estrarre i link ai PDF da una pagina web data l'URL della pagina
def PDF(url):
    st.write("URL (link prima pagina):", url)  # Mostra l'URL della pagina web
    response = requests.get(url)  # Effettua la richiesta GET all'URL della pagina
    if response.status_code == 200:  # Verifica se la richiesta è andata a buon fine
        soup = BeautifulSoup(response.text, 'html.parser')  # Parsing dell'HTML della pagina
        pdf_links = soup.find_all('a')  # Trova tutti i link 'a' nella pagina

        if len(pdf_links) > 2:
            pdf_links = pdf_links[2:-1]  # Rimuove i primi due e l'ultimo link, considerando solo quelli rilevanti
        else:
            st.write("Non sono stati trovati abbastanza link ai PDF.")
            return []

        pdf_urls = []
        for link in pdf_links:  # Itera tra tutti i link trovati
            provvisorio = link.get('href')  # Ottiene l'attributo href del link
            if provvisorio and not provvisorio.startswith('javascript:'):  # Controlla se è un link valido
                url_completo = 'https://cir-reports.cir-safety.org/' + provvisorio.lstrip('/')
                # Costruisce l'URL completo del PDF

                pdf_response = requests.get(url_completo)  # Effettua la richiesta GET al PDF
                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                    # Verifica se la risposta è valida e il tipo di contenuto è PDF
                    pdf_urls.append(url_completo)  # Aggiunge l'URL del PDF alla lista dei risultati
                else:
                    st.write("PDF non apribile, errore")  # Se il PDF non è valido, mostra un messaggio di errore

        return pdf_urls  # Ritorna la lista di URL dei PDF trovati
    else:
        st.write("Impossibile recuperare l'URL. Codice di stato:", response.status_code)
        return []  # Se la richiesta non è andata a buon fine, ritorna una lista vuota

# Funzione per cercare un farmaco specifico e ottenere i PDF correlati
def farmaci(farmaco):
    farmaco = farmaco.strip().lower()  # Normalizza l'input per il confronto
    try:
        with open("C:/Users/GabrieleIncorvaia/OneDrive - ITS Angelo Rizzoli/Desktop/Project Work/Ispezione.html", "r", encoding="utf-8") as web:
            content = web.read()  # Legge il contenuto dell'HTML

        soup = BeautifulSoup(content, 'html.parser')  # Parsing dell'HTML
        siti = soup.find_all('a')  # Trova tutti i link 'a' nell'HTML

        # Crea un dizionario per mappare i nomi dei farmaci ai loro URL
        drug_to_url = {link.text.strip().lower(): 'https://cir-reports.cir-safety.org' + link['href'] for link in siti}

        if farmaco in drug_to_url:  # Se il nome del farmaco è nel dizionario
            st.session_state['farmaco_url'] = drug_to_url[farmaco]  # Salva l'URL del farmaco nella sessione
            st.session_state['farmaco_trovato'] = True  # Imposta il flag per indicare che il farmaco è stato trovato
            st.write("Farmaco trovato:", farmaco.title())  # Mostra il nome del farmaco trovato
            st.session_state['pdf_urls'] = PDF(st.session_state['farmaco_url'])  # Ottiene i PDF correlati al farmaco
        else:
            st.write("Il farmaco non è presente o il nome non è completo.")  # Se il farmaco non è nel dizionario
            st.session_state['farmaco_trovato'] = False  # Imposta il flag per indicare che il farmaco non è stato trovato
    except FileNotFoundError:
        st.write("File HTML non trovato. Si prega di verificare il percorso.")  # Gestisce il caso in cui il file HTML non è trovato
        st.session_state['farmaco_trovato'] = False  # Imposta il flag per indicare che il farmaco non è stato trovato
    except Exception as e:
        st.write(f"Si è verificato un errore: {e}")  # Gestisce tutte le altre eccezioni mostrando l'errore
        st.session_state['farmaco_trovato'] = False  # Imposta il flag per indicare che il farmaco non è stato trovato

# Funzione per ottenere tutti gli ingredienti dall'HTML
def get_all_ingredients():
    try:
        with open("C:/Users/GabrieleIncorvaia/OneDrive - ITS Angelo Rizzoli/Desktop/Project Work/Ispezione.html", "r", encoding="utf-8") as web:
            content = web.read()  # Legge il contenuto dell'HTML

        soup = BeautifulSoup(content, 'html.parser')  # Parsing dell'HTML
        links = soup.find_all('a')  # Trova tutti i link 'a' nell'HTML

        ingredients = [link.text.strip() for link in links if link.text.strip() and 'cir' not in link.text.lower() and not re.match(r'^[A-Z#!]$', link.text.strip())]
        # Ottiene tutti gli ingredienti escludendo alcuni link e testi specifici

        return ingredients  # Ritorna la lista di ingredienti trovati
    except FileNotFoundError:
        st.write("File HTML non trovato. Si prega di verificare il percorso.")  # Gestisce il caso in cui il file HTML non è trovato
        return []  # Ritorna una lista vuota se il file HTML non è trovato
    except Exception as e:
        st.write(f"Si è verificato un errore: {e}")  # Gestisce tutte le altre eccezioni mostrando l'errore
        return []  # Ritorna una lista vuota se si verifica un errore

# Streamlit Applicazione
st.title("Ricerca Ingredienti")  # Titolo dell'applicazione

# Ottieni tutti gli ingredienti dall'HTML
all_ingredients = get_all_ingredients()

# Aggiungi una sezione vuota all'inizio della lista degli ingredienti
all_ingredients.insert(0, "")

# Utilizza st.form per gestire il submit con il tasto Invio
with st.form(key='ingredient_form'):
    ingredient_name = st.selectbox("Seleziona un ingrediente", all_ingredients, key='ingredient_name')

    # Gestisci il submit con il tasto Invio
    submitted = st.form_submit_button("Cerca")

    if submitted and ingredient_name:
        farmaci(ingredient_name.lower())  # Esegui la ricerca del farmaco corrispondente all'ingrediente selezionato

# Verifica se è stato trovato un farmaco e visualizza le informazioni associate
if 'farmaco_trovato' in st.session_state and st.session_state['farmaco_trovato']:
    if st.session_state.get('pdf_urls'):  # Se sono stati trovati dei PDF associati al farmaco
        st.write("PDF n. 1:", st.session_state['pdf_urls'][0])  # Mostra il primo PDF trovato
        for i, pdf_url in enumerate(st.session_state['pdf_urls'][1:], start=2):
            st.write(f"PDF n. {i}:", pdf_url)  # Mostra gli altri PDF trovati

    if st.button("Visualizza NOAEL"):  # Se il pulsante NOAEL viene premuto
        all_noael_results = []  # Lista per memorizzare tutti i risultati NOAEL trovati
        for pdf_url in st.session_state['pdf_urls']:  # Itera tra tutti i PDF associati al farmaco
            results = search_terms_in_pdf(pdf_url, 'NOAEL')  # Cerca i termini NOAEL in ogni PDF
            all_noael_results.extend(results)  # Aggiunge i risultati trovati alla lista totale
        if all_noael_results:  # Se sono stati trovati dei risultati NOAEL
            st.write("NOAEL trovato in:")  # Mostra un messaggio di conferma
            for result in all_noael_results:  # Itera tra tutti i risultati NOAEL trovati
                st.write(result)  # Mostra ogni risultato NOAEL trovato
        else:
            st.write("NOAEL non trovato in nessun PDF.")  # Se non sono stati trovati risultati NOAEL, mostra un messaggio di avviso

    if st.button("Visualizza LD50"):  # Se il pulsante LD50 viene premuto
        all_ld50_results = []  # Lista per memorizzare tutti i risultati LD50 trovati
        for pdf_url in st.session_state['pdf_urls']:  # Itera tra tutti i PDF associati al farmaco
            results = search_terms_in_pdf(pdf_url, 'LD50')  # Cerca i termini LD50 in ogni PDF
            all_ld50_results.extend(results)  # Aggiunge i risultati trovati alla lista totale
        if all_ld50_results:  # Se sono stati trovati dei risultati LD50
            st.write("LD50 trovato in:")  # Mostra un messaggio di conferma
            for result in all_ld50_results:  # Itera tra tutti i risultati LD50 trovati
                st.write(result)  # Mostra ogni risultato LD50 trovato
        else:
            st.write("LD50 non trovato in nessun PDF.")  # Se non sono stati trovati risultati LD50, mostra un messaggio di avviso
