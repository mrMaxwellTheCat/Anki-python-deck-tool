# Plan de Acción: Fix Silent Media Errors

## Información General

| Campo          | Detalle                     |
|----------------|-----------------------------|
| **Tarea**      | Fix: Silent Media Errors    |
| **Prioridad**  | CRÍTICA                     |
| **Ubicación**  | `src/anki_yaml_tool/cli.py` |
| **Líneas**     | 910-911, 1013-1014          |
| **Estimación** | 2-3 horas (3 story points)  |

---

## 1. Objetivo Concreto

**Descripción:** Reemplazar los bloques `except Exception: pass` que silenciosamente ignoran errores al procesar archivos multimedia con logging adecuado y mensajes de error claros para el usuario.

### Criterios de Aceptación Medibles

- [ ] ✅ Todo error de procesamiento de medios debe ser logged con nivel WARNING o ERROR
- [ ] ✅ El usuario debe recibir un mensaje claro indicando qué archivos fallaron y por qué
- [ ] ✅ El proceso debe continuar procesando otros archivos (no fallar todo el batch)
- [ ] ✅ Los tests unitarios deben cubrir los nuevos casos de error
- [ ] ✅ El código pasa linting (ruff) y type checking (mypy)

---

## 2. Archivos a Modificar

### Archivo Principal
- **`src/anki_yaml_tool/cli.py`**
  - Línea 910-911: `_batch_build_merged()` - push de deck mergeado
  - Línea 1013-1014: `_batch_build_separate()` - push de decks separados

### Archivos de Tests
- **`tests/test_cli_batch.py`** - Añadir tests para manejo de errores de media

---

## 3. Dependencias y Tareas Previas

### Dependencias Resueltas ✅
- Sistema de logging ya configurado en `logging_config.py`
- Módulo `logging` importado en cli.py
- Convenciones de errores existentes en el proyecto

### Dependencias Externas
- Ninguna (solo stdlib y dependencias existentes)

---

## 4. Pasos de Implementación

### Paso 1: Analizar el Código Existente (15 min)
```
- Revisar las 4 ubicaciones donde se procesa media:
  1. cli.py:910-911 (_batch_build_merged)
  2. cli.py:1013-1014 (_batch_build_separate)
- Identificar tipos de errores posibles:
  - KeyError (media no existe en zip)
  - Exception genérica (fallo en storeMediaFile)
```

### Paso 2: Implementar Logging en _batch_build_merged (30 min)
```python
# Antes (cli.py:910-911):
except Exception:
    pass  # Skip media errors

# Después:
except KeyError as e:
    log.warning("Media file %s not found in apkg: %s", idx, e)
    click.echo(f"Warning: Media file {idx} not found in package", err=True)
except Exception as e:
    log.warning("Failed to store media %s: %s", filename, e)
    click.echo(f"Warning: Failed to store media file: {filename}", err=True)
```

### Paso 3: Implementar Logging en _batch_build_separate (30 min)
```python
# Mismo patrón que Paso 2, aplicar en cli.py:1013-1014
```

### Paso 4: Añadir Contador de Errores (15 min)
- Crear variable para trackear errores de media
- Mostrar resumen al final: "X media files failed to upload"

### Paso 5: Escribir Tests Unitarios (45 min)
```python
def test_push_media_error_handling():
    """Test that media errors are logged and reported."""
    # Mock connector to raise exception
    # Verify warning is logged
    # Verify user is notified
```

### Paso 6: Verificar Linting y Type Checking (15 min)
```bash
ruff check src/anki_yaml_tool/cli.py
mypy src/anki_yaml_tool/cli.py
```

---

## 5. Estrategia de Pruebas

### Tests Unitarios
- **Archivo:** `tests/test_cli_batch.py`
- **Casos de prueba:**
  1. Media file no encontrado en zip (KeyError)
  2. Fallo al invocar storeMediaFile (AnkiConnectError)
  3. Error genérico inesperado
  4. Verificar que el proceso continúa tras errores

### Tests de Integración (opcional)
- Test con archivo .apkg corrupto o malformado

### Cobertura Objetivo
- Añadir ~15-20 líneas de código cubrible
- Mantener cobertura existente (~97%)

---

## 6. Estimación de Esfuerzo

| Actividad                            | Tiempo         |
|--------------------------------------|----------------|
| Análisis y diseño                    | 15 min         |
| Implementación _batch_build_merged   | 30 min         |
| Implementación _batch_build_separate | 30 min         |
| Contador de errores                  | 15 min         |
| Tests unitarios                      | 45 min         |
| Linting/Type check                   | 15 min         |
| **TOTAL**                            | **~2.5 horas** |

**Story Points:** 3

---

## 7. Notes Adicionales

### Consideraciones de UX
- Mostrar errores al usuario pero NO detener el proceso
- Resumen al final indica éxito/parcial/fallo
- En modo verbose, mostrar más detalles

### Consideraciones de Rendimiento
- Mínimo impacto (solo logging adicional)
- No afecta flujo principal de datos

### Consideraciones de Seguridad
- No exponer información sensible en logs
- Sanitizar nombres de archivos en mensajes de error
