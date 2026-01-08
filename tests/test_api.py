"""
ECO-MOVE API - Script de Pruebas Completas
Testea todos los casos de uso según los requerimientos
"""
import requests
from datetime import date, timedelta
import json

BASE_URL = "http://127.0.0.1:8000"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {status} - {name}")
    if details and not passed:
        print(f"         {Colors.YELLOW}{details}{Colors.END}")

def print_section(name):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_subsection(name):
    print(f"\n{Colors.YELLOW}--- {name} ---{Colors.END}")


class APITester:
    def __init__(self):
        self.token = None
        self.admin_token = None
        self.created_cliente_id = None
        self.created_alquiler_id = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def test(self, name, condition, details=""):
        if condition:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        print_test(name, condition, details)
        return condition
    
    def get_headers(self, token=None):
        t = token or self.admin_token
        return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}
    
    # =========================================
    # TESTS DE AUTENTICACIÓN
    # =========================================
    def test_auth(self):
        print_section("1. AUTENTICACIÓN")
        
        # Test login admin existente
        print_subsection("Login Admin")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@ecomove.com",
            "password": "admin123"
        })
        self.test("Login admin exitoso", resp.status_code == 200)
        
        if resp.status_code == 200:
            data = resp.json()
            self.admin_token = data["access_token"]
            self.test("Token JWT recibido", "access_token" in data)
            self.test("Rol admin correcto", data["usuario"]["rol"] == "admin")
        
        # Test login incorrecto
        print_subsection("Login Incorrecto")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@ecomove.com",
            "password": "wrongpassword"
        })
        self.test("Login con contraseña incorrecta rechazado", resp.status_code == 401)
        
        # Test registro nuevo usuario
        print_subsection("Registro Nuevo Usuario")
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": "empleado@ecomove.com",
            "password": "empleado123",
            "nombre": "Juan",
            "apellido": "Pérez",
            "rol": "empleado"
        })
        # Puede fallar si ya existe
        if resp.status_code == 201:
            self.test("Registro empleado exitoso", True)
        else:
            self.test("Registro empleado (ya existe)", resp.status_code == 400)
        
        # Test /me
        print_subsection("Perfil Usuario")
        resp = requests.get(f"{BASE_URL}/auth/me", headers=self.get_headers())
        self.test("GET /auth/me funciona", resp.status_code == 200)
        if resp.status_code == 200:
            self.test("Nombre correcto", resp.json()["nombre"] == "Admin")
    
    # =========================================
    # TESTS DE VEHÍCULOS
    # =========================================
    def test_vehiculos(self):
        print_section("2. VEHÍCULOS (Requerimiento 01)")
        
        # Listar vehículos
        print_subsection("Catálogo de Vehículos")
        resp = requests.get(f"{BASE_URL}/vehiculos/", headers=self.get_headers())
        self.test("Listar vehículos", resp.status_code == 200)
        
        if resp.status_code == 200:
            vehiculos = resp.json()
            self.test("Hay 4 vehículos en catálogo", len(vehiculos) == 4)
            
            # Verificar datos según requerimientos
            codigos = {v["codigo"]: v for v in vehiculos}
            
            self.test("V01 - Scooter $25/día", 
                float(codigos.get("V01", {}).get("tarifa_diaria", 0)) == 25)
            self.test("V02 - Bicicleta $35/día", 
                float(codigos.get("V02", {}).get("tarifa_diaria", 0)) == 35)
            self.test("V03 - Monopatín $20/día", 
                float(codigos.get("V03", {}).get("tarifa_diaria", 0)) == 20)
            self.test("V04 - Moto $30/día", 
                float(codigos.get("V04", {}).get("tarifa_diaria", 0)) == 30)
            
            # Verificar restricción de edad
            self.test("V01 requiere mayor edad", 
                codigos.get("V01", {}).get("requiere_mayor_edad") == True)
            self.test("V02 cualquier edad", 
                codigos.get("V02", {}).get("requiere_mayor_edad") == False)
            self.test("V04 requiere mayor edad", 
                codigos.get("V04", {}).get("requiere_mayor_edad") == True)
        
        # Vehículos disponibles
        print_subsection("Vehículos Disponibles")
        resp = requests.get(f"{BASE_URL}/vehiculos/disponibles", headers=self.get_headers())
        self.test("Endpoint disponibles funciona", resp.status_code == 200)
        
        # Buscar por código
        print_subsection("Buscar por Código")
        resp = requests.get(f"{BASE_URL}/vehiculos/codigo/V01", headers=self.get_headers())
        self.test("Buscar V01 por código", resp.status_code == 200)
    
    # =========================================
    # TESTS DE CLIENTES
    # =========================================
    def test_clientes(self):
        print_section("3. CLIENTES (CRUD)")
        
        # Crear cliente frecuente (mayor de edad)
        print_subsection("Crear Cliente Frecuente (Mayor de edad)")
        cliente_frecuente = {
            "dni": "12345678A",
            "nombre": "María",
            "apellido": "García",
            "telefono": "555-1234",
            "email": "maria@test.com",
            "fecha_nacimiento": "1990-05-15",
            "es_frecuente": True,
            "direccion": "Calle Principal 123"
        }
        resp = requests.post(f"{BASE_URL}/clientes/", 
            json=cliente_frecuente, headers=self.get_headers())
        
        if resp.status_code == 201:
            self.test("Crear cliente frecuente", True)
            self.created_cliente_id = resp.json()["id"]
            self.cliente_frecuente_id = self.created_cliente_id
        else:
            self.test("Crear cliente frecuente (puede existir)", resp.status_code == 400)
            # Buscar por DNI
            resp = requests.get(f"{BASE_URL}/clientes/dni/12345678A", headers=self.get_headers())
            if resp.status_code == 200:
                self.created_cliente_id = resp.json()["id"]
                self.cliente_frecuente_id = self.created_cliente_id
        
        # Crear cliente NO frecuente
        print_subsection("Crear Cliente NO Frecuente")
        cliente_normal = {
            "dni": "87654321B",
            "nombre": "Pedro",
            "apellido": "López",
            "telefono": "555-5678",
            "email": "pedro@test.com",
            "fecha_nacimiento": "1985-08-20",
            "es_frecuente": False
        }
        resp = requests.post(f"{BASE_URL}/clientes/", 
            json=cliente_normal, headers=self.get_headers())
        if resp.status_code == 201:
            self.test("Crear cliente normal", True)
            self.cliente_normal_id = resp.json()["id"]
        else:
            self.test("Crear cliente normal (puede existir)", resp.status_code == 400)
            resp = requests.get(f"{BASE_URL}/clientes/dni/87654321B", headers=self.get_headers())
            if resp.status_code == 200:
                self.cliente_normal_id = resp.json()["id"]
        
        # Crear cliente menor de edad
        print_subsection("Crear Cliente Menor de Edad")
        cliente_menor = {
            "dni": "11111111C",
            "nombre": "Carlos",
            "apellido": "Joven",
            "telefono": "555-9999",
            "email": "carlos@test.com",
            "fecha_nacimiento": "2015-01-01",  # Menor de edad
            "es_frecuente": False
        }
        resp = requests.post(f"{BASE_URL}/clientes/", 
            json=cliente_menor, headers=self.get_headers())
        if resp.status_code == 201:
            self.test("Crear cliente menor", True)
            self.cliente_menor_id = resp.json()["id"]
        else:
            resp = requests.get(f"{BASE_URL}/clientes/dni/11111111C", headers=self.get_headers())
            if resp.status_code == 200:
                self.cliente_menor_id = resp.json()["id"]
                self.test("Cliente menor existe", True)
        
        # Listar clientes
        print_subsection("Listar Clientes")
        resp = requests.get(f"{BASE_URL}/clientes/", headers=self.get_headers())
        self.test("Listar clientes", resp.status_code == 200)
        
        # Filtrar frecuentes
        resp = requests.get(f"{BASE_URL}/clientes/?es_frecuente=true", headers=self.get_headers())
        self.test("Filtrar clientes frecuentes", resp.status_code == 200)
    
    # =========================================
    # TESTS DE ALQUILER (Requerimiento 02)
    # =========================================
    def test_alquileres(self):
        print_section("4. ALQUILERES (Requerimiento 02)")
        
        # Obtener vehículo disponible
        resp = requests.get(f"{BASE_URL}/vehiculos/codigo/V01", headers=self.get_headers())
        if resp.status_code == 200:
            vehiculo_v01 = resp.json()
        
        # ---- TEST CASO 1: Alquiler > 5 días + Cliente Frecuente ----
        print_subsection("Caso 1: 6 días + Cliente Frecuente (Ejemplo del documento)")
        
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=6)
        
        alquiler_data = {
            "cliente_id": self.cliente_frecuente_id,
            "vehiculo_id": 1,  # V01
            "fecha_inicio": str(fecha_inicio),
            "fecha_tentativa_devolucion": str(fecha_fin)
        }
        
        # Primero calcular preview
        resp = requests.post(f"{BASE_URL}/alquileres/calcular", 
            json=alquiler_data, headers=self.get_headers())
        
        if resp.status_code == 200:
            calc = resp.json()
            print(f"\n  Cálculo Preview:")
            print(f"    Días: {calc['dias']}")
            print(f"    Importe (6 x $25): ${calc['importe']}")
            print(f"    Descuento Uso Extendido (15%): ${calc['descuento_uso_extendido']}")
            print(f"    Descuento Cliente Frecuente (10%): ${calc['descuento_cliente_frecuente']}")
            print(f"    Depósito (12%): ${calc['deposito']}")
            print(f"    Total a Pagar: ${calc['total_pagar']}")
            
            self.test("Días calculados = 6", calc["dias"] == 6)
            self.test("Importe = $150 (6 x $25)", float(calc["importe"]) == 150.0)
            self.test("Descuento uso extendido aplicado (15%)", float(calc["descuento_uso_extendido"]) == 22.5)
            # El descuento frecuente se aplica sobre (150 - 22.5) = 127.5 * 0.10 = 12.75
            self.test("Descuento cliente frecuente aplicado (10%)", float(calc["descuento_cliente_frecuente"]) == 12.75)
            self.test("Depósito = 12% del importe", float(calc["deposito"]) == 18.0)
        
        # Crear el alquiler
        resp = requests.post(f"{BASE_URL}/alquileres/", 
            json=alquiler_data, headers=self.get_headers())
        
        if resp.status_code == 201:
            self.test("Alquiler creado exitosamente", True)
            self.alquiler_frecuente_id = resp.json()["id"]
        else:
            self.test("Crear alquiler", False, resp.json().get("detail", "Error"))
        
        # Verificar que vehículo cambió a 'alquilado'
        resp = requests.get(f"{BASE_URL}/vehiculos/1", headers=self.get_headers())
        if resp.status_code == 200:
            self.test("Vehículo V01 ahora está 'alquilado'", 
                resp.json()["estado"] == "alquilado")
        
        # ---- TEST CASO 2: Alquiler 1 día, cliente NO frecuente ----
        print_subsection("Caso 2: 1 día + Cliente NO Frecuente")
        
        alquiler_data2 = {
            "cliente_id": self.cliente_normal_id,
            "vehiculo_id": 3,  # V03 - Monopatín $20
            "fecha_inicio": str(fecha_inicio),
            "fecha_tentativa_devolucion": str(fecha_inicio + timedelta(days=1))
        }
        
        resp = requests.post(f"{BASE_URL}/alquileres/calcular", 
            json=alquiler_data2, headers=self.get_headers())
        
        if resp.status_code == 200:
            calc = resp.json()
            print(f"\n  Cálculo Preview:")
            print(f"    Días: {calc['dias']}")
            print(f"    Importe (1 x $20): ${calc['importe']}")
            print(f"    Descuento Uso Extendido: ${calc['descuento_uso_extendido']}")
            print(f"    Descuento Cliente Frecuente: ${calc['descuento_cliente_frecuente']}")
            print(f"    Depósito (12%): ${calc['deposito']}")
            print(f"    Total a Pagar: ${calc['total_pagar']}")
            
            self.test("Sin descuento uso extendido (≤5 días)", float(calc["descuento_uso_extendido"]) == 0)
            self.test("Sin descuento cliente frecuente", float(calc["descuento_cliente_frecuente"]) == 0)
        
        resp = requests.post(f"{BASE_URL}/alquileres/", 
            json=alquiler_data2, headers=self.get_headers())
        if resp.status_code == 201:
            self.test("Alquiler sin descuentos creado", True)
            self.alquiler_normal_id = resp.json()["id"]
        
        # ---- TEST: Restricción de edad ----
        print_subsection("Restricción de Edad")
        
        alquiler_menor = {
            "cliente_id": self.cliente_menor_id,
            "vehiculo_id": 1,  # V01 requiere mayor edad
            "fecha_inicio": str(fecha_inicio),
            "fecha_tentativa_devolucion": str(fecha_inicio + timedelta(days=2))
        }
        
        resp = requests.post(f"{BASE_URL}/alquileres/", 
            json=alquiler_menor, headers=self.get_headers())
        self.test("Menor no puede alquilar V01 (requiere mayor edad)", 
            resp.status_code == 400)
        
        # Pero SÍ puede alquilar V02 (cualquier edad)
        alquiler_menor_ok = {
            "cliente_id": self.cliente_menor_id,
            "vehiculo_id": 2,  # V02 - Bicicleta (cualquier edad)
            "fecha_inicio": str(fecha_inicio),
            "fecha_tentativa_devolucion": str(fecha_inicio + timedelta(days=2))
        }
        resp = requests.post(f"{BASE_URL}/alquileres/", 
            json=alquiler_menor_ok, headers=self.get_headers())
        if resp.status_code == 201:
            self.test("Menor SÍ puede alquilar V02 (cualquier edad)", True)
            self.alquiler_menor_id = resp.json()["id"]
        else:
            self.test("Menor puede alquilar bicicleta", False, resp.json().get("detail"))
        
        # ---- TEST: Vehículo ya alquilado ----
        print_subsection("Vehículo No Disponible")
        
        resp = requests.post(f"{BASE_URL}/alquileres/", 
            json=alquiler_data, headers=self.get_headers())  # V01 ya está alquilado
        self.test("No se puede alquilar vehículo ya alquilado", resp.status_code == 400)
    
    # =========================================
    # TESTS DE DEVOLUCIÓN (Requerimiento 03)
    # =========================================
    def test_devoluciones(self):
        print_section("5. DEVOLUCIONES (Requerimiento 03)")
        
        # ---- CASO 1: Devolución a tiempo (sin multa) ----
        print_subsection("Caso 1: Devolución a Tiempo (sin multa)")
        
        if hasattr(self, 'alquiler_normal_id'):
            # Obtener datos del alquiler
            resp = requests.get(f"{BASE_URL}/alquileres/{self.alquiler_normal_id}", 
                headers=self.get_headers())
            if resp.status_code == 200:
                alquiler = resp.json()
                
                devolucion_data = {
                    "alquiler_id": self.alquiler_normal_id,
                    "fecha_devolucion_real": alquiler["fecha_tentativa_devolucion"],
                    "observaciones": "Devolución a tiempo"
                }
                
                # Calcular preview
                resp = requests.post(f"{BASE_URL}/devoluciones/calcular", 
                    json=devolucion_data, headers=self.get_headers())
                
                if resp.status_code == 200:
                    calc = resp.json()
                    print(f"\n  Cálculo Devolución:")
                    print(f"    Días mora: {calc['dias_mora']}")
                    print(f"    Multa: ${calc['multa']}")
                    print(f"    Depósito devuelto: ${calc['deposito_devuelto']}")
                    
                    self.test("Sin días de mora", calc["dias_mora"] == 0)
                    self.test("Sin multa", float(calc["multa"]) == 0)
                    self.test("Depósito devuelto completo", float(calc["deposito_devuelto"]) > 0)
                
                # Crear devolución
                resp = requests.post(f"{BASE_URL}/devoluciones/", 
                    json=devolucion_data, headers=self.get_headers())
                self.test("Devolución a tiempo registrada", resp.status_code == 201)
        
        # ---- CASO 2: Devolución con retraso (con multa) ----
        print_subsection("Caso 2: Devolución con 2 días de Retraso")
        
        if hasattr(self, 'alquiler_frecuente_id'):
            resp = requests.get(f"{BASE_URL}/alquileres/{self.alquiler_frecuente_id}", 
                headers=self.get_headers())
            
            if resp.status_code == 200:
                alquiler = resp.json()
                fecha_tentativa = date.fromisoformat(alquiler["fecha_tentativa_devolucion"])
                fecha_real = fecha_tentativa + timedelta(days=2)  # 2 días tarde
                
                devolucion_data = {
                    "alquiler_id": self.alquiler_frecuente_id,
                    "fecha_devolucion_real": str(fecha_real),
                    "observaciones": "Devolución con 2 días de retraso"
                }
                
                # Calcular preview
                resp = requests.post(f"{BASE_URL}/devoluciones/calcular", 
                    json=devolucion_data, headers=self.get_headers())
                
                if resp.status_code == 200:
                    calc = resp.json()
                    print(f"\n  Cálculo Devolución con Retraso:")
                    print(f"    Días mora: {calc['dias_mora']}")
                    print(f"    Multa (10% diario x días): ${calc['multa']}")
                    print(f"    Depósito devuelto: ${calc['deposito_devuelto']}")
                    print(f"    Monto adicional: ${calc['monto_adicional']}")
                    print(f"    Total final: ${calc['total_final']}")
                    
                    self.test("2 días de mora", calc["dias_mora"] == 2)
                    self.test("Multa calculada (10% x 2 días)", float(calc["multa"]) > 0)
                
                # Crear devolución
                resp = requests.post(f"{BASE_URL}/devoluciones/", 
                    json=devolucion_data, headers=self.get_headers())
                self.test("Devolución con multa registrada", resp.status_code == 201)
                
                # Verificar vehículo liberado
                resp = requests.get(f"{BASE_URL}/vehiculos/1", headers=self.get_headers())
                if resp.status_code == 200:
                    self.test("Vehículo V01 liberado (disponible)", 
                        resp.json()["estado"] == "disponible")
    
    # =========================================
    # TESTS DE REPORTES
    # =========================================
    def test_reportes(self):
        print_section("6. REPORTES (Consultas Requeridas)")
        
        # Reporte 1: Clientes con múltiples alquileres
        print_subsection("Reporte 1: Clientes con más de un alquiler")
        resp = requests.get(f"{BASE_URL}/reportes/clientes-multiples-alquileres", 
            headers=self.get_headers())
        self.test("Endpoint funciona", resp.status_code == 200)
        if resp.status_code == 200:
            print(f"    Resultado: {resp.json()}")
        
        # Reporte 2: Vehículos más alquilados
        print_subsection("Reporte 2: Vehículos más alquilados")
        resp = requests.get(f"{BASE_URL}/reportes/vehiculos-mas-alquilados", 
            headers=self.get_headers())
        self.test("Endpoint funciona", resp.status_code == 200)
        if resp.status_code == 200:
            vehiculos = resp.json()
            print(f"    Vehículos alquilados: {len([v for v in vehiculos if v['total_alquileres'] > 0])}")
        
        # Reporte 3: Alquileres con doble descuento
        print_subsection("Reporte 3: Alquileres con descuento extendido + frecuente")
        resp = requests.get(f"{BASE_URL}/reportes/alquileres-doble-descuento", 
            headers=self.get_headers())
        self.test("Endpoint funciona", resp.status_code == 200)
        if resp.status_code == 200:
            print(f"    Alquileres con doble descuento: {len(resp.json())}")
        
        # Reporte 4: Total recaudado
        print_subsection("Reporte 4: Total recaudado por ECO-MOVE")
        resp = requests.get(f"{BASE_URL}/reportes/total-recaudado", 
            headers=self.get_headers())
        self.test("Endpoint funciona", resp.status_code == 200)
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Total alquileres: ${data.get('total_alquileres', 0)}")
            print(f"    Total depósitos: ${data.get('total_depositos', 0)}")
            print(f"    Total multas: ${data.get('total_multas', 0)}")
            print(f"    TOTAL RECAUDADO: ${data.get('total_recaudado', 0)}")
        
        # Reporte 5: Clientes con multa > depósito
        print_subsection("Reporte 5: Clientes con multa mayor al depósito")
        resp = requests.get(f"{BASE_URL}/reportes/clientes-multa-mayor-deposito", 
            headers=self.get_headers())
        self.test("Endpoint funciona", resp.status_code == 200)
        if resp.status_code == 200:
            print(f"    Clientes con multa > depósito: {len(resp.json())}")
    
    # =========================================
    # EJECUTAR TODOS LOS TESTS
    # =========================================
    def run_all(self):
        print(f"\n{Colors.BOLD}{'#'*60}{Colors.END}")
        print(f"{Colors.BOLD}   ECO-MOVE API - SUITE DE PRUEBAS COMPLETA{Colors.END}")
        print(f"{Colors.BOLD}{'#'*60}{Colors.END}")
        
        try:
            self.test_auth()
            self.test_vehiculos()
            self.test_clientes()
            self.test_alquileres()
            self.test_devoluciones()
            self.test_reportes()
        except Exception as e:
            print(f"\n{Colors.RED}Error durante las pruebas: {e}{Colors.END}")
        
        # Resumen
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}RESUMEN DE PRUEBAS{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}")
        total = self.tests_passed + self.tests_failed
        print(f"  Total: {total} pruebas")
        print(f"  {Colors.GREEN}Pasadas: {self.tests_passed}{Colors.END}")
        print(f"  {Colors.RED}Fallidas: {self.tests_failed}{Colors.END}")
        
        if self.tests_failed == 0:
            print(f"\n  {Colors.GREEN}{Colors.BOLD}✓ TODOS LOS TESTS PASARON{Colors.END}")
        else:
            print(f"\n  {Colors.YELLOW}⚠ Hay {self.tests_failed} tests que requieren atención{Colors.END}")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all()
