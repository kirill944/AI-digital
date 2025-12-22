# S04 – eda_cli: HTTP-сервис качества датасетов (FastAPI)

Расширенная версия проекта eda-cli из Семинара 03.

К существующему CLI-приложению для EDA добавлен HTTP-сервис на FastAPI с эндпоинтами /health, /quality, /quality-from-csv и /quality-flags-from-csv.
Используется в рамках Семинара 04 курса «Инженерия ИИ».

## Связь с S03

Проект в S04 основан на том же пакете eda_cli, что и в S03:

сохраняется структура src/eda_cli/ и CLI-команда eda-cli;

добавлен модуль api.py с FastAPI-приложением;

в зависимости добавлены fastapi и uvicorn[standard].

Цель S04 – показать, как поверх уже написанного EDA-ядра поднять простой HTTP-сервис.

## Требования   

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) установлен в систему
- Браузер (для Swagger UI /docs) или любой HTTP-клиент:


## Инициализация проекта

В корне проекта (HW04/eda-cli):

```bash
uv sync
```

Эта команда:

- создаст виртуальное окружение `.venv`;
- установит зависимости из `pyproject.toml`;
- установит сам проект `eda-cli` в окружение.

## Запуск CLI

### Краткий обзор

```bash
uv run eda-cli overview data/example.csv
```

Параметры:

- `--sep` – разделитель (по умолчанию `,`);
- `--encoding` – кодировка (по умолчанию `utf-8`).

### Полный EDA-отчёт

```bash
uv run eda-cli report data/example.csv --out-dir reports
```

### Команды

--max-hist-columns – сколько числовых колонок включать в набор гистограмм (по умолчанию: 6)

--top-k-categories – сколько top-значений выводить для категориальных признаков (по умолчанию: 5)

--title – заголовок отчёта в Markdown (по умолчанию: "EDA-отчёт")

--min-missing-share – порог доли пропусков для выделения проблемных колонок (по умолчанию: 0.3)

### Влияние команд на отчет
--max-hist-columns – ограничивает количество гистограмм для числовых колонок

--top-k-categories – определяет сколько значений показывать для категориальных признаков

--title – задаёт заголовок Markdown-отчёта

--min-missing-share – колонки с долей пропусков выше этого порога попадают в отдельный список "проблемных"
### Пример

```bash
uv run eda-cli report data/dataset.csv \
  --out-dir my_report \
  --max-hist-columns 10 \
  --top-k-categories 8 \
  --title "Анализ пользовательских данных" \
  --min-missing-share 0.4
```

###

В результате в каталоге `reports/` появятся:

- `report.md` – основной отчёт в Markdown;
- `summary.csv` – таблица по колонкам;
- `missing.csv` – пропуски по колонкам;
- `correlation.csv` – корреляционная матрица (если есть числовые признаки);
- `top_categories/*.csv` – top-k категорий по строковым признакам;
- `hist_*.png` – гистограммы числовых колонок;
- `missing_matrix.png` – визуализация пропусков;
- `correlation_heatmap.png` – тепловая карта корреляций.

## Тесты

```bash
uv run pytest -q
```

## Запуск HTTP-сервиса

```bash
uv run uvicorn eda_cli.api:app --reload --port 8000
```

### Пояснения:

- eda_cli.api:app - путь до объекта FastAPI app в модуле eda_cli.api;

- --reload - автоматический перезапуск сервера при изменении кода (удобно для разработки);

- --port 8000 - порт сервиса (можно поменять при необходимости).

После запуска сервис будет доступен по адресу:
http://127.0.0.1:8000

## Эндпоинты сервиса

### 1. `GET /health`

Простейший health-check.

**Запрос:**

```http
GET /health
```

**Ожидаемый ответ `200 OK` (JSON):**

```json
{
  "status": "ok",
  "service": "dataset-quality",
  "version": "0.2.0"
}
```

Пример проверки через `curl`:

```bash
curl http://127.0.0.1:8000/health
```

---

### 2. Swagger UI: `GET /docs`

