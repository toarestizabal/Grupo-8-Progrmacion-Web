-- PixelForge Games - datos iniciales idempotentes para Oracle
-- Ejecutar conectado como PIXELFORGE_APP después de las migraciones.
WHENEVER SQLERROR EXIT SQL.SQLCODE
SET DEFINE OFF

MERGE INTO PF_ROLES r USING (SELECT N'CLIENTE' codigo FROM dual) s ON (r.codigo=s.codigo)
WHEN MATCHED THEN UPDATE SET r.nombre=N'Cliente', r.descripcion=N'Compra productos y revisa sus pedidos.'
WHEN NOT MATCHED THEN INSERT (codigo,nombre,descripcion) VALUES (N'CLIENTE',N'Cliente',N'Compra productos y revisa sus pedidos.');
MERGE INTO PF_ROLES r USING (SELECT N'ADMINISTRADOR' codigo FROM dual) s ON (r.codigo=s.codigo)
WHEN MATCHED THEN UPDATE SET r.nombre=N'Administrador', r.descripcion=N'Gestiona productos, inventario, usuarios y pedidos.'
WHEN NOT MATCHED THEN INSERT (codigo,nombre,descripcion) VALUES (N'ADMINISTRADOR',N'Administrador',N'Gestiona productos, inventario, usuarios y pedidos.');

DECLARE
    PROCEDURE upsert_categoria(p_nombre NVARCHAR2, p_slug NVARCHAR2, p_descripcion NVARCHAR2, p_imagen NVARCHAR2) IS
    BEGIN
        MERGE INTO PF_CATEGORIAS c
        USING (SELECT p_slug slug FROM dual) s ON (c.slug=s.slug)
        WHEN MATCHED THEN UPDATE SET c.nombre=p_nombre,c.descripcion=p_descripcion,c.imagen=p_imagen,c.activa=1
        WHEN NOT MATCHED THEN INSERT (nombre,slug,descripcion,imagen,activa)
            VALUES (p_nombre,p_slug,p_descripcion,p_imagen,1);
    END;
BEGIN
    upsert_categoria(UNISTR('Acci\00F3n'),N'accion',UNISTR('Combate intenso, estrategia r\00E1pida y adrenalina.'),N'accion.svg');
    upsert_categoria(N'Aventura',N'aventura',N'Explora mundos, resuelve misterios y vive grandes historias.',N'aventura.svg');
    upsert_categoria(N'Deportes',N'deportes',N'Competencia deportiva para jugar solo o con amigos.',N'deportes.svg');
    upsert_categoria(N'RPG',N'rpg',UNISTR('Personajes, decisiones y progresi\00F3n en mundos inolvidables.'),N'rpg.svg');
    upsert_categoria(N'Combate',N'combate',UNISTR('Domina t\00E9cnicas y enfr\00E9ntate a rivales legendarios.'),N'combate.svg');
END;
/

DECLARE
    PROCEDURE upsert_producto(
        p_nombre NVARCHAR2, p_categoria NVARCHAR2, p_descripcion NVARCHAR2,
        p_precio NUMBER, p_stock NUMBER, p_imagen NVARCHAR2
    ) IS
        v_producto_id NUMBER;
    BEGIN
        MERGE INTO PF_PRODUCTOS p
        USING (SELECT p_nombre nombre FROM dual) s ON (p.nombre=s.nombre)
        WHEN MATCHED THEN UPDATE SET
            p.categoria_id=(SELECT id FROM PF_CATEGORIAS WHERE slug=p_categoria),
            p.descripcion=p_descripcion,p.precio=p_precio,p.imagen=p_imagen,
            p.activo=1,p.actualizado=SYSTIMESTAMP
        WHEN NOT MATCHED THEN INSERT
            (nombre,descripcion,precio,imagen,activo,creado,actualizado,categoria_id)
            VALUES (p_nombre,p_descripcion,p_precio,p_imagen,1,SYSTIMESTAMP,SYSTIMESTAMP,
                    (SELECT id FROM PF_CATEGORIAS WHERE slug=p_categoria));
        SELECT id INTO v_producto_id FROM PF_PRODUCTOS WHERE nombre=p_nombre;
        MERGE INTO PF_INVENTARIO i
        USING (SELECT v_producto_id producto_id FROM dual) s ON (i.producto_id=s.producto_id)
        WHEN MATCHED THEN UPDATE SET i.stock=p_stock,i.actualizado=SYSTIMESTAMP
        WHEN NOT MATCHED THEN INSERT (stock,actualizado,producto_id)
            VALUES (p_stock,SYSTIMESTAMP,v_producto_id);
    END;
