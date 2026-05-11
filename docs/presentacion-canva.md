# Presentacion WARDEN - Contenido para Canva

> Cada seccion es una diapositiva. Las instrucciones de imagen van en **[IMAGEN: descripcion]**.
> El texto en bloques de codigo va en un cuadro de codigo con fondo oscuro en Canva.

---

## DIAPOSITIVA 1 - Portada

**Titulo principal (letra grande, centrado):**
WARDEN

**Subtitulo:**
Wireless Attack Reproduction and Detection Environment

**Integrantes:**
- Santiago Valencia Leon
- Daniel Yadir Perea Murillo
- Sofia Valdez Londono

**[IMAGEN: logo o fondo abstracto de redes WiFi / ondas de radio]**

---

## DIAPOSITIVA 2 - ¿Que es WARDEN?

**Titulo:** ¿Que es WARDEN?

**Descripcion:**
WARDEN es un laboratorio academico de seguridad WiFi de doble subsistema:

- Reproduce una cadena de ataque WiFi de tres fases usando un microcontrolador ESP32
- Detecta esa misma cadena en tiempo real usando un sensor Python/Scapy en una laptop
- Todo el trafico entre el atacante y el defensor ocurre unicamente por el aire (802.11)
- Un Validador Etico en el firmware restringe los ataques exclusivamente a BSSIDs y MACs del laboratorio

**Objetivo:**
Demostrar de forma controlada y etica como funciona un ataque Evil Twin completo y como un sistema de deteccion puede identificarlo.

**[IMAGEN: diagrama de dos laptops separadas por el aire con un ESP32 en el centro emitiendo ondas WiFi]**

---

## DIAPOSITIVA 3 - Componentes de Hardware

**Titulo:** Componentes de Hardware

| Componente | Rol en el sistema |
|---|---|
| ESP32-WROOM-32 (4 MB flash) | Subsistema ofensivo - genera el ataque |
| Panda Wireless PAU0B (panda0) | Adaptador USB WiFi en modo monitor para captura |
| Router TP-Link (LAB_WARDEN_UTP) | Red victima del laboratorio |
| Laptop 1 - Atacante | Ejecuta el Panel del Atacante y controla el ESP32 |
| Laptop 2 - Defensor | Ejecuta el detector Python y el Panel del Defensor |
| Telefono Android (victima) | Dispositivo que se conecta al Evil Twin |

**[IMAGEN: foto del ESP32-WROOM-32 sobre una mesa]**

**[IMAGEN: foto del adaptador Panda Wireless PAU0B (USB)]**

**[IMAGEN: foto del router TP-Link]**

**[IMAGEN: foto de ambas laptops lado a lado durante la demo]**

---

## DIAPOSITIVA 4 - Arquitectura General del Sistema

**Titulo:** Arquitectura del Sistema

**Descripcion del diagrama:**

```
[Laptop Atacante]              [ESP32]              [Aire 2.4 GHz]    [Laptop Defensor]
  Panel Atacante  <---HTTP-->  API REST   -------->  802.11 frames --> panda0 (monitor)
  localhost:8080               192.168.4.1             Beacon / Deauth  Detector Python
                                                       / Evil Twin       Panel Defensor
                                                                         localhost:8000
```

**Puntos clave:**
- Los dos subsistemas NO estan conectados por cable ni por socket directo
- El ESP32 tiene su propia red WiFi de control: `WARDEN_CONTROL` (192.168.4.1)
- La laptop atacante se conecta a `WARDEN_CONTROL` para dar ordenes al ESP32
- La laptop defensora usa el adaptador Panda en modo monitor para "escuchar" el aire
- Los paneles son interfaces web locales en cada laptop

**[IMAGEN: captura de pantalla del diagrama de arquitectura o recrearlo en Canva]**

---

## DIAPOSITIVA 5 - Subsistema Ofensivo: ESP32

**Titulo:** Subsistema Ofensivo - Firmware ESP32

**¿Que hace el ESP32?**
El ESP32 es el "atacante hardware". Ejecuta tres modulos de ataque en secuencia:

