"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const tablaCarrito = document.querySelector("#listaCarrito");
    const formPago = document.querySelector("#formPago");
    const listaCompras = document.querySelector("#listaCompras");

    function datosCarrito() {
        const productos = PixelForge.leer(PixelForge.claves.productos, []);
        const carrito = PixelForge.leer(PixelForge.claves.carrito, []);
        return carrito.map((item) => ({ ...item, producto: productos.find((producto) => producto.id === item.id) }))
            .filter((item) => item.producto);
    }

    function totalCarrito() {
        return datosCarrito().reduce((total, item) => total + item.producto.precio * item.cantidad, 0);
    }

    function renderCarrito() {
        if (!tablaCarrito) return;
        const items = datosCarrito();
        const resumen = document.querySelector("#totalCarrito");
        const botonPago = document.querySelector("#irPago");

        if (!items.length) {
            tablaCarrito.innerHTML = `<tr><td colspan="5" class="text-center py-5">Tu carrito está vacío.</td></tr>`;
            resumen.textContent = PixelForge.dinero(0);
            botonPago.classList.add("disabled");
            return;
        }

        tablaCarrito.innerHTML = items.map((item) => `<tr>
            <td>${item.producto.nombre}</td><td>${PixelForge.dinero(item.producto.precio)}</td>
            <td><input class="cantidad-carrito" type="number" min="1" max="${item.producto.stock}" value="${item.cantidad}" data-id="${item.id}" aria-label="Cantidad de ${item.producto.nombre}"></td>
            <td>${PixelForge.dinero(item.producto.precio * item.cantidad)}</td>
            <td><button class="btn btn-sm btn-outline-danger quitar-producto" data-id="${item.id}">Quitar</button></td></tr>`).join("");
        resumen.textContent = PixelForge.dinero(totalCarrito());

        tablaCarrito.querySelectorAll(".cantidad-carrito").forEach((campo) => campo.addEventListener("change", () => {
            const carrito = PixelForge.leer(PixelForge.claves.carrito, []);
            const item = carrito.find((actual) => actual.id === Number(campo.dataset.id));
            item.cantidad = Math.max(1, Math.min(Number(campo.max), Number(campo.value)));
            PixelForge.guardar(PixelForge.claves.carrito, carrito);
            renderCarrito();
        }));
        tablaCarrito.querySelectorAll(".quitar-producto").forEach((boton) => boton.addEventListener("click", () => {
            const carrito = PixelForge.leer(PixelForge.claves.carrito, []).filter((item) => item.id !== Number(boton.dataset.id));
            PixelForge.guardar(PixelForge.claves.carrito, carrito);
            renderCarrito();
        }));
    }

    if (formPago) {
        const sesion = PixelForge.exigirSesion();
        const items = datosCarrito();
        if (!sesion || !items.length) return;
        const vencimiento = document.querySelector("#vencimiento");

        vencimiento.addEventListener("input", () => {
            const numeros = vencimiento.value.replace(/\D/g, "").slice(0, 4);
            vencimiento.value = numeros.length > 2
                ? `${numeros.slice(0, 2)}/${numeros.slice(2)}`
                : numeros;
            vencimiento.setCustomValidity("");

            if (/^(0[1-9]|1[0-2])\/[0-9]{2}$/.test(vencimiento.value)) {
                const [mes, anio] = vencimiento.value.split("/").map(Number);
                const hoy = new Date();
                const vencida = 2000 + anio < hoy.getFullYear()
                    || (2000 + anio === hoy.getFullYear() && mes < hoy.getMonth() + 1);
                if (vencida) vencimiento.setCustomValidity("La tarjeta está vencida.");
            }
        });

        document.querySelector("#resumenPago").innerHTML = items.map((item) => `<li>${item.cantidad} × ${item.producto.nombre}<span>${PixelForge.dinero(item.cantidad * item.producto.precio)}</span></li>`).join("");
        document.querySelector("#totalPago").textContent = PixelForge.dinero(totalCarrito());

        formPago.addEventListener("submit", (evento) => {
            evento.preventDefault();
            if (!formPago.checkValidity()) {
                formPago.classList.add("was-validated");
                return;
            }
            const productos = PixelForge.leer(PixelForge.claves.productos, []);
            const sinStock = items.some((item) => item.cantidad > item.producto.stock);
            if (sinStock) return PixelForge.mensaje("Cambió el stock disponible. Revisa tu carrito.", "danger");

            items.forEach((item) => {
                const producto = productos.find((actual) => actual.id === item.id);
                producto.stock -= item.cantidad;
            });
            const pedidos = PixelForge.leer(PixelForge.claves.pedidos, []);
            pedidos.push({
                id: Date.now(), usuarioId: sesion.id, cliente: sesion.nombre, fecha: new Date().toLocaleDateString("es-CL"),
                total: totalCarrito(), estado: "Pagado", productos: items.map((item) => ({ nombre: item.producto.nombre, cantidad: item.cantidad }))
            });
            PixelForge.guardar(PixelForge.claves.productos, productos);
            PixelForge.guardar(PixelForge.claves.pedidos, pedidos);
            PixelForge.guardar(PixelForge.claves.carrito, []);
            document.querySelector("#pagoExitoso").classList.remove("d-none");
            formPago.classList.add("d-none");
        });
    }

    if (listaCompras) {
        const sesion = PixelForge.exigirSesion();
        if (!sesion) return;
        const pedidos = PixelForge.leer(PixelForge.claves.pedidos, []).filter((pedido) => pedido.usuarioId === sesion.id).reverse();
        listaCompras.innerHTML = pedidos.length ? pedidos.map((pedido) => `<article class="pedido">
            <div><strong>Pedido #${pedido.id}</strong><br><span>${pedido.fecha}</span></div>
            <div>${pedido.productos.map((item) => `${item.cantidad} × ${item.nombre}`).join("<br>")}</div>
            <div><span class="estado-pedido">${pedido.estado}</span><br><strong>${PixelForge.dinero(pedido.total)}</strong></div>
        </article>`).join("") : `<p class="estado-vacio">Todavía no tienes compras registradas.</p>`;
    }

    renderCarrito();
});