BEGIN
    upsert_producto(N'Halo: Campaign Evolved',N'accion',UNISTR('Una campa\00F1a de ciencia ficci\00F3n completamente renovada.'),49990,12,N'Halo Campaign Evolved.jpg');
    upsert_producto(UNISTR('Ghost of Y\014Dtei'),N'accion',UNISTR('Acci\00F3n samur\00E1i en un territorio salvaje y espectacular.'),69990,8,UNISTR('Ghost of Y\014Dtei.jpg'));
    upsert_producto(N'Big Walk',N'aventura',N'Una aventura cooperativa relajada llena de descubrimientos.',19990,20,N'Big Walk.jpg');
    upsert_producto(N'007 First Light',N'aventura',UNISTR('Los or\00EDgenes de un agente en una misi\00F3n cinematogr\00E1fica.'),69990,6,N'007 First Light.jpg');
    upsert_producto(N'eBaseball: PRO SPIRIT 2026',N'deportes',UNISTR('B\00E9isbol profesional con estadios y plantillas actualizadas.'),59990,10,N'eBaseball PRO SPIRIT 2026.jpg');
    upsert_producto(N'Streetdog BMX',N'deportes',N'Trucos, velocidad y libertad sobre dos ruedas.',19990,15,N'Streetdog BMX.jpg');
    upsert_producto(N'Beast of Reincarnation',N'rpg',UNISTR('Un RPG de acci\00F3n ambientado en una tierra misteriosa.'),59990,7,N'Beast of Reincarnation.jpg');
    upsert_producto(N'Nioh 3',N'rpg',N'Combates exigentes contra guerreros y criaturas sobrenaturales.',69990,9,N'Nioh 3.jpg');
    upsert_producto(UNISTR('MARVEL T\014Dkon: Fighting Souls'),N'combate',UNISTR('H\00E9roes y villanos se enfrentan en equipos espectaculares.'),59990,11,UNISTR('MARVEL T\014Dkon Fighting Souls.jpg'));
    upsert_producto(N'Avatar Legends: The Fighting Game',N'combate',N'Domina los elementos en combates competitivos.',29990,14,N'Avatar Legends The Fighting Game.jpg');
END;
/

-- Las contraseñas son hashes PBKDF2 de Admin123! y Cliente123!; nunca se guardan en texto plano.
MERGE INTO PF_USUARIOS u USING (SELECT N'admin' username FROM dual) s ON (u.username=s.username)
WHEN MATCHED THEN UPDATE SET u.email=N'admin@pixelforge.cl',u.nombre_completo=N'Administrador PixelForge',u.rol_id=(SELECT id FROM PF_ROLES WHERE codigo=N'ADMINISTRADOR'),u.is_staff=1,u.is_active=1
WHEN NOT MATCHED THEN INSERT
    (password,is_superuser,username,first_name,last_name,is_staff,is_active,date_joined,email,nombre_completo,fecha_nacimiento,direccion,rol_id)
    VALUES (N'pbkdf2_sha256$1000000$EyMwF6S6LHKAW64rIdZvzP$9WNFk42cCgTYzItuZFgh7eCjXZBzpYthelWBzkhaUNY=',0,N'admin',N'',N'',1,1,SYSTIMESTAMP,N'admin@pixelforge.cl',N'Administrador PixelForge',DATE '1992-03-15',N'Av. Libertador Bernardo O''Higgins 1449, Santiago',(SELECT id FROM PF_ROLES WHERE codigo=N'ADMINISTRADOR'));

MERGE INTO PF_USUARIOS u USING (SELECT N'cliente' username FROM dual) s ON (u.username=s.username)
WHEN MATCHED THEN UPDATE SET u.email=N'cliente@pixelforge.cl',u.nombre_completo=N'Cliente de prueba',u.rol_id=(SELECT id FROM PF_ROLES WHERE codigo=N'CLIENTE'),u.is_staff=0,u.is_active=1
WHEN NOT MATCHED THEN INSERT
    (password,is_superuser,username,first_name,last_name,is_staff,is_active,date_joined,email,nombre_completo,fecha_nacimiento,direccion,rol_id)
    VALUES (N'pbkdf2_sha256$1000000$ASQVh3nENsHPvRmCo7Tf4F$NKOyWCMQI7PF0xjJ//0gZK7BljFPFk57hqa196wB5ws=',0,N'cliente',N'',N'',0,1,SYSTIMESTAMP,N'cliente@pixelforge.cl',N'Cliente de prueba',DATE '1998-07-27',N'Av. Providencia 1234, Providencia, Santiago',(SELECT id FROM PF_ROLES WHERE codigo=N'CLIENTE'));

COMMIT;
PROMPT Datos iniciales de PixelForge cargados correctamente.
