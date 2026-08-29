"use strict";

const PixelForge = (() => {
    const claves = {
        usuarios: "pixelforge_usuarios",
        sesion: "pixelforge_sesion",
        productos: "pixelforge_productos",
        carrito: "pixelforge_carrito",
        pedidos: "pixelforge_pedidos"
    };

    const usuariosIniciales = [
        {
            id: 1,
            nombre: "Administrador PixelForge",
            usuario: "admin",
            correo: "admin@pixelforge.cl",
            clave: "Admin1!",
            fecha: "1992-03-15",
            direccion: "Av. Libertador Bernardo O'Higgins 1449, Santiago",
            rol: "administrador",
            activo: true
        },
        {
            id: 2,
            nombre: "Cliente de prueba",
            usuario: "cliente",
            correo: "cliente@pixelforge.cl",
            clave: "Cliente1!",
            fecha: "1998-07-27",
            direccion: "Av. Providencia 1234, Providencia, Santiago",
            rol: "cliente",
            activo: true
        }
    ];

    const productosIniciales = [
        { id: 1, nombre: "Halo: Campaign Evolved", categoria: "Acción", precio: 49.99, stock: 12, imagen: "imagenes/Halo Campaign Evolved.jpg", activo: true },
        { id: 2, nombre: "Ghost of Yōtei", categoria: "Acción", precio: 69.99, stock: 8, imagen: "imagenes/Ghost of Yōtei.jpg", activo: true },
        { id: 3, nombre: "Big Walk", categoria: "Aventura", precio: 19.99, stock: 20, imagen: "imagenes/Big Walk.jpg", activo: true },
        { id: 4, nombre: "007 First Light", categoria: "Aventura", precio: 69.99, stock: 6, imagen: "imagenes/007 First Light.jpg", activo: true },
        { id: 5, nombre: "eBaseball: PRO SPIRIT 2026", categoria: "Deportes", precio: 59.99, stock: 10, imagen: "imagenes/eBaseball PRO SPIRIT 2026.jpg", activo: true },
        { id: 6, nombre: "Streetdog BMX", categoria: "Deportes", precio: 19.99, stock: 15, imagen: "imagenes/Streetdog BMX.jpg", activo: true },
        { id: 7, nombre: "Beast of Reincarnation", categoria: "RPG", precio: 59.99, stock: 7, imagen: "imagenes/Beast of Reincarnation.jpg", activo: true },
        { id: 8, nombre: "Nioh 3", categoria: "RPG", precio: 69.99, stock: 9, imagen: "imagenes/Nioh 3.jpg", activo: true },
        { id: 9, nombre: "MARVEL Tōkon: Fighting Souls", categoria: "Combate", precio: 59.99, stock: 11, imagen: "imagenes/MARVEL Tōkon Fighting Souls.jpg", activo: true },
        { id: 10, nombre: "Avatar Legends: The Fighting Game", categoria: "Combate", precio: 29.99, stock: 14, imagen: "imagenes/Avatar Legends The Fighting Game.jpg", activo: true }
    ];

    function leer(clave, valorInicial = []) {
        const guardado = localStorage.getItem(clave);
        if (!guardado) {
            localStorage.setItem(clave, JSON.stringify(valorInicial));
            return valorInicial;
        }
        try {
            return JSON.parse(guardado);
        } catch {
            return valorInicial;
        }
    }

    function guardar(clave, valor) {
        localStorage.setItem(clave, JSON.stringify(valor));
    }

    function iniciarDatos() {
        const usuarios = leer(claves.usuarios, usuariosIniciales);
        const clientePrueba = usuarios.find((usuario) => usuario.correo === "cliente@pixelforge.cl");

        if (clientePrueba && clientePrueba.fecha === "2000-01-01") {
            clientePrueba.fecha = "1998-07-27";
        }
        if (clientePrueba && clientePrueba.direccion === "Av. Siempre Viva 123") {
            clientePrueba.direccion = "Av. Providencia 1234, Providencia, Santiago";
        }
        const administrador = usuarios.find((usuario) => usuario.correo === "admin@pixelforge.cl");
        if (administrador && administrador.fecha === "1990-01-01") {
            administrador.fecha = "1992-03-15";
        }
        if (administrador && administrador.direccion === "") {
            administrador.direccion = "Av. Libertador Bernardo O'Higgins 1449, Santiago";
        }
        guardar(claves.usuarios, usuarios);
        leer(claves.productos, productosIniciales);
        leer(claves.carrito, []);
        leer(claves.pedidos, []);
    }

    function obtenerSesion() {
        return leer(claves.sesion, null);
    }

    function cerrarSesion() {
        localStorage.removeItem(claves.sesion);
        window.location.href = rutaBase() + "index.html";
    }

    function rutaBase() {
        return document.querySelector('link[href="../css/estilos.css"]') ? "../" : "";
    }

    function dinero(valor) {
        return new Intl.NumberFormat("es-CL", {
            style: "currency",
            currency: "USD"
        }).format(valor);
    }

    function mensaje(texto, tipo = "success") {
        const aviso = document.createElement("div");
        aviso.className = `aviso-flotante alert alert-${tipo}`;
        aviso.textContent = texto;
        document.body.appendChild(aviso);
        setTimeout(() => aviso.remove(), 2600);
    }

    function actualizarMenu() {
        const contenedor = document.querySelector(".navbar-nav") || document.querySelector("nav .container");
        if (!contenedor || document.querySelector("[data-enlace-cuenta]")) return;

        const base = rutaBase();
        const sesion = obtenerSesion();
        const carrito = leer(claves.carrito, []);
        const cantidad = carrito.reduce((total, item) => total + item.cantidad, 0);

        const enlaces = document.createElement("span");
        enlaces.className = "enlaces-cuenta";
        enlaces.dataset.enlaceCuenta = "true";
        enlaces.innerHTML = `<a href="${base}tienda/carrito.html">Carrito (${cantidad})</a>`;

        if (sesion) {
            enlaces.innerHTML += `<a href="${base}cuenta/perfil.html">Mi perfil</a>`;
            enlaces.innerHTML += `<a href="${base}tienda/compras.html">Mis compras</a>`;
            if (sesion.rol === "administrador") {
                enlaces.innerHTML += `<a href="${base}admin/productos.html">Administración</a>`;
            }
            enlaces.innerHTML += `<button type="button" class="enlace-boton" id="cerrarSesion">Salir</button>`;
        } else {
            enlaces.innerHTML += `<a href="${base}cuenta/login.html">Ingresar</a>`;
            if (!contenedor.querySelector('a[href$="registro.html"]')) {
                enlaces.innerHTML += `<a href="${base}cuenta/registro.html">Registro</a>`;
            }
        }

        contenedor.appendChild(enlaces);
        document.querySelector("#cerrarSesion")?.addEventListener("click", cerrarSesion);
    }

    function prepararCatalogo() {
        const productos = leer(claves.productos, productosIniciales);

        document.querySelectorAll(".tarjeta .contenido").forEach((contenido) => {
            const nombre = contenido.querySelector("h3")?.textContent.trim();
            const producto = productos.find((item) => item.nombre === nombre);
            if (!producto) return;

            const precio = contenido.querySelector(".precio");
            if (precio) precio.textContent = dinero(producto.precio);

            const boton = document.createElement("button");
            boton.type = "button";
            boton.className = "boton boton-carrito";
            boton.textContent = producto.stock > 0 ? "Agregar al carrito" : "Sin stock";
            boton.disabled = producto.stock < 1 || !producto.activo;
            boton.addEventListener("click", () => agregarAlCarrito(producto.id));
            contenido.appendChild(boton);
        });
    }

    function agregarAlCarrito(idProducto) {
        const productos = leer(claves.productos, productosIniciales);
        const producto = productos.find((item) => item.id === idProducto);
        const carrito = leer(claves.carrito, []);
        const existente = carrito.find((item) => item.id === idProducto);

        if (!producto || producto.stock < 1) return;
        if (existente && existente.cantidad >= producto.stock) {
            mensaje("No hay más unidades disponibles.", "warning");
            return;
        }

        if (existente) existente.cantidad++;
        else carrito.push({ id: idProducto, cantidad: 1 });

        guardar(claves.carrito, carrito);
        mensaje(`${producto.nombre} fue agregado al carrito.`);
        document.querySelector("[data-enlace-cuenta]")?.remove();
        actualizarMenu();
    }

    function exigirSesion(rol) {
        const sesion = obtenerSesion();
        if (!sesion || (rol && sesion.rol !== rol)) {
            window.location.href = rutaBase() + (sesion ? "index.html" : "cuenta/login.html");
            return null;
        }
        return sesion;
    }

    iniciarDatos();
    document.addEventListener("DOMContentLoaded", () => {
        actualizarMenu();
        prepararCatalogo();
    });

    return {
        claves,
        leer,
        guardar,
        dinero,
        mensaje,
        obtenerSesion,
        exigirSesion,
        usuariosIniciales,
        productosIniciales
    };
})();
