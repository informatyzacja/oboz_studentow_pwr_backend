# Bingo App – Dokumentacja Backendowa

Aplikacja Django obsługująca rozgrywkę w **Bingo** – w tym losowanie planszy zadań, przesyłanie dowodów ich wykonania, recenzję przez admina oraz weryfikację wygranej.

## Spis treści

- [Modele](#modele)
- [API i Endpointy](#api-i-endpointy)
- [Zasady działania gry](#zasady-działania-gry)
- [Admin panel](#admin-panel)
- [Utils (logika gry)](#utils-logika-gry)
- [Przykładowy JSON](#przykładowy-json)
- [Uwagi](#uwagi)


---

## Modele

### `BingoTaskTemplate`

Szablon zadania, które może pojawić się na planszy bingo.

| Pole | Typ | Opis |
|------|-----|------|
| `task_name` | `TextField` | Nazwa zadania |
| `description` | `TextField (optional)` | Opis |
| `is_active` | `Boolean` | Czy zadanie może być losowane |

---

### `BingoUserInstance`

Plansza użytkownika. Jedna plansza = jedna gra bingo.

| Pole | Typ | Opis |
|------|-----|------|
| `user` | `ForeignKey` → `User` | Właściciel planszy |
| `created_at` | `DateTime` | Data utworzenia |
| `completed_at` | `DateTime` | Data zakończenia (jeśli użytkownik zgłosił bingo) |
| `has_won` | `Boolean` | Czy użytkownik wygrał |
| `needs_bingo_admin_review` | `Boolean` | Czy plansza wymaga sprawdzenia admina |
| `swap_used` | `Boolean` | Czy użytkownik wykorzystał możliwość zamiany zadania |

---

### `BingoUserTask`

Zadanie przypisane do pola (komórki) planszy użytkownika.

| Pole | Typ | Opis |
|------|-----|------|
| `task` | `ForeignKey` → `BingoTaskTemplate` | Zadanie bazowe |
| `instance` | `ForeignKey` → `BingoUserInstance` | Plansza użytkownika |
| `row`, `col` | `int` | Pozycja w siatce 5x5 |
| `task_state` | `CharField` | Stan zadania (`not_started`, `submitted`, `approved`, `rejected`) |
| `user_comment` | `TextField` | Komentarz użytkownika |
| `reviewer_comment` | `TextField` | Komentarz recenzenta |
| `photo_proof` | `ImageField` | Zdjęcie jako dowód |
| `submitted_at`, `reviewed_at` | `DateTime` | Timestamps |
| `reviewed_by` | `User` | Kto recenzował |

---

## API i Endpointy

> Prefix: `/api/`

### `GET /bingo/`
Zwraca wszystkie plansze użytkownika (BingoUserInstance).

---

### `PUT /bingo/{id}/submit_bingo/`
Użytkownik zgłasza zakończenie planszy.

---

### `GET /bingo-task/`
Zadania przypisane do plansz użytkownika.

---

### `PUT /bingo-task/{id}/upload-photo/`
Wysyłka zdjęcia dowodowego do danego zadania.

**Payload (multipart/form-data):**
```
photo_proof: file
```

---

### `PUT /bingo-task/{id}/add_comment/`
Dodanie komentarza użytkownika do zadania.

**Payload (JSON):**
```json
{
  "user_comment": "To zdjęcie pokazuje wykonanie zadania"
}
```

---

### `PUT /bingo-task/{id}/swap_task/`
Użytkownik zamienia to zadanie na inne.

---

### `GET /bingo-review/`
Dostępne tylko dla adminów – pokazuje plansze do recenzji.

---

### `PUT /bingo-review/{id}/approve_bingo_win/`
Admin zatwierdza wygraną.

---

### `PUT /bingo-review/{id}/reject_bingo_win/`
Admin odrzuca zgłoszoną wygraną.

---

### `PUT /bingo-review/{id}/review-task/{task_id}/`
Recenzja konkretnego zadania.

**Payload (JSON):**
```json
{
  "task_state": "approved",
  "reviewer_comment": "Świetna robota!"
}
```

---

## Zasady działania gry

- **Plansza 5x5** generowana jest losowo z aktywnych zadań (`create_bingo_for_user`).
- Użytkownik wykonuje zadania, dodaje komentarze i zdjęcia.
- Wysyłka zdjęcia automatycznie zmienia status zadania na `submitted`.
- Admin recenzuje zadania i zatwierdza (`approved`) lub odrzuca (`rejected`).
- Po zatwierdzeniu odpowiedniego układu (wiersz, kolumna, przekątna), system automatycznie oznacza planszę jako wymagającą recenzji wygranej (`needs_bingo_admin_review`).

---

## Admin panel

- Admin widzi zadania (`BingoTaskTemplate`), plansze (`BingoUserInstance`) i może recenzować je z poziomu panelu.
- Plansze użytkowników mają inline podgląd zadań.

---

## Utils (logika gry)

### `create_bingo_for_user(user, num_tasks=25)`
Tworzy nową planszę użytkownika z losowymi zadaniami 5x5.

---

### `swap_user_task(task)`
Zamienia dane zadanie użytkownika na inne, jeśli nie wykorzystano jeszcze możliwości zamiany.

---

### `check_bingo_win(instance)`
Sprawdza, czy użytkownik ma wypełnioną linię w planszy (wiersz, kolumna lub przekątna) składającą się z **zaakceptowanych zadań**.

---

## Przykładowy JSON

```json
{
  "task": {
    "task_name": "Zrób 10 pompek",
    "description": "Udokumentuj na zdjęciu",
    "is_active": true
  },
  "row": 1,
  "col": 2,
  "task_state": "approved",
  "photo_url": "https://example.com/media/bingo_photos/pompki.jpg"
}
```

---

## Uwagi 

- Pola `photo_proof` i `photo_url` to zdjęcia użytkownika – do podglądu.
- `task_state` można wizualnie oznaczać kolorami:
  - `approved` = zielony
  - `rejected` = czerwony
  - `submitted` = niebieski
  - `not_started` = szary
- Status planszy użytkownika (`has_won`, `needs_bingo_admin_review`) można wykorzystać do pokazywania banerów informacyjnych.
- `swap_used` pozwala pokazać przycisk zamiany tylko raz na planszę.

