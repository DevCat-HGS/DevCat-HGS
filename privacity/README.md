# Privacity

Muestra en el README del perfil una lista **elegida por ti** de repositorios privados, sin exponer el código ni nombres que no quieras publicar.

## Cómo funciona

1. Tú decides qué aparece en [`featured.json`](featured.json). **Nada se publica por defecto**: un repo nuevo, aunque sea privado, no aparece hasta que lo agregues.
2. Cada entrada lleva un título y una descripción públicos escritos por ti (en inglés y español).
3. El script [`update_private_repos.py`](update_private_repos.py) dibuja una tabla en `README.md` y `README.es.md`, entre los marcadores:

   ```
   <!-- PRIVATE-REPOS:START -->
   <!-- PRIVATE-REPOS:END -->
   ```

4. Los repos privados salen con la etiqueta **Private repository** y **sin enlace** (para los demás darían 404).
5. Si `featured.json` está vacío, la sección no aparece.

## Agregar un repo

Copia el formato de [`featured.example.json`](featured.example.json) dentro de `repos` en `featured.json`:

| Campo | Qué es |
| :--- | :--- |
| `repo` | `owner/name` exacto del repositorio |
| `private` | `true` o `false`. Con token, se verifica contra GitHub y se usa el valor real |
| `title` / `description` | Texto público en `en` y `es`. Obligatorios |
| `stack` | Lista de tecnologías |
| `url` | Opcional. Un enlace público (por ejemplo el sitio en vivo) |
| `client` + `show_client` | El cliente solo se muestra si `show_client` es `true` |
| `show_updated` | Muestra "actualizado mes año" según el último push |

`blocked_terms` es una lista de palabras que **no pueden** aparecer en el texto público (nombres de cliente, por ejemplo). Si una aparece, el script falla en vez de publicarla.

## Ejecutarlo

```bash
python privacity/update_private_repos.py              # escribe los README
python privacity/update_private_repos.py --check      # no escribe; falla si algo está desactualizado
python privacity/update_private_repos.py --no-verify  # sin llamadas a la API de GitHub
```

No necesita dependencias: usa solo la biblioteca estándar de Python.

## Automático (GitHub Actions)

El workflow [`.github/workflows/privacity.yml`](../.github/workflows/privacity.yml) corre al cambiar `featured.json`, a mano y cada día (para refrescar la fecha de "actualizado"). Hace commit de los README solo si cambiaron.

Para verificar repos privados necesita el secreto **`METRICS_TOKEN`** (el mismo del workflow de métricas):

- Token clásico con alcance `repo`, o
- token de grano fino con acceso de solo lectura (*Metadata*) a los repos que listes.

Sin token el script funciona igual, pero no puede comprobar la visibilidad real y lo avisa en el log.

> El README del perfil se muestra desde la rama **main**. Para que el programa diario (`schedule`) corra, este workflow tiene que existir en `main`.