1. **FASE 1 - Beacon Flood:** Emite ~50 redes WiFi falsas por segundo para saturar la lista de redes del dispositivo victima
2. **FASE 2 - Deautenticacion:** Inyecta tramas deauth suplantando el AP real, desconectando a la victima por la fuerza
3. **FASE 3 - Evil Twin:** Levanta una red clonada con el mismo SSID del router real; cuando la victima se conecta, aparece un portal cautivo que captura sus credenciales WiFi

**Modulos internos del firmware:**
- `chain_controller` - maquina de estados de la cadena de ataque
- `beacon_flood` - tarea FreeRTOS que emite tramas beacon falsas
- `deauth_module` - inyecta tramas de desautenticacion dirigidas
- `evil_twin` - configura el SoftAP clonado + portal cautivo + DNS local
- `ethical_validator` - bloquea ataques a redes que no sean del laboratorio
- `api_server` - servidor REST en el ESP32 (192.168.4.1)

**Stack tecnologico:**
- C++ / Arduino-ESP32 3.3.8
- ESPAsyncWebServer + AsyncTCP
- ArduinoJson 7
- FreeRTOS (incluido en ESP-IDF)

**[IMAGEN: captura de pantalla del codigo fuente del chain_controller o del serial monitor mostrando FASE_1 -> FASE_2 -> FASE_3]**

---

## DIAPOSITIVA 6 - Compilacion y Carga del Firmware

**Titulo:** Compilacion y Carga del Firmware ESP32

**Herramienta usada:** `arduino-cli` (linea de comandos, sin IDE)

**Paso 1 - Compilar el firmware:**
```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32 \
  --build-path /tmp/warden-build \
  --build-property "compiler.cpp.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  --build-property "compiler.c.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  src/attacker
```

**Paso 2 - Flashear al ESP32 por USB:**
```bash
arduino-cli upload \
  --fqbn esp32:esp32:esp32 \
  --port /dev/ttyUSB0 \
  --input-dir /tmp/warden-build \
  src/attacker
```

**Paso 3 - Ver logs del ESP32 por serial:**
```bash
python3 -c "
import serial, sys
s = serial.Serial('/dev/ttyUSB0', 115200)
[sys.stdout.write(s.readline().decode(errors='replace')) for _ in iter(int,1)]
"
```

**Resultado esperado:** El ESP32 transmite la red `WARDEN_CONTROL` con IP `192.168.4.1`

**¿Por que arduino-cli y no el IDE de Arduino?**
Permite automatizar la compilacion y carga en scripts reproducibles sin interfaz grafica. Compila exactamente los mismos archivos que el IDE pero desde la terminal.

**[IMAGEN: captura de pantalla de la terminal mostrando el output de arduino-cli compile con "Sketch uses X bytes of program storage space"]**

**[IMAGEN: captura de pantalla del monitor serial mostrando el boot del ESP32 y la aparicion de WARDEN_CONTROL]**

---

## DIAPOSITIVA 7 - Panel del Atacante

**Titulo:** Panel del Atacante (Attacker Panel)

**¿Como se sirve?**
Es un SPA (Single Page Application) estatico: HTML + JavaScript puro + Tailwind CSS. No requiere compilacion. Se sirve directamente desde la laptop atacante:

```bash
cd src/attacker-panel
python3 -m http.server 8080
```

Luego abrir en el navegador: `http://localhost:8080`

