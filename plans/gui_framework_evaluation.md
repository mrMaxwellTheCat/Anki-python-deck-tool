# Evaluación de Frameworks GUI para Anki-python-deck-tool

## 1. Contexto del Proyecto

**Proyecto**: Anki-python-deck-tool
**Propósito**: Herramienta CLI para crear mazos de Anki desde archivos YAML
**Stack actual**: Python 3.10+, Click, Pydantic, Jinja2, genanki
**Usuario objetivo**: Usuarios que crean tarjetas Anki desde archivos YAML

## 2. Requerimientos de GUI (según ROADMAP 5.2)

### Funcionalidades Fase 1
- [x] Selectores de archivos para config y data
- [x] Selector de ruta de salida
- [x] Input de nombre del mazo
- [x] Botón construir con barra de progreso
- [x] Notificaciones éxito/error

### Funcionalidades Avanzadas (Fase 2+)
- [ ] Editor visual de templates
- [ ] Preview de tarjetas
- [ ] Validación en tiempo real de YAML
- [ ] Panel de configuración avanzada

---

## 3. Comparación de Frameworks

| Criterio                    | PySide6/PyQt6 | Tkinter | Electron+Python | Streamlit/NiceGUI | Tauri+Python |
|-----------------------------|---------------|---------|-----------------|-------------------|--------------|
| **Soporte multiplataforma** | ★★★★★         | ★★★★★   | ★★★★☆           | ★★★★★             | ★★★★★        |
| **Facilidad desarrollo**    | ★★★★☆         | ★★★★★   | ★★★☆☆           | ★★★★★             | ★★★☆☆        |
| **Mantenimiento**           | ★★★★☆         | ★★★★★   | ★★☆☆☆           | ★★★★☆             | ★★★★☆        |
| **Tamaño paquete**          | ★★★☆☆         | ★★★★★   | ★★☆☆☆           | ★★★★☆             | ★★★★★        |
| **Distribución**            | ★★★☆☆         | ★★★★★   | ★★☆☆☆           | ★★★★☆             | ★★★★★        |
| **UX nativa**               | ★★★★★         | ★★☆☆☆   | ★★★☆☆           | ★★★☆☆             | ★★★★☆        |
| **Bindings Python**         | Nativo        | Nativo  | JSON-RPC        | Nativo            | Rust+Python  |
| **Curva aprendizaje**       | Media         | Baja    | Alta            | Baja              | Alta         |

---

## 4. Análisis Detallado por Framework

### 4.1 PySide6 / PyQt6

**Descripción**: bindings oficiales de Qt para Python (PySide6 = LGPL, PyQt6 = GPL/comercial)

**Pros**:
- UI nativa de escritorio con apariencia profesional
- Widgets ricos y personalizables (QFileDialog, QProgressBar, etc.)
- Excelente documentación y comunidad grande
- WYSIWYG designer (Qt Designer) disponible
- Soporte robusto para operaciones de archivo nativas
- Signals/slots para manejo de eventos
- Styled with Qt Style Sheets (QSS) similar a CSS

**Contras**:
- Tamaño de paquete grande (~50-100MB)
- Licencia GPL puede ser restrictiva (PyQt6)
- Requiere compilación para distribución
- Instalación de dependencias puede ser compleja
- Learning curve media-alta para Qt específico

**Integración con proyecto**:
- Compatible con código Python existente
- Necesita refactorización de CLI a funciones modulares
- genanki funciona sin problemas en el mismo proceso

**Evaluación para este proyecto**: ★★★★☆

---

### 4.2 Tkinter

**Descripción**: Biblioteca GUI estándar de Python (incluida con Python)

**Pros**:
- Sin dependencias externas
- Instalación instantánea
- Perfecto para herramientas simples
- Documentación extensa
- Fácil de distribuir
- tkinter.filedialog para selectores nativos

**Contras**:
- Apariencia anticuada y limitada
- Widgets básicos sin muchas opciones de styling
- Difícil crear UIs complejas/modernas
- No suitable para aplicaciones profesionales
- Gestión de eventos limitada
- Sin soporte nativo para barras de progreso atractivas

**Integración con proyecto**:
- Totalmente compatible
- Fácil迁移 desde CLI
- Limitado para funcionalidades avanzadas futuras

**Evaluación para este proyecto**: ★★☆☆☆

---

### 4.3 Electron + Python Backend

**Descripción**: Frontend web (HTML/CSS/JS) con backend Python (servidor local)

**Pros**:
- Flexibilidad de desarrollo web
- UI moderna con CSS/frameworks (React, Vue, etc.)
- Gran ecosistema de componentes
- Separación clara UI/backend

**Contras**:
- Arquitectura compleja (2 procesos)
- Tamaño de paquete muy grande
- Performance menor que nativo
- Mantenimiento complejo
- Comunicación inter-proceso (IPC) necesaria
- Distribución difícil (Electron bundle + Python)
- Overhead de servidor local innecesario

