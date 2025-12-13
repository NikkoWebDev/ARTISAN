/* =======================================================
   WHATSAPP — Desde página de producto
======================================================= */
function enviarWhatsApp() {

    const numero = "573123580705";

    let nombreProducto = "";
    const nombreElemento = document.getElementById("producto-nombre");
    if (nombreElemento) nombreProducto = nombreElemento.textContent.trim();

    let imgActual = "";
    const imgElemento = document.getElementById("imagen-principal");
    if (imgElemento) imgActual = imgElemento.src;

    let precioActual = "";
    const precioElemento = document.getElementById("producto-precio");
    if (precioElemento) precioActual = precioElemento.textContent.trim();

    const mensaje =
        `Hola, quiero comprar:\n` +
        `Producto: ${nombreProducto}\n` +
        `Imagen seleccionada: ${window.location.origin}/${imgActual}\n` +
        `Precio: ${precioActual}`;

    const url = `https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}`;
    window.open(url, "_blank");
}



/* =======================================================
   CABECERA OCULTABLE
======================================================= */
let ultimoScroll = 0;
const cabecera = document.querySelector(".cabecera");

if (cabecera) {
    window.addEventListener("scroll", () => {
        const scrollActual = window.pageYOffset;

        if (scrollActual > ultimoScroll && scrollActual > 20) {
            cabecera.style.top = "-200px";
        } else {
            cabecera.style.top = "0";
        }

        ultimoScroll = scrollActual;
    });
}



/* =======================================================
   LOADER
======================================================= */
window.addEventListener("load", () => {
    const loader = document.getElementById("loader");
    if (loader) {
        setTimeout(() => loader.classList.add("loader-oculto"), 800);
    }
});



/* =======================================================
   CAMBIAR MINIATURA
======================================================= */
function cambiarImagen(img) {
    const principal = document.getElementById("imagen-principal");
    if (!principal) return;

    document.querySelectorAll(".thumb")
        .forEach(t => t.classList.remove("activa"));

    img.classList.add("activa");
    principal.src = img.src;
}



/* =======================================================
   CARRITO — sistema
======================================================= */
if (!localStorage.getItem("carrito")) {
    localStorage.setItem("carrito", JSON.stringify([]));
}

function agregarAlCarrito(producto) {
    if (!producto || !producto.nombre) {
        mostrarToast("Error: Producto no válido");
        return;
    }

    const carrito = JSON.parse(localStorage.getItem("carrito"));

    // Verificar si el producto ya existe
    const existente = carrito.find(item => item.nombre === producto.nombre);
    if (existente) {
        existente.cantidad = (existente.cantidad || 1) + 1;
    } else {
        producto.cantidad = 1;
        carrito.push(producto);
    }

    localStorage.setItem("carrito", JSON.stringify(carrito));

    mostrarToast(`Producto añadido: ${producto.nombre}`);

    cargarCarrito();
}



/* =======================================================
   MODAL DE NOTIFICACIÓN
======================================================= */
function mostrarToast(mensaje) {

    const existente = document.getElementById("modal-toast");
    if (existente) existente.remove();

    const overlay = document.createElement("div");
    overlay.id = "modal-toast";
    overlay.className = "modal-overlay";

    const caja = document.createElement("div");
    caja.className = "modal-caja";

    const texto = document.createElement("p");
    texto.textContent = mensaje;

    const boton = document.createElement("button");
    boton.className = "modal-boton";
    boton.textContent = "Cerrar";
    boton.onclick = () => overlay.remove();

    caja.appendChild(texto);
    caja.appendChild(boton);
    overlay.appendChild(caja);

    document.body.appendChild(overlay);
}



/* =======================================================
   VER INFO DE PRODUCTO EN CARRITO
======================================================= */
function verProductoCarrito(index) {
    const carrito = JSON.parse(localStorage.getItem("carrito"));
    const item = carrito[index];

    if (!item) return;

    const cantidad = item.cantidad || 1;
    let mensaje = `Producto: ${item.nombre}\nCantidad: ${cantidad}\nPrecio unitario: $${item.precio.toLocaleString()} COP\nSubtotal: $${(item.precio * cantidad).toLocaleString()} COP`;

    if (item.origen) mensaje += `\nOrigen: ${item.origen}`;
    if (item.dimensiones) mensaje += `\nDimensiones: ${item.dimensiones}`;
    if (item.caracteristicas && item.caracteristicas.length > 0) {
        mensaje += `\nCaracterísticas:\n${item.caracteristicas.map(c => `• ${c}`).join('\n')}`;
    }

    mostrarToast(mensaje);
}



