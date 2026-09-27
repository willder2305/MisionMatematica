"""Contextos narrativos variados para proporcionalidad directa e inversa."""

DIRECTA = (
    ("cuadernos", "Si {a} cuadernos cuestan Q{b}, ¿cuánto cuestan {c} cuadernos?"),
    ("receta", "Para preparar {a} porciones se usan {b} gramos de harina. ¿Cuántos gramos se necesitan para {c} porciones?"),
    ("combustible", "Un vehículo recorre {b} kilómetros con {a} litros de combustible. ¿Cuántos kilómetros recorrerá con {c} litros?"),
    ("tela", "Con {a} metros de tela se confeccionan {b} banderines. ¿Cuántos banderines se harán con {c} metros?"),
    ("pintura", "Para pintar {a} paredes se usan {b} litros de pintura. ¿Cuántos litros se requieren para {c} paredes?"),
    ("plantas", "En {a} filas se siembran {b} plantas. ¿Cuántas plantas habrá en {c} filas iguales?"),
    ("entradas", "Un grupo compra {a} entradas por Q{b}. ¿Cuánto pagará por {c} entradas al mismo precio?"),
    ("paquetes", "Cada {a} paquetes contienen {b} lápices. ¿Cuántos lápices contienen {c} paquetes?"),
    ("paginas", "En {a} días se leen {b} páginas al mismo ritmo. ¿Cuántas páginas se leerán en {c} días?"),
    ("fruta", "Por {a} kilogramos de fruta se pagan Q{b}. ¿Cuánto se paga por {c} kilogramos?"),
)

INVERSA = (
    ("trabajadores", "Si {a} trabajadores terminan una tarea en {b} días, ¿cuántos días necesitarán {c} trabajadores al mismo ritmo?"),
    ("bombas", "Una piscina se llena en {b} horas con {a} bombas iguales. ¿Cuántas horas tomará con {c} bombas?"),
    ("impresoras", "{a} impresoras imprimen un lote en {b} minutos. ¿Cuántos minutos tardarán {c} impresoras iguales?"),
    ("maquinas", "{a} máquinas producen un pedido en {b} horas. ¿Cuántas horas necesitarán {c} máquinas?"),
    ("obreros", "{a} obreros construyen una pared en {b} días. ¿En cuántos días la construirán {c} obreros?"),
    ("grifos", "{a} grifos llenan un tanque en {b} horas. ¿Cuánto tardarán {c} grifos iguales?"),
    ("equipos", "{a} equipos ordenan materiales en {b} horas. ¿Cuántas horas usarán {c} equipos?"),
    ("vehiculos", "{a} vehículos realizan una entrega en {b} viajes. ¿Cuántos viajes harán {c} vehículos?"),
    ("cocineros", "{a} cocineros preparan un pedido en {b} minutos. ¿Cuántos minutos necesitan {c} cocineros?"),
    ("excavadoras", "{a} excavadoras terminan una zanja en {b} horas. ¿Cuántas horas tomarán {c} excavadoras?"),
)


def elegir_contexto(rng, tipo):
    """Elige una estructura narrativa y conserva su llave para evitar repeticiones."""
    context_key, enunciado = rng.choice(DIRECTA if tipo == "directa" else INVERSA)
    return context_key, enunciado