Интерфейс документации и тестирования API:

```text
http://127.0.0.1:8000/docs
```

Через `/docs` можно:

- вызывать `GET /health`;
- вызывать `POST /quality` (форма для JSON);
- вызывать `POST /quality-from-csv` (форма для загрузки файла).

---

### 3. `POST /quality` – заглушка по агрегированным признакам

Эндпоинт принимает **агрегированные признаки датасета** (размеры, доля пропусков и т.п.) и возвращает эвристическую оценку качества.

**Пример запроса:**

```http
POST /quality
Content-Type: application/json
```

Тело:

```json
{
  "n_rows": 10000,
  "n_cols": 12,
  "max_missing_share": 0.15,
  "numeric_cols": 8,
  "categorical_cols": 4
}
```

**Пример ответа `200 OK`:**

```json
{
  "ok_for_model": true,
  "quality_score": 0.8,
  "message": "Данных достаточно, модель можно обучать (по текущим эвристикам).",
  "latency_ms": 3.2,
  "flags": {
    "too_few_rows": false,
    "too_many_columns": false,
    "too_many_missing": false,
    "no_numeric_columns": false,
    "no_categorical_columns": false
  },
  "dataset_shape": {
    "n_rows": 10000,
    "n_cols": 12
  }
}
```

**Пример вызова через `curl`:**

```bash
curl -X POST "http://127.0.0.1:8000/quality" \
  -H "Content-Type: application/json" \
  -d '{"n_rows": 10000, "n_cols": 12, "max_missing_share": 0.15, "numeric_cols": 8, "categorical_cols": 4}'
```

---

### 4. `POST /quality-from-csv` – оценка качества по CSV-файлу

Эндпоинт принимает CSV-файл, внутри:

- читает его в `pandas.DataFrame`;
- вызывает функции из `eda_cli.core`:

  - `summarize_dataset`,
  - `missing_table`,
  - `compute_quality_flags`;
- возвращает оценку качества датасета в том же формате, что `/quality`.

**Запрос:**

```http
POST /quality-from-csv
Content-Type: multipart/form-data
file: <CSV-файл>
```

Через Swagger:

- в `/docs` открыть `POST /quality-from-csv`,
- нажать `Try it out`,
- выбрать файл (например, `data/example.csv`),
- нажать `Execute`.

**Пример вызова через `curl` (Linux/macOS/WSL):**

```bash
curl -X POST "http://127.0.0.1:8000/quality-from-csv" \
  -F "file=@data/example.csv"
```

Ответ будет содержать:

- `ok_for_model` - результат по эвристикам;
- `quality_score` - интегральный скор качества;
- `flags` - булевы флаги из `compute_quality_flags`;
- `dataset_shape` - реальные размеры датасета (`n_rows`, `n_cols`);
- `latency_ms` - время обработки запроса.

### 5. POST /quality-flags-from-csv – полный набор флагов качества по CSV-файлу
Эндпоинт принимает CSV-файл и возвращает полный набор флагов качества с дополнительной информацией о датасете. В отличие от /quality-from-csv, этот эндпоинт предоставляет более детализированную информацию, включая все булевы флаги и расширенные сведения о датасете.

**Запрос:**

```http
POST /quality-flags-from-csv
Content-Type: multipart/form-data
file: <CSV-файл>
```

Пример вызова через curl:
```bash
curl -X POST "http://127.0.0.1:8000/quality-flags-from-csv" \
-F "file=@data/example.csv"
```

Пример ответа:
```json
{
  "flags": {
    "too_few_rows": false,
    "too_many_columns": false,
    "too_many_missing": false,
    "has_constant_columns": false,
    "has_high_cardinality_categoricals": false
  },
  "dataset_info": {
    "filename": "example.csv",
    "n_rows": 1500,
    "n_cols": 8,
    "numeric_cols": 5,
    "categorical_cols": 3
  },
  "latency_ms": 45.3
}
```
Этот эндпоинт полезен, когда нужно получить не только итоговую оценку, но и детализированный анализ всех аспектов качества данных.