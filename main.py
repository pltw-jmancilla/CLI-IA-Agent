from dotenv import load_dotenv
load_dotenv()

from os import system
import threading

from langchain_core.messages import HumanMessage

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.padding import Padding
from rich.console import Group
from rich.live import Live
from rich.table import Table

import time
import uuid

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from graph.graph_manage import crear_grafo
from tool_log import flush_tools  

console = Console()

# --- PALETA DE COLORES PLATWAVE ---
COLOR_MAIN = "#14B8A6"  # Teal principal
COLOR_SOFT = "#0FA7A9"  # Turquesa secundario
COLOR_FADE = "#134E4A"  # Verde oscuro para bordes
COLOR_BG   = "#F0FDFA"  # Fondo muy claro
COLOR_DIM  = "#536766"  # Gris azulado secundario

# --- LOGO CORPORATIVO ASCII ---
ASCII_LOGO = r"""
                      _______
                      ++++++++
                        +++++++
                   ++++  +++++++
                  ++++++  +++++++
                 ++++++    +++++++
                ++++++      +++++++
             _______________  +++++++
            +++++++++++++++++  +++++++
           +++++++++++++++++  ++++++++
          ++++++++ ___       ++++++++ __
         +++++++  +++++     ++++++++ ++++
        +++++++  ++++++++  ++++++++  +++++
       +++++++   +++++++++  ++++++    +++++
      +++++++ ___ +++++++++  ++++      +++++
     +++++++ +++++ +++++++++__________________
    +++++++ +++++++ +++++++++++++++++++++++++++
    ++++++ +++++++++ +++++++++++++++++++++++++
"""

langfuse_handler = CallbackHandler()
langfuse_client = get_client()

grafo = crear_grafo()

thread_id = str(uuid.uuid4())

config = {
    "configurable": {"thread_id": thread_id},
    "recursion_limit": 8,
    "callbacks": [langfuse_handler],
    "metadata": {
        "langfuse_session_id": thread_id
    }
}

system("cls")

# --- CONSTRUCCIÓN DEL HEADER (LOGO + INFO LATERAL) ---
header_grid = Table.grid(expand=True)
header_grid.add_column(justify="left", width=48) # Espacio para el logo
header_grid.add_column(justify="left", vertical="middle") # Espacio para la info

# Bloque de información con colores independientes
info_side = Group(
    Text(""),
    Text(""),
    Text(""),
    Text.assemble(
        ("Powered by: ", COLOR_DIM), 
        ("Fireworks AI ", f"bold {COLOR_SOFT}"), 
        ("⦣V∠", COLOR_MAIN)
    ),
    Text("AI Multi-Agent System · Professional Internship", style=f"italic {COLOR_DIM}"),
    Text("Platwave Technologies™ · 2026", style="dim"),
)

header_grid.add_row(
    Text(ASCII_LOGO, style=COLOR_MAIN),
    info_side
)

# IMPRESIÓN DEL HEADER INICIAL (CENTRADO)
console.print(
    Align.center(
        Panel(
            header_grid,
            title=f"[bold {COLOR_BG}] SYSTEM ONLINE [/bold {COLOR_BG}]",
            title_align="center",
            border_style=COLOR_MAIN,
            padding=(1, 2),
            width=100,
        )
    )
)

console.print()
console.print(Text("   ▹ Escribe tu pregunta y presiona enter", style=f"italic {COLOR_DIM}"))
console.print(Text("   ▹ exit / q para salir", style=f"italic {COLOR_DIM}"))
console.print(Rule(style=COLOR_FADE)) 
console.print()


# Función de tipeo animado
def type_panel(text, speed=0.01, tool_logs=None):
    output = ""

    def build_panel(content):
        body_parts = []
        if tool_logs:
            for msg in tool_logs:
                t = Text()
                t.append(f" ⚙ {msg}", style=f"italic {COLOR_SOFT}")
                body_parts.append(t)
            body_parts.append(Text(""))

        body_parts.append(Text(content))

        return Panel(
            Padding(Group(*body_parts), (0, 1)),
            title=f"[bold {COLOR_BG}]Platwave AI Response[/bold {COLOR_BG}]",
            border_style=COLOR_SOFT,
            padding=(1, 2),
        )

    with Live(refresh_per_second=30) as live:
        for char in text:
            output += char
            live.update(build_panel(output))
            time.sleep(speed)


# Spinner de pensamiento
def thinking_spinner(done_event):
    thinking_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    with Live(refresh_per_second=15) as live:
        while not done_event.is_set():
            live.update(
                Text.assemble(
                    (f" {thinking_frames[idx % len(thinking_frames)]} ", f"bold {COLOR_MAIN}"),
                    ("Procesando con agentes...", f"dim {COLOR_DIM}"),
                )
            )
            time.sleep(0.08)
            idx += 1
        live.update(Text(""))


# BUCLE PRINCIPAL
while True:
    try:
        pregunta = console.input(
            f" [bold white]You[/bold white] [bold {COLOR_MAIN}]›[/bold {COLOR_MAIN}] "
        )
        
        if pregunta.lower() in ["exit", "q"]:
            langfuse_client.flush()
            system("cls")
            console.print()
            console.print(
                Panel(
                    Group(
                        Align.center(Text("◈", style=f"bold {COLOR_MAIN}")),
                        Text(""),
                        Align.center(Text("Cerrando sesión de Agente", style="bold white")),
                        Text(""),
                        Align.center(Text("Platwave Technologies™", style=f"dim {COLOR_DIM}")),
                    ),
                    border_style=COLOR_SOFT,
                    padding=(1, 2),
                    width=50,
                )
            )
            time.sleep(1.2)
            system("cls")
            break

        print(" ") # Espacio estético
        
        state = {"resultado": None}
        done  = threading.Event()

        def invoke():
            state["resultado"] = grafo.invoke(
                {"messages": [HumanMessage(content=pregunta)]},
                config=config,
            )
            done.set()

        t = threading.Thread(target=invoke, daemon=True)
        t.start()
        thinking_spinner(done)

        tool_logs = flush_tools()
        respuesta = state["resultado"]["messages"][-1].content
        type_panel(respuesta, 0.008, tool_logs=tool_logs)

        console.print()

    except Exception as e:
        error_msg = str(e)
        console.print(Align.center(Text(f"⚠ ERROR: {error_msg}", style="bold red")))
        print("")