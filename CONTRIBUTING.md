# 🤝 Contributing

¡Gracias por tu interés en contribuir a Artisan Web!

## 📋 Pasos para Contribuir

### 1. Fork y Clone
```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/tu_usuario/artisan-web.git
cd artisan-web
```

### 2. Crear Rama de Desarrollo
```bash
git checkout -b feature/tu-feature-nombre
```

### 3. Instalar Dependencias
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Hacer Cambios
- Sigue el estilo de código existente
- Comenta tu código
- Asegúrate de que los cambios funcionen localmente

### 5. Testear
```bash
python app.py
# Visita http://127.0.0.1:5000
# Prueba todas las funcionalidades afectadas
```

> `e2e_test.py` está desactualizado (GET en rutas POST y sin CSRF); no lo tomes como referencia hasta reescribirlo.

### 6. Commit y Push
```bash
git add .
git commit -m "feat: descripción clara de los cambios"
git push origin feature/tu-feature-nombre
```

### 7. Pull Request
- Ve a GitHub y crea un Pull Request
- Describe claramente qué cambios hiciste
- Espera revisión

## 📝 Convenciones de Commit

```
feat: Nueva funcionalidad
fix: Corrección de bug
docs: Cambios en documentación
style: Cambios de formato (sin cambio lógico)
refactor: Refactorización de código
perf: Mejora de performance
test: Agregar o mejorar tests
chore: Cambios en build o dependencias
```

## 🧪 Testing

Antes de hacer PR:
- [ ] Login/Registro funciona
- [ ] Agregar productos funciona
- [ ] Carrito funciona
- [ ] Checkout funciona
- [ ] Panel admin funciona
- [ ] No hay errores en consola

## 🔐 Seguridad

**NUNCA** commits:
- Archivos `.env`
- Tokens o API keys
- Contraseñas
- Información sensible

## 📚 Documentación

Si agregas una nueva funcionalidad:
- Actualiza [README.md](README.md) y la documentación de [docs/](docs/README.md)
- Documenta en código
- Explica en el PR

> Esta versión no carga `.env` automáticamente: exporta las variables o usa `dotenv run` (ver [Instalación](docs/02-instalacion.md#3-variables-de-entorno)).

## 📞 Contacta

Preguntas o sugerencias:
- Abre una Issue
- Contacta al equipo de desarrollo

---

¡Agradecemos tu contribución! 🙏
