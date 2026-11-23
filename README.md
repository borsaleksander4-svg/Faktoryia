# Faktoryia

Automatyczny generator polskich filmów YouTube Shorts z ciekawostkami.

## Co robi obecna wersja

- Wybiera ciekawostkę z `data/facts.json`.
- Nie powtarza faktów, dopóki nie wykorzysta całej listy.
- Tworzy polską narrację głosową przez darmowy syntezator eSpeak NG.
- Projektuje pionową planszę 1080 × 1920.
- Łączy obraz i narrację w plik MP4 w formacie 9:16.
- Dodaje plik tekstowy z opisem i linkiem do źródła.
- Udostępnia oba pliki jako artefakt GitHub Actions.

## Uruchamianie

### Automatycznie

Workflow jest zaplanowany na każdy dzień o 16:00 UTC. Godzina odpowiada 17:00 w Polsce zimą i 18:00 latem. Każde uruchomienie generuje jeden film.

### Ręcznie

1. Otwórz repozytorium **Faktoryia** na GitHubie.
2. Wejdź w zakładkę **Actions**.
3. Wybierz workflow **Generuj film Faktoryia**.
4. Kliknij **Run workflow**.
5. Pole `fact_id` pozostaw puste, aby wybrać losowy niewykorzystany fakt, albo wpisz ID konkretnego faktu z `data/facts.json`.
6. Po zakończeniu otwórz wykonanie workflow i pobierz artefakt **faktoryia-short**.

W archiwum ZIP znajdziesz film MP4 oraz plik TXT z opisem i źródłem. Artefakt jest przechowywany przez 7 dni, więc pobierz go przed upływem tego czasu.

## Dodawanie kolejnych ciekawostek

Dopisz do `data/facts.json` kolejny obiekt z unikalnym `id`, tytułem, tekstem narracji i wiarygodnym adresem źródła:

```json
{
  "id": 3,
  "title": "Tytuł ciekawostki",
  "script": "Krótki tekst, który ma zostać przeczytany przez lektora.",
  "source": "https://example.org/źródło"
}
```

Dodanie lub zmiana faktu automatycznie uruchomi generator.

## Koszt i ograniczenia

Projekt używa GitHub Actions, Pythona, Pillow, FFmpeg i eSpeak NG. Nie używa płatnych API, kluczy API ani płatnych subskrypcji. Repozytorium jest publiczne, więc standardowe GitHub-hosted runners dla tego repozytorium są bezpłatne.

Lektor eSpeak NG jest wyraźnie syntetyczny i brzmi bardziej mechanicznie niż komercyjne głosy AI. Obecna wersja tworzy prosty film z planszą i delikatnym ruchem kamery, a nie rozbudowany montaż z nagraniami wideo.

**Publikacja na YouTube nie jest automatyczna.** Gotowy film trzeba sprawdzić, a następnie ręcznie przesłać na kanał.

## Struktura

- `.github/workflows/generate-short.yml` — harmonogram i budowanie filmu.
- `data/facts.json` — baza ciekawostek.
- `data/history.json` — historia wykorzystanych ciekawostek.
- `src/generate.py` — generator grafiki, narracji i MP4.
- `requirements.txt` — biblioteki Pythona.