**Integración con proyecto**:
- Requiere crear servidor API REST/JSON-RPC
- Mucho boilerplate para funcionalidad simple
- Excesivo para las necesidades del proyecto

**Evaluación para este proyecto**: ★★☆☆☆

---

### 4.4 Streamlit / NiceGUI

**Descripción**: Frameworks web-based que crean UIs desde Python

**Streamlit**:
- Orientado a data science/ML
- Inputs simples y automáticos
- No customizable UI

**NiceGUI**:
- Más moderno y personalizable
- Basado en Vue.js
- Mejor para aplicaciones interactivas
- Soporte para elementos de escritorio

**Pros**:
- Desarrollo muy rápido desde Python
- UI responsiva y moderna
- Reutilización de código Python directo
- Buena documentación
- Live reload durante desarrollo
- Componentes interactivos自带

**Contras**:
- No es aplicación nativa de escritorio (abre en navegador)
- Estilo "web app" no "desktop app"
- Limited control sobre look & feel
- Puede parecer " menos profesional" para usuarios
- No hay acceso directo al filesystem (requiere Workbench)
- NiceGUI tiene comunidad más pequeña que Streamlit

**Integración con proyecto**:
- Integración directa con lógica Python existente
- Llamada directa a funciones de builder/exporter
- Perfecto para prototipado rápido

**Evaluación para este proyecto**: NiceGUI ★★★★☆ / Streamlit ★★★☆☆

---

### 4.5 Tauri + Python

**Descripción**: Framework moderno usando Rust para frontend y Python para backend

**Pros**:
- Aplicación nativa真正的 nativa
- Tamaño de paquete extremadamente pequeño (5-10MB)
- Excelente performance
- UI con tecnologías web modernas (HTML/CSS/JS o WASM)
- Seguridad mejorada (sandboxed)
- Distribución simple (single executable)
- Mejor que Electron en casi todos los aspectos

**Contras**:
- Requiere aprender Rust (aunque sea mínimo)
- Python bindings para Tauri aún en desarrollo activo
- Comunidad más pequeña que Qt
- Menos widgets готовos que Qt
- Complex setup inicial
-pyoo/tauri-python pueden tener limitaciones
- Integración con bibliotecas Python complejas puede ser tricky

**Integración con proyecto**:
- Posible pero complejo
- Necesita wrapper como `tauri-python` o `pyoo`
- Funcionalidades de CLI existentes deberían modularizarse
- Comunicación async entre frontend y backend

**Evaluación para este proyecto**: ★★★☆☆

---

## 5. Matriz de Decisión Ponderada

| Criterio       | Peso | PySide6 | Tkinter | Electron | NiceGUI | Tauri   |
|----------------|------|---------|---------|----------|---------|---------|
| Cross-platform | 25%  | 5       | 5       | 4        | 5       | 5       |
| Ease dev       | 25%  | 4       | 5       | 3        | 5       | 3       |
| Package size   | 20%  | 3       | 5       | 2        | 4       | 5       |
| UX quality     | 20%  | 5       | 2       | 3        | 3       | 4       |
| Maintenance    | 10%  | 4       | 5       | 2        | 4       | 4       |
| **Puntuación** | 100% | **4.3** | **4.4** | **2.8**  | **4.3** | **4.2** |

---

## 6. Recomendación

### Opción Principal: PySide6 (Qt for Python)

**Justificación**:
1. **UI profesional nativa**: Los usuarios de Anki están acostumbrados a aplicaciones de escritorio nativas
2. **Widgets ready-to-use**: QFileDialog, QProgressBar, QMessageBox vienen gratis
3. **Capacidad de expansión**: Fácil agregar editor visual, preview, etc. en fases futuras
4. **Comunidad activa**: Problemas tiene solución fácil
5. **Qt Designer**: Permite prototipado visual rápido

**Concerns a resolver**:
- Tamaño de paquete: Aceptable para aplicación de escritorio
- GPL: Usar PySide6 (LGPL) o GPL con exención

### Alternativa: NiceGUI

**Cuándo considerarlo**:
- Prioridad en velocidad de desarrollo
- UI web-acceptable para usuarios
- Equipo con experiencia web

---

## 7. Próximos Pasos (Si se selecciona PySide6)

1. Crear módulo `gui/` con estructura base
2. Definir clase principal `AnkiDeckToolGUI`
3. Implementar ventana principal con Qt Designer o código
4. Conectar con módulos existentes de `builder.py`, `exporter.py`
5. Agregar sistema de logging/feedback
6. Testing de integración GUI
7. Configurar PyInstaller para distribución

---

*Documento generado para evaluación de ROADMAP.md sección 5.1*
*Fecha: 2026-02-14*
