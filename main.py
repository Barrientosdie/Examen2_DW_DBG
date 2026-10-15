from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="API Pollo Loco",
    version="1.0.0",
    description="Administra clientes, ventas y costo de pollo.",
)


class ClienteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre_cliente: str = Field(..., min_length=1, max_length=100, examples=["Pedro Picapiedra"])
    direccion: str = Field(..., min_length=1, max_length=200, examples=["Av. Diego Diaz, San Nicolás"])


class Cliente(ClienteIn):
    id_cliente: int  
    active: bool = True  


class VentaIn(BaseModel):
    id_cliente: int = Field(..., examples=[1])
    cantidad_pollo: float = Field(..., ge=0, examples=[10.5])
    fecha_registro: Optional[datetime] = Field(None, examples=[None])


class VentaUpdate(BaseModel):
    cantidad_pollo: float = Field(..., ge=0, examples=[12])
    fecha_registro: Optional[datetime] = Field(None, examples=[None])


class Venta(BaseModel):
    id_venta: int
    id_cliente: int
    cantidad_pollo: float
    fecha_registro: datetime
    costo_pollo: float


class CostoIn(BaseModel):
    costo_pollo: float = Field(..., ge=0, examples=[400.00])


clientes: list[Cliente] = []
ventas: list[Venta] = []
costo_pollo: float = 350.00  

siguiente_id_cliente: int = 1
siguiente_id_venta: int = 1


def buscar_cliente(id_cliente: int) -> Optional[Cliente]:
    for cliente in clientes:
        if cliente.id_cliente == id_cliente:
            return cliente
    return None


def buscar_venta(id_venta: int) -> Optional[Venta]:
    for venta in ventas:
        if venta.id_venta == id_venta:
            return venta
    return None


def cliente_o_404(id_cliente: int) -> Cliente:
    cliente = buscar_cliente(id_cliente)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"El cliente {id_cliente} no existe")
    return cliente


def venta_o_404(id_venta: int) -> Venta:
    venta = buscar_venta(id_venta)
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"La venta {id_venta} no existe")
    return venta


def armar_reporte(venta: Venta, cliente: Cliente) -> dict:
    return {
        "id_venta": venta.id_venta,
        "id_cliente": cliente.id_cliente,
        "nombre_cliente": cliente.nombre_cliente,
        "direccion": cliente.direccion,
        "cantidad_pollo": venta.cantidad_pollo,
        "fecha_registro": venta.fecha_registro,
        "costo_pollo": venta.costo_pollo,
        "total_venta": round(venta.cantidad_pollo * venta.costo_pollo, 2),
    }


@app.get("/v1/api/clientes")
def consultar_clientes():
    return {"success": True, "total": len(clientes), "clientes": clientes}


@app.post("/v1/api/clientes", status_code=status.HTTP_201_CREATED)
def registrar_cliente(datos: ClienteIn):
    global siguiente_id_cliente

    nuevo = Cliente(id_cliente=siguiente_id_cliente, **datos.model_dump())
    siguiente_id_cliente += 1
    clientes.append(nuevo)
    return {"success": True, "cliente": nuevo}


@app.put("/v1/api/clientes/{id_cliente}")
def actualizar_cliente(id_cliente: int, datos: ClienteIn):
    cliente = cliente_o_404(id_cliente)  
    cliente.nombre_cliente = datos.nombre_cliente
    cliente.direccion = datos.direccion
    return {"success": True, "cliente": cliente}


@app.delete("/v1/api/clientes/{id_cliente}")
def desactivar_cliente(id_cliente: int):
    cliente = cliente_o_404(id_cliente) 
    cliente.active = False
    return {"success": True, "mensaje": f"Cliente {id_cliente} desactivado correctamente", "cliente": cliente}


@app.post("/v1/api/ventas", status_code=status.HTTP_201_CREATED)
def registrar_venta(datos: VentaIn):
    global siguiente_id_venta

    cliente = cliente_o_404(datos.id_cliente) 

    if not cliente.active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"No se puede registrar la venta: el cliente {cliente.id_cliente} está inactivo",
        )

    nueva = Venta(
        id_venta=siguiente_id_venta,
        id_cliente=cliente.id_cliente,
        cantidad_pollo=datos.cantidad_pollo,
        fecha_registro=datos.fecha_registro or datetime.now(),
        costo_pollo=costo_pollo,
    )
    siguiente_id_venta += 1
    ventas.append(nueva)
    return {"success": True, "venta": armar_reporte(nueva, cliente)}


@app.get("/v1/api/ventas")
def consultar_ventas(
    fecha_inicio: Optional[date] = Query(None, description="Solo ventas desde este día (AAAA-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Solo ventas hasta este día (AAAA-MM-DD)"),
):
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "fecha_inicio no puede ser mayor que fecha_fin")

    reporte = []
    for venta in ventas:
        cliente = buscar_cliente(venta.id_cliente)

        if cliente is None or not cliente.active:
            continue

        dia = venta.fecha_registro.date()
        if fecha_inicio and dia < fecha_inicio:
            continue
        if fecha_fin and dia > fecha_fin:
            continue

        reporte.append(armar_reporte(venta, cliente))

    total_vendido = round(sum(item["total_venta"] for item in reporte), 2)
    return {
        "success": True,
        "total_ventas": len(reporte),
        "total_vendido": total_vendido,
        "ventas": reporte,
    }


@app.put("/v1/api/ventas/{id_venta}")
def actualizar_venta(id_venta: int, datos: VentaUpdate):
    venta = venta_o_404(id_venta)  
    cliente = cliente_o_404(venta.id_cliente)

    if not cliente.active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"No se puede actualizar la venta: el cliente {cliente.id_cliente} está inactivo",
        )

    venta.cantidad_pollo = datos.cantidad_pollo
    if datos.fecha_registro is not None: 
        venta.fecha_registro = datos.fecha_registro
    return {"success": True, "venta": armar_reporte(venta, cliente)}


@app.get("/v1/api/costo-pollo")
def consultar_costo():
    return {"success": True, "costo_pollo": costo_pollo}


@app.put("/v1/api/costo-pollo")
def actualizar_costo(datos: CostoIn):
    global costo_pollo 
    costo_pollo = datos.costo_pollo
    return {"success": True, "mensaje": "Costo actualizado correctamente", "costo_pollo": costo_pollo}
