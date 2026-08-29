"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sesion = PixelForge.exigirSesion("administrador");
    if (!sesion) return;

    const cuerpoProductos = document.querySelector("#tablaProductos");
    const cuerpoInventario = document.querySelector("#tablaInventario");
    const cuerpoUsuarios = document.querySelector("#tablaUsuarios");
    const cuerpoPedidos = document.querySelector("#tablaPedidos");
    const formProducto = document.querySelector("#formProducto");

    function renderProductos() {
        if (!cuerpoProductos) return;
        const productos = PixelForge.leer(PixelForge.claves.productos, []);
        cuerpoProductos.innerHTML = productos.map((producto) => `<tr><td>${producto.nombre}</td><td>${producto.categoria}</td><td>${PixelForge.dinero(producto.precio)}</td><td>${producto.stock}</td><td>${producto.activo ? "Activo" : "Oculto"}</td><td><button class="btn btn-sm btn-outline-light editar" data-id="${producto.id}">Editar</button> <button class="btn btn-sm btn-outline-danger eliminar" data-id="${producto.id}">Eliminar</button></td></tr>`).join("");
        cuerpoProductos.querySelectorAll(".editar").forEach((boton) => boton.addEventListener("click", () => cargarProducto(Number(boton.dataset.id))));
        cuerpoProductos.querySelectorAll(".eliminar").forEach((boton) => boton.addEventListener("click", () => eliminarProducto(Number(boton.dataset.id))));
    }

    function cargarProducto(id) {
        const producto = PixelForge.leer(PixelForge.claves.productos, []).find((item) => item.id === id);
        formProducto.idProducto.value = producto.id;
        formProducto.nombre.value = producto.nombre;
        formProducto.categoria.value = producto.categoria;
        formProducto.precio.value = producto.precio;
        formProducto.stock.value = producto.stock;
        formProducto.imagen.value = producto.imagen;
        formProducto.activo.checked = producto.activo;
        document.querySelector("#tituloProducto").textContent = "Modificar producto";
        formProducto.scrollIntoView({ behavior: "smooth" });
    }

    function eliminarProducto(id) {
        if (!confirm("¿Eliminar este producto del catálogo?")) return;
        const productos = PixelForge.leer(PixelForge.claves.productos, []).filter((item) => item.id !== id);
        PixelForge.guardar(PixelForge.claves.productos, productos);
        renderProductos();
    }

    formProducto?.addEventListener("submit", (evento) => {
        evento.preventDefault();
        if (!formProducto.checkValidity()) {
            formProducto.classList.add("was-validated");
            return;
        }
        const productos = PixelForge.leer(PixelForge.claves.productos, []);
        const id = Number(formProducto.idProducto.value);
        const datos = {
            nombre: formProducto.nombre.value.trim(), categoria: formProducto.categoria.value,
            precio: Number(formProducto.precio.value), stock: Number(formProducto.stock.value),
            imagen: formProducto.imagen.value.trim(), activo: formProducto.activo.checked
        };
        if (id) Object.assign(productos.find((item) => item.id === id), datos);
        else productos.push({ id: Date.now(), ...datos });
        PixelForge.guardar(PixelForge.claves.productos, productos);
        formProducto.reset(); formProducto.idProducto.value = ""; formProducto.activo.checked = true;
        document.querySelector("#tituloProducto").textContent = "Registrar producto";
        renderProductos();
        PixelForge.mensaje("Producto guardado correctamente.");
    });
    document.querySelector("#cancelarEdicion")?.addEventListener("click", () => {
        formProducto.reset(); formProducto.idProducto.value = ""; formProducto.activo.checked = true;
        document.querySelector("#tituloProducto").textContent = "Registrar producto";
    });

    function renderInventario() {
        if (!cuerpoInventario) return;
        const productos = PixelForge.leer(PixelForge.claves.productos, []);
        cuerpoInventario.innerHTML = productos.map((producto) => `<tr><td>${producto.nombre}</td><td>${producto.categoria}</td><td><input class="stock-admin" type="number" min="0" value="${producto.stock}" data-id="${producto.id}"></td><td><span class="badge ${producto.stock < 5 ? "text-bg-danger" : "text-bg-success"}">${producto.stock < 5 ? "Stock bajo" : "Disponible"}</span></td></tr>`).join("");
        cuerpoInventario.querySelectorAll(".stock-admin").forEach((campo) => campo.addEventListener("change", () => {
            const producto = productos.find((item) => item.id === Number(campo.dataset.id));
            producto.stock = Math.max(0, Number(campo.value));
            PixelForge.guardar(PixelForge.claves.productos, productos); renderInventario();
        }));
    }

    function renderUsuarios() {
        if (!cuerpoUsuarios) return;
        const usuarios = PixelForge.leer(PixelForge.claves.usuarios, []);
        cuerpoUsuarios.innerHTML = usuarios.map((usuario) => `<tr><td>${usuario.nombre}</td><td>${usuario.correo}</td><td><select class="rol-admin form-select form-select-sm" data-id="${usuario.id}" ${usuario.id === sesion.id ? "disabled" : ""}><option value="cliente" ${usuario.rol === "cliente" ? "selected" : ""}>Cliente</option><option value="administrador" ${usuario.rol === "administrador" ? "selected" : ""}>Administrador</option></select></td><td><button class="btn btn-sm ${usuario.activo ? "btn-outline-warning" : "btn-outline-success"} estado-usuario" data-id="${usuario.id}" ${usuario.id === sesion.id ? "disabled" : ""}>${usuario.activo ? "Desactivar" : "Activar"}</button></td></tr>`).join("");
        cuerpoUsuarios.querySelectorAll(".rol-admin").forEach((campo) => campo.addEventListener("change", () => { usuarios.find((item) => item.id === Number(campo.dataset.id)).rol = campo.value; PixelForge.guardar(PixelForge.claves.usuarios, usuarios); }));
        cuerpoUsuarios.querySelectorAll(".estado-usuario").forEach((boton) => boton.addEventListener("click", () => { const usuario = usuarios.find((item) => item.id === Number(boton.dataset.id)); usuario.activo = !usuario.activo; PixelForge.guardar(PixelForge.claves.usuarios, usuarios); renderUsuarios(); }));
    }

    function renderPedidos() {
        if (!cuerpoPedidos) return;
        const pedidos = PixelForge.leer(PixelForge.claves.pedidos, []).reverse();
        cuerpoPedidos.innerHTML = pedidos.length ? pedidos.map((pedido) => `<tr><td>#${pedido.id}</td><td>${pedido.cliente}</td><td>${pedido.fecha}</td><td>${PixelForge.dinero(pedido.total)}</td><td><select class="estado-admin form-select form-select-sm" data-id="${pedido.id}">${["Pagado", "Preparando", "Enviado", "Entregado"].map((estado) => `<option ${pedido.estado === estado ? "selected" : ""}>${estado}</option>`).join("")}</select></td></tr>`).join("") : `<tr><td colspan="5" class="text-center py-4">No existen pedidos todavía.</td></tr>`;
        cuerpoPedidos.querySelectorAll(".estado-admin").forEach((campo) => campo.addEventListener("change", () => { const todos = PixelForge.leer(PixelForge.claves.pedidos, []); todos.find((item) => item.id === Number(campo.dataset.id)).estado = campo.value; PixelForge.guardar(PixelForge.claves.pedidos, todos); }));
    }

    renderProductos(); renderInventario(); renderUsuarios(); renderPedidos();
});
