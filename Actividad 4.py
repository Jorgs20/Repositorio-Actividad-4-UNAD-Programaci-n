from abc import ABC, abstractmethod
from datetime import datetime
import logging
import time

# Configuración del sistema de logs

logging.basicConfig(
    filename='sistema_reservas.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    encoding='utf-8'
)

# Excepciones personalizadas ye ncadenamiento

class SistemaError(Exception):
    """Excepción base para todos los errores del sistema."""
    pass

class DatoInvalidoError(SistemaError):
    """Se lanza cuando un dato ingresado no cumple con el formato o reglas."""
    pass

class ParametroFaltanteError(SistemaError):
    """Se lanza cuando falta un parámetro obligatorio."""
    pass

class OperacionNoPermitidaError(SistemaError):
    """Se lanza cuando se intenta realizar una acción prohibida por el estado actual."""
    pass

class ReservaIncorrectaError(SistemaError):
    """Se lanza cuando hay un fallo lógico o de validación en la reserva."""
    pass

class ServicioNoDisponibleError(SistemaError):
    """Se lanza cuando el servicio seleccionado no está activo o disponible."""
    pass

class CalculoInconsistenteError(SistemaError):
    """Se lanza cuando ocurre un error matemático o incongruencia en montos."""
    pass

# Clases Abstractas t Entidades POO

class EntidadBase(ABC):
    """Clase abstracta que representa entidades generales del sistema."""
    def __init__(self, id_entidad: str):
        self._id_entidad = id_entidad
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @abstractmethod
    def validar(self) -> bool:
        """Método abstracto para validar la integridad de la entidad."""
        pass


class Cliente(EntidadBase):
    """Clase Cliente con validaciones robustas y encapsulación."""
    def __init__(self, id_entidad: str, nombre: str, email: str, telefono: str):
        super().__init__(id_entidad)
        self.nombre = nombre       # Usa propiedad con validación
        self.email = email         # Usa propiedad con validación
        self.telefono = telefono   # Usa propiedad con validación

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str):
        if not value or not isinstance(value, str) or len(value.strip()) < 3:
            raise DatoInvalidoError(f"Nombre de cliente inválido: '{value}'. Debe tener al menos 3 caracteres.")
        self._nombre = value.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        if not value or "@" not in value or "." not in value:
            raise DatoInvalidoError(f"Correo electrónico inválido: '{value}'.")
        self._email = value.strip()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, value: str):
        if not value or not value.isdigit() or len(value) < 7:
            raise DatoInvalidoError(f"Teléfono inválido: '{value}'. Debe contener solo dígitos (mín. 7).")
        self._telefono = value

    def validar(self) -> bool:
        if self._nombre and self._email and self._telefono:
            return True
        return False

    def __str__(self):
        return f"Cliente [ID: {self._id_entidad}, Nombre: {self._nombre}, Email: {self._email}]"


class Servicio(EntidadBase, ABC):
    """Clase abstracta Servicio que implementa polimorfismo."""
    def __init__(self, id_entidad: str, nombre_servicio: str, costo_base: float, disponible: bool = True):
        super().__init__(id_entidad)
        self.nombre_servicio = nombre_servicio
        self.costo_base = costo_base
        self.disponible = disponible

    @property
    def costo_base(self) -> float:
        return self._costo_base

    @costo_base.setter
    def costo_base(self, value: float):
        if value < 0:
            raise CalculoInconsistenteError("El costo base no puede ser negativo.")
        self._costo_base = float(value)

    @abstractmethod
    def calcular_costo(self, *args, **kwargs) -> float:
        """Método de polimorfismo para calcular costo."""
        pass

    @abstractmethod
    def describir(self) -> str:
        """Devuelve la descripción detallada del servicio."""
        pass

    @abstractmethod
    def validar_parametros(self, **kwargs):
        """Valida parámetros específicos del servicio."""
        pass

    def validar(self) -> bool:
        return self.disponible

# Polimorfismo

