# Faktoryia

Automatyczny generator około dwuminutowych polskich filmów w stylu **„Co, gdyby…?”**.

## Jak działa

- Wybiera odcinek z `data/facts.json`.
- Generuje polską narrację neuronowym głosem Piper.
- Renderuje sześć animowanych scen 3D w Blenderze, z miastem, postaciami, wodą i lodem.
- Dodaje delikatny ruch kamery, napisy rozdziałów i montuje pionowe wideo 1080 × 1920.
- Dopasowuje długość filmu do nagrania lektora (docelowo około 2 minut).
- Zapisuje film MP4 oraz osobny plik TXT z opisem i źródłami.
- Udostępnia gotowe pliki jako artefakt GitHub Actions.

## Uruchamianie

### Automatycznie
Workflow uruchamia się codziennie o 16:00 UTC (17:00 zimą / 18:00 latem w Polsce).

### Ręcznie
1. Otwórz repozytorium Faktoryia.
2. Wejdź w Actions.
3. Wybierz „Generuj film Faktoryia”.
4. Kliknij Run workflow.
5. Opcjonalnie wpisz `episode_id` z `data/facts.json`.
6. Po zakończeniu pobierz artefakt `faktoryia-what-if-odcinek`.

## Dodawanie odcinków

Każdy odcinek musi zawierać:
- `id` – unikalny numer,
- `title` – tytuł pytania „Co, gdyby…?”,
- `description` – krótki opis do publikacji,
- `script` – pełny tekst narracji (około 180–300 słów),
- `sources` – lista wiarygodnych źródeł,
- `scenes` – co najmniej pięć krótkich podpisów scen.

Generator sprawdza długość lektora. Jeśli narracja trwa mniej niż 95 sekund lub więcej niż 155 sekund, przerwie budowanie zamiast tworzyć film o złej długości.

## Koszt i ograniczenia

Projekt używa darmowych narzędzi: GitHub Actions, Python, Blender, Pillow, FFmpeg i Piper. Nie korzysta z płatnych API ani subskrypcji. Lektor jest syntezowany lokalnie w maszynie GitHub Actions.

Sceny są stylizowanymi animacjami 3D renderowanymi w Blenderze. Nie są to realistyczne klipy generowane przez model wideo AI. Publikacja na YouTube nie jest automatyczna: przed publikacją człowiek powinien sprawdzić film, opis i źródła.

## Struktura

- `.github/workflows/generate-short.yml` – automatyzacja.
- `data/facts.json` – scenariusze odcinków.
- `src/generate.py` – generator scen, narracji i MP4.
- `requirements.txt` – zależności Pythona.
