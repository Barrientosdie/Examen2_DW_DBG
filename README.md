# API Pollo Loco

API REST para administrar clientes, ventas de pollo y el costo del pollo.
Hecha con **Python, FastAPI y Pydantic**. No usa base de datos: los datos se
guardan en listas y variables, por lo que se pierden al reiniciar el servidor.

## Requisitos

- Python 3.9 o superior

## Cómo ejecutarla

1. Clona el repositorio y entra a la carpeta:
   ```
   git clone https://github.com/TU-USUARIO/NOMBRE-DEL-REPO.git
   cd NOMBRE-DEL-REPO
   ```
2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Arranca el servidor:
   ```
   python -m uvicorn main:app --reload
   ```
4. Abre Swagger en el navegador para probar todo: http://127.0.0.1:8000/docs

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/v1/api/clientes` | Lista los clientes |
| POST | `/v1/api/clientes` | Registra un cliente |
| PUT | `/v1/api/clientes/{id_cliente}` | Actualiza un cliente |
| DELETE | `/v1/api/clientes/{id_cliente}` | Desactiva un cliente (`active = false`) |
| POST | `/v1/api/ventas` | Registra una venta (solo clientes activos) |
| GET | `/v1/api/ventas` | Reporte de ventas; filtros opcionales `?fecha_inicio=` y `?fecha_fin=` |
| PUT | `/v1/api/ventas/{id_venta}` | Actualiza una venta |
| GET | `/v1/api/costo-pollo` | Consulta el costo actual del pollo |
| PUT | `/v1/api/costo-pollo` | Cambia el costo del pollo |

## Reglas principales

- Los clientes no se eliminan, solo se desactivan.
- No se pueden registrar ni actualizar ventas de clientes inactivos.
- `total_venta = cantidad_pollo × costo_pollo`. Cada venta guarda el costo
  vigente al momento de registrarse.
- Errores: `404` si no existe el cliente o la venta, `400` si el cliente está
  inactivo, `422` si los datos son inválidos.