/* =======================================================
   CARGAR CARRITO EN LA PÁGINA
======================================================= */
function cargarCarrito() {
    const carrito = JSON.parse(localStorage.getItem("carrito")) || [];

    const lista = document.getElementById("carrito-lista");
    const totalTexto = document.getElementById("carrito-total");

    if (!lista || !totalTexto) return;

    lista.innerHTML = "";
    let total = 0;

    if (carrito.length === 0) {
        lista.innerHTML = `<p>Tu carrito está vacío.</p>`;
        totalTexto.textContent = "Total: $0 COP";
        return;
    }

    carrito.forEach((item, index) => {
        if (!item.nombre || !item.precio) return; // Saltar items inválidos

        const cantidad = item.cantidad || 1;
        const subtotal = item.precio * cantidad;
        total += subtotal;

        const div = document.createElement("div");
        div.className = "carrito-item";

        div.innerHTML = `
            <img src="${item.imagen}" alt="${item.nombre}" onclick="verProductoCarrito(${index})">
            <div class="carrito-info">
                <h3>${item.nombre}</h3>
                <p>$${item.precio.toLocaleString()} COP c/u</p>
                <div class="carrito-cantidad">
                    <button onclick="cambiarCantidad(${index}, -1)">-</button>
                    <span>${cantidad}</span>
                    <button onclick="cambiarCantidad(${index}, 1)">+</button>
                </div>
                <p>Subtotal: $${subtotal.toLocaleString()} COP</p>
            </div>
            <button class="carrito-eliminar" onclick="eliminarDelCarrito(${index})">X</button>
        `;

        lista.appendChild(div);
    });

    totalTexto.textContent = `Total: $${total.toLocaleString()} COP`;
}



/* =======================================================
   ELIMINAR DEL CARRITO
======================================================= */
function eliminarDelCarrito(index) {
    const carrito = JSON.parse(localStorage.getItem("carrito"));

    carrito.splice(index, 1);

    localStorage.setItem("carrito", JSON.stringify(carrito));

    mostrarToast("Producto eliminado ❌");

    cargarCarrito();
}



/* =======================================================
   CAMBIAR CANTIDAD EN CARRITO
======================================================= */
function cambiarCantidad(index, delta) {
    const carrito = JSON.parse(localStorage.getItem("carrito"));
    const item = carrito[index];

    if (!item) return;

    item.cantidad = (item.cantidad || 1) + delta;

    if (item.cantidad <= 0) {
        carrito.splice(index, 1);
        mostrarToast("Producto eliminado ❌");
    }

    localStorage.setItem("carrito", JSON.stringify(carrito));

    cargarCarrito();
}



/* =======================================================
   PAGAR WHATSAPP
======================================================= */
function pagarWhatsApp() {
    const carrito = JSON.parse(localStorage.getItem("carrito"));

    if (!carrito || carrito.length === 0) {
        mostrarToast("Tu carrito está vacío");
        return;
    }

    let mensaje = "Hola, quiero comprar estos productos:\n\n";
    let total = 0;

    carrito.forEach(item => {
        if (!item.nombre || typeof item.precio !== 'number' || item.precio <= 0) return; // Saltar items inválidos

        const cantidad = item.cantidad || 1;
        const subtotal = item.precio * cantidad;
        mensaje += `• ${item.nombre} - Cantidad: ${cantidad} - $${item.precio.toLocaleString()} COP c/u - Subtotal: $${subtotal.toLocaleString()} COP\nImagen: ${window.location.origin}/${item.imagen}\n\n`;
        total += subtotal;
    });

    if (total === 0) {
        mostrarToast("No hay productos válidos en el carrito");
        return;
    }

    mensaje += `TOTAL: $${total.toLocaleString()} COP`;

    const numero = "573123580705";
    const url = `https://api.whatsapp.com/send?phone=${numero}&text=${encodeURIComponent(mensaje)}`;

    // Crear enlace temporal y simular click para abrir en nueva pestaña
    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer'; // Seguridad
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}



/* =======================================================
   AUTO-CARGA
======================================================= */
document.addEventListener("DOMContentLoaded", cargarCarrito);