**¿Por que localhost:8080?**
El panel es HTML/JS estatico. El navegador necesita un servidor HTTP para cargarlo (no puede hacer fetch() desde file://). Se usa `python3 -m http.server` porque es la herramienta mas simple que no requiere instalacion adicional. El panel hace sus llamadas API a `http://192.168.4.1` (el ESP32), no a localhost.

**Requisito previo:** La laptop atacante debe estar conectada a la red WiFi `WARDEN_CONTROL` del ESP32.

**Flujo de uso del panel:**

1. **Pestana Recon** - Escanea redes WiFi cercanas (`GET /scan`), selecciona el router victima, escanea clientes conectados, identifica el fabricante del telefono victima por OUI
2. **Pestana Ethics** - Muestra el BSSID objetivo, el operador debe escribir `confirm` para desbloquear el ataque (valida que el BSSID sea del laboratorio)
3. **Pestana Attack** - Configura duracion de cada fase, selecciona modo `cadena_automatica`, inicia el ataque, muestra progreso en tiempo real
4. **Pestana Summary** - Muestra las credenciales capturadas en el portal cautivo al finalizar

**[IMAGEN: screenshot de la pestana Recon mostrando la lista de redes WiFi escaneadas]**

**[IMAGEN: screenshot de la pestana Ethics mostrando el campo de confirmacion]**

**[IMAGEN: screenshot de la pestana Attack durante la ejecucion de la cadena de ataque]**

**[IMAGEN: screenshot de la pestana Summary mostrando credenciales capturadas]**

---

## DIAPOSITIVA 8 - Subsistema Defensivo: Detector

**Titulo:** Subsistema Defensivo - Detector Python

**¿Que hace el detector?**
Captura tramas 802.11 desde el adaptador Panda en modo monitor y aplica tres analizadores independientes:

| Analizador | Que detecta | Alerta generada |
|---|---|---|
| D-01 BeaconFloodAnalyzer | Mas de 30 beacons/seg de BSSIDs distintos | `BEACON_FLOOD / ALERT` |
| D-02 DeauthAnalyzer | Mas de 5 deauths/seg dirigidos al BSSID protegido | `DEAUTH / ALERT` |
| D-03 EvilTwinAnalyzer | Beacon del SSID protegido desde un BSSID desconocido | `EVIL_TWIN / CRITICAL` |
| ChainCorrelator | Las tres alertas anteriores en orden ascendente | `CADENA_OFENSIVA / CRITICAL` |

**Pipeline interno:**

```
panda0 (monitor)
   |
   v
Scapy sniff() -> Dispatcher -> [BeaconFloodAnalyzer]
                             -> [DeauthAnalyzer     ]  -> Reporter
                             -> [EvilTwinAnalyzer   ]       |
                             -> [ChainCorrelator    ]   asyncio.Queue
                                                            |
                                                    WebSocketManager
                                                            |
                                                    Panel Defensor (browser)
```

**Stack tecnologico:**
- Python 3.10+ / Scapy 2.5
- FastAPI 0.110 + Uvicorn 0.27
- WebSockets nativos del browser
- 56 tests automatizados con pytest

**[IMAGEN: captura del terminal mostrando pytest corriendo con los 56 tests en verde]**

---

## DIAPOSITIVA 9 - Activar Modo Monitor en Panda PAU0B

**Titulo:** Configurar el Adaptador Panda en Modo Monitor

**¿Por que modo monitor?**
En modo gestionado (managed) una tarjeta WiFi solo recibe tramas dirigidas a su MAC. En modo monitor captura TODAS las tramas del canal sin importar el destinatario, igual que Wireshark captura paquetes en una red cableada.

**Comando simple (script automatizado):**
```bash
sudo bash scripts/setup-monitor-mode.sh panda0 1
```

**Comandos equivalentes paso a paso:**
```bash
# 1. Evitar que NetworkManager interfiera
nmcli dev set panda0 managed no

# 2. Apagar la interfaz
sudo ip link set panda0 down

# 3. Cambiar a modo monitor
sudo iw dev panda0 set type monitor

# 4. Encender la interfaz
sudo ip link set panda0 up

# 5. Sintonizar el canal (debe coincidir con el canal del router victima)
sudo iw dev panda0 set channel 1

# 6. Verificar que quedo en modo monitor
iw dev panda0 info | grep type
# Resultado esperado: type monitor
```

**Importante:** El numero de canal (`1` en el ejemplo) debe ser el mismo canal en que transmite el router victima (`LAB_WARDEN_UTP`). Si los canales no coinciden, el detector no vera las tramas del ataque.

**Para restaurar modo normal (despues de la demo):**
```bash
sudo ip link set panda0 down
sudo iw dev panda0 set type managed
sudo ip link set panda0 up
```

**[IMAGEN: captura de pantalla de la terminal ejecutando el script y el output de iw dev panda0 info confirmando type monitor]**

---

## DIAPOSITIVA 10 - Panel del Defensor

**Titulo:** Panel del Defensor (Defender Panel)

**Instalacion de dependencias (una sola vez):**
```bash
cd /ruta/al/proyecto/warden
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Iniciar el servidor:**
```bash
source .venv/bin/activate
uvicorn detector.web.server:app --host 0.0.0.0 --port 8000
```

Abrir en el navegador: `http://localhost:8000`

**¿Por que localhost:8000?**
El detector corre en la misma laptop defensora como un servidor FastAPI. Los paneles son interfaces web locales. No necesitan estar publicados en internet porque el laboratorio es una red privada. `localhost` significa "este mismo equipo". El puerto 8000 es el estandar de FastAPI.

**Flujo de uso del panel:**
1. Escribir el numero de canal del router victima en **"Canal a monitorear"** (ej: `1`)
2. Hacer click en **"Activar modo monitor"** - el badge de panda0 debe cambiar a `monitor ch 1`
3. Llenar **"BSSID protegido"** y **"SSID protegido"** del router del laboratorio
4. Hacer click en **"Iniciar detector"**
5. Ver las alertas aparecer en tiempo real mientras el atacante ejecuta la cadena
6. Al finalizar, hacer click en **"Resetear sesion"** para borrar contadores

**¿Por que WebSockets y no polling?**
Con polling el navegador preguntaria cada X segundos si hay alertas nuevas. Con WebSockets el servidor empuja cada alerta al instante en que ocurre. La diferencia es latencia sub-segundo vs varios segundos de retraso.

**[IMAGEN: screenshot del Panel del Defensor en estado inicial (sin detector activo)]**

**[IMAGEN: screenshot del Panel del Defensor durante el ataque mostrando alertas BEACON_FLOOD y DEAUTH en tiempo real]**

**[IMAGEN: screenshot del Panel del Defensor mostrando la alerta CADENA_OFENSIVA / CRITICAL en rojo]**

---

## DIAPOSITIVA 11 - FASE 1: Beacon Flood

**Titulo:** FASE 1 - Beacon Flood (Inundacion de Beacons)

**¿Que es un Beacon?**
Un beacon es una trama que cada router WiFi emite ~10 veces por segundo para anunciar su existencia. Es lo que hace que tu telefono "vea" las redes disponibles.

**¿Que hace el ESP32 en FASE 1?**
Emite ~50 beacons por segundo con SSIDs completamente falsos (`"Red_fake_0001"`, `"Red_fake_0002"`, etc.) desde MACs aleatorias. El objetivo es saturar la lista de redes del dispositivo victima para confundirlo y prepararlo para el ataque siguiente.

**Parametros configurables:**
- Duracion por defecto: 30 segundos
- Se puede cambiar via `POST http://192.168.4.1/config`

**Como se detecta:**
El `BeaconFloodAnalyzer` mantiene una ventana deslizante de 5 segundos. Si detecta mas de 30 beacons/segundo con BSSIDs distintos, genera la alerta `BEACON_FLOOD / ALERT`.

**Log del ESP32 durante FASE 1 (monitor serial):**
```
[WARDEN] Estado: FASE_1 - Beacon Flood iniciado
[WARDEN] Enviando beacon 1/seg: RED_FALSA_0042 desde AA:BB:CC:11:22:33
[WARDEN] Enviando beacon 1/seg: RED_FALSA_0043 desde AA:BB:CC:11:22:34
...
[WARDEN] FASE_1 completada, pasando a FASE_2
```

**[IMAGEN: screenshot del telefono victima mostrando decenas de redes WiFi falsas en la lista]**

**[IMAGEN: screenshot del Panel Defensor mostrando la alerta BEACON_FLOOD activada]**

---

## DIAPOSITIVA 12 - FASE 2: Deautenticacion

**Titulo:** FASE 2 - Deautenticacion (Desconexion Forzada)

**¿Que es una trama Deauth?**
802.11 define tramas de "desautenticacion" que un AP envia a los clientes para desconectarlos. En redes sin WPA3, estas tramas no estan autenticadas, es decir, cualquiera puede enviarlas suplantando la MAC del AP real.

**¿Que hace el ESP32 en FASE 2?**
Inyecta tramas deauth en el canal del router victima, suplantando su BSSID como fuente. El telefono victima cree que el router real lo esta desconectando y pierde la conexion a `LAB_WARDEN_UTP`.

**Parametros:**
- Duracion por defecto: 30 segundos
- La victima MAC debe seleccionarse en el panel de Recon antes del ataque

**Como se detecta:**
El `DeauthAnalyzer` cuenta tramas deauth donde el campo `addr3` (BSSID) coincide con el BSSID protegido. Si supera 5 deauths/segundo en una ventana de 3 segundos, genera `DEAUTH / ALERT`.

**Log del ESP32 durante FASE 2:**
```
[WARDEN] Estado: FASE_2 - Deauth iniciado
[WARDEN] Enviando deauth a AA:BB:CC:DD:EE:FF desde BSSID E4:AB:89:D6:9B:80
[WARDEN] Deauth frame #47 enviado
...
[WARDEN] FASE_2 completada, pasando a FASE_3
```

**[IMAGEN: screenshot del telefono victima mostrando que perdio la conexion WiFi]**

**[IMAGEN: screenshot del Panel Defensor mostrando la alerta DEAUTH activada]**

---

## DIAPOSITIVA 13 - FASE 3: Evil Twin y Portal Cautivo

**Titulo:** FASE 3 - Evil Twin + Portal Cautivo

**¿Que es un Evil Twin?**
Un Evil Twin es una red WiFi falsa que usa el mismo SSID que una red legitima. El objetivo es que la victima se conecte a la red falsa creyendo que es la real.

**¿Que hace el ESP32 en FASE 3?**
1. Configura un SoftAP (Access Point virtual) con el mismo SSID que `LAB_WARDEN_UTP`
2. Usa una IP no-privada (`4.3.2.1`) para activar el captive portal en dispositivos Android y iPhone
3. Activa un servidor DNS local que responde todas las consultas con su propia IP
4. Cuando el telefono se conecta, el sistema operativo detecta automaticamente el portal cautivo y abre el navegador

**Portal cautivo:**
Una pagina HTML en el ESP32 simula una pantalla de "Autenticacion requerida" y pide las credenciales WiFi. Cuando la victima las ingresa, se envian por POST al ESP32 y quedan almacenadas en memoria.

**Como se detecta:**
El `EvilTwinAnalyzer` registra todos los BSSIDs que han emitido beacons con el SSID protegido. Cuando detecta un BSSID que no es el router real, genera `EVIL_TWIN / CRITICAL`.

**[IMAGEN: screenshot del telefono mostrando la notificacion de "Iniciar sesion en la red" del sistema operativo]**

**[IMAGEN: screenshot del portal cautivo en el telefono pidiendo usuario y contrasena WiFi]**

**[IMAGEN: screenshot de la pestana Summary del Panel Atacante mostrando las credenciales capturadas]**

---

## DIAPOSITIVA 14 - Deteccion de la Cadena Completa

**Titulo:** Deteccion de la Cadena Ofensiva Completa

**El ChainCorrelator:**
Una vez que se generaron las tres alertas individuales (BEACON_FLOOD, DEAUTH, EVIL_TWIN) en orden temporal ascendente y dentro de una ventana de correlacion, el `ChainCorrelator` genera la alerta maestra:

`CADENA_OFENSIVA / CRITICAL`

Esta alerta significa que las tres fases ocurrieron de forma coordinada y que no son eventos aislados, sino un ataque intencional de tipo Evil Twin.

**Verificar credenciales capturadas via API:**
```bash
curl http://192.168.4.1/credentials
```

Respuesta del ESP32:
```json
{
  "credenciales": [
    {"usuario": "LAB_WARDEN_UTP", "contrasena": "contraseña_victima", "ts_ms": 38420}
  ],
  "total": 1
}
```

**Verificar estado del ataque:**
```bash
curl http://192.168.4.1/attack/status
```

**[IMAGEN: screenshot del Panel Defensor mostrando las cuatro alertas: BEACON_FLOOD, DEAUTH, EVIL_TWIN, CADENA_OFENSIVA]**

**[IMAGEN: screenshot del terminal con el curl a /credentials mostrando las credenciales capturadas en JSON]**

---

## DIAPOSITIVA 15 - Decisiones de Diseno (ADRs)

**Titulo:** Decisiones Clave de Diseno

Los ADRs (Architecture Decision Records) documentan el "por que" de cada decision tecnica importante.

| # | Decision | Razon |
|---|---|---|
| ADR-01 | Comunicacion solo por el aire (802.11) | Los subsistemas deben ser independientes. El detector ve exactamente lo que veria un WIDS real, sin inyeccion artificial |
| ADR-02 | Python + Scapy para el detector | Ecosistema rico (Scapy, asyncio, FastAPI), desarrollo rapido, equipo familiarizado con Python |
| ADR-03 | ESP32 para el modulo ofensivo | Soporte nativo de inyeccion de tramas 802.11 crudas y SoftAP simultaneo. Presupuesto: ~30 USD |
| ADR-04 | Deteccion heuristica, sin ML | El ML requiere conjuntos de entrenamiento y es un proyecto academico. Las heuristicas de ventana deslizante son suficientes y verificables |
| ADR-06 | Validador Etico dentro del firmware | La restriccion debe estar en el hardware, no en el software externo. No se puede deshabilitar sin recompilar |
| ADR-07 | Panel del atacante servido desde la laptop | El flash del ESP32 (4 MB) esta ocupado con la base de datos OUI. El frontend puede actualizarse sin reflashear |
| ADR-08 | FastAPI + WebSockets para alertas | El polling introduce latencia. Con WebSockets las alertas llegan en menos de 1 segundo al navegador |
| ADR-09 | Base de datos OUI embebida en flash | Sin conexion a internet en el laboratorio. 5500 entradas en PROGMEM (flash), busqueda binaria en O(log n) |

---

## DIAPOSITIVA 16 - Requerimientos Funcionales Implementados

**Titulo:** Requerimientos Funcionales

**Modulo Ofensivo (ESP32):**

| ID | Requerimiento | Estado |
|---|---|---|
| RF-ATK-001 | El ESP32 debe emitir beacons con SSIDs falsos a razon minima de 10/seg | Implementado - 50/seg |
| RF-ATK-002 | El ESP32 debe inyectar tramas deauth al BSSID objetivo | Implementado |
| RF-ATK-003 | El ESP32 debe clonar el SSID del AP objetivo en FASE_3 | Implementado |
| RF-ATK-004 | El portal cautivo debe capturar credenciales ingresadas | Implementado |
| RF-ATK-005 | El Validador Etico debe bloquear BSSIDs fuera de la lista del lab | Implementado |
| RF-ATK-006 | La API REST debe exponer estado y control de la cadena | Implementado (11 endpoints) |
| RF-ATK-007 | El operador debe seleccionar dispositivo victima especifico | Implementado (mac_victima) |

**Modulo Defensivo (Detector):**

| ID | Requerimiento | Estado |
|---|---|---|
| RF-DET-001 | Detectar Beacon Flood con umbral configurable | Implementado - umbral 30/seg |
| RF-DET-002 | Detectar Deauthenticacion masiva | Implementado - umbral 5/seg |
| RF-DET-003 | Detectar Evil Twin (SSID clonado desde BSSID distinto) | Implementado |
| RF-DET-004 | Correlacionar las tres fases como cadena ofensiva | Implementado - ChainCorrelator |
| RF-DET-005 | Alertas en tiempo real en el panel web | Implementado - WebSocket |
| RF-DET-006 | Operar sobre captura live (modo monitor) y archivos PCAP | Implementado |
| RF-DET-007 | Todos los umbrales deben ser configurables en tiempo de ejecucion | Implementado - POST /api/config |

---

## DIAPOSITIVA 17 - El Validador Etico

**Titulo:** Validador Etico - Seguridad en el Hardware

**¿Por que existe?**
El firmware del ESP32 tiene capacidad de atacar CUALQUIER red WiFi. El Validador Etico es la barrera que impide usarlo fuera del laboratorio.

**¿Como funciona?**
Es una libreria C++ (`src/ethical_validator/`) que se compila e integra directamente en el firmware. La logica de validacion:

```
1. BSSID = FF:FF:FF:FF:FF:FF (broadcast)  -> RECHAZADO
2. BSSID = 00:00:00:00:00:00 (nulo)       -> RECHAZADO
3. BSSID coincide con el router del lab   -> VALIDO (confianza incondicional)
4. OUI del BSSID en lista negra de ISPs   -> RECHAZADO (red de un ISP real)
5. El operador escribio "confirm"         -> VALIDO
6. Ninguna condicion anterior             -> REQUIERE_CONFIRMACION
```

**Lista negra de OUIs:** Incluye los prefijos de MAC de los principales ISPs colombianos (EPM, Claro, ETB, Tigo, Une). Esto impide atacar redes de operadores reales aunque el operador intente confirmar.

**La validacion no se puede saltar:**
Cada endpoint de ataque (`POST /attack/start`) verifica que `bssid_validado == true`. Si el validador no aprobo el BSSID, el ataque no arranca.

**[IMAGEN: screenshot del panel de Ethics mostrando el flujo de confirmacion]**

**[IMAGEN: diagrama de flujo de la logica del validador etico]**

---

## DIAPOSITIVA 18 - Demo Completa: Paso a Paso

**Titulo:** Demo Completa - Secuencia de Comandos

**Preparacion (5 terminales):**

**Terminal 1 - Monitor serial del ESP32:**
```bash
python3 -c "
import serial, sys
s = serial.Serial('/dev/ttyUSB0', 115200)
[sys.stdout.write(s.readline().decode(errors='replace')) for _ in iter(int,1)]
"
```

**Terminal 2 - Modo monitor en panda0:**
```bash
sudo bash scripts/setup-monitor-mode.sh panda0 1
iw dev panda0 info | grep type   # verificar: type monitor
```

**Terminal 3 - Panel del atacante:**
```bash
cd src/attacker-panel
python3 -m http.server 8080
# Abrir navegador en: http://localhost:8080
```

**Terminal 4 - Panel del defensor:**
```bash
source .venv/bin/activate
uvicorn detector.web.server:app --host 0.0.0.0 --port 8000
# Abrir navegador en: http://localhost:8000
```

**Secuencia del operador atacante:**
1. Conectar laptop a WiFi `WARDEN_CONTROL` (clave: `warden-control-pwd`)
2. Abrir `http://localhost:8080`
3. En **Recon:** escanear redes, seleccionar `LAB_WARDEN_UTP`, escanear clientes, seleccionar el telefono victima
4. En **Ethics:** confirmar BSSID escribiendo `confirm`
5. En **Attack:** seleccionar `cadena_automatica`, configurar duraciones, iniciar

**Secuencia del operador defensor:**
1. En el panel `http://localhost:8000`: escribir canal `1`
2. Click **Activar modo monitor**
3. Llenar BSSID y SSID del router lab
4. Click **Iniciar detector**
5. Esperar alertas en tiempo real

**[IMAGEN: screenshot de todas las terminales abiertas mostrando el sistema activo]**

---

## DIAPOSITIVA 19 - Pruebas y Verificacion

**Titulo:** Pruebas y Verificacion del Sistema

**Suite de pruebas automatizadas:**
```bash
source .venv/bin/activate
pytest tests/ -v
```

**Resultado:** 56 pruebas en verde, 0 fallos

**Tipos de pruebas:**

| Categoria | Cantidad | Que verifica |
|---|---|---|
| Detector unit tests | 32 | Cada analizador individualmente con PCAPs sinteticos |
| FastAPI integration | 8 | Endpoints REST del panel defensor |
| WebSocket test | 4 | Transmision de alertas en tiempo real |
| Acceptance E2E | 1 | Cadena completa: chain.pcap produce las 4 alertas |
| C++ firmware tests | 8 | Validador etico + frame builder con doctest |
| No-duplicate helpers | 1 | Ninguna funcion definida dos veces entre modulos |

**Prueba de aceptacion (la mas importante):**
```bash
pytest tests/test_acceptance_chain.py -v
```
Ejecuta el servidor completo, alimenta el archivo `chain.pcap` y verifica que las alertas `BEACON_FLOOD`, `DEAUTH`, `EVIL_TWIN` y `CADENA_OFENSIVA` lleguen al WebSocket en menos de 3 segundos.

**Verificacion del firmware:**
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 src/attacker
# Resultado: Sketch uses 87% of program storage space (flash)
```

**[IMAGEN: captura de pantalla de pytest corriendo con todos los tests en verde (PASSED)]**

---

## DIAPOSITIVA 20 - ¿Por que Localhost? Arquitectura de Red del Laboratorio

**Titulo:** ¿Por que los Paneles son en Localhost?

**Descripcion de la red del laboratorio:**

```
[Internet]
    |
[Router de casa]
    |
[TP-Link LAB_WARDEN_UTP] <-------- Dispositivos de laboratorio
    |                               - Laptop atacante (WiFi WARDEN_CONTROL)
[Canal WiFi 1]                      - Laptop defensora
    |                               - Telefono victima
[ESP32 WARDEN_CONTROL]
   192.168.4.1
```

**Respuesta corta:** Los paneles son aplicaciones web que corren LOCALMENTE en cada laptop, no en un servidor remoto.

**Panel Atacante (localhost:8080):**
- Es un servidor de archivos estaticos. `python3 -m http.server` sirve los archivos HTML/JS del disco local
- El panel hace fetch a `http://192.168.4.1` (ESP32), que es accesible porque la laptop esta en la red `WARDEN_CONTROL`
- No necesita internet ni un servidor externo

**Panel Defensor (localhost:8000):**
- Es un servidor FastAPI que corre en la laptop defensora
- El detector captura paquetes del adaptador panda0 (hardware local)
- Las alertas se muestran en el mismo navegador de esa laptop
- No tiene sentido publicarlo en internet porque solo opera en el laboratorio

**Conclusion:** Localhost no es una limitacion, es la arquitectura correcta para un sistema de laboratorio cerrado.

---

## DIAPOSITIVA 21 - Conclusion

**Titulo:** Conclusion

**Lo que construimos:**

WARDEN es un sistema funcional y completo de laboratorio WiFi que:
- Ejecuta una cadena de ataque de tres fases (Beacon Flood -> Deauth -> Evil Twin) de forma automatizada desde un ESP32
- Detecta esa misma cadena en tiempo real con un sensor Python/Scapy y la presenta en un dashboard web
- Incluye un Validador Etico en hardware que impide su uso fuera del laboratorio
- Tiene 56 pruebas automatizadas que verifican todos los modulos
- Funciona completamente sin internet en un ambiente de laboratorio cerrado

**Resultados del demo:**
- Credenciales capturadas exitosamente via portal cautivo Evil Twin
- Panel defensor mostrando CADENA_OFENSIVA / CRITICAL en tiempo real
- Latencia de alerta < 1 segundo desde la trama hasta el navegador

**Aprendizajes clave:**
- Los ataques Evil Twin son posibles con hardware de menos de USD 30
- La deteccion heuristica basada en ventanas deslizantes es efectiva y predecible
- La separacion de subsistemas por el aire (ADR-01) da realismo academico al sistema

**[IMAGEN: foto del equipo con el hardware completo del laboratorio]**

**[IMAGEN: screenshot final del Panel Defensor mostrando la alerta CADENA_OFENSIVA en rojo]**

---

## NOTAS PARA EL PRESENTADOR

**Orden de apertura de paneles antes de la demo:**
1. Flashear ESP32 con arduino-cli (ya listo si el firmware no cambio)
2. Conectar laptop atacante a WARDEN_CONTROL
3. Terminal: monitor serial del ESP32
4. Terminal: activar modo monitor en panda0 canal 1
5. Terminal: python3 -m http.server 8080
6. Terminal: uvicorn detector.web.server:app --port 8000
7. Navegadores: localhost:8080 y localhost:8000

**Si el ESP32 se bloquea:**
```bash
# Verificar que el puerto serial no este ocupado
fuser /dev/ttyUSB0
# Detener proceso ocupando el puerto
kill <PID>
```

**Si panda0 no aparece en modo monitor:**
```bash
# Verificar que NetworkManager no lo haya tomado
nmcli dev set panda0 managed no
iw dev panda0 info
```

**Verificar credenciales en tiempo real:**
```bash
curl http://192.168.4.1/credentials
```
