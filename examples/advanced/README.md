# Ejemplos de Características Avanzadas de YAML

Este directorio contiene ejemplos que demuestran las características avanzadas de YAML disponibles en anki-yaml-tool.

## Características Incluidas

### 1. YAML Includes (!include)

Permite incluir fragmentos de otros archivos YAML.

```yaml
# Incluir un archivo completo
config: !include config_fragment.yaml

# Incluir solo una clave específica
data: !include [data_fragment.yaml, section_name]
```

**Archivos de ejemplo:**
- `config_fragment.yaml` - Fragmento de configuración
- `data_fragment.yaml` - Fragmento de datos

### 2. Variables de Entorno

Sustitución automática de variables de entorno en el YAML.

```yaml
# Sintaxis ${VAR} o $VAR
front: "Usuario: ${USER}"
back: "Ruta: $HOME"
```

**Resultado:** `front: "Usuario: lauren"` (cuando $USER=lauren)

### 3. Templates Jinja2

Plantillas dinámicas con sintaxis Jinja2.

```yaml
front: "Bienvenido {{ name }}"
back: "Tu puntuación: {{ score }}"
```

**Uso avanzado con contexto:**
```python
from anki_yaml_tool.core import yaml_advanced

result = yaml_advanced.load_yaml_advanced(
    "deck.yaml",
    jinja_context={"name": "Juan", "score": 100}
)
```

**Nota:** Las plantillas Anki como `{{Front}}` (sin espacios) se tratan como texto literal y no se procesan como Jinja2.

### 4. Contenido Condicional

Filtrado de notas basado en flags y tags.

```yaml
# Deshabilitar una nota
- front: "Nota deshabilitada"
  back: "No aparecerá"
  _enabled: false

# Incluir solo si tiene tags específicos
- front: "Solo desarrollo"
  back: "Contenido"
  _tags: [dev, test]
```

**Filtrado por tags:**
```python
# Incluir solo notas con tag 'dev'
result = yaml_advanced.load_yaml_advanced(
    "deck.yaml",
    include_tags=["dev"]
)
```

### 5. YAML Anchors (& y *)

Reutilización de contenido con aliases.

```yaml
# Definición del anchor
respuesta: &respuesta "Texto reutilizable"

# Uso del alias
- back: *respuesta
- back: *respuesta
```

**Nota:** Los anchors deben definirse antes de su uso en el archivo YAML.

## Archivo de Ejemplo: deck.yaml

El archivo `deck.yaml` demuestra todas las características en un solo archivo:

1. **Includes**: Carga configuración y datos de archivos externos
2. **Variables de entorno**: Muestra usuario y ruta del sistema
3. **Jinja2**: Procesa plantillas con variables
4. **Conditional**: Filtra notas deshabilitadas
5. **Anchors**: Reutiliza respuestas entre notas

## Uso desde Python

```python
from anki_yaml_tool.core import config

# Cargar deck con todas las características avanzadas
model_config, data, deck_name, media_folder = config.load_deck_file("deck.yaml")

# Con tags específicos para contenido condicional
model_config, data, deck_name, media_folder = config.load_deck_file(
    "deck.yaml",
    include_tags=["dev", "prod"]
)

# Con contexto Jinja2
model_config, data, deck_name, media_folder = config.load_deck_file(
    "deck.yaml",
    jinja_context={"title": "Mi Título", "value": 42}
)
```

## Uso desde CLI

```bash
# Construir el deck
anki-yaml-tool build examples/advanced/deck.yaml
```