class ServicioAlojamiento(Servicio):
    def __init__(self, id_entidad: str, nombre_servicio: str, costo_base: float, categoria_hotel: int, disponible: bool = True):
        super().__init__(id_entidad, nombre_servicio, costo_base, disponible)
        self.categoria_hotel = categoria_hotel # 3 a 5 estrellas

    def validar_parametros(self, **kwargs):
        noches = kwargs.get('noches')
        if noches is None:
            raise ParametroFaltanteError("Falta el parámetro 'noches' para alojamiento.")
        if not isinstance(noches, int) or noches <= 0:
            raise DatoInvalidoError("El número de noches debe ser un entero mayor a cero.")

    # Sobrecarga simulada mediante argumentos opcionales como los impuestos o descuentos
    def calcular_costo(self, noches: int, incluye_impuestos: bool = True, descuento_porcentaje: float = 0.0) -> float:
        self.validar_parametros(noches=noches)
        if descuento_porcentaje < 0 or descuento_porcentaje > 100:
            raise CalculoInconsistenteError("El porcentaje de descuento debe estar entre 0 y 100.")
        
        subtotal = self.costo_base * noches
        if descuento_porcentaje > 0:
            subtotal -= subtotal * (descuento_porcentaje / 100)
        
        if incluye_impuestos:
            subtotal *= 1.19  # IVA 19%
            
        if subtotal < 0:
            raise CalculoInconsistenteError("Cálculo de costo resultó en un valor negativo.")
        return round(subtotal, 2)

    def describir(self) -> str:
        return f"Alojamiento Hotelero ({self.categoria_hotel} Estrellas) - {self.nombre_servicio}"


class ServicioTransporte(Servicio):
    def __init__(self, id_entidad: str, nombre_servicio: str, costo_base: float, tipo_vehiculo: str, disponible: bool = True):
        super().__init__(id_entidad, nombre_servicio, costo_base, disponible)
        self.tipo_vehiculo = tipo_vehiculo

    def validar_parametros(self, **kwargs):
        distancia_km = kwargs.get('distancia_km')
        if distancia_km is None:
            raise ParametroFaltanteError("Falta el parámetro 'distancia_km' para transporte.")
        if not isinstance(distancia_km, (int, float)) or distancia_km <= 0:
            raise DatoInvalidoError("La distancia en kilómetros debe ser mayor a cero.")

    def calcular_costo(self, distancia_km: float, tarifa_nocturna: bool = False) -> float:
        self.validar_parametros(distancia_km=distancia_km)
        costo = self.costo_base + (distancia_km * 2.5)
        if tarifa_nocturna:
            costo *= 1.25
        return round(costo, 2)

    def describir(self) -> str:
        return f"Transporte Terrestre ({self.tipo_vehiculo}) - {self.nombre_servicio}"


class ServicioTour(Servicio):
    def __init__(self, id_entidad: str, nombre_servicio: str, costo_base: float, guia_bilingue: bool, disponible: bool = True):
        super().__init__(id_entidad, nombre_servicio, costo_base, disponible)
        self.guia_bilingue = guia_bilingue

    def validar_parametros(self, **kwargs):
        personas = kwargs.get('personas')
        if personas is None:
            raise ParametroFaltanteError("Falta el parámetro 'personas' para el tour.")
        if not isinstance(personas, int) or personas <= 0:
            raise DatoInvalidoError("El número de personas debe ser un entero positivo.")

    def calcular_costo(self, personas: int, temporada_alta: bool = False) -> float:
        self.validar_parametros(personas=personas)
        costo = self.costo_base * personas
        if temporada_alta:
            costo *= 1.40
        if self.guia_bilingue:
            costo += 50.0 # Cargo fijo por guía bilingüe
        return round(costo, 2)

    def describir(self) -> str:
        return f"Tour Guiado ({'Bilingüe' if self.guia_bilingue else 'Estándar'}) - {self.nombre_servicio}"

