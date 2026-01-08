"""
ECO-MOVE API - Business Logic Services
"""
from datetime import date
from decimal import Decimal
from typing import Tuple
from sqlalchemy.orm import Session
from app.models import Cliente, Vehiculo, Alquiler


# Constantes de negocio
DESCUENTO_USO_EXTENDIDO_PORCENTAJE = Decimal("0.15")  # 15%
DESCUENTO_CLIENTE_FRECUENTE_PORCENTAJE = Decimal("0.10")  # 10%
DEPOSITO_PORCENTAJE = Decimal("0.12")  # 12%
MULTA_RETRASO_PORCENTAJE = Decimal("0.10")  # 10% por día
DIAS_MINIMOS_USO_EXTENDIDO = 5
EDAD_MAYOR = 18


def calcular_edad(fecha_nacimiento: date) -> int:
    """Calcula la edad actual de una persona"""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    
    # Ajustar si aún no ha cumplido años este año
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return edad


def validar_edad_cliente(cliente: Cliente, vehiculo: Vehiculo) -> Tuple[bool, str]:
    """
    Valida si el cliente puede alquilar el vehículo según su edad
    Returns: (es_valido, mensaje)
    """
    if not vehiculo.requiere_mayor_edad:
        return True, "OK"
    
    edad = calcular_edad(cliente.fecha_nacimiento)
    
    if edad < EDAD_MAYOR:
        return False, f"El cliente debe ser mayor de {EDAD_MAYOR} años para alquilar {vehiculo.nombre}"
    
    return True, "OK"


def calcular_alquiler(
    vehiculo: Vehiculo,
    cliente: Cliente,
    fecha_inicio: date,
    fecha_tentativa_devolucion: date
) -> dict:
    """
    Calcula todos los valores del alquiler según las reglas de negocio:
    - DÍAS: fecha_tentativa - fecha_inicio
    - IMPORTE: días × tarifa_diaria
    - DESCUENTO USO EXTENDIDO: 15% si días > 5
    - DESCUENTO CLIENTE FRECUENTE: 10% adicional si es frecuente
    - DEPÓSITO: 12% del importe
    - TOTAL: importe - descuentos + depósito
    """
    # Calcular días
    dias = (fecha_tentativa_devolucion - fecha_inicio).days
    if dias < 1:
        dias = 1
    
    # Calcular importe base
    tarifa = Decimal(str(vehiculo.tarifa_diaria))
    importe = tarifa * dias
    
    # Descuento por uso extendido (> 5 días = 15%)
    descuento_uso_extendido = Decimal("0")
    if dias > DIAS_MINIMOS_USO_EXTENDIDO:
        descuento_uso_extendido = importe * DESCUENTO_USO_EXTENDIDO_PORCENTAJE
    
    # Descuento cliente frecuente (10% adicional)
    descuento_cliente_frecuente = Decimal("0")
    if cliente.es_frecuente:
        # Se aplica sobre el importe después del primer descuento
        importe_con_descuento = importe - descuento_uso_extendido
        descuento_cliente_frecuente = importe_con_descuento * DESCUENTO_CLIENTE_FRECUENTE_PORCENTAJE
    
    # Depósito (12% del importe)
    deposito = importe * DEPOSITO_PORCENTAJE
    
    # Total a pagar
    total_pagar = importe - descuento_uso_extendido - descuento_cliente_frecuente + deposito
    
    return {
        "dias": dias,
        "importe": round(importe, 2),
        "descuento_uso_extendido": round(descuento_uso_extendido, 2),
        "descuento_cliente_frecuente": round(descuento_cliente_frecuente, 2),
        "deposito": round(deposito, 2),
        "total_pagar": round(total_pagar, 2),
    }


def calcular_devolucion(alquiler: Alquiler, fecha_devolucion_real: date) -> dict:
    """
    Calcula los valores de la devolución según las reglas de negocio:
    - DÍAS MORA: Si fecha_devolucion_real > fecha_tentativa
    - MULTA: 10% del importe diario por cada día extra
    - DEPÓSITO DEVUELTO: Se reduce en caso de multas
    - MONTO ADICIONAL: Si multa > depósito, el cliente paga la diferencia
    """
    # Calcular días de mora
    dias_mora = 0
    fecha_tentativa = alquiler.fecha_tentativa_devolucion
    
    if fecha_devolucion_real > fecha_tentativa:
        dias_mora = (fecha_devolucion_real - fecha_tentativa).days
    
    # Calcular multa por retraso (10% del importe diario por cada día extra)
    multa = Decimal("0")
    deposito = Decimal(str(alquiler.deposito))
    importe = Decimal(str(alquiler.importe))
    
    if dias_mora > 0:
        importe_diario = importe / alquiler.dias
        multa = importe_diario * MULTA_RETRASO_PORCENTAJE * dias_mora
    
    # Calcular depósito devuelto y monto adicional
    deposito_devuelto = Decimal("0")
    monto_adicional = Decimal("0")
    
    if multa >= deposito:
        # La multa se cubre con el depósito y se cobra lo adicional
        deposito_devuelto = Decimal("0")
        monto_adicional = multa - deposito
    else:
        # Se devuelve el depósito menos la multa
        deposito_devuelto = deposito - multa
    
    # Total final (lo que el cliente tiene pendiente)
    # Si hay monto adicional, es lo que debe pagar
    # Si no, ya no debe nada (el depósito cubre todo)
    total_pagar_original = Decimal(str(alquiler.total_pagar))
    total_final = total_pagar_original + monto_adicional - deposito_devuelto
    
    return {
        "dias_mora": dias_mora,
        "multa": round(multa, 2),
        "deposito_devuelto": round(deposito_devuelto, 2),
        "monto_adicional": round(monto_adicional, 2),
        "total_final": round(total_final, 2),
    }
