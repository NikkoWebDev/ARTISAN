/* =======================================================
   DATOS DE PRODUCTOS
======================================================= */
const productos = {
    textiles: {
        ruana1_cafe: {
            esBase: true,
            tipo: "ruana",
            nombre: "Ruana Espina - Café",
            descripcionCorta: "Ruana artesanal con diseño espina de pez",
            precio: 130000,
            origen: "Boyacá, Colombia",
            dimensiones: "2m x 1.5m",
            caracteristicas: [
                "Hecho a mano",
                "Lana 100% natural",
                "Suave y cálida",
                "Diseño exclusivo espina de pez"
            ],
            imagenes: [
                "img/productos/textiles/ruanas/ruana1_cafe.png",
                "img/productos/textiles/ruanas/ruana1_cafe_material.png",
                "img/productos/textiles/ruanas/ruana1_cafe_dimensiones.png"
            ],
            variantes: ["ruana1_morado"]
        },

        poncho2: {
            esBase: true,
            tipo: "poncho",
            nombre: "Poncho de Lana Artesanal",
            descripcionCorta: "Poncho de lana suave y cálido",
            precio: 95000,
            origen: "Nariño, Colombia",
            dimensiones: "1.8m x 1.4m",
            caracteristicas: [
                "Hecho a mano",
                "Lana de oveja",
                "Diseño clásico"
            ],
            imagenes: [
                "img/productos/textiles/ruanas/ruana2.png",
                "img/productos/textiles/ruanas/ruana2_2.png",
                "img/productos/textiles/ruanas/ruana2_3.png"
            ],
            variantes: []
        },

        ruana1_morado: {
            esBase: false,
            tipo: "ruana",
            nombre: "Ruana Espina - Morado",
            descripcionCorta: "Ruana artesanal con diseño espina de pez",
            precio: 100000,
            origen: "Boyacá, Colombia",
            dimensiones: "2m x 1.5m",
            caracteristicas: [
                "Hecho a mano",
                "Lana 100% natural",
                "Suave y cálida",
                "Diseño exclusivo espina de pez",
                "Diseño exclusivo espina de pez"
            ],
            imagenes: [
                "img/productos/textiles/ruanas/ruana1_morado.png",
                "img/productos/textiles/ruanas/ruana1_morado_material.png",
                "img/productos/textiles/ruanas/ruana1_morado_dimensiones.png"
            ],
            variantes: ["ruana1_cafe"]
        }
    }
};

/* =======================================================
   OBTENER PRODUCTO DESDE URL
======================================================= */
function getProductoSeleccionado() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("producto");
    const categoria = params.get("categoria");

    if (!categoria || !id || !productos[categoria] || !productos[categoria][id]) {
        console.error("Producto no encontrado:", categoria, id);
        return null;
    }

    return { ...productos[categoria][id], categoria, id };
}

/* =======================================================
   BUSCAR PRODUCTO POR ID
======================================================= */
function getProductoPorID(id) {
    for (let categoria in productos) {
        if (productos[categoria][id]) {
            return { ...productos[categoria][id], categoria, id };
        }
    }
    return null;
}

/* =======================================================
   CARGAR PRODUCTO EN LA PÁGINA
======================================================= */
function cargarProducto(productoID = null) {
    const productoActual = productoID ? getProductoPorID(productoID) : getProductoSeleccionado();
    if (!productoActual) return;

    // Elementos HTML
    document.getElementById("producto-nombre").textContent = productoActual.nombre;
    document.getElementById("producto-precio").textContent = `$${productoActual.precio.toLocaleString()} COP`;
    document.getElementById("producto-descripcion").textContent = productoActual.descripcionCorta;

    const imagenPrincipal = document.getElementById("imagen-principal");
    const miniaturasDiv = document.getElementById("miniaturas");

    imagenPrincipal.src = productoActual.imagenes[0];

    // Miniaturas
    miniaturasDiv.innerHTML = "";
    productoActual.imagenes.forEach((imgSrc, index) => {
        const img = document.createElement("img");
        img.src = imgSrc;
        img.classList.add("thumb");
        if (index === 0) img.classList.add("activa");
        img.onclick = () => cambiarImagen(img);
        miniaturasDiv.appendChild(img);
    });

    // Datos
    document.getElementById("producto-origen").textContent = productoActual.origen;
    document.getElementById("producto-dimensiones").textContent = productoActual.dimensiones;
    document.getElementById("producto-caracteristicas").innerHTML =
        productoActual.caracteristicas.map(c => `<li>${c}</li>`).join("");

    // Variantes
    const variantesDiv = document.getElementById("producto-variantes");
    variantesDiv.innerHTML = "";

    if (productoActual.variantes.length > 0) {
        productoActual.variantes.forEach(vID => {
            const variante = getProductoPorID(vID);
            if (!variante) return;

            const img = document.createElement("img");
            img.src = variante.imagenes[0];
            img.classList.add("thumb-variant");
            img.onclick = () => cargarProducto(vID);
            variantesDiv.appendChild(img);
        });
    }
}

/* =======================================================
   CAMBIAR IMAGEN PRINCIPAL
======================================================= */
function cambiarImagen(img) {
    const principal = document.getElementById("imagen-principal");
    principal.src = img.src;

    document.querySelectorAll(".thumb").forEach(t => t.classList.remove("activa"));
    img.classList.add("activa");
}

/* =======================================================
   AGREGAR PRODUCTO ACTUAL AL CARRITO
======================================================= */
function agregarAlCarritoActual() {
    // Obtener información del producto desde el DOM
    const nombreElemento = document.getElementById("producto-nombre");
    const precioElemento = document.getElementById("producto-precio");
    const origenElemento = document.getElementById("producto-origen");
    const dimensionesElemento = document.getElementById("producto-dimensiones");
    const caracteristicasElemento = document.getElementById("producto-caracteristicas");

    if (!nombreElemento || !precioElemento) {
        alert("Error: Información del producto no disponible.");
        return;
    }

    const nombre = nombreElemento.textContent.trim();
    const precioTexto = precioElemento.textContent.trim();
    const precio = parseInt(precioTexto.replace(/[^0-9]/g, ''));
    const imagenActual = document.getElementById("imagen-principal").src;
    const origen = origenElemento ? origenElemento.textContent.trim() : '';
    const dimensiones = dimensionesElemento ? dimensionesElemento.textContent.trim() : '';
    const caracteristicas = caracteristicasElemento ? Array.from(caracteristicasElemento.querySelectorAll('li')).map(li => li.textContent.trim()) : [];

    if (!nombre || isNaN(precio)) {
        alert("Error: Nombre o precio del producto inválido.");
        return;
    }

    agregarAlCarrito({
        nombre: nombre,
        precio: precio,
        imagen: imagenActual,
        origen: origen,
        dimensiones: dimensiones,
        caracteristicas: caracteristicas
    });
}

/* =======================================================
   INICIAR
======================================================= */
document.addEventListener("DOMContentLoaded", () => cargarProducto());