# Clase Reserva con manejo avanzado
class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado con manejo de excepciones try/except/else/finally."""
    def __init__(self, id_entidad: str, cliente: Cliente, servicio: Servicio, detalles_calculo: dict):
        super().__init__(id_entidad)
        self.cliente = cliente
        self.servicio = servicio
        self.detalles_calculo = detalles_calculo
        self.estado = "Pendiente" # Pendiente, Confirmada, Cancelada o Fallida
        self.costo_total = 0.0

    def validar(self) -> bool:
        if not self.cliente or not self.cliente.validar():
            raise ReservaIncorrectaError("La reserva tiene asociado un cliente inválido o nulo.")
        if not self.servicio or not self.servicio.validar():
            raise ServicioNoDisponibleError(f"El servicio '{self.servicio.nombre_servicio}' no está disponible.")
        return True

    def procesar(self):
        """Procesa la reserva utilizando try/except/else/finally y encadenamiento de excepciones."""
        logging.info(f"Iniciando procesamiento de reserva ID: {self._id_entidad}")
        try:
            # Validaciones previas
            self.validar()

            # Cálculo polimorfismo del costo
            metodo = self.detalles_calculo.get('metodo_calculo', 'estandar')
            if isinstance(self.servicio, ServicioAlojamiento):
                self.costo_total = self.servicio.calcular_costo(
                    noches=self.detalles_calculo.get('noches', 1),
                    incluye_impuestos=self.detalles_calculo.get('impuestos', True),
                    descuento_porcentaje=self.detalles_calculo.get('descuento', 0.0)
                )
            elif isinstance(self.servicio, ServicioTransporte):
                self.costo_total = self.servicio.calcular_costo(
                    distancia_km=self.detalles_calculo.get('distancia_km', 10),
                    tarifa_nocturna=self.detalles_calculo.get('nocturna', False)
                )
            elif isinstance(self.servicio, ServicioTour):
                self.costo_total = self.servicio.calcular_costo(
                    personas=self.detalles_calculo.get('personas', 1),
                    temporada_alta=self.detalles_calculo.get('temporada_alta', False)
                )
            else:
                raise OperacionNoPermitidaError("Tipo de servicio desconocido para procesamiento.")

            self.estado = "Confirmada"
            logging.info(f"Reserva {self._id_entidad} procesada con éxito. Costo total: ${self.costo_total}")

        except SistemaError as se:
            self.estado = "Fallida"
            logging.error(f"Error de negocio en reserva {self._id_entidad}: {se}")
            # Encadenamiento de excepciones solicitado
            raise ReservaIncorrectaError(f"Fallo crítico al procesar la reserva {self._id_entidad}") from se

        except Exception as e:
            self.estado = "Fallida"
            logging.critical(f"Error inesperado en reserva {self._id_entidad}: {e}")
            raise SistemaError(f"Error sistémico desconocido en reserva {self._id_entidad}") from e

        else:
            # Se ejecuta solo si no hubo excepciones
            print(f"-> [ÉXITO] Reserva {self._id_entidad} confirmada para {self.cliente.nombre}. Total: ${self.costo_total}")

        finally:
            # Se ejecuta siempre (limpieza o registro final)
            logging.info(f"Finalizó ciclo de procesamiento para reserva {self._id_entidad}. Estado final: {self.estado}")

    def cancelar(self):
        if self.estado == "Cancelada":
            raise OperacionNoPermitidaError("La reserva ya se encuentra cancelada.")
        if self.estado == "Fallida":
            raise OperacionNoPermitidaError("No se puede cancelar una reserva que falló en su creación.")
        self.estado = "Cancelada"
        logging.info(f"Reserva {self._id_entidad} cancelada exitosamente.")
        print(f"-> [CANCELADA] La reserva {self._id_entidad} ha sido cancelada.")

# Simulación de operaciones
def ejecutar_simulacion():
    print(" INICIANDO SIMULACIÓN DE 10 OPERACIONES (SIN BD)")

    # Instanciamos servicios de prueba
    hotel = ServicioAlojamiento("SRV-01", "Hotel Gran Plaza", 150.0, 5, disponible=True)
    transporte = ServicioTransporte("SRV-02", "Taxi Ejecutivo", 10.0, "Sedán", disponible=True)
    tour = ServicioTour("SRV-03", "Tour Histórico Centro", 45.0, guia_bilingue=True, disponible=False) # No disponible a propósito

    operaciones = [
        # Op 1: Cliente y reserva válidos
        {"tipo": "reserva", "id": "RES-001", "cli": ("Carlos Pérez", "carlos@mail.com", "3001234567"), "srv": hotel, "detalles": {"noches": 3, "descuento": 10.0}},
        
        # Op 2: Cliente con email inválido
        {"tipo": "reserva", "id": "RES-002", "cli": ("Ana Gómez", "correo-malo-sin-arroba", "3109876543"), "srv": transporte, "detalles": {"distancia_km": 15}},
        
        # Op 3: Parámetro faltante en alojamiento
        {"tipo": "reserva", "id": "RES-003", "cli": ("Luis Torres", "luis@mail.com", "3201112233"), "srv": hotel, "detalles": {"descuento": 0.0}},
        
        # Op 4: Servicio no disponible
        {"tipo": "reserva", "id": "RES-004", "cli": ("Sofia Ruiz", "sofia@mail.com", "3154445566"), "srv": tour, "detalles": {"personas": 2}},
        
        # Op 5: Operación válida de Transporte Nocturno
        {"tipo": "reserva", "id": "RES-005", "cli": ("Mateo Diaz", "mateo@mail.com", "3112223344"), "srv": transporte, "detalles": {"distancia_km": 25, "nocturna": True}},
        
        # Op 6: Datos de teléfono inválidos en cliente
        {"tipo": "reserva", "id": "RES-006", "cli": ("Elena Gil", "elena@mail.com", "abc-telefono"), "srv": transporte, "detalles": {"distancia_km": 5}},
        
        # Op 7: Operación válida de Tour
        {"tipo": "reserva", "id": "RES-007", "cli": ("Roberto Sanchez", "roberto@mail.com", "3185556677"), "srv": tour, "detalles": {"activar_temporal": True, "personas": 4, "temporada_alta": True}},
        
        # Op 8: Cálculo inconsistente por valor negativo simulado en costo base
        {"tipo": "reserva", "id": "RES-008", "cli": ("Lucia Mendez", "lucia@mail.com", "3167778899"), "srv": hotel, "detalles": {"noches": -2}}, # Noches negativas
        
        # Op 9: Prueba de cancelación de reserva existente
        {"tipo": "cancelar", "id": "RES-001"},
        
        # Op 10: Intento de cancelar una reserva que no existe o falló
        {"tipo": "cancelar", "id": "RES-999"}
    ]

    for idx, op in enumerate(operaciones, start=1):
        print(f"\n--- Operación #{idx} [{op['tipo'].upper()}] ---")
        try:
            if op['tipo'] == 'reserva':
                # Parche temporal para simular disponibilidad en Op 7
                if op['id'] == 'RES-007':
                    op['srv'].disponible = True

                # Crear cliente 
                nombre, email, tel = op['cli']
                cliente = Cliente(f"CLI-00{idx}", nombre, email, tel)

                # Crear y procesar reserva
                reserva = Reserva(op['id'], cliente, op['srv'], op['detalles'])
                reserva.procesar()

            elif op['tipo'] == 'cancelar':
                # Buscamos simular una cancelación sobre un ID
                if op['id'] == 'RES-001':
                    # Como RES-001 fue creada en el paso 1, la cancelamos directamente
                    print(f"Cancelando reserva {op['id']} previamente creada...")
                    # Simulación de objeto reserva existente
                    cliente_dummy = Cliente("CLI-DUMMY", "Test", "test@mail.com", "3000000000")
                    res_temp = Reserva(op['id'], cliente_dummy, hotel, {"noches": 1})
                    res_temp.estado = "Confirmada"
                    res_temp.cancelar()
                else:
                    raise OperacionNoPermitidaError(f"La reserva con ID {op['id']} no fue encontrada en el sistema.")

        except SistemaError as e:
            print(f"-> [CONTROLADO] Error capturado correctamente: {e}")
        except Exception as e:
            print(f"-> [CRÍTICO] Error no controlado: {e}")
        
        time.sleep(0.2) # Pausa breve para legibilidad en consola

    
    print(" SIMULACIÓN FINALIZADA. VER ARCHIVO 'sistema_reservas.log'")

if __name__ == "__main__":
    ejecutar_simulacion()
