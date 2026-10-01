# Curriculum

Genera la hoja de vida en PDF (inglés y español) a partir de un único archivo de datos.

| Archivo | Para qué sirve |
| :--- | :--- |
| `cv_data.json` | Fuente de verdad: experiencia, proyectos, habilidades, educación (EN y ES) |
| `generate_cv.py` | Genera los PDF con ReportLab |
| `output/` | PDF finales (se versionan) |
| `../portfolio/public/cv/` | Copia que descarga el botón "Download CV" del portafolio |

## Uso local

```bash
pip install -r curriculum/requirements.txt
python curriculum/generate_cv.py
```

## Automático

El workflow `.github/workflows/curriculum.yml` corre en cada push a `main` o `portafolio`,
regenera los PDF y los sube con el commit `chore: update CV` solo si cambiaron.
El PDF es determinista, así que un commit que no toca `cv_data.json` no produce cambios.

## Pensado para ATS

- Una sola columna, sin tablas, imágenes ni íconos.
- Texto real y seleccionable, fuente estándar (Helvetica).
- Encabezados convencionales: Professional Summary, Work Experience, Technical Skills, Selected Projects, Education.
- Fechas con formato uniforme (`Sep 2026 - Present`) y guiones simples como viñetas.
- Metadatos del PDF (título, autor) completos.

## Mantenerlo al día

Edita solo `cv_data.json`. Para agregar estudios, llena `education` en cada idioma:

```json
"education": [
  { "degree": "Tecnólogo en ...", "institution": "SENA", "place": "Colombia", "start": "2023", "end": "2025" }
]
```
